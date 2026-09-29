"""S3-compatible object storage adapter."""

from urllib.parse import quote

from .base import StoredObject
from .utils import normalize_key


class S3Storage:
	def __init__(self, client, bucket: str, public_base_url: str | None = None) -> None:
		if not bucket:
			raise ValueError("bucket is required")
		self.client = client
		self.bucket = bucket
		self.public_base_url = public_base_url.rstrip("/") if public_base_url else None

	def save(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> StoredObject:
		safe_key = normalize_key(key)
		self.client.put_object(Bucket=self.bucket, Key=safe_key, Body=content, ContentType=content_type)
		return StoredObject(safe_key, len(content), content_type)

	def read(self, key: str) -> bytes:
		response = self.client.get_object(Bucket=self.bucket, Key=normalize_key(key))
		return response["Body"].read()

	def delete(self, key: str) -> bool:
		self.client.delete_object(Bucket=self.bucket, Key=normalize_key(key))
		return True

	def url(self, key: str) -> str:
		safe_key = quote(normalize_key(key), safe="/")
		if self.public_base_url:
			return f"{self.public_base_url}/{safe_key}"
		return self.client.generate_presigned_url(
			"get_object", Params={"Bucket": self.bucket, "Key": normalize_key(key)}
		)