"""Base typed domain exception carrying a stable code and safe context."""


class DomainError(Exception):
	code = "domain_error"

	def __init__(self, message: str, *, code: str | None = None, context: dict | None = None):
		super().__init__(message)
		self.message = message
		self.code = code or type(self).code
		self.context = context or {}

	def as_dict(self) -> dict[str, object]:
		return {"code": self.code, "message": self.message, "context": self.context}