from pydantic import BaseModel, Field


class EscrowCreateRequest(BaseModel):
    job_id: str = Field(..., min_length=1)
    application_id: str = Field(..., min_length=1)
    employer_id: str = Field(..., min_length=1)
    worker_id: str = Field(..., min_length=1)
    worker_account_id: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0)


class EscrowFundRequest(BaseModel):
    amount: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default="INR", min_length=3, max_length=3)
    payment_id: str | None = Field(default=None, min_length=1)
    funding_reference: str = Field(..., min_length=3)
    funding_note: str | None = Field(default=None, min_length=1)


class EscrowApproveReleaseRequest(BaseModel):
    approval_note: str | None = Field(default=None, min_length=1)


class EscrowReleaseRequest(BaseModel):
    payout_id: str | None = Field(default=None, min_length=3)
    payout_note: str | None = Field(default=None, min_length=1)


class EscrowRefundRequest(BaseModel):
    refund_id: str | None = Field(default=None, min_length=3)
    refund_note: str | None = Field(default=None, min_length=1)
