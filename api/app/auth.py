"""Master-admin password and opaque cookie-session helpers."""

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal, get_db
from .models import AdminSession, AdminUser


COOKIE_NAME = "employee_assistant_admin_session"
PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(derived).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), base64.b64decode(salt), int(iterations)
        )
        return hmac.compare_digest(base64.b64encode(derived).decode("ascii"), expected)
    except (TypeError, ValueError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def initialize_admin() -> None:
    """Create the one admin exactly once, only when an initial password is supplied."""
    with SessionLocal() as db:
        if db.scalar(select(AdminUser.id).limit(1)) is not None:
            return
        if not settings.admin_initial_password:
            return
        db.add(AdminUser(id=1, username="admin", passwordHash=hash_password(settings.admin_initial_password)))
        db.commit()


def create_session(db: Session, admin: AdminUser) -> tuple[str, int]:
    lifetime = max(1, settings.admin_session_hours) * 60 * 60
    token = secrets.token_urlsafe(32)
    db.add(AdminSession(
        tokenHash=token_hash(token),
        adminId=admin.id,
        expiresAt=datetime.now(timezone.utc) + timedelta(seconds=lifetime),
    ))
    db.commit()
    return token, lifetime


def require_admin(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    session = db.get(AdminSession, token_hash(token))
    now = datetime.now(timezone.utc)
    if not session or session.expiresAt <= now:
        if session:
            db.delete(session)
            db.commit()
        raise HTTPException(status_code=401, detail="Authentication required")
    admin = db.get(AdminUser, session.adminId)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    return admin


def revoke_all_sessions(db: Session, admin_id: int) -> None:
    db.execute(delete(AdminSession).where(AdminSession.adminId == admin_id))
