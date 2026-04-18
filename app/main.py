# app/main.py

from fastapi import FastAPI
from app.routes import escrow, webhook

app = FastAPI()

app.include_router(escrow.router, prefix="/escrow")
app.include_router(webhook.router, prefix="/webhook")