"""
Encryption Service - AES-256-GCM for encrypting chunk text at rest
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config.settings import settings


_KEY_FILE_NAME = "enc_key.bin"


def _get_key_path() -> Path:
    return settings.KEYSTORE_PATH / _KEY_FILE_NAME


def get_or_create_key() -> bytes:
    """Load the AES-256 key from keystore or create a new one with strict perms."""
    key_path = _get_key_path()
    if key_path.exists():
        return key_path.read_bytes()

    key = AESGCM.generate_key(bit_length=256)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    # Ensure restrictive permissions on POSIX systems
    with open(key_path, "wb") as f:
        f.write(key)
    try:
        os.chmod(key_path, 0o600)
    except Exception:
        # Best-effort on non-POSIX
        pass
    return key


def encrypt_bytes(plaintext: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """
    Encrypt bytes using AES-256-GCM and return nonce+ciphertext.
    Layout: [12-byte nonce][ciphertext+tag]
    """
    key = get_or_create_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    return nonce + ciphertext


def decrypt_bytes(data: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """Decrypt bytes produced by encrypt_bytes."""
    if len(data) < 13:
        raise ValueError("Invalid encrypted payload")
    key = get_or_create_key()
    aesgcm = AESGCM(key)
    nonce = data[:12]
    ciphertext = data[12:]
    return aesgcm.decrypt(nonce, ciphertext, associated_data)


def encrypt_to_file(target_path: Path, plaintext: bytes) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    blob = encrypt_bytes(plaintext)
    target_path.write_bytes(blob)


def decrypt_file(source_path: Path) -> bytes:
    data = source_path.read_bytes()
    return decrypt_bytes(data)


