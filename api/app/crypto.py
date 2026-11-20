import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _key() -> bytes:
    encoded = os.getenv("ENCRYPTION_KEY", "")
    if not encoded:
        raise RuntimeError("ENCRYPTION_KEY must be configured before handling sensitive fields.")
    try:
        key = base64.urlsafe_b64decode(encoded.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        raise RuntimeError("ENCRYPTION_KEY must be URL-safe base64 encoding of 32 bytes.") from error
    if len(key) != 32:
        raise RuntimeError("ENCRYPTION_KEY must decode to exactly 32 bytes.")
    return key


def encrypt_text(value: str) -> bytes:
    nonce = os.urandom(12)
    return nonce + AESGCM(_key()).encrypt(nonce, value.encode("utf-8"), None)


def decrypt_text(value: bytes) -> str:
    if len(value) < 29:
        raise ValueError("Encrypted value is not a valid AES-GCM payload.")
    nonce, ciphertext = value[:12], value[12:]
    return AESGCM(_key()).decrypt(nonce, ciphertext, None).decode("utf-8")
