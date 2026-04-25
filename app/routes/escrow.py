from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user, require_admin_user
from app.core.config import settings
from app.schemas.escrow import (
    EscrowApproveReleaseRequest,
    EscrowCreateRequest,
    EscrowFundRequest,
    EscrowRefundRequest,
    EscrowReleaseRequest,
)
from app.services.escrow_service import (
    create_escrow,
    get_escrow,
    mark_escrow_funded,
    transition_escrow_status,
)

router = APIRouter()


def _is_admin_claims(user: dict) -> bool:
    claims = user.get("claims", {})
    role = str(claims.get("role", "")).lower()
    return role in {"admin", "ops", "superadmin"} or claims.get("is_admin") is True or claims.get("admin") is True


def _build_dev_transfer(escrow: dict) -> dict:
    return {
        "id": f"dev_transfer_{escrow['id']}",
        "account": escrow.get("worker_account_id"),
        "amount": escrow["amount"],
        "currency": "INR",
        "mode": "dev",
    }


def _is_razorpay_provider() -> bool:
    return settings.ESCROW_PAYMENT_PROVIDER == "razorpay"


@router.post("/create")
def create(data: EscrowCreateRequest, current_user: dict = Depends(get_current_user)):
    if data.employer_id != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Employer id must match authenticated user")

    escrow = create_escrow(data.model_dump())
    return {
        "escrow_id": escrow["escrow_id"],
        "order_id": escrow["order"]["id"],
        "provider": escrow["provider"],
        "amount": escrow["amount"],
    }


@router.get("/{escrow_id}")
def get_by_id(escrow_id: str, current_user: dict = Depends(get_current_user)):
    escrow = get_escrow(escrow_id)
    if not _is_admin_claims(current_user) and current_user["uid"] not in {
        escrow["employer_id"],
        escrow["worker_id"],
    }:
        raise HTTPException(status_code=403, detail="Not allowed to view this escrow")
    return escrow


@router.post("/fund/{escrow_id}")
def fund(
    escrow_id: str,
    data: EscrowFundRequest,
    current_user: dict = Depends(require_admin_user),
):
    updated = mark_escrow_funded(
        escrow_id=escrow_id,
        funded_by=current_user["uid"],
        funding_reference=data.funding_reference,
        funding_note=data.funding_note,
        payment_id=data.payment_id,
        amount=data.amount,
        currency=data.currency,
    )
    return {
        "status": updated["status"],
        "escrow_id": updated["id"],
        "payment_id": updated.get("razorpay_payment_id"),
        "provider": settings.ESCROW_PAYMENT_PROVIDER,
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


@router.post("/approve-release/{escrow_id}")
def approve_release(
    escrow_id: str,
    data: EscrowApproveReleaseRequest | None = None,
    current_user: dict = Depends(get_current_user),
):
    data = data or EscrowApproveReleaseRequest()
    escrow = get_escrow(escrow_id)
    if escrow["employer_id"] != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Only the employer can approve release")

    updated = transition_escrow_status(
        escrow,
        "APPROVED_FOR_RELEASE",
        extra_updates={
            "release_approved_by": current_user["uid"],
            "release_approved_at": datetime.now(UTC).isoformat(),
            "release_approval_note": data.approval_note,
        },
    )
    return {
        "status": updated["status"],
        "escrow_id": updated["id"],
    }


@router.post("/release/{escrow_id}")
def release(
    escrow_id: str,
    data: EscrowReleaseRequest,
    current_user: dict = Depends(require_admin_user),
):
    escrow = get_escrow(escrow_id)
    if escrow["status"] != "APPROVED_FOR_RELEASE":
        raise HTTPException(
            status_code=409,
            detail="Escrow must be in APPROVED_FOR_RELEASE state before release",
        )

    if settings.ESCROW_RELEASE_DEV_MODE:
        if settings.APP_ENV == "production":
            raise HTTPException(status_code=500, detail="Dev escrow release mode is not allowed in production")
        transfer = _build_dev_transfer(escrow)
    elif _is_razorpay_provider():
        from app.services.razorpay_service import transfer_to_worker

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
    else:
        if not data.payout_id:
            raise HTTPException(status_code=400, detail="payout_id is required for manual release")
        transfer = {
            "id": data.payout_id,
            "account": escrow.get("worker_account_id"),
            "amount": escrow["amount"],
            "currency": "INR",
            "mode": "manual",
        }

    payout_reference = transfer["id"] if _is_razorpay_provider() else data.payout_id
    updated = transition_escrow_status(
        escrow,
        "RELEASED",
        extra_updates={
            "released_by": current_user["uid"],
            "released_at": datetime.now(UTC).isoformat(),
            "payout_reference": payout_reference,
            "payout_note": data.payout_note,
        },
    )
    return {
        "status": updated["status"],
        "escrow_id": updated["id"],
        "transfer_id": transfer["id"],
    }


@router.post("/refund/{escrow_id}")
def refund_api(
    escrow_id: str,
    data: EscrowRefundRequest,
    current_user: dict = Depends(require_admin_user),
):
    escrow = get_escrow(escrow_id)

    if _is_razorpay_provider() and not settings.ESCROW_RELEASE_DEV_MODE:
        if not escrow.get("razorpay_payment_id"):
            raise HTTPException(status_code=400, detail="No payment to refund")

        try:
            from app.services.razorpay_service import refund

            refund_response = refund(escrow["razorpay_payment_id"])
            refund_id = refund_response.get("id")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Refund failed: {str(e)}") from e
    else:
        if not data.refund_id:
            raise HTTPException(status_code=400, detail="refund_id is required for manual refund")
        refund_id = data.refund_id

    updated = transition_escrow_status(
        escrow,
        "REFUNDED",
        extra_updates={
            "refunded_by": current_user["uid"],
            "refunded_at": datetime.now(UTC).isoformat(),
            "refund_reference": refund_id,
            "refund_note": data.refund_note,
        },
    )

    return {
        "status": updated["status"],
        "refund_id": refund_id,
    }
