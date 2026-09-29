"""Soft-delete-aware Django managers and querysets."""

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
	def alive(self):
		return self.filter(deleted_at__isnull=True)

	def dead(self):
		return self.filter(deleted_at__isnull=False)

	def delete(self):
		count = self.alive().update(deleted_at=timezone.now())
		return count, {self.model._meta.label: count}

	def hard_delete(self):
		return super().delete()


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
	def get_queryset(self):
		return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
	"""Unfiltered manager that retains soft-delete queryset operations."""