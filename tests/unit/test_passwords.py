"""UNIT tests - password hashing (OBS-SR-002, TC-Sec-02)."""
from app.passwords import hash_password, verify_password


def test_TC_Sec_02_hash_is_not_plaintext():
    stored = hash_password("Secret123")
    assert "Secret123" not in stored
    assert stored.startswith("pbkdf2_sha256$")


def test_TC_Sec_02_same_password_gets_different_salted_hashes():
    assert hash_password("Secret123") != hash_password("Secret123")


def test_correct_password_verifies():
    assert verify_password("Secret123", hash_password("Secret123")) is True


def test_wrong_password_is_rejected():
    assert verify_password("Wrong123", hash_password("Secret123")) is False


def test_empty_password_is_rejected():
    assert verify_password("", hash_password("Secret123")) is False


def test_malformed_stored_hash_is_rejected_not_crashing():
    assert verify_password("Secret123", "not-a-valid-hash") is False
    assert verify_password("Secret123", "a$b$c$d") is False
