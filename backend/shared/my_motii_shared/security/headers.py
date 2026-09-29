"""HTTP security-header defaults for edge applications."""

SECURITY_HEADERS = {
	"X-Content-Type-Options": "nosniff",
	"Referrer-Policy": "strict-origin-when-cross-origin",
	"X-Frame-Options": "DENY",
	"Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def apply_security_headers(response):
	for name, value in SECURITY_HEADERS.items():
		response.headers.setdefault(name, value)
	return response