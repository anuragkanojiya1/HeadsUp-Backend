import hashlib
import hmac
import json

from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.services.escrow_service import mark_order_funded

router = APIRouter()


@router.post("/razorpay")
async def webhook(request: Request):
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

        if not order_id or not payment_id:
            raise HTTPException(status_code=400, detail="Invalid payment.captured payload")

        mark_order_funded(order_id, payment_id)

    return {"status": "ok", "event": event_type}
