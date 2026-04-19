from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user
from app.core.config import settings
from app.schemas.escrow import EscrowCreateRequest
from app.services.escrow_service import (
    create_escrow,
    get_escrow,
    transition_escrow_status,
)
from app.services.razorpay_service import refund, transfer_to_worker

router = APIRouter()


def _build_dev_transfer(escrow: dict) -> dict:
    return {
        "id": f"dev_transfer_{escrow['id']}",
        "account": escrow.get("worker_account_id"),
        "amount": escrow["amount"],
        "currency": "INR",
        "mode": "dev",
    }


@router.post("/create")
def create(data: EscrowCreateRequest, current_user: dict = Depends(get_current_user)):
    if data.employer_id != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Employer id must match authenticated user")

    escrow = create_escrow(data.model_dump())
    return {
        "escrow_id": escrow["escrow_id"],
        "order_id": escrow["order"]["id"],
        "amount": escrow["amount"],
    }


@router.post("/submit-work/{escrow_id}")
def submit(escrow_id: str, current_user: dict = Depends(get_current_user)):
    escrow = get_escrow(escrow_id)
    if escrow["worker_id"] != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Only the assigned worker can submit work")

    updated = transition_escrow_status(escrow, "WORK_SUBMITTED")
    return {
        "status": updated["status"],
        "escrow_id": updated["id"],
    }


@router.post("/release/{escrow_id}")
def release(escrow_id: str, current_user: dict = Depends(get_current_user)):
    escrow = get_escrow(escrow_id)
    if escrow["employer_id"] != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Only the employer can release escrow")

    if escrow["status"] != "WORK_SUBMITTED":
        raise HTTPException(
            status_code=409,
            detail="Escrow must be in WORK_SUBMITTED state before release",
        )

    if settings.ESCROW_RELEASE_DEV_MODE:
        if settings.APP_ENV == "production":
            raise HTTPException(status_code=500, detail="Dev escrow release mode is not allowed in production")
        transfer = _build_dev_transfer(escrow)
    else:
        if not escrow.get("worker_account_id") or not escrow["worker_account_id"].startswith("acc_"):
            raise HTTPException(status_code=400, detail="Invalid worker account")

        try:
            transfer = transfer_to_worker(
                escrow["worker_account_id"],
                escrow["amount"],
                escrow["id"],
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Transfer failed: {str(e)}") from e

    updated = transition_escrow_status(escrow, "RELEASED")
    return {
        "status": updated["status"],
        "escrow_id": updated["id"],
        "transfer_id": transfer["id"],
    }

@router.post("/refund/{escrow_id}")
def refund_api(escrow_id: str, current_user: dict = Depends(get_current_user)):
    escrow = get_escrow(escrow_id)
    if escrow["employer_id"] != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Only the employer can refund escrow")

    if not escrow.get("razorpay_payment_id"):
        raise HTTPException(status_code=400, detail="No payment to refund")

    try:
        refund_response = refund(escrow["razorpay_payment_id"])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Refund failed: {str(e)}")

    updated = transition_escrow_status(escrow, "REFUNDED")

    return {
        "status": updated["status"],
        "refund_id": refund_response.get("id"),
    }
