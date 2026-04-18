# app/services/razorpay_service.py

import razorpay
from app.core.config import settings

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET)
)

def create_order(amount, receipt):
    return client.order.create({
        "amount": amount,
        "currency": "INR",
        "receipt": receipt,
        "payment_capture": 1
    })

def transfer_to_worker(account_id, amount, escrow_id):
    return client.transfer.create({
        "account": account_id,
        "amount": amount,
        "currency": "INR",
        "notes": {
            "escrow_id": escrow_id
        }
    })

def refund(payment_id):
    return client.payment.refund(payment_id)