"""Payment-result signing / verification (OBS-F-015, OBS-SR-006).

The gateway signs "<paymentRequestId>:<result>" with a shared secret (HMAC-SHA256).
Our server recomputes the signature; if it does not match, the result was
forged or altered and the order is NOT marked paid.
"""
import hashlib
import hmac

from app import config


def sign(payment_request_id: str, result: str) -> str:
    message = f"{payment_request_id}:{result}".encode()
    return hmac.new(config.PAYMENT_SECRET.encode(), message, hashlib.sha256).hexdigest()


def verify(payment_request_id: str, result: str, signature: str) -> bool:
    return hmac.compare_digest(sign(payment_request_id, result), signature or "")
