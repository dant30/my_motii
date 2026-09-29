"""Transactional POS checkout across sales, stock, numbering, and audit."""

from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.audit.services import record_audit_event
from apps.branches.models import Branch
from apps.catalog.models import Product
from apps.customers.models import Customer
from apps.documents.services import next_document_number
from apps.inventory.models import StockMovementType
from apps.inventory.services import record_stock_movement
from apps.pos.models import CashSession, Register
from apps.sales.models import Sale, SaleItem, TaxRateCode
from apps.tenancy.models import Tenant
from my_motii_shared.constants.taxes import TAX_RATES
from my_motii_shared.domain.money import Money
from my_motii_shared.domain.tax import calculate_tax


@dataclass(frozen=True, slots=True)
class CheckoutLine:
	product: Product
	quantity: int
	unit_price_minor: int
	discount_minor: int = 0
	tax_rate_code: str = TaxRateCode.A


@transaction.atomic
def create_sale(
	*,
	tenant: Tenant,
	branch: Branch,
	cashier: User,
	customer: Customer,
	lines: list[CheckoutLine],
	register: Register | None = None,
	session: CashSession | None = None,
) -> Sale:
	if not lines:
		raise ValidationError("A sale must contain at least one line.")
	if branch.tenant_id != tenant.pk or customer.tenant_id != tenant.pk:
		raise ValidationError("Branch and customer must belong to the supplied tenant.")
	if cashier.tenant_id != tenant.pk and not cashier.is_superuser:
		raise ValidationError("Cashier must belong to the supplied tenant.")
	if register is not None and (register.tenant_id != tenant.pk or register.branch_id != branch.pk):
		raise ValidationError("Register must belong to the sale tenant and branch.")
	if session is not None and (
		session.tenant_id != tenant.pk or session.branch_id != branch.pk or session.status != CashSession.Status.OPEN
	):
		raise ValidationError("Cash session must be open and belong to the sale tenant and branch.")

	prepared: list[tuple[CheckoutLine, int, int]] = []
	subtotal_minor = 0
	tax_minor = 0
	for line in lines:
		if line.product.tenant_id != tenant.pk:
			raise ValidationError("Every product must belong to the sale tenant.")
		if line.quantity < 1 or line.unit_price_minor < 0 or line.discount_minor < 0:
			raise ValidationError("Sale quantities and amounts are invalid.")
		if line.tax_rate_code not in TAX_RATES:
			raise ValidationError({"tax_rate_code": "Unsupported tax rate code."})
		line_net = line.quantity * line.unit_price_minor - line.discount_minor
		if line_net < 0:
			raise ValidationError("A line discount cannot exceed its gross line amount.")
		tax_breakdown = calculate_tax(
			Money(line_net, "KES", 2), TAX_RATES[line.tax_rate_code]
		)
		prepared.append((line, line_net, tax_breakdown.tax.minor))
		subtotal_minor += line_net
		tax_minor += tax_breakdown.tax.minor

	document_number = next_document_number(tenant=tenant, branch=branch, doc_type="INV")
	receipt_number = next_document_number(tenant=tenant, branch=branch, doc_type="RCT")
	sale = Sale.objects.create(
		tenant=tenant,
		document_number=document_number,
		receipt_number=receipt_number,
		branch=branch,
		register=register,
		session=session,
		cashier=cashier,
		cashier_name_snapshot=cashier.full_name,
		customer=customer,
		customer_name_snapshot=customer.name,
		customer_phone_snapshot=customer.phone or "",
		customer_pin_snapshot=customer.kra_pin or "",
		currency_code="KES",
		subtotal_minor=subtotal_minor,
		tax_minor=tax_minor,
		total_minor=subtotal_minor + tax_minor,
	)
	for line, line_total, _tax in prepared:
		SaleItem.objects.create(
			sale=sale,
			product=line.product,
			part_sku=line.product.sku,
			part_name=line.product.name,
			quantity=line.quantity,
			unit_price_minor=line.unit_price_minor,
			discount_minor=line.discount_minor,
			tax_rate_code=line.tax_rate_code,
			line_total_minor=line_total,
		)
		record_stock_movement(
			tenant=tenant,
			product=line.product,
			branch=branch,
			movement_type=StockMovementType.SALE,
			quantity_delta=-line.quantity,
			unit_cost_minor=line.product.cost_price_minor,
			reference_type="SALE",
			reference_id=sale.id,
			performed_by=cashier,
		)
	record_audit_event(
		tenant=tenant,
		user=cashier,
		action="sale.completed",
		object_type="Sale",
		object_id=sale.id,
		changes={"total_minor": (None, sale.total_minor), "status": (None, sale.status)},
	)
	return sale