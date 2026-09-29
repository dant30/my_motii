"""Document-number sequence behavior."""

import pytest

from apps.branches.models import Branch
from apps.documents.services import next_document_number
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_document_numbers_increment_within_tenant_branch_type_and_year():
	tenant = Tenant.objects.create(name="Docs tenant", slug="docs-test", kra_pin="P051839284Z", phone="+254722550120")
	branch = Branch.objects.create(tenant=tenant, code="MAIN", name="Main")
	assert next_document_number(tenant=tenant, branch=branch, doc_type="INV", fiscal_year=2026) == "MAIN-INV-2026-00001"
	assert next_document_number(tenant=tenant, branch=branch, doc_type="INV", fiscal_year=2026) == "MAIN-INV-2026-00002"
	assert next_document_number(tenant=tenant, branch=branch, doc_type="RCT", fiscal_year=2026) == "MAIN-RCT-2026-00001"