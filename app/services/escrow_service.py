from uuid import uuid4
from fastapi import HTTPException
from app.db.supabase import supabase
from app.services.razorpay_service import create_order
from app.utils.state_machine import can_transition, VALID_TRANSITIONS


def _require_single_record(response, error_message: str):
    data = getattr(response, "data", None)
    if not data:
        raise HTTPException(status_code=404, detail=error_message)
    return data


def create_escrow(data):
    order = create_order(data["amount"], str(uuid4()))

    escrow = {
        "id": str(uuid4()),
        "job_id": data["job_id"],
        "application_id": data["application_id"],
        "employer_id": data["employer_id"],
        "worker_id": data["worker_id"],
        "worker_account_id": data["worker_account_id"],
        "amount": data["amount"],
        "razorpay_order_id": order["id"],
        "status": "INITIATED"
    }

    supabase.table("escrow_transactions").insert(escrow).execute()

    return {
        "escrow_id": escrow["id"],
        "amount": escrow["amount"],
        "order": order,
    }


def get_escrow(escrow_id):
    response = (
        supabase.table("escrow_transactions")
        .select("*")
        .eq("id", escrow_id)
        .single()
        .execute()
    )
    return _require_single_record(response, "Escrow not found")


def get_escrow_by_order_id(order_id: str):
    response = (
        supabase.table("escrow_transactions")
        .select("*")
        .eq("razorpay_order_id", order_id)
        .single()
        .execute()
    )
    return _require_single_record(response, "Escrow not found for Razorpay order")


def transition_escrow_status(escrow: dict, new_status: str, payment_id: str | None = None):
    current_status = escrow["status"]
    if current_status == new_status:
        return escrow

    if not can_transition(current_status, new_status):
        allowed = ", ".join(VALID_TRANSITIONS.get(current_status, [])) or "none"
        raise HTTPException(
            status_code=409,
            detail=f"Cannot transition escrow from {current_status} to {new_status}. Allowed: {allowed}",
        )

    update_data = {"status": new_status}
    if payment_id:
        update_data["razorpay_payment_id"] = payment_id

    response = (
        supabase.table("escrow_transactions")
        .update(update_data) \
        .eq("id", escrow["id"]) \
        .execute()
    )
    updated_records = getattr(response, "data", None) or []
    if updated_records:
        return updated_records[0]

    escrow.update(update_data)
    return escrow


def mark_order_funded(order_id: str, payment_id: str):
    escrow = get_escrow_by_order_id(order_id)
    return transition_escrow_status(escrow, "FUNDED", payment_id=payment_id)
