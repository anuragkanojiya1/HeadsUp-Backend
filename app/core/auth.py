import json

import firebase_admin
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def _get_or_init_firebase_app():
    existing_apps = getattr(firebase_admin, "_apps", {})
    if existing_apps:
        return firebase_admin.get_app()

    credential = None
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        credential = credentials.Certificate(json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON))
    elif settings.FIREBASE_SERVICE_ACCOUNT_PATH:
        credential = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
    else:
        credential = credentials.ApplicationDefault()

    options = {}
    if settings.FIREBASE_PROJECT_ID:
        options["projectId"] = settings.FIREBASE_PROJECT_ID

    return firebase_admin.initialize_app(credential=credential, options=options or None)


def get_current_user(
    credentials_value: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_debug_user_id: str | None = Header(default=None),
    x_debug_user_email: str | None = Header(default=None),
    x_debug_user_role: str | None = Header(default=None),
):
    if settings.AUTH_DEV_MODE and settings.APP_ENV != "production" and x_debug_user_id:
        role = (x_debug_user_role or "user").lower()
        return {
            "uid": x_debug_user_id,
            "email": x_debug_user_email,
            "claims": {
                "uid": x_debug_user_id,
                "email": x_debug_user_email,
                "role": role,
                "is_admin": role in {"admin", "ops", "superadmin"},
                "auth_mode": "debug",
            },
        }

    if credentials_value is None or credentials_value.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Firebase bearer token or X-Debug-User-Id header",
        )

    try:
        firebase_app = _get_or_init_firebase_app()
        decoded_token = auth.verify_id_token(credentials_value.credentials, app=firebase_app)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
        ) from exc

    uid = decoded_token.get("uid")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token missing uid",
        )

    return {
        "uid": uid,
        "email": decoded_token.get("email"),
        "claims": decoded_token,
    }


def _is_admin_from_claims(claims: dict) -> bool:
    role = str(claims.get("role", "")).lower()
    if role in {"admin", "ops", "superadmin"}:
        return True

    if claims.get("is_admin") is True or claims.get("admin") is True:
        return True

    return False


def require_admin_user(current_user: dict = Depends(get_current_user)):
    if not _is_admin_from_claims(current_user.get("claims", {})):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
