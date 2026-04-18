# app/services/escrow_service.py

from uuid import uuid4
from app.db.supabase import supabase
from app.services.razorpay_service import create_order
from app.utils.state_machine import can_transition

def create_escrow(data):
    order = create_order(data["amount"], str(uuid4()))

    escrow = {
        "id": str(uuid4()),
        "job_id": data["job_id"],
        "application_id": data["application_id"],
        "employer_id": data["employer_id"],
        "worker_id": data["worker_id"],
        "amount": data["amount"],
        "razorpay_order_id": order["id"],
        "status": "INITIATED"
    }

    supabase.table("escrow_transactions").insert(escrow).execute()

    return order

def update_status(order_id, status, payment_id=None):
    update_data = {"status": status}
    if payment_id:
        update_data["razorpay_payment_id"] = payment_id

    supabase.table("escrow_transactions") \
        .update(update_data) \
        .eq("razorpay_order_id", order_id) \
        .execute()

def get_escrow(id):
    return supabase.table("escrow_transactions") \
        .select("*") \
        .eq("id", id).single().execute().data