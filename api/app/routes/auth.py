from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..auth import COOKIE_NAME, create_session, require_admin, revoke_all_sessions, token_hash, verify_password
from ..config import settings
from ..database import get_db
from ..models import AdminSession, AdminUser
from ..schemas import AuthUserOut, ChangePasswordRequest, LoginRequest


router = APIRouter(prefix="/auth", tags=["authentication"])


def set_session_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        COOKIE_NAME, token, max_age=max_age, httponly=True, samesite="lax",
        secure=settings.auth_cookie_secure, path="/",
    )


@router.post("/login", response_model=AuthUserOut)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    admin = db.scalar(select(AdminUser).where(AdminUser.username == "admin"))
    if not admin or data.username != "admin" or not verify_password(data.password, admin.passwordHash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token, max_age = create_session(db, admin)
    set_session_cookie(response, token, max_age)
    return AuthUserOut(username=admin.username)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        db.execute(delete(AdminSession).where(AdminSession.tokenHash == token_hash(token)))
        db.commit()
    response.delete_cookie(COOKIE_NAME, path="/", secure=settings.auth_cookie_secure, samesite="lax")


@router.get("/me", response_model=AuthUserOut)
def me(admin: AdminUser = Depends(require_admin)):
    return AuthUserOut(username=admin.username)


@router.post("/change-password", status_code=204)
def change_password(data: ChangePasswordRequest, response: Response, db: Session = Depends(get_db), admin: AdminUser = Depends(require_admin)):
    if not verify_password(data.currentPassword, admin.passwordHash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if not data.newPassword:
        raise HTTPException(status_code=422, detail="New password must not be empty")
    from ..auth import hash_password
    admin.passwordHash = hash_password(data.newPassword)
    revoke_all_sessions(db, admin.id)
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/", secure=settings.auth_cookie_secure, samesite="lax")
