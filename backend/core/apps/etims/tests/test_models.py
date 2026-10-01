"""eTIMS tenant configuration and credential linkage."""

import pytest

from apps.etims.models import EtimsConfiguration
from apps.integrations.models import IntegrationCredential
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_etims_configuration_uses_encrypted_integration_credential():
	tenant = Tenant.objects.create(name="eTIMS tenant", slug="etims-test", kra_pin="P051839284Z", phone="+254722550120")
	credential = IntegrationCredential.objects.create(
		tenant=tenant,
		provider="ETIMS_KRA",
		key_name="primary",
		encrypted_payload="encrypted-value",
		encryption_key_id="kms-key-1",
	)
	configuration = EtimsConfiguration.objects.create(tenant=tenant, tin="P051839284Z", credential=credential)
	assert configuration.credential.encryption_key_id == "kms-key-1"