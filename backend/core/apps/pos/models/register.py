"""Tenant-owned POS registers assigned to physical branches."""

from django.db import models

from apps.common.models import TenantModel


class Register(TenantModel):
	branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="registers")
	register_code = models.CharField(max_length=50, default="POS-01")
	is_active = models.BooleanField(default=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "branch", "register_code"], name="uniq_register_per_branch"
			),
		]

	def __str__(self) -> str:
		return f"{self.branch.code} - {self.register_code}"


class ThermalPrinterProfile(TenantModel):
	name = models.CharField(max_length=100, default="Counter Thermal Printer")
	paper_width = models.CharField(
		max_length=10,
		choices=(("80mm", "80mm"), ("58mm", "58mm")),
		default="80mm",
	)
	feed_lines = models.PositiveIntegerField(default=3)
	print_qr_code = models.BooleanField(default=True)
	include_loyalty_summary = models.BooleanField(default=True)