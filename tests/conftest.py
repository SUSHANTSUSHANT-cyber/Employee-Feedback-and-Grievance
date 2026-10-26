import os
import sys
from pathlib import Path
import pytest
from sqlalchemy import text

# Ensure api directory is on sys.path
api_path = Path(__file__).resolve().parent.parent / "api"
if str(api_path) not in sys.path:
    sys.path.insert(0, str(api_path))

from app.main import app
from app.database import SessionLocal, engine
from app.models import AdminSession, AdminUser, DeletedGrievance, InteractionLog
from app.auth import COOKIE_NAME, token_hash
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def admin_client(client, db):
    """Client with a valid admin session cookie for testing protected endpoints."""
    import secrets
    from datetime import datetime, timedelta, timezone

    token = secrets.token_urlsafe(32)
    thash = token_hash(token)

    # Ensure admin user exists with id=1
    admin_user = db.get(AdminUser, 1)
    if not admin_user:
        admin_user = AdminUser(id=1, username="admin", passwordHash="dummy")
        db.add(admin_user)
        db.commit()

    session = AdminSession(
        tokenHash=thash,
        adminId=1,
        expiresAt=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db.add(session)
    db.commit()

    client.cookies.set(COOKIE_NAME, token)

    yield client

    # Cleanup session
    client.cookies.delete(COOKIE_NAME)
    db.execute(text("DELETE FROM admin_sessions WHERE \"tokenHash\" = :th"), {"th": thash})
    db.commit()


@pytest.fixture(scope="session", autouse=True)
def verify_baseline_counts():
    """Verify unrelated tables remain intact before and after all tests."""
    unrelated_tables = [
        ("employees", 843),
        ("custom_categories", 8),
        ("custom_presets", 14),
        ("admin_config", 1),
        ("interaction_logs_duplicate_backup", 269),
    ]

    with engine.connect() as conn:
        for tbl, expected in unrelated_tables:
            count = conn.execute(text(f'SELECT COUNT(*) FROM "{tbl}"')).scalar()
            assert count == expected, f"Pre-test baseline mismatch for {tbl}: expected {expected}, got {count}"

    yield

    with engine.connect() as conn:
        for tbl, expected in unrelated_tables:
            count = conn.execute(text(f'SELECT COUNT(*) FROM "{tbl}"')).scalar()
            assert count == expected, f"Post-test baseline mismatch for {tbl}: expected {expected}, got {count}"
