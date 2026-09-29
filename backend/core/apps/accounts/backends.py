"""Email authentication scoped to a tenant or platform account."""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class TenantEmailBackend(ModelBackend):
	def authenticate(self, request, username=None, password=None, **kwargs):
		email = kwargs.get("email", username)
		if not email or not password:
			return None

		tenant_slug = kwargs.get("tenant_slug")
		if tenant_slug is None and request is not None:
			tenant_slug = getattr(getattr(request, "tenant", None), "slug", None)

		lookup = {"email__iexact": email}
		if tenant_slug:
			lookup["tenant__slug"] = tenant_slug
		else:
			lookup["tenant__isnull"] = True

		user_model = get_user_model()
		try:
			user = user_model._default_manager.get(**lookup)
		except user_model.DoesNotExist:
			user_model().set_password(password)
			return None

		if user.check_password(password) and self.user_can_authenticate(user):
			return user
		return None