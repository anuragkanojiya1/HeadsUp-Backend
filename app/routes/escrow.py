# app/routes/escrow.py

from fastapi import APIRouter
from app.services.escrow_service import create_escrow, get_escrow
from app.services.razorpay_service import transfer_to_worker, refund

router = APIRouter()

@router.post("/create")
def create(data: dict):
    order = create_escrow(data)
    return {
        "order_id": order["id"],
        "amount": data["amount"]
    }

@router.post("/submit-work/{escrow_id}")
def submit(escrow_id: str):
    # update status
    pass

@router.post("/release/{escrow_id}")
def release(escrow_id: str):
    escrow = get_escrow(escrow_id)

    transfer_to_worker(
        escrow["worker_account_id"],
        escrow["amount"],
        escrow["id"]
    )

    return {"status": "released"}

@router.post("/refund/{escrow_id}")
def refund_api(escrow_id: str):
    escrow = get_escrow(escrow_id)
    refund(escrow["razorpay_payment_id"])
    return {"status": "refunded"}