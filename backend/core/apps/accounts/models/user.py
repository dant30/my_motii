"""Custom user model scoped to a tenant where applicable."""

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower

from apps.common.models import BaseModel
from apps.common.validators import phone_validator
from apps.accounts.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
	tenant = models.ForeignKey(
		"tenancy.Tenant",
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name="users",
	)
	email = models.EmailField(db_index=True)
	phone = models.CharField(max_length=30, blank=True, null=True, validators=[phone_validator])
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	is_tenant_admin = models.BooleanField(default=False)

	USERNAME_FIELD = "email"
	REQUIRED_FIELDS = ["first_name", "last_name"]

	objects = UserManager()

	class Meta:
		constraints = [
			models.UniqueConstraint(
				Lower("email"),
				"tenant",
				condition=models.Q(tenant__isnull=False),
				name="uniq_user_email_per_tenant",
			),
			models.UniqueConstraint(
				Lower("email"),
				condition=models.Q(tenant__isnull=True),
				name="uniq_platform_user_email",
			),
		]

	def clean(self) -> None:
		super().clean()
		if self.email:
			self.email = self.email.lower()

	def save(self, *args, **kwargs) -> None:
		if self.email:
			self.email = self.email.lower()
		super().save(*args, **kwargs)

	def __str__(self) -> str:
		return f"{self.first_name} {self.last_name} ({self.email})"

	@property
	def full_name(self) -> str:
		return f"{self.first_name} {self.last_name}".strip()