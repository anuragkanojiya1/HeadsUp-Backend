from fastapi import APIRouter, HTTPException
from app.schemas.escrow import EscrowCreateRequest
from app.services.escrow_service import (
    create_escrow,
    get_escrow,
    transition_escrow_status,
)
from app.services.razorpay_service import transfer_to_worker, refund

router = APIRouter()

@router.post("/create")
def create(data: EscrowCreateRequest):
    escrow = create_escrow(data.model_dump())
    return {
        "escrow_id": escrow["escrow_id"],
        "order_id": escrow["order"]["id"],
        "amount": escrow["amount"]
    }

@router.post("/submit-work/{escrow_id}")
def submit(escrow_id: str):
    escrow = get_escrow(escrow_id)
    updated = transition_escrow_status(escrow, "WORK_SUBMITTED")
    return {
        "status": updated["status"],
        "escrow_id": updated["id"],
    }

@router.post("/release/{escrow_id}")
def release(escrow_id: str):
    escrow = get_escrow(escrow_id)
    updated = transition_escrow_status(escrow, "RELEASED")

    transfer = transfer_to_worker(updated["worker_account_id"], updated["amount"], updated["id"])

    return {
        "status": updated["status"],
        "transfer_id": transfer.get("id"),
    }

@router.post("/refund/{escrow_id}")
def refund_api(escrow_id: str):
    escrow = get_escrow(escrow_id)
    if not escrow.get("razorpay_payment_id"):
        raise HTTPException(status_code=400, detail="Escrow has no captured payment to refund")

    updated = transition_escrow_status(escrow, "REFUNDED")
    refund_response = refund(updated["razorpay_payment_id"])
    return {
        "status": updated["status"],
        "refund_id": refund_response.get("id"),
    }
