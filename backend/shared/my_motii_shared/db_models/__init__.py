"""Public Django ORM primitives shared across my_motii apps."""

try:
	from .base import BaseModel, TenantModel
	from .managers import AllObjectsManager, SoftDeleteManager, SoftDeleteQuerySet
	from .mixins import SoftDeleteMixin
except ModuleNotFoundError as error:
	if error.name != "django":
		raise
	raise ImportError("my_motii_shared.db_models requires Django; install the backend requirements.") from error

__all__ = [
	"AllObjectsManager",
	"BaseModel",
	"SoftDeleteManager",
	"SoftDeleteMixin",
	"SoftDeleteQuerySet",
	"TenantModel",
]
