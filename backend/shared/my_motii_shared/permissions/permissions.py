"""Permission evaluation with exact and wildcard grants."""

from collections.abc import Iterable


def has_permission(grants: Iterable[str], required: str) -> bool:
	grant_set = set(grants)
	if "*" in grant_set or required in grant_set:
		return True
	resource = required.partition(".")[0]
	return f"{resource}.*" in grant_set


def require_permission(grants: Iterable[str], required: str) -> None:
	if not has_permission(grants, required):
		raise PermissionError(f"Permission required: {required}")