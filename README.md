# Escrow Backend (FastAPI)

Backend service for escrow lifecycle management between employers and workers.
The service supports two payment providers:

- `manual` (default): for off-platform transfers and confirmations
- `razorpay`: for automated order, transfer, and refund actions

## Installation

1. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Server

To run the server in development mode:
```
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Environment

Required:

- `SUPABASE_URL`
- `SUPABASE_KEY`

Optional:

- `ESCROW_PAYMENT_PROVIDER=manual|razorpay` (default: `manual`)
- `ESCROW_RELEASE_DEV_MODE=true|false` (default: `false`)
- `AUTH_DEV_MODE=true|false` (default: `false`)
- Razorpay keys/webhook only if provider is `razorpay`

## DB Migration (Required For Audit Fields)

Run SQL file in Supabase SQL editor:

- `sql/2026-04-23_escrow_audit_columns.sql`

## Escrow Flow (Manual Mode)

1. `POST /escrow/create` (employer) -> creates escrow in `INITIATED`
2. `POST /escrow/fund/{escrow_id}` (admin) -> marks escrow `FUNDED` with funding proof
3. `POST /escrow/submit-work/{escrow_id}` (worker) -> marks escrow `WORK_SUBMITTED`
4. `POST /escrow/approve-release/{escrow_id}` (employer) -> marks escrow `APPROVED_FOR_RELEASE`
5. `POST /escrow/release/{escrow_id}` (admin) -> marks escrow `RELEASED` with payout proof
6. `POST /escrow/refund/{escrow_id}` (admin, if applicable) -> marks escrow `REFUNDED` with refund proof

## Local Testing (Swagger/Postman)

Use `AUTH_DEV_MODE=true` and headers:

- Employer calls: `X-Debug-User-Id: emp_1`, `X-Debug-User-Role: user`
- Worker calls: `X-Debug-User-Id: worker_1`, `X-Debug-User-Role: user`
- Admin calls: `X-Debug-User-Id: admin_1`, `X-Debug-User-Role: admin`

Suggested payloads:

1. `POST /escrow/create`
```json
{
  "job_id": "job_101",
  "application_id": "app_201",
  "employer_id": "emp_1",
  "worker_id": "worker_1",
  "worker_account_id": "manual_worker_account_1",
  "amount": 50000
}
```

2. `POST /escrow/fund/{escrow_id}`
```json
{
  "amount": 50000,
  "currency": "INR",
  "funding_reference": "UTR123456789",
  "funding_note": "Employer transfer received",
  "payment_id": "bank_txn_123"
}
```

3. `POST /escrow/submit-work/{escrow_id}` with worker header

4. `POST /escrow/approve-release/{escrow_id}`
```json
{
  "approval_note": "Deliverables accepted"
}
```

5. `POST /escrow/release/{escrow_id}`
```json
{
  "payout_id": "NEFT987654321",
  "payout_note": "Paid to worker account"
}
```

6. `POST /escrow/refund/{escrow_id}` (alternative path)
```json
{
  "refund_id": "REF123456789",
  "refund_note": "Refunded to employer"
}
```

## API Docs

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
