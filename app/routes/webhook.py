import hashlib
import hmac
import json

from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.services.escrow_service import mark_order_funded_from_payment

router = APIRouter()


@router.post("/razorpay")
async def webhook(request: Request):
    if settings.ESCROW_PAYMENT_PROVIDER != "razorpay":
        raise HTTPException(status_code=409, detail="Razorpay webhook is disabled for current provider")

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Razorpay signature")

    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event = json.loads(body)
    event_type = event.get("event")

    if event_type == "payment.captured":
        payment = event.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        payment_id = payment.get("id")
        amount = payment.get("amount")
        currency = payment.get("currency")

        if not order_id or not payment_id:
            raise HTTPException(status_code=400, detail="Invalid payment.captured payload")

        mark_order_funded_from_payment(
            order_id,
            payment_id,
            amount=amount,
            currency=currency,
        )

    return {"status": "ok", "event": event_type}
