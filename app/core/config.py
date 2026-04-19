# app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_ENV = os.getenv("APP_ENV", "development").lower()
    AUTH_DEV_MODE = os.getenv("AUTH_DEV_MODE", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
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
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

settings = Settings()
