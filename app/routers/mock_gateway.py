"""Mock external Payment Gateway (STP risk table: "use mocked payment responses").

The real gateway is out of scope (SRS 1.2), so this endpoint plays its role:
it receives a payment request id and returns a SIGNED result that the browser
(or a test) then posts to /api/orders/{id}/payment-result.

outcome = success   -> valid signed success
outcome = failed    -> valid signed failure
outcome = tampered  -> says "success" but the signature belongs to "failed"
                       (simulates an altered result; must be rejected)
"""
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import config
from app.services import payment

router = APIRouter(prefix="/api/mock-gateway", tags=["mock-gateway"])


class GatewayPayIn(BaseModel):
    paymentRequestId: str
    outcome: Literal["success", "failed", "tampered"]


@router.post("/pay")
def pay(body: GatewayPayIn):
    if not config.ENABLE_MOCK_GATEWAY:
        raise HTTPException(status_code=404, detail="Mock gateway is disabled")
    if body.outcome == "tampered":
        return {
            "paymentRequestId": body.paymentRequestId,
            "result": "success",
            "signature": payment.sign(body.paymentRequestId, "failed"),
        }
    return {
        "paymentRequestId": body.paymentRequestId,
        "result": body.outcome,
        "signature": payment.sign(body.paymentRequestId, body.outcome),
    }
