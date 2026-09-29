"""Platform mapping from superseded OEM number to replacement OEM number."""

from django.db import models

from apps.common.models import BaseModel


class OemSupersession(BaseModel):
	old_part = models.ForeignKey("fitment.OemPart", on_delete=models.PROTECT, related_name="superseded_by")
	new_part = models.ForeignKey("fitment.OemPart", on_delete=models.PROTECT, related_name="supersedes")
	effective_from = models.DateField(null=True, blank=True)
	notes = models.CharField(max_length=255, blank=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["old_part", "new_part"], name="uniq_oem_supersession_pair"),
			models.CheckConstraint(check=~models.Q(old_part=models.F("new_part")), name="chk_oem_supersession_distinct"),
		]