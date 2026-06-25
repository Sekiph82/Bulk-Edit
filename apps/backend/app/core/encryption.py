"""
Centralized Fernet encryption for Etsy token storage.

WARNING: The dev fallback key is deterministic and NOT secret.
         Set ENCRYPTION_KEY to a real Fernet key in production:
         python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
from cryptography.fernet import Fernet
from app.core.config import settings

_DEV_FALLBACK_KEY = b"ZGV2X2VuY3J5cHRpb25fa2V5X3BsYWNlaG9sZGVyISE="


def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY.strip()
    if not key or "placeholder" in key.lower():
        return Fernet(_DEV_FALLBACK_KEY)
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
