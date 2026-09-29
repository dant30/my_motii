"""Tests for shared abstract model behavior."""

from types import SimpleNamespace
from unittest.mock import Mock

from apps.common.managers import SoftDeleteQuerySet
from apps.common.mixins import SoftDeleteMixin


def test_soft_delete_queryset_returns_django_deletion_tuple():
	queryset = Mock()
	queryset.model = SimpleNamespace(_meta=SimpleNamespace(label="inventory.Product"))
	queryset.alive.return_value.update.return_value = 2

	result = SoftDeleteQuerySet.delete(queryset)

	assert result == (2, {"inventory.Product": 2})
	queryset.alive.assert_called_once_with()
	queryset.alive.return_value.update.assert_called_once()
	assert queryset.alive.return_value.update.call_args.kwargs["deleted_at"] is not None


def test_soft_delete_instance_sets_timestamp_and_returns_deletion_tuple():
	instance = SimpleNamespace(
		deleted_at=None,
		save=Mock(),
		_meta=SimpleNamespace(label="inventory.Product"),
	)

	result = SoftDeleteMixin.delete(instance)

	assert result == (1, {"inventory.Product": 1})
	assert instance.deleted_at is not None
	instance.save.assert_called_once_with(using=None, update_fields=["deleted_at"])