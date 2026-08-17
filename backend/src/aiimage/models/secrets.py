import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SecretCipher:
    def __init__(self, encoded_key: str) -> None:
        key = base64.b64decode(encoded_key, validate=True)
        if len(key) != 32:
            raise ValueError("AIIMAGE_SECRET_KEY_BASE64 must decode to 32 bytes")
        self._aes = AESGCM(key)

    def encrypt(self, secret: str, *, authenticated_data: str) -> tuple[bytes, bytes]:
        nonce = os.urandom(12)
        ciphertext = self._aes.encrypt(nonce, secret.encode(), authenticated_data.encode())
        return ciphertext, nonce

    def decrypt(self, ciphertext: bytes, nonce: bytes, *, authenticated_data: str) -> str:
        value = self._aes.decrypt(nonce, ciphertext, authenticated_data.encode())
        return value.decode()

