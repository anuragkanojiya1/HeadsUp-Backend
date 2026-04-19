# app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    RAZORPAY_KEY = os.getenv("RAZORPAY_KEY")
    RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")
    WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    ESCROW_RELEASE_DEV_MODE = os.getenv("ESCROW_RELEASE_DEV_MODE", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

settings = Settings()
