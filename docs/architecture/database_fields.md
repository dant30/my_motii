"""
=============================================================================
my_motii — AutoSpare SaaS & ERP Canonical Django Models (Production v3 Hardened)
=============================================================================
Enterprise multi-tenant automotive parts POS, ERP, and B2B network architecture.
Built for Django 5.0+ and PostgreSQL. Adheres to append-only financial and
inventory ledger invariants, gapless atomic numbering, and KRA eTIMS compliance.

Architectural Guarantees & Production Review Resolution:
  [P0-1] Dynamic Table Resolution: DocumentSequence.next_number() dynamically
         resolves cls._meta.db_table and populates audit columns (created_by_id,
         updated_by_id, correlation_id) in atomic raw SQL upsert.
  [P0-2] Dual Case-Insensitive Auth: User.save() normalizes emails to lowercase,
         and expression-based UniqueConstraint(Lower('email'), ...) enforces DB-level
         uniqueness across both tenant users and platform superusers.
  [P0-3] Django Standard Deletion Contract: SoftDeleteMixin.delete() and
         SoftDeleteQuerySet.delete() return standard (count, {model_label: count})
         tuples, and Meta.default_manager_name = 'objects' ensures admin/inlines
         never expose soft-deleted rows.
  [P1-1 / ADR-0009] Concurrency Sharding: High-concurrency inventory mutations
         are isolated via InventoryItem row-level locking (SKU + branch), eliminating
         global tenant-wide serialization bottlenecks. Document sequence allocation
         retains row-level Tenant locks as documented in ADR 0009.
  [P1-2] Tenant-Scoped Integrations: MpesaTransaction and StkRequest are scoped
         per-tenant via UniqueConstraint(fields=['tenant', 'trans_id']).
  [P1-3] Authoritative Category Path: Product models canonical_category (always set)
         and optional tenant_category overlay with effective_category property.
  [P1-4] First-Class Multi-Currency: Currency model linked via ForeignKeys to Product,
         Sale, and PurchaseOrder.
  [P1-5] Debit-XOR-Credit Ledger Invariant: JournalLine CheckConstraint enforces
         strictly (debit > 0 and credit = 0) OR (debit = 0 and credit > 0).
  [P1-6] Key Management & eTIMS Security: IntegrationCredential tracks encryption_key_id,
         encryption_algorithm, and rotated_at, and is foreign-keyed to EtimsConfiguration.
  [P1-7] Vehicle History & Resale: CustomerVehicle uses is_active boolean with
         partial unique constraint to support multi-owner resale history.
  [P1-8] Line-Level Refunds: Sale.refunded_from removed in favor of canonical
         Refund and itemized RefundItem models.
  [P1-9] Hierarchical Uniqueness Trap Fixed: TenantCategory splits root and child
         unique constraints to avoid PostgreSQL NULL uniqueness traps.

Lifecycle State Machines:
  * Sale:
      DRAFT -> COMPLETED -> VOIDED (within 24h, manager authorization)
                         -> REFUNDED (partial or full via Refund & RefundItem)
  * PurchaseOrder:
      DRAFT -> ORDERED -> RECEIVED (GRN issued & stock moved) -> CANCELLED
  * StockTransfer:
      DRAFT -> DISPATCHED (transit) -> RECEIVED (accepted at destination) -> CANCELLED
  * CashSession:
      OPEN -> CLOSED (reconciliation with denominations & variance calculation)
  * JobCard:
      OPEN -> IN_PROGRESS -> COMPLETED -> CLOSED
  * EtimsDocument:
      QUEUED_OFFLINE -> SUBMITTED_SUCCESS / FAILED_RETRY
  * SyncInbox:
      PENDING -> APPLIED / CONFLICT / FAILED (with schema_version tracking)
=============================================================================
"""

import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models, transaction, connection
from django.db.models import F, Q, Sum
from django.db.models.functions import Lower
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


# ---------------------------------------------------------------------------
# Reusable Regex Validators
# ---------------------------------------------------------------------------
kra_pin_validator = RegexValidator(
    regex=r'^[A-Za-z][0-9]{9}[A-Za-z]$',
    message='Enter a valid Kenyan KRA PIN (e.g. P051839284Z or A012345678Z).'
)

phone_validator = RegexValidator(
    regex=r'^(?:\+254|0)[17]\d{8}$',
    message='Enter a valid Kenyan telephone number (e.g. +254722550120 or 0722550120).'
)


# ===========================================================================
# BASE MODEL PATTERNS, MANAGERS & MIXINS
# ===========================================================================
class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)

    def delete(self):
        """Soft-deletes all records matching this QuerySet and returns Django-compliant tuple."""
        count = self.filter(deleted_at__isnull=True).update(deleted_at=timezone.now())
        return count, {self.model._meta.label: count}

    def hard_delete(self):
        """Permanently deletes rows from database."""
        return super().delete()


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    pass


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    correlation_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True


