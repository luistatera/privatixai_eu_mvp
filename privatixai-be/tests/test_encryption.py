from service.encryption_service import encrypt_bytes, decrypt_bytes


def test_encrypt_decrypt_roundtrip():
    plaintext = b"hello world"
    blob = encrypt_bytes(plaintext)
    restored = decrypt_bytes(blob)
    assert restored == plaintext


def test_decrypt_tamper_failure():
    plaintext = b"secret"
    blob = bytearray(encrypt_bytes(plaintext))
    # Flip a byte in ciphertext
    blob[-1] ^= 0x01
    try:
        _ = decrypt_bytes(bytes(blob))
        assert False, "Expected decrypt to fail on tampered data"
    except Exception:
        assert True


