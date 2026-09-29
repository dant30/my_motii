"""Authenticated encryption helpers backed by Fernet."""

from cryptography.fernet import Fernet, InvalidToken


def generate_encryption_key() -> bytes:
	return Fernet.generate_key()


def encrypt_secret(value: str, key: bytes | str) -> str:
	key_bytes = key.encode() if isinstance(key, str) else key
	return Fernet(key_bytes).encrypt(value.encode()).decode()


def decrypt_secret(value: str, key: bytes | str) -> str:
	key_bytes = key.encode() if isinstance(key, str) else key
	try:
		return Fernet(key_bytes).decrypt(value.encode()).decode()
	except (InvalidToken, UnicodeError) as error:
		raise ValueError("Secret could not be decrypted with the supplied key.") from error