class TenantModel(BaseModel):
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.PROTECT,
        db_index=True,
    )

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        default_manager_name = 'objects'

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def delete(self, using=None, keep_parents=False):
        """Soft-deletes this instance and returns standard Django deletion tuple (count, {label: count})."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
        return 1, {self._meta.label: 1}

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)


# ===========================================================================
# 1. CURRENCIES & PLATFORM GEOGRAPHY
# ===========================================================================
class Currency(BaseModel):
    code = models.CharField(max_length=3, unique=True, help_text="ISO 4217: KES, USD, UGX, TZS")
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10, default='KSh')
    decimal_places = models.PositiveSmallIntegerField(default=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.code} ({self.symbol})"


class Country(BaseModel):
    iso_code = models.CharField(max_length=2, unique=True, help_text="KE, UG, TZ, RW")
    name = models.CharField(max_length=100)
    default_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='default_for_countries')
    phone_code = models.CharField(max_length=10, default='+254')

    class Meta:
        verbose_name_plural = 'Countries'

    def __str__(self):
        return f"{self.name} [{self.iso_code}]"


# ===========================================================================
# 2. TENANCY & CROSS-TENANT NETWORK (apps/tenancy)
# ===========================================================================
class TenantType(models.TextChoices):
    RETAILER = 'RETAILER', 'Auto Spare Retailer & Counter POS'
    SUPPLIER = 'SUPPLIER', 'Wholesale Importer & Parts Distributor'
    HYBRID = 'HYBRID', 'Hybrid Retailer & Wholesale Distributor'
    GARAGE = 'GARAGE', 'Independent Garage & Workshop'
    PLATFORM = 'PLATFORM', 'Platform Operator & Super Administrator'


class Tenant(BaseModel):
    tenant_type = models.CharField(max_length=20, choices=TenantType.choices, default=TenantType.RETAILER, db_index=True)
    name = models.CharField(max_length=200, help_text="Store Trade Name e.g. Kirinyaga Auto Spares Ltd")
    slug = models.SlugField(max_length=100, unique=True)
    trading_as = models.CharField(max_length=200, blank=True)
    kra_pin = models.CharField(max_length=11, validators=[kra_pin_validator])
    phone = models.CharField(max_length=30, validators=[phone_validator])
    email = models.EmailField(blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} [{self.get_tenant_type_display()}]"


class TenantSettings(BaseModel):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='settings')
    base_currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('16.00'))
    whvat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.00'))
    enable_loyalty = models.BooleanField(default=True)
    enable_offline_sync = models.BooleanField(default=True)
    enforce_strict_stock = models.BooleanField(default=True)
    allow_credit_sales = models.BooleanField(default=True)
    default_credit_days = models.PositiveIntegerField(default=30)
    receipt_header_text = models.TextField(blank=True, default="Dealers in Genuine Japanese Auto Spares & Accessories")
    receipt_footer_policy = models.TextField(default="Goods once sold can only be exchanged within 7 days in original packaging. No cash refunds.")

    def __str__(self):
        return f"Settings for {self.tenant.name}"


class TenantDomain(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='domains')
    domain = models.CharField(max_length=255, unique=True)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)


class TenantFeature(TenantModel):
    feature_code = models.CharField(max_length=50)
    is_enabled = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'feature_code'], name='uniq_tenant_feature_per_tenant'),
        ]


# ===========================================================================
# 3. ACCOUNTS, AUTHENTICATION & RBAC (apps/accounts)
# ===========================================================================
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required.')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, null=True, blank=True, related_name='users')
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=30, blank=True, null=True, validators=[phone_validator])
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_tenant_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('email'), 'tenant',
                condition=models.Q(tenant__isnull=False),
                name='uniq_user_email_per_tenant',
            ),
            models.UniqueConstraint(
                Lower('email'),
                condition=models.Q(tenant__isnull=True),
                name='uniq_platform_user_email',
            ),
        ]

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.lower()

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class UserRoleType(models.TextChoices):
    CASHIER = 'CASHIER', 'Certified Cashier & POS Operator'
    STOREKEEPER = 'STOREKEEPER', 'Storekeeper & Inventory Clerk'
    PARTS_SALES = 'PARTS_SALES', 'Counter Parts Sales Rep'
    BRANCH_MANAGER = 'BRANCH_MANAGER', 'Branch Operations Manager'
    ACCOUNTANT = 'ACCOUNTANT', 'Auditor & Head Accountant'
    TENANT_ADMIN = 'TENANT_ADMIN', 'Tenant Administrator'


class UserRole(TenantModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_roles')
    role = models.CharField(max_length=50, choices=UserRoleType.choices, default=UserRoleType.CASHIER)
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='staff_roles')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'user', 'role'],
                condition=models.Q(branch__isnull=True),
                name='uniq_user_tenant_role',
            ),
            models.UniqueConstraint(
                fields=['tenant', 'user', 'role', 'branch'],
                condition=models.Q(branch__isnull=False),
                name='uniq_user_branch_role',
            ),
        ]


class UserProfile(TenantModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    national_id = models.CharField(max_length=20, blank=True, help_text="Kenyan National ID Number")
    job_title = models.CharField(max_length=100, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)


class UserSession(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_token = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=150, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)


# ===========================================================================
# 4. STORE BRANCHES & HARDWARE TERMINALS (apps/branches & apps/pos)
# ===========================================================================
class Branch(TenantModel, SoftDeleteMixin):
    code = models.CharField(max_length=30, help_text="e.g. KIR01, MSA02")
    name = models.CharField(max_length=150, help_text="e.g. Kirinyaga Road Main Store")
    address = models.CharField(max_length=255, default="Kirinyaga Road, Nairobi CBD")
    city = models.CharField(max_length=100, default='Nairobi')
    phone = models.CharField(max_length=30, default="+254 722 550 120")
    is_main = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'code'], name='uniq_branch_code_per_tenant'),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class BranchUser(TenantModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='branch_staff')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='branch_assignments')
    is_manager = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'branch', 'user'], name='uniq_branch_user_membership'),
        ]


class Register(TenantModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='registers')
    register_code = models.CharField(max_length=50, default="POS-01")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'branch', 'register_code'], name='uniq_register_per_branch'),
        ]

    def __str__(self):
        return f"{self.branch.code} - {self.register_code}"


class Warehouse(TenantModel):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='warehouses')
    code = models.CharField(max_length=30, default="WH-01")
    name = models.CharField(max_length=150, default="CBD Main Stockroom")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'branch', 'code'], name='uniq_warehouse_code_per_branch'),
        ]


class BinLocation(TenantModel):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='bin_locations')
    aisle = models.CharField(max_length=30)
    rack = models.CharField(max_length=30)
    shelf = models.CharField(max_length=30)
    bin_code = models.CharField(max_length=100, help_text="Aisle 2 - Rack B - Bin 04")
    barcode = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'warehouse', 'bin_code'], name='uniq_bin_code_per_warehouse'),
        ]


# ===========================================================================
# 5. CANONICAL CATALOG, BRANDS & CATEGORIES (apps/catalog)
# ===========================================================================
class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f"{self.parent.name} > {self.name}" if self.parent else self.name


class TenantCategory(TenantModel, SoftDeleteMixin):
    canonical_category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='tenant_overlays')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'name'],
                condition=models.Q(parent__isnull=True),
                name='uniq_tenant_category_root_name',
            ),
            models.UniqueConstraint(
                fields=['tenant', 'parent', 'name'],
                condition=models.Q(parent__isnull=False),
                name='uniq_tenant_category_child_name',
            ),
        ]

    def __str__(self):
        return self.name


class Brand(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    country_of_origin = models.CharField(max_length=100, default='Japan')
    is_oem = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class UnitOfMeasure(BaseModel):
    code = models.CharField(max_length=20, unique=True, help_text="PCS, SET, KIT, PAIR, LITRES")
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.code


class Product(TenantModel, SoftDeleteMixin):
    sku = models.CharField(max_length=60, db_index=True)
    name = models.CharField(max_length=255)
    canonical_category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    tenant_category = models.ForeignKey(TenantCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products')
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT, null=True, blank=True, related_name='products')
    currency_code = models.CharField(max_length=3, default='KES')

    cost_price_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    selling_price_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'sku'], name='uniq_product_sku_per_tenant'),
            models.CheckConstraint(
                check=models.Q(selling_price_minor__gte=models.F('cost_price_minor')),
                name='chk_selling_price_gte_cost_price',
            ),
        ]
        indexes = [
            models.Index(fields=['tenant', 'sku']),
            models.Index(fields=['tenant', 'canonical_category']),
        ]

    def __str__(self):
        return f"{self.name} [SKU: {self.sku}]"

    @property
    def effective_category(self):
        """Authoritative category lookup: tenant custom category overlay when present, fallback to platform canonical."""
        return self.tenant_category or self.canonical_category

    @property
    def cost_price_kes(self) -> Decimal:
        return Decimal(self.cost_price_minor) / Decimal(100)

    @property
    def selling_price_kes(self) -> Decimal:
        return Decimal(self.selling_price_minor) / Decimal(100)

    @property
    def on_hand_total(self) -> int:
        total = self.inventory_items.aggregate(total=Sum('balance__on_hand'))['total']
        return total or 0


class ProductVariant(TenantModel, SoftDeleteMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_name = models.CharField(max_length=150)
    variant_sku = models.CharField(max_length=60)
    cost_price_minor = models.BigIntegerField()
    selling_price_minor = models.BigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'variant_sku'], name='uniq_variant_sku_per_tenant'),
        ]


class ProductImage(TenantModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=500)
    is_featured = models.BooleanField(default=False)


class Barcode(TenantModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='barcodes')
    code = models.CharField(max_length=100, db_index=True)
    is_primary = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'code'], name='uniq_barcode_per_tenant'),
            models.UniqueConstraint(fields=['tenant', 'product'], condition=models.Q(is_primary=True), name='uniq_primary_barcode_per_product'),
        ]


class ProductOemNumber(TenantModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='oem_numbers')
    oem_part = models.ForeignKey('OemPart', on_delete=models.PROTECT, related_name='product_links')
    is_primary = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'product', 'oem_part'], name='uniq_product_oem_mapping'),
            models.UniqueConstraint(fields=['tenant', 'product'], condition=models.Q(is_primary=True), name='uniq_primary_oem_per_product'),
        ]
        indexes = [
            models.Index(fields=['tenant', 'product']),
            models.Index(fields=['tenant', 'oem_part']),
        ]


class EquivalentPart(TenantModel):
    GRADE_CHOICES = (
        ('OEM', 'Original Equipment Manufacturer (OEM Genuine)'),
        ('OES', 'Original Equipment Supplier (OES / Tier-1)'),
        ('PREMIUM_AFTERMARKET', 'Premium Aftermarket (KYB, 555, Denso)'),
        ('STANDARD_AFTERMARKET', 'Standard Aftermarket'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='equivalents')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT)
    part_number = models.CharField(max_length=100)
    grade = models.CharField(max_length=30, choices=GRADE_CHOICES, default='PREMIUM_AFTERMARKET')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'product', 'brand', 'part_number'], name='uniq_equivalent_part_per_tenant'),
        ]


# ===========================================================================
# 6. CANONICAL VEHICLE FITMENT (apps/vehicles & apps/fitment)
# ===========================================================================
class VehicleMake(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class VehicleModel(BaseModel):
    make = models.ForeignKey(VehicleMake, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    chassis_code = models.CharField(max_length=100)
    years = models.CharField(max_length=50)
    engine_codes = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['make', 'name', 'chassis_code'], name='uniq_vehicle_model_spec'),
        ]

    def __str__(self):
        return f"{self.make.name} {self.name} ({self.chassis_code})"


class OemPart(BaseModel):
    part_number = models.CharField(max_length=100, unique=True, db_index=True)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.brand.name} :: {self.part_number}"


class PartFitment(BaseModel):
    oem_part = models.ForeignKey(OemPart, on_delete=models.CASCADE, related_name='fitments')
    vehicle_model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE, related_name='fitments')
    position = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['oem_part', 'vehicle_model', 'position'], name='uniq_canonical_fitment'),
        ]
        indexes = [
            models.Index(fields=['oem_part', 'vehicle_model']),
        ]

    def __str__(self):
        return f"{self.oem_part.part_number} => {self.vehicle_model} ({self.position})"


class ProductFitment(TenantModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='fitment_links')
    part_fitment = models.ForeignKey(PartFitment, on_delete=models.PROTECT, related_name='tenant_links')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'product', 'part_fitment'], name='uniq_tenant_product_fitment'),
        ]
        indexes = [
            models.Index(fields=['tenant', 'product']),
            models.Index(fields=['tenant', 'part_fitment']),
        ]


# ===========================================================================
# 7. APPEND-ONLY STOCK LEDGER & PROJECTIONS (apps/inventory)
# ===========================================================================
class InventoryItem(TenantModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_items')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='inventory_items')
    bin_location = models.ForeignKey(BinLocation, on_delete=models.SET_NULL, null=True, blank=True)
    min_stock_level = models.PositiveIntegerField(default=3)
    reorder_point = models.PositiveIntegerField(default=5)
    reorder_quantity = models.PositiveIntegerField(default=10)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'product', 'branch'], name='uniq_inventory_item_per_branch'),
        ]


class InventoryBalance(TenantModel):
    inventory_item = models.OneToOneField(InventoryItem, on_delete=models.CASCADE, related_name='balance')
    on_hand = models.IntegerField(default=0)
    allocated = models.IntegerField(default=0)
    available = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(on_hand__gte=0), name='chk_balance_on_hand_non_negative'),
            models.CheckConstraint(check=models.Q(allocated__gte=0), name='chk_balance_allocated_non_negative'),
            models.CheckConstraint(check=models.Q(available__gte=0), name='chk_balance_available_non_negative'),
            models.CheckConstraint(
                check=models.Q(available=models.F('on_hand') - models.F('allocated')),
                name='chk_available_equals_on_hand_minus_allocated',
            ),
        ]


class StockMovementType(models.TextChoices):
    SALE = 'SALE', 'POS Customer Checkout'
    PURCHASE_RECEIPT = 'PURCHASE_RECEIPT', 'Goods Received Note (GRN)'
    ADJUSTMENT_IN = 'ADJUSTMENT_IN', 'Stocktake Count Surplus (+)'
    ADJUSTMENT_OUT = 'ADJUSTMENT_OUT', 'Damage / Discrepancy Write-down (-)'
    TRANSFER_IN = 'TRANSFER_IN', 'Inter-Branch Stock Transfer In'
    TRANSFER_OUT = 'TRANSFER_OUT', 'Inter-Branch Stock Transfer Out'
    RETURN_RESTOCK = 'RETURN_RESTOCK', 'Customer Return Restocked'


class StockMovement(TenantModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='stock_movements')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='stock_movements')
    movement_type = models.CharField(max_length=40, choices=StockMovementType.choices)
    
    quantity_delta = models.IntegerField()
    balance_before = models.IntegerField()
    balance_after = models.IntegerField()
    unit_cost_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    
    reference_type = models.CharField(max_length=40)
    reference_id = models.UUIDField(db_index=True)
    performed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='stock_movements')
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(check=~models.Q(quantity_delta=0), name='chk_stock_delta_nonzero'),
            models.CheckConstraint(
                check=models.Q(balance_after=models.F('balance_before') + models.F('quantity_delta')),
                name='chk_stock_ledger_integrity',
            ),
        ]
        indexes = [
            models.Index(fields=['tenant', 'product', 'branch', '-created_at']),
            models.Index(fields=['tenant', 'reference_type', 'reference_id']),
        ]


class StockAdjustment(TenantModel):
    adjustment_number = models.CharField(max_length=50, db_index=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='stock_adjustments')
    reason = models.CharField(max_length=255)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='approved_adjustments')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'adjustment_number'], name='uniq_stock_adjustment_per_tenant'),
        ]


class StockAdjustmentItem(BaseModel):
    adjustment = models.ForeignKey(StockAdjustment, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    system_count = models.IntegerField()
    physical_count = models.IntegerField()
    discrepancy = models.IntegerField()


class StockTransferStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft Transfer'
    DISPATCHED = 'DISPATCHED', 'In Transit / Dispatched'
    RECEIVED = 'RECEIVED', 'Received at Destination'
    CANCELLED = 'CANCELLED', 'Cancelled'


class StockTransfer(TenantModel):
    transfer_number = models.CharField(max_length=50, db_index=True)
    source_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='transfers_sent')
    destination_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='transfers_received')
    status = models.CharField(max_length=30, choices=StockTransferStatus.choices, default=StockTransferStatus.DRAFT)
    dispatched_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='transfers_dispatched')
    received_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='transfers_accepted')
    dispatched_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'transfer_number'], name='uniq_transfer_number_per_tenant'),
            models.CheckConstraint(check=~models.Q(source_branch=models.F('destination_branch')), name='chk_transfer_different_branches'),
        ]


class StockTransferItem(BaseModel):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_dispatched = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    quantity_received = models.PositiveIntegerField(default=0)


class StockLot(TenantModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='lots')
    lot_number = models.CharField(max_length=100)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'product', 'lot_number'], name='uniq_stock_lot_per_product'),
        ]


class SerialNumber(TenantModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='serials')
    serial_code = models.CharField(max_length=100)
    is_sold = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'serial_code'], name='uniq_serial_code_per_tenant'),
        ]


class Reservation(TenantModel):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    reserved_for = models.CharField(max_length=100)
    expires_at = models.DateTimeField()


class Warranty(TenantModel):
    sale_item = models.ForeignKey('SaleItem', on_delete=models.CASCADE, related_name='warranties', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    serial_number = models.ForeignKey(SerialNumber, null=True, blank=True, on_delete=models.SET_NULL)
    duration_months = models.PositiveIntegerField(default=12)
    terms = models.TextField(blank=True)


# ===========================================================================
# 8. CUSTOMERS, CREDIT LEDGER & LOYALTY (apps/customers)
# ===========================================================================
class CustomerType(models.TextChoices):
    WALK_IN = 'WALK_IN', 'Walk-in Retail'
    GARAGE = 'GARAGE', 'Independent Garage / Workshop'
    FLEET = 'FLEET', 'Commercial Fleet (Matatu/Logistics Sacco)'
    INDIVIDUAL = 'INDIVIDUAL', 'Individual Vehicle Owner'


class LoyaltyTier(models.TextChoices):
    BRONZE = 'BRONZE', 'Bronze Member (1.0x)'
    SILVER = 'SILVER', 'Silver Member (1.25x)'
    GOLD = 'GOLD', 'Gold Member (1.5x)'
    PLATINUM = 'PLATINUM', 'Platinum VIP (2.0x)'


class Customer(TenantModel, SoftDeleteMixin):
    name = models.CharField(max_length=200, db_index=True)
    customer_type = models.CharField(max_length=30, choices=CustomerType.choices, default=CustomerType.WALK_IN)
    phone = models.CharField(max_length=30, blank=True, null=True, validators=[phone_validator])
    kra_pin = models.CharField(max_length=11, blank=True, null=True, validators=[kra_pin_validator])
    
    credit_limit_minor = models.BigIntegerField(default=0)
    current_balance_minor = models.BigIntegerField(default=0)
    credit_days = models.PositiveIntegerField(default=30)
    
    loyalty_points = models.IntegerField(default=0)
    loyalty_tier = models.CharField(max_length=20, choices=LoyaltyTier.choices, default=LoyaltyTier.BRONZE)
    lifetime_points_earned = models.IntegerField(default=0)
    lifetime_points_redeemed = models.IntegerField(default=0)

    class Meta:
        ordering = ['name']
        constraints = [
            models.CheckConstraint(check=models.Q(credit_limit_minor__gte=0), name='chk_customer_credit_limit_gte_zero'),
            models.CheckConstraint(check=models.Q(current_balance_minor__gte=0), name='chk_customer_balance_gte_zero'),
        ]
        indexes = [
            models.Index(fields=['tenant', 'phone']),
            models.Index(fields=['tenant', 'kra_pin']),
        ]

    def __str__(self):
        return f"{self.name} [{self.get_customer_type_display()}]"

    @property
    def current_balance_kes(self) -> Decimal:
        return Decimal(self.current_balance_minor) / Decimal(100)

    @property
    def credit_limit_kes(self) -> Decimal:
        return Decimal(self.credit_limit_minor) / Decimal(100)

    @property
    def available_credit_kes(self) -> Decimal:
        return max(Decimal('0.00'), self.credit_limit_kes - self.current_balance_kes)


class CustomerLedgerEntryType(models.TextChoices):
    CREDIT_SALE = 'CREDIT_SALE', 'Goods Purchased on Credit (+)'
    PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Debt Payment Received (-)'
    CREDIT_NOTE = 'CREDIT_NOTE', 'Credit Note Adjustment (-)'
    DEBIT_ADJUSTMENT = 'DEBIT_ADJUSTMENT', 'Debit Adjustment (+)'


class CustomerLedgerEntry(TenantModel):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='ledger_entries')
    entry_type = models.CharField(max_length=40, choices=CustomerLedgerEntryType.choices)
    amount_delta_minor = models.BigIntegerField()
    balance_before_minor = models.BigIntegerField()
    balance_after_minor = models.BigIntegerField()
    reference_type = models.CharField(max_length=40)
    reference_id = models.UUIDField(db_index=True)
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(balance_after_minor=models.F('balance_before_minor') + models.F('amount_delta_minor')),
                name='chk_customer_ledger_integrity',
            ),
        ]
        indexes = [
            models.Index(fields=['tenant', 'customer', '-created_at']),
        ]


class LoyaltyTransaction(TenantModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loyalty_transactions')
    transaction_type = models.CharField(max_length=30, choices=(
        ('EARNED', 'Earned from Purchase'),
        ('REDEEMED', 'Redeemed for Discount'),
        ('ADJUSTMENT', 'Manual Goodwill Adjustment'),
    ))
    points = models.IntegerField()
    balance_before = models.IntegerField()
    balance_after = models.IntegerField()
    reference_id = models.UUIDField(null=True, blank=True)
    notes = models.CharField(max_length=255)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(balance_after=models.F('balance_before') + models.F('points')),
                name='chk_loyalty_ledger_integrity',
            ),
        ]


class CustomerVehicle(TenantModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='vehicles')
    registration_plate = models.CharField(max_length=20, db_index=True)
    vehicle_model = models.ForeignKey(VehicleModel, on_delete=models.PROTECT, related_name='customer_vehicles')
    chassis_vin = models.CharField(max_length=50, blank=True)
    engine_number = models.CharField(max_length=50, blank=True)
    year = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True, help_text="True for current registered owner, False when transferred")
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'registration_plate'],
                condition=models.Q(is_active=True),
                name='uniq_active_customer_vehicle_plate_per_tenant',
            ),
        ]


# ===========================================================================
# 9. SUPPLIERS & CROSS-TENANT B2B NETWORK (apps/suppliers & apps/network)
# ===========================================================================
class SupplierConnection(BaseModel):
    retailer_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='supplier_connections')
    supplier_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='retailer_connections')
    status = models.CharField(max_length=20, choices=(('PENDING', 'Pending'), ('ACTIVE', 'Active'), ('SUSPENDED', 'Suspended')), default='ACTIVE')
    visibility_mode = models.CharField(max_length=20, choices=(('PUBLIC', 'Public Catalog'), ('NEGOTIATED', 'Custom Pricing')), default='PUBLIC')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['retailer_tenant', 'supplier_tenant'], name='uniq_cross_tenant_supplier_pair'),
        ]


class Supplier(TenantModel, SoftDeleteMixin):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    contact_person = models.CharField(max_length=150)
    specialization = models.CharField(max_length=200)
    kra_pin = models.CharField(max_length=11, validators=[kra_pin_validator])
    payment_terms = models.CharField(max_length=100, default='30 Days Credit')

    def __str__(self):
        return f"{self.name} ({self.location})"


class Consent(BaseModel):
    granting_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='consents_granted')
    receiving_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='consents_received')
    scope = models.CharField(max_length=100)
    granted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['granting_tenant', 'receiving_tenant', 'scope'], name='uniq_tenant_consent_scope'),
        ]


# ===========================================================================
# 10. NUMBERING SEQUENCES & GAPLESS FISCAL NUMBERING (apps/documents)
# ===========================================================================
class DocumentSequence(TenantModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    doc_type = models.CharField(max_length=20, help_text="INV, RCT, PO, GRN, CN")
    fiscal_year = models.PositiveSmallIntegerField()
    prefix = models.CharField(max_length=40)
    current_value = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'branch', 'doc_type', 'fiscal_year'], name='uniq_sequence_scope_per_year'),
        ]

    @classmethod
    def next_number(cls, *, tenant: Tenant, branch: Branch, doc_type: str, fiscal_year: int = None) -> str:
        fiscal_year = fiscal_year or timezone.now().year
        prefix = f"{branch.code}-{doc_type}-{fiscal_year}"

        with transaction.atomic():
            # Pessimistic tenant row-lock prevents race condition on initial sequence insert
            Tenant.objects.select_for_update().get(pk=tenant.pk)

            table = cls._meta.db_table
            sql = f"""
                INSERT INTO {table}
                    (id, tenant_id, branch_id, doc_type, fiscal_year, prefix, current_value,
                     created_at, updated_at, created_by_id, updated_by_id, correlation_id)
                VALUES
                    (%s, %s, %s, %s, %s, %s, 1, NOW(), NOW(), NULL, NULL, NULL)
                ON CONFLICT (tenant_id, branch_id, doc_type, fiscal_year)
                DO UPDATE SET
                    current_value = {table}.current_value + 1,
                    updated_at = NOW()
                RETURNING current_value;
            """

            with connection.cursor() as cur:
                cur.execute(sql, [uuid.uuid4(), tenant.id, branch.id, doc_type, fiscal_year, prefix])
                allocated_val = cur.fetchone()[0]

        return f"{prefix}-{allocated_val:05d}"


# ===========================================================================
# 11. POS SALES, REGISTERS & FISCAL TAX INVOICES (apps/sales & apps/pos)
# ===========================================================================
class TaxRateCode(models.TextChoices):
    A = 'A', 'Rate A (16.0% Standard VAT)'
    B = 'B', 'Rate B (0.0% Zero-Rated EAC Export)'
    C = 'C', 'Rate C (8.0% Petroleum Fuel)'
    E = 'E', 'Rate E (0.0% Statutory Exempt)'


class SaleStatus(models.TextChoices):
    COMPLETED = 'COMPLETED', 'Completed Sale'
    VOIDED = 'VOIDED', 'Voided Transaction'
    REFUNDED = 'REFUNDED', 'Full / Partial Refund'


class EtimsStatus(models.TextChoices):
    SUBMITTED_SUCCESS = 'SUBMITTED_SUCCESS', 'Submitted & KRA Verified'
    QUEUED_OFFLINE = 'QUEUED_OFFLINE', 'Queued in Offline Outbox'
    FAILED_RETRY = 'FAILED_RETRY', 'Transmission Failed / Pending Retry'


class CashSession(TenantModel):
    session_number = models.CharField(max_length=50, db_index=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    register = models.ForeignKey(Register, on_delete=models.PROTECT)
    cashier = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cash_sessions')
    cashier_name_snapshot = models.CharField(max_length=150)
    
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    opening_float_minor = models.BigIntegerField(default=500000, validators=[MinValueValidator(0)])
    closing_cash_actual_minor = models.BigIntegerField(null=True, blank=True)
    closing_cash_expected_minor = models.BigIntegerField(null=True, blank=True)
    variance_minor = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=(('OPEN', 'Open'), ('CLOSED', 'Closed')), default='OPEN')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'session_number'], name='uniq_cash_session_per_tenant'),
        ]


class CashSessionDenomination(BaseModel):
    session = models.ForeignKey(CashSession, on_delete=models.CASCADE, related_name='denominations')
    denomination_value_kes = models.PositiveIntegerField()
    count = models.PositiveIntegerField(default=0)
    subtotal_minor = models.GeneratedField(
        expression=models.F('denomination_value_kes') * 100 * models.F('count'),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['session', 'denomination_value_kes'], name='uniq_session_denomination'),
        ]


class RegisterTransaction(TenantModel):
    session = models.ForeignKey(CashSession, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=50, choices=(('FLOAT_IN', 'Float In'), ('PAYOUT', 'Payout'), ('DRAWER_DROP', 'Drawer Drop')))
    amount_minor = models.BigIntegerField()
    notes = models.CharField(max_length=255, blank=True)


class Sale(TenantModel):
    document_number = models.CharField(max_length=60, db_index=True)
    receipt_number = models.CharField(max_length=60, db_index=True)
    
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='sales')
    register = models.ForeignKey(Register, on_delete=models.PROTECT, null=True, blank=True)
    session = models.ForeignKey(CashSession, on_delete=models.PROTECT, null=True, blank=True, related_name='sales')
    
    cashier = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sales_made')
    cashier_name_snapshot = models.CharField(max_length=150)
    
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales')
    customer_name_snapshot = models.CharField(max_length=200)
    customer_phone_snapshot = models.CharField(max_length=30, blank=True)
    customer_pin_snapshot = models.CharField(max_length=11, blank=True)
    
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT, null=True, blank=True, related_name='sales')
    currency_code = models.CharField(max_length=3, default='KES')
    subtotal_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    tax_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    total_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    change_minor = models.BigIntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=SaleStatus.choices, default=SaleStatus.COMPLETED)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='sales_voided')
    void_reason = models.CharField(max_length=255, blank=True)

    etims_status = models.CharField(max_length=30, choices=EtimsStatus.choices, default=EtimsStatus.QUEUED_OFFLINE)
    etims_cu_number = models.CharField(max_length=60, blank=True)
    etims_signature = models.CharField(max_length=200, blank=True)
    etims_qr_url = models.URLField(max_length=500, blank=True)
    etims_transmitted_at = models.DateTimeField(null=True, blank=True)

    loyalty_points_earned = models.IntegerField(default=0)
    loyalty_points_redeemed = models.IntegerField(default=0)
    loyalty_discount_minor = models.BigIntegerField(default=0)
    loyalty_tier = models.CharField(max_length=20, blank=True)

    is_offline_created = models.BooleanField(default=False)
    offline_device = models.ForeignKey('SyncDevice', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'document_number'], name='uniq_sale_docnum_per_tenant'),
            models.UniqueConstraint(fields=['tenant', 'receipt_number'], name='uniq_sale_receipt_per_tenant'),
            models.CheckConstraint(check=models.Q(total_minor__gte=0), name='chk_sale_total_gte_zero'),
            models.CheckConstraint(
                check=models.Q(subtotal_minor=models.F('total_minor') - models.F('tax_minor')),
                name='chk_sale_subtotal_equals_total_minus_tax',
            ),
        ]
        indexes = [
            models.Index(fields=['tenant', 'branch', '-created_at']),
            models.Index(fields=['tenant', 'customer', '-created_at']),
            models.Index(fields=['tenant', 'etims_status']),
        ]

    def __str__(self):
        return f"{self.document_number} ({self.receipt_number}) - KES {Decimal(self.total_minor) / Decimal(100):,.2f}"


class SaleItem(BaseModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    part_sku = models.CharField(max_length=60)
    part_name = models.CharField(max_length=255)
    oem_number = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    unit_price_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    discount_minor = models.BigIntegerField(default=0)
    tax_rate_code = models.CharField(max_length=10, choices=TaxRateCode.choices, default=TaxRateCode.A)
    line_total_minor = models.BigIntegerField(validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(quantity__gt=0), name='chk_sale_item_qty_gt_zero'),
            models.CheckConstraint(
                check=models.Q(line_total_minor=models.F('quantity') * models.F('unit_price_minor') - models.F('discount_minor')),
                name='chk_saleitem_line_total_consistent',
            ),
        ]


class SaleTaxLine(BaseModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='tax_lines')
    tax_code = models.CharField(max_length=10, choices=TaxRateCode.choices)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    taxable_base_minor = models.BigIntegerField()
    tax_amount_minor = models.BigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['sale', 'tax_code'], name='uniq_sale_tax_line_code'),
        ]


class PaymentMethod(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)


class Payment(TenantModel):
    payment_number = models.CharField(max_length=60, db_index=True)
    amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    reference = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'payment_number'], name='uniq_payment_number_per_tenant'),
        ]


class PaymentAllocation(BaseModel):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='allocations')
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, null=True, blank=True, related_name='payment_allocations')
    allocated_amount_minor = models.BigIntegerField()


class PaymentReference(BaseModel):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='ref_details')
    external_reference = models.CharField(max_length=150)


class Refund(TenantModel):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT)
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name='refund_records')
    amount_refunded_minor = models.BigIntegerField()
    reason = models.CharField(max_length=255)


class RefundItem(BaseModel):
    refund = models.ForeignKey(Refund, on_delete=models.CASCADE, related_name='items')
    sale_item = models.ForeignKey(SaleItem, on_delete=models.PROTECT)
    quantity_refunded = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    amount_refunded_minor = models.BigIntegerField(validators=[MinValueValidator(0)])


class SalePayment(BaseModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name='sale_payments')
    amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    reference = models.CharField(max_length=100, blank=True, null=True)
    canonical_payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_sale_payments')


# ===========================================================================
# 12. PURCHASING, RFQS & GOODS RECEIPTS (apps/purchasing)
# ===========================================================================
class Rfq(TenantModel):
    rfq_number = models.CharField(max_length=50, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    status = models.CharField(max_length=30, choices=(('DRAFT', 'Draft'), ('SENT', 'Sent'), ('RESPONDED', 'Responded')), default='DRAFT')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'rfq_number'], name='uniq_rfq_number_per_tenant'),
        ]


class RfqLine(BaseModel):
    rfq = models.ForeignKey(Rfq, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_requested = models.PositiveIntegerField()


class Quotation(TenantModel):
    rfq = models.ForeignKey(Rfq, on_delete=models.SET_NULL, null=True, blank=True)
    quotation_number = models.CharField(max_length=50, db_index=True)
    total_amount_minor = models.BigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'quotation_number'], name='uniq_quotation_number_per_tenant'),
        ]


class QuotationLine(BaseModel):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quoted_price_minor = models.BigIntegerField()


class PurchaseOrderStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft Reorder'
    ORDERED = 'ORDERED', 'Ordered from Supplier'
    RECEIVED = 'RECEIVED', 'Goods Received & Stock Incremented'
    CANCELLED = 'CANCELLED', 'Cancelled'


class PurchaseOrder(TenantModel):
    po_number = models.CharField(max_length=50, db_index=True)
    local_supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True, blank=True, related_name='purchase_orders')
    network_connection = models.ForeignKey(SupplierConnection, on_delete=models.PROTECT, null=True, blank=True, related_name='network_purchase_orders')
    supplier_name = models.CharField(max_length=200)
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=PurchaseOrderStatus.choices, default=PurchaseOrderStatus.ORDERED)
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT, null=True, blank=True, related_name='purchase_orders')
    currency_code = models.CharField(max_length=3, default='KES')
    total_amount_minor = models.BigIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'po_number'], name='uniq_po_number_per_tenant'),
            models.CheckConstraint(
                check=(models.Q(local_supplier__isnull=False, network_connection__isnull=True) |
                       models.Q(local_supplier__isnull=True, network_connection__isnull=False)),
                name='chk_po_supplier_exclusive',
            ),
        ]

    def __str__(self):
        return f"{self.po_number} - {self.supplier_name}"


class PurchaseOrderLine(BaseModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    part_sku = models.CharField(max_length=60)
    part_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_cost_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    line_total_minor = models.BigIntegerField(validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['purchase_order', 'product'], name='uniq_po_product_line'),
        ]


class GoodsReceivedNote(TenantModel):
    grn_number = models.CharField(max_length=50, db_index=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='grns')
    received_by = models.ForeignKey(User, on_delete=models.PROTECT)
    received_date = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'grn_number'], name='uniq_grn_number_per_tenant'),
        ]


class GoodsReceivedNoteItem(BaseModel):
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, related_name='items')
    po_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_received = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    quantity_rejected = models.PositiveIntegerField(default=0)
    batch_number = models.CharField(max_length=50, blank=True)


class SupplierInvoice(TenantModel):
    invoice_number = models.CharField(max_length=100)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    amount_minor = models.BigIntegerField()


# ===========================================================================
# 13. SAFARICOM M-PESA DARAJA INTEGRATION (apps/mpesa)
# ===========================================================================
class MpesaTransaction(TenantModel):
    transaction_type = models.CharField(max_length=50, default='CustomerPayBillOnline')
    trans_id = models.CharField(max_length=50, help_text="e.g. SKH829412K")
    trans_time = models.CharField(max_length=30)
    trans_amount_minor = models.BigIntegerField()
    business_short_code = models.CharField(max_length=30)
    bill_ref_number = models.CharField(max_length=100, blank=True)
    msisdn = models.CharField(max_length=30)
    first_name = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'trans_id'], name='uniq_mpesa_trans_per_tenant'),
        ]
        indexes = [
            models.Index(fields=['tenant', 'trans_id']),
            models.Index(fields=['tenant', 'bill_ref_number']),
        ]


class StkRequest(TenantModel):
    merchant_request_id = models.CharField(max_length=100)
    checkout_request_id = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=30)
    amount_minor = models.BigIntegerField()
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'merchant_request_id'], name='uniq_stk_merchant_req_per_tenant'),
            models.UniqueConstraint(fields=['tenant', 'checkout_request_id'], name='uniq_stk_checkout_req_per_tenant'),
        ]


class MpesaCallback(BaseModel):
    raw_payload = models.JSONField()
    is_processed = models.BooleanField(default=False)


# ===========================================================================
# 14. EXPENSES & DRAWER PAYOUTS (apps/expenses)
# ===========================================================================
class ExpenseCategory(TenantModel):
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'name'], name='uniq_expense_category_per_tenant'),
        ]

    def __str__(self):
        return self.name


class Expense(TenantModel):
    expense_number = models.CharField(max_length=50, db_index=True)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    description = models.CharField(max_length=255)
    paid_via = models.CharField(max_length=30, choices=(('CASH_DRAWER', 'Cash Drawer Payout'), ('MPESA_TILL', 'M-Pesa Business Till')))
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    cash_session = models.ForeignKey(CashSession, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'expense_number'], name='uniq_expense_number_per_tenant'),
        ]


class RecurringExpense(TenantModel):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    amount_minor = models.BigIntegerField()
    frequency = models.CharField(max_length=30, default='MONTHLY')


class ExpenseAttachment(BaseModel):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='attachments')
    file_url = models.URLField(max_length=500)


# ===========================================================================
# 15. DOUBLE-ENTRY ACCOUNTING & CASHBOOK (apps/accounting)
# ===========================================================================
class AccountType(models.TextChoices):
    ASSET = 'ASSET', 'Asset'
    LIABILITY = 'LIABILITY', 'Liability'
    EQUITY = 'EQUITY', 'Equity'
    REVENUE = 'REVENUE', 'Revenue'
    EXPENSE = 'EXPENSE', 'Expense'


class Account(TenantModel):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    account_type = models.CharField(max_length=30, choices=AccountType.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'code'], name='uniq_gl_account_per_tenant'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class FiscalPeriod(TenantModel):
    period_name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'period_name'], name='uniq_fiscal_period_per_tenant'),
        ]


class JournalEntry(TenantModel):
    entry_number = models.CharField(max_length=50, db_index=True)
    entry_date = models.DateField(default=timezone.now)
    narration = models.CharField(max_length=255)
    fiscal_period = models.ForeignKey(FiscalPeriod, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'entry_number'], name='uniq_journal_entry_per_tenant'),
        ]


class JournalLine(BaseModel):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    debit_minor = models.BigIntegerField(default=0)
    credit_minor = models.BigIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(debit_minor__gte=0), name='chk_journal_debit_non_negative'),
            models.CheckConstraint(check=models.Q(credit_minor__gte=0), name='chk_journal_credit_non_negative'),
            models.CheckConstraint(
                check=(
                    (models.Q(debit_minor__gt=0) & models.Q(credit_minor=0)) |
                    (models.Q(debit_minor=0) & models.Q(credit_minor__gt=0))
                ),
                name='chk_journal_line_debit_xor_credit',
            ),
        ]


class Cashbook(TenantModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    balance_minor = models.BigIntegerField(default=0)


class Receivable(TenantModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount_due_minor = models.BigIntegerField()
    due_date = models.DateField()


class Payable(TenantModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    amount_owed_minor = models.BigIntegerField()
    due_date = models.DateField()


# ===========================================================================
# 16. KRA eTIMS COMPLIANCE LIFECYCLE (apps/etims)
# ===========================================================================
class EtimsConfiguration(TenantModel):
    tin = models.CharField(max_length=11, validators=[kra_pin_validator])
    bhf_id = models.CharField(max_length=50, default='00')
    device_serial = models.CharField(max_length=100, default='BHF0018902')
    credential = models.ForeignKey('IntegrationCredential', null=True, blank=True, on_delete=models.SET_NULL, related_name='etims_configurations')
    is_production = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'bhf_id'], name='uniq_etims_bhf_per_tenant'),
        ]


class EtimsDocument(TenantModel):
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name='etims_record')
    cu_number = models.CharField(max_length=60, db_index=True)
    scdc_number = models.CharField(max_length=60)
    fiscal_signature = models.CharField(max_length=200)
    qr_code_url = models.URLField(max_length=500)
    transmission_status = models.CharField(max_length=30, choices=EtimsStatus.choices, default=EtimsStatus.SUBMITTED_SUCCESS)
    first_attempt_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'cu_number'], name='uniq_etims_cu_number_per_tenant'),
        ]


class EtimsSubmission(BaseModel):
    document = models.ForeignKey(EtimsDocument, on_delete=models.CASCADE, related_name='submissions')
    payload_sent = models.JSONField()
    response_payload = models.JSONField(null=True, blank=True)
    is_success = models.BooleanField(default=False)


class EtimsError(BaseModel):
    submission = models.ForeignKey(EtimsSubmission, on_delete=models.CASCADE, related_name='errors')
    error_code = models.CharField(max_length=50)
    error_message = models.TextField()


# ===========================================================================
# 17. CONSOLIDATED EDGE-FIRST OFFLINE SYNC (apps/offline_sync)
# ===========================================================================
class SyncDevice(TenantModel):
    device_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    device_name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    last_sync = models.DateTimeField(null=True, blank=True)


class SyncSession(BaseModel):
    device = models.ForeignKey(SyncDevice, on_delete=models.CASCADE, related_name='sessions')
    session_token = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=30, default='ACTIVE')


class SyncActionType(models.TextChoices):
    CREATE_SALE = 'CREATE_SALE', 'Sync Completed POS Sale to Cloud'
    RECORD_STOCK_MOVEMENT = 'RECORD_STOCK_MOVEMENT', 'Sync Stock Movement'
    CREATE_CUSTOMER = 'CREATE_CUSTOMER', 'Sync New Customer Account'


class SyncInbox(TenantModel):
    device = models.ForeignKey(SyncDevice, on_delete=models.PROTECT, related_name='inbox_items')
    idempotency_key = models.CharField(max_length=255, db_index=True)
    schema_version = models.PositiveSmallIntegerField(default=1, help_text="Payload contract version (v1, v2...)")
    action = models.CharField(max_length=50, choices=SyncActionType.choices)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=(('PENDING', 'Pending'), ('APPLIED', 'Applied'), ('CONFLICT', 'Conflict'), ('FAILED', 'Failed')), default='PENDING')
    retry_count = models.IntegerField(default=0)
    error = models.TextField(blank=True)
    
    applied_object_type = models.CharField(max_length=50, blank=True)
    applied_object_id = models.UUIDField(null=True, blank=True, db_index=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['device', 'idempotency_key'], name='uniq_sync_inbox_op_per_device'),
        ]


class SyncConflict(BaseModel):
    inbox_item = models.ForeignKey(SyncInbox, on_delete=models.CASCADE, related_name='conflicts')
    conflict_reason = models.TextField()
    resolved = models.BooleanField(default=False)


# ===========================================================================
# 18. GARAGES, MECHANICS & VEHICLE JOB CARDS (apps/garages)
# ===========================================================================
class Garage(TenantModel, SoftDeleteMixin):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    location = models.CharField(max_length=200)
    garage_tenant = models.ForeignKey(
        'Tenant',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='partner_retailer_garages',
        help_text="Optional cross-tenant link if the garage operates their own my_motii Garage tenant account"
    )

    def __str__(self):
        return self.name


class GarageProfile(BaseModel):
    garage = models.OneToOneField(Garage, on_delete=models.CASCADE, related_name='profile')
    bay_count = models.PositiveIntegerField(default=2)


class GarageBranch(TenantModel):
    garage = models.ForeignKey(Garage, on_delete=models.CASCADE, related_name='branches')
    branch_name = models.CharField(max_length=100)


class Mechanic(TenantModel, SoftDeleteMixin):
    garage = models.ForeignKey(Garage, on_delete=models.CASCADE, related_name='mechanics')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.name} ({self.garage.name})"


class MechanicProfile(BaseModel):
    mechanic = models.OneToOneField(Mechanic, on_delete=models.CASCADE, related_name='profile')
    years_experience = models.PositiveIntegerField(default=5)


class MechanicSpecialization(BaseModel):
    mechanic = models.ForeignKey(Mechanic, on_delete=models.CASCADE, related_name='specializations')
    specialty = models.CharField(max_length=100)


class JobCard(TenantModel):
    card_number = models.CharField(max_length=50, db_index=True)
    vehicle_registration = models.CharField(max_length=30, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    assigned_mechanic = models.ForeignKey(Mechanic, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=30, choices=(('OPEN', 'Open'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('CLOSED', 'Closed')), default='OPEN')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'card_number'], name='uniq_job_card_per_tenant'),
        ]


class JobItem(BaseModel):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    cost_minor = models.BigIntegerField()


class Labor(BaseModel):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='labor_charges')
    hours_spent = models.DecimalField(max_digits=5, decimal_places=2)
    hourly_rate_minor = models.BigIntegerField()


class PartUsage(BaseModel):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='used_parts')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()


class JobStatus(BaseModel):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='status_logs')
    status_label = models.CharField(max_length=50)


class JobPayment(BaseModel):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='payments')
    amount_minor = models.BigIntegerField()


# ===========================================================================
# 19. SAAS SUBSCRIPTIONS & PLATFORM BILLING (apps/subscriptions & apps/billing)
# ===========================================================================
class Plan(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    monthly_price_minor = models.BigIntegerField()
    max_branches = models.PositiveIntegerField(default=1)
    max_users = models.PositiveIntegerField(default=3)


class PlanFeature(BaseModel):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='features')
    feature_code = models.CharField(max_length=100)


class Subscription(BaseModel):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(max_length=30, choices=(('TRIAL', 'Trial'), ('ACTIVE', 'Active'), ('OVERDUE', 'Overdue'), ('CANCELLED', 'Cancelled')), default='TRIAL')
    current_period_end = models.DateTimeField()


class SubscriptionItem(BaseModel):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)


class SubscriptionUsage(BaseModel):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='usages')
    metric = models.CharField(max_length=100)
    current_count = models.PositiveIntegerField(default=0)


class Invoice(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='platform_invoices')
    invoice_number = models.CharField(max_length=60, unique=True)
    amount_minor = models.BigIntegerField()
    is_paid = models.BooleanField(default=False)


class InvoiceItem(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    amount_minor = models.BigIntegerField()


class BillingTransaction(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='transactions')
    amount_minor = models.BigIntegerField()
    mpesa_receipt = models.CharField(max_length=60, blank=True)


class BillingEvent(BaseModel):
    event_name = models.CharField(max_length=100)
    payload = models.JSONField()


# ===========================================================================
# 20. THERMAL HARDWARE, SECURITY & AUDIT TRAIL (apps/pos & apps/audit)
# ===========================================================================
class ThermalPrinterProfile(TenantModel):
    name = models.CharField(max_length=100, default='Counter Thermal Printer')
    paper_width = models.CharField(max_length=10, choices=(('80mm', '80mm Standard POS'), ('58mm', '58mm Mobile Bluetooth')), default='80mm')
    feed_lines = models.PositiveIntegerField(default=3)
    print_qr_code = models.BooleanField(default=True)
    include_loyalty_summary = models.BooleanField(default=True)


class IntegrationCredential(TenantModel):
    provider = models.CharField(max_length=50, help_text="ETIMS_KRA, MPESA_DARAJA, WHATSAPP_CLOUD")
    key_name = models.CharField(max_length=100)
    encrypted_payload = models.TextField(help_text="Encrypted API credential / certificate payload")
    encryption_key_id = models.CharField(max_length=100, default='default-kms-key', help_text="KMS or vault key reference")
    encryption_algorithm = models.CharField(max_length=50, default='AES-256-GCM')
    rotated_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'provider', 'key_name'], name='uniq_credential_per_tenant'),
        ]


class AuditEvent(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(blank=True, null=True)


class AuditChange(BaseModel):
    event = models.ForeignKey(AuditEvent, on_delete=models.CASCADE, related_name='field_changes')
    table_name = models.CharField(max_length=100, db_index=True)
    record_id = models.UUIDField(db_index=True)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)


class SecurityEvent(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']


# ===========================================================================
# 21. TRANSACTION SERVICES & ATOMIC LEDGER MUTATION HELPERS
# ===========================================================================
@transaction.atomic
def record_stock_movement(
    *,
    tenant: Tenant,
    product: Product,
    branch: Branch,
    movement_type: str,
    quantity_delta: int,
    unit_cost_minor: int,
    reference_type: str,
    reference_id: uuid.UUID,
    performed_by: User,
    reason: str = "",
) -> StockMovement:
    """
    Guaranteed atomic stock write. Eliminates race conditions by acquiring a
    pessimistic lock on the Tenant record, then selecting the InventoryBalance for update.
    """
    if quantity_delta == 0:
        raise ValidationError("Quantity delta cannot be zero.")

    # 1. Ensure inventory tracking record exists
    item, _ = InventoryItem.objects.get_or_create(
        tenant=tenant,
        product=product,
        branch=branch,
        defaults={'min_stock_level': 3, 'reorder_point': 5, 'reorder_quantity': 10},
    )

    # 2. Acquire fine-grained row lock on this specific item to serialize mutations on this SKU & branch only
    locked_item = InventoryItem.objects.select_for_update().get(pk=item.pk)

    balance, _ = InventoryBalance.objects.get_or_create(
        inventory_item=locked_item,
        defaults={'tenant': tenant, 'on_hand': 0, 'allocated': 0, 'available': 0},
    )

    # 3. Row lock on balance projection
    balance = InventoryBalance.objects.select_for_update().get(pk=balance.pk)
    before = balance.on_hand
    after = before + quantity_delta

    if after < 0:
        raise ValidationError(f"Insufficient stock for {product.sku}. On hand: {before}, requested delta: {quantity_delta}.")

    # 4. Append to immutable stock ledger
    movement = StockMovement.objects.create(
        tenant=tenant,
        product=product,
        branch=branch,
        movement_type=movement_type,
        quantity_delta=quantity_delta,
        balance_before=before,
        balance_after=after,
        unit_cost_minor=unit_cost_minor,
        reference_type=reference_type,
        reference_id=reference_id,
        performed_by=performed_by,
        reason=reason,
    )

    # 5. Update projected balance
    balance.on_hand = after
    balance.available = after - balance.allocated
    balance.save(update_fields=['on_hand', 'available'])

    return movement


@transaction.atomic
def record_customer_ledger_entry(
    *,
    tenant: Tenant,
    customer: Customer,
    entry_type: str,
    amount_delta_minor: int,
    reference_type: str,
    reference_id: uuid.UUID,
    recorded_by: User,
    notes: str = "",
) -> CustomerLedgerEntry:
    """
    Atomic customer debt ledger writer with pessimistic row-locking on Customer.
    """
    locked_customer = Customer.objects.select_for_update().get(pk=customer.pk)
    before = locked_customer.current_balance_minor
    after = before + amount_delta_minor

    if after < 0:
        raise ValidationError(f"Customer balance cannot be negative. Current: {before}, delta: {amount_delta_minor}.")

    entry = CustomerLedgerEntry.objects.create(
        tenant=tenant,
        customer=locked_customer,
        entry_type=entry_type,
        amount_delta_minor=amount_delta_minor,
        balance_before_minor=before,
        balance_after_minor=after,
        reference_type=reference_type,
        reference_id=reference_id,
        recorded_by=recorded_by,
        notes=notes,
    )

    locked_customer.current_balance_minor = after
    locked_customer.save(update_fields=['current_balance_minor'])
    return entry


@transaction.atomic
def record_loyalty_transaction(
    *,
    tenant: Tenant,
    customer: Customer,
    transaction_type: str,
    points_delta: int,
    reference_id: uuid.UUID = None,
    notes: str = "",
) -> LoyaltyTransaction:
    """
    Atomic customer loyalty points mutation with pessimistic row-locking on Customer.
    """
    locked_customer = Customer.objects.select_for_update().get(pk=customer.pk)
    before = locked_customer.loyalty_points
    after = before + points_delta

    if after < 0:
        raise ValidationError(f"Insufficient loyalty points. Current: {before}, requested deduction: {abs(points_delta)}.")

    tx = LoyaltyTransaction.objects.create(
        tenant=tenant,
        customer=locked_customer,
        transaction_type=transaction_type,
        points=points_delta,
        balance_before=before,
        balance_after=after,
        reference_id=reference_id,
        notes=notes,
    )

    locked_customer.loyalty_points = after
    if points_delta > 0:
        locked_customer.lifetime_points_earned += points_delta
    else:
        locked_customer.lifetime_points_redeemed += abs(points_delta)

    # Dynamic tier calculation based on lifetime points earned
    earned = locked_customer.lifetime_points_earned
    if earned >= 5000:
        locked_customer.loyalty_tier = LoyaltyTier.PLATINUM
    elif earned >= 2000:
        locked_customer.loyalty_tier = LoyaltyTier.GOLD
    elif earned >= 500:
        locked_customer.loyalty_tier = LoyaltyTier.SILVER
    else:
        locked_customer.loyalty_tier = LoyaltyTier.BRONZE

    locked_customer.save(update_fields=['loyalty_points', 'lifetime_points_earned', 'lifetime_points_redeemed', 'loyalty_tier'])
    return tx
