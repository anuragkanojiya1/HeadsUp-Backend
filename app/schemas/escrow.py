from pydantic import BaseModel, Field


class EscrowCreateRequest(BaseModel):
    job_id: str = Field(..., min_length=1)
    application_id: str = Field(..., min_length=1)
    employer_id: str = Field(..., min_length=1)
    worker_id: str = Field(..., min_length=1)
    worker_account_id: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0)
