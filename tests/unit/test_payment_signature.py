"""UNIT tests - payment signature (OBS-F-015, OBS-SR-006, TC-Sec-06)."""
from app.services import payment


def test_valid_signature_verifies():
    sig = payment.sign("req-1", "success")
    assert payment.verify("req-1", "success", sig) is True


def test_altered_result_fails_verification():
    sig = payment.sign("req-1", "failed")
    assert payment.verify("req-1", "success", sig) is False  # result changed after signing


def test_other_request_id_fails_verification():
    sig = payment.sign("req-1", "success")
    assert payment.verify("req-2", "success", sig) is False


def test_empty_or_garbage_signature_fails():
    assert payment.verify("req-1", "success", "") is False
    assert payment.verify("req-1", "success", "abc") is False
