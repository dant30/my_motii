"""Reusable Django model mixins."""

from django.db import models
from django.utils import timezone

from .managers import AllObjectsManager, SoftDeleteManager


class SoftDeleteMixin(models.Model):
	deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
	deleted_by = models.ForeignKey(
		"accounts.User",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	objects = SoftDeleteManager()
	all_objects = AllObjectsManager()

	class Meta:
		abstract = True
		default_manager_name = "objects"

	@property
	def is_deleted(self) -> bool:
		return self.deleted_at is not None

	def delete(self, using=None, keep_parents=False):
		self.deleted_at = timezone.now()
		self.save(using=using, update_fields=["deleted_at"])
		return 1, {self._meta.label: 1}

	def hard_delete(self, using=None, keep_parents=False):
		return super().delete(using=using, keep_parents=keep_parents)