# app/routes/webhook.py

from fastapi import APIRouter, Request
import hmac, hashlib, json
from app.core.config import settings
from app.services.escrow_service import update_status

router = APIRouter()

@router.post("/razorpay")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return {"error": "invalid"}

    event = json.loads(body)

    if event["event"] == "payment.captured":
        payment = event["payload"]["payment"]["entity"]

        update_status(
            payment["order_id"],
            "FUNDED",
            payment["id"]
        )

    return {"status": "ok"}