"""Salted one-way password hashing (OBS-SR-002) using only the standard library.

Stored format:  pbkdf2_sha256$<iterations>$<salt-hex>$<hash-hex>
A fresh random salt per password means two users with the same password
get different hashes, and the plaintext is never stored.
"""
import hashlib
import hmac
import secrets

ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), expected)  # constant-time compare
