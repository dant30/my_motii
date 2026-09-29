"""Platform-owned canonical product categories."""

from django.db import models

from apps.common.models import BaseModel


class Category(BaseModel):
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=120, unique=True)
	parent = models.ForeignKey(
		"self",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="subcategories",
	)
	is_active = models.BooleanField(default=True)

	class Meta:
		verbose_name_plural = "categories"
		ordering = ["name"]

	def __str__(self) -> str:
		return f"{self.parent.name} > {self.name}" if self.parent else self.name