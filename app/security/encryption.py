"""Envelope encryption for target DB credentials at rest."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionError(Exception):
    pass


@dataclass(frozen=True)
class EncryptedBlob:
    """Wire format stored in connections.encrypted_credentials (BYTEA)."""

    encrypted_dek: bytes
    dek_nonce: bytes
    ciphertext: bytes
    cred_nonce: bytes

    def to_bytes(self) -> bytes:
        payload = {
            "encrypted_dek": base64.b64encode(self.encrypted_dek).decode("ascii"),
            "dek_nonce": base64.b64encode(self.dek_nonce).decode("ascii"),
            "ciphertext": base64.b64encode(self.ciphertext).decode("ascii"),
            "cred_nonce": base64.b64encode(self.cred_nonce).decode("ascii"),
        }
        return json.dumps(payload).encode("utf-8")

    @classmethod
    def from_bytes(cls, raw: bytes) -> EncryptedBlob:
        payload = json.loads(raw.decode("utf-8"))
        return cls(
            encrypted_dek=base64.b64decode(payload["encrypted_dek"]),
            dek_nonce=base64.b64decode(payload["dek_nonce"]),
            ciphertext=base64.b64decode(payload["ciphertext"]),
            cred_nonce=base64.b64decode(payload["cred_nonce"]),
        )


def _decode_kek(kek_secret: str) -> bytes:
    try:
        key = base64.b64decode(kek_secret)
    except Exception as exc:
        raise EncryptionError("KEK_SECRET must be base64-encoded 32 bytes") from exc
    if len(key) != 32:
        raise EncryptionError("KEK_SECRET must decode to exactly 32 bytes")
    return key


def encrypt_credentials(password: str, kek_secret: str) -> bytes:
    """
    Envelope encryption: random DEK encrypts password; KEK wraps DEK.
    Compromise of metadata DB alone cannot decrypt passwords without KEK from env/KMS.
    """
    kek = _decode_kek(kek_secret)
    dek = AESGCM.generate_key(bit_length=256)
    dek_nonce = os.urandom(12)
    kek_cipher = AESGCM(kek)
    encrypted_dek = kek_cipher.encrypt(dek_nonce, dek, None)

    cred_nonce = os.urandom(12)
    cred_cipher = AESGCM(dek)
    ciphertext = cred_cipher.encrypt(cred_nonce, password.encode("utf-8"), None)

    return EncryptedBlob(
        encrypted_dek=encrypted_dek,
        dek_nonce=dek_nonce,
        ciphertext=ciphertext,
        cred_nonce=cred_nonce,
    ).to_bytes()


def decrypt_credentials(blob_bytes: bytes, kek_secret: str) -> str:
    kek = _decode_kek(kek_secret)
    blob = EncryptedBlob.from_bytes(blob_bytes)
    kek_cipher = AESGCM(kek)
    try:
        dek = kek_cipher.decrypt(blob.dek_nonce, blob.encrypted_dek, None)
        cred_cipher = AESGCM(dek)
        plaintext = cred_cipher.decrypt(blob.cred_nonce, blob.ciphertext, None)
    except InvalidTag as exc:
        raise EncryptionError(
            "Stored credentials cannot be decrypted with the current KEK_SECRET. "
            "Re-register this connection in the UI."
        ) from exc
    return plaintext.decode("utf-8")
