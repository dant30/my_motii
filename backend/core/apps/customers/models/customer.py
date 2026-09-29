"""Tenant-owned customer records and customer financial ledgers."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from apps.common.mixins import SoftDeleteMixin
from apps.common.models import BaseModel, TenantModel
from apps.common.validators import kra_pin_validator, phone_validator


class CustomerType(models.TextChoices):
	WALK_IN = "WALK_IN", "Walk-in retail"
	GARAGE = "GARAGE", "Garage"
	FLEET = "FLEET", "Fleet"
	INDIVIDUAL = "INDIVIDUAL", "Individual"


class LoyaltyTier(models.TextChoices):
	BRONZE = "BRONZE", "Bronze"
	SILVER = "SILVER", "Silver"
	GOLD = "GOLD", "Gold"
	PLATINUM = "PLATINUM", "Platinum"


class Customer(TenantModel, SoftDeleteMixin):
	name = models.CharField(max_length=200, db_index=True)
	customer_type = models.CharField(max_length=30, choices=CustomerType.choices, default=CustomerType.WALK_IN)
	phone = models.CharField(max_length=30, blank=True, null=True, validators=[phone_validator])
	kra_pin = models.CharField(max_length=11, blank=True, null=True, validators=[kra_pin_validator])
	credit_limit_minor = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	current_balance_minor = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	credit_days = models.PositiveIntegerField(default=30)
	loyalty_points = models.IntegerField(default=0)
	loyalty_tier = models.CharField(max_length=20, choices=LoyaltyTier.choices, default=LoyaltyTier.BRONZE)
	lifetime_points_earned = models.IntegerField(default=0)
	lifetime_points_redeemed = models.IntegerField(default=0)

	class Meta:
		ordering = ["name"]
		constraints = [
			models.CheckConstraint(check=models.Q(credit_limit_minor__gte=0), name="chk_customer_credit_limit_nonnegative"),
			models.CheckConstraint(check=models.Q(current_balance_minor__gte=0), name="chk_customer_balance_nonnegative"),
		]
		indexes = [models.Index(fields=["tenant", "phone"]), models.Index(fields=["tenant", "kra_pin"])]

	@property
	def current_balance_kes(self) -> Decimal:
		return Decimal(self.current_balance_minor) / Decimal(100)

	@property
	def credit_limit_kes(self) -> Decimal:
		return Decimal(self.credit_limit_minor) / Decimal(100)

	@property
	def available_credit_kes(self) -> Decimal:
		return max(Decimal("0.00"), self.credit_limit_kes - self.current_balance_kes)

	def __str__(self) -> str:
		return f"{self.name} [{self.get_customer_type_display()}]"


class CustomerGroup(TenantModel):
	name = models.CharField(max_length=100)
	description = models.CharField(max_length=255, blank=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="uniq_customer_group_per_tenant")]


class CustomerProfile(TenantModel):
	customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="profile")
	group = models.ForeignKey(CustomerGroup, null=True, blank=True, on_delete=models.SET_NULL, related_name="customers")
	address = models.CharField(max_length=255, blank=True)
	email = models.EmailField(blank=True)
	notes = models.TextField(blank=True)


class CustomerContact(TenantModel):
	customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="contacts")
	name = models.CharField(max_length=150)
	phone = models.CharField(max_length=30, validators=[phone_validator])
	email = models.EmailField(blank=True)
	role = models.CharField(max_length=80, blank=True)
	is_primary = models.BooleanField(default=False)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant", "customer", "name", "phone"], name="uniq_customer_contact"),
		]


class CustomerLedgerEntryType(models.TextChoices):
	CREDIT_SALE = "CREDIT_SALE", "Credit sale"
	PAYMENT_RECEIVED = "PAYMENT_RECEIVED", "Payment received"
	CREDIT_NOTE = "CREDIT_NOTE", "Credit note"
	DEBIT_ADJUSTMENT = "DEBIT_ADJUSTMENT", "Debit adjustment"


class CustomerLedgerEntry(TenantModel):
	customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="ledger_entries")
	entry_type = models.CharField(max_length=40, choices=CustomerLedgerEntryType.choices)
	amount_delta_minor = models.BigIntegerField()
	balance_before_minor = models.BigIntegerField()
	balance_after_minor = models.BigIntegerField()
	reference_type = models.CharField(max_length=40)
	reference_id = models.UUIDField(db_index=True)
	recorded_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
	notes = models.CharField(max_length=255, blank=True)

	class Meta:
		ordering = ["-created_at"]
		constraints = [
			models.CheckConstraint(
				check=Q(balance_after_minor=F("balance_before_minor") + F("amount_delta_minor")),
				name="chk_customer_ledger_integrity",
			),
			models.CheckConstraint(check=Q(balance_after_minor__gte=0), name="chk_customer_ledger_balance_nonnegative"),
		]
		indexes = [models.Index(fields=["tenant", "customer", "-created_at"])]


class LoyaltyTransaction(TenantModel):
	class TransactionType(models.TextChoices):
		EARNED = "EARNED", "Earned"
		REDEEMED = "REDEEMED", "Redeemed"
		ADJUSTMENT = "ADJUSTMENT", "Adjustment"

	customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="loyalty_transactions")
	transaction_type = models.CharField(max_length=30, choices=TransactionType.choices)
	points = models.IntegerField()
	balance_before = models.IntegerField()
	balance_after = models.IntegerField()
	reference_id = models.UUIDField(null=True, blank=True)
	notes = models.CharField(max_length=255, blank=True)

	class Meta:
		ordering = ["-created_at"]
		constraints = [
			models.CheckConstraint(
				check=Q(balance_after=F("balance_before") + F("points")),
				name="chk_loyalty_ledger_integrity",
			),
			models.CheckConstraint(check=Q(balance_after__gte=0), name="chk_loyalty_balance_nonnegative"),
		]


class CustomerVehicle(TenantModel):
	customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="vehicles")
	registration_plate = models.CharField(max_length=20, db_index=True)
	vehicle_model = models.ForeignKey("vehicles.VehicleModel", on_delete=models.PROTECT, related_name="customer_vehicles")
	chassis_vin = models.CharField(max_length=50, blank=True)
	engine_number = models.CharField(max_length=50, blank=True)
	year = models.CharField(max_length=10, blank=True)
	is_active = models.BooleanField(default=True)
	notes = models.TextField(blank=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "registration_plate"],
				condition=models.Q(is_active=True),
				name="uniq_active_customer_vehicle_plate_per_tenant",
			),
		]