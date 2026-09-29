"""Transaction-safe document number allocation."""

from django.db import transaction
from django.utils import timezone

from apps.branches.models import Branch
from apps.documents.models import DocumentSequence
from apps.tenancy.models import Tenant


@transaction.atomic
def next_document_number(
	*, tenant: Tenant, branch: Branch, doc_type: str, fiscal_year: int | None = None
) -> str:
	if branch.tenant_id != tenant.pk:
		raise ValueError("Branch must belong to the supplied tenant.")
	if not doc_type or len(doc_type) > 20:
		raise ValueError("doc_type must contain 1 to 20 characters.")
	fiscal_year = fiscal_year or timezone.now().year
	if fiscal_year < 1:
		raise ValueError("fiscal_year must be positive.")
	prefix = f"{branch.code}-{doc_type}-{fiscal_year}"
	sequence, _ = DocumentSequence.objects.get_or_create(
		tenant=tenant,
		branch=branch,
		doc_type=doc_type,
		fiscal_year=fiscal_year,
		defaults={"prefix": prefix},
	)
	sequence = DocumentSequence.objects.select_for_update().get(pk=sequence.pk)
	sequence.current_value += 1
	sequence.prefix = prefix
	sequence.save(update_fields=["current_value", "prefix", "updated_at"])
	return f"{prefix}-{sequence.current_value:05d}"