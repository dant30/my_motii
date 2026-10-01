"""Branches or workshop locations belonging to a garage."""

from django.db import models

from apps.common.models import TenantModel


class GarageBranch(TenantModel):
	garage = models.ForeignKey("garages.Garage", on_delete=models.CASCADE, related_name="branches")
	branch_name = models.CharField(max_length=100)