from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import audit, models, schemas, security
from .database import get_db
from .settings import get_settings

router = APIRouter()
settings = get_settings()

security_scheme = HTTPBearer(auto_error=False)


@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.AuthUser).filter_by(email=user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.AuthUser(email=user_in.email, password_hash=security.hash_password(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    audit.log_event(db, "register", user.id)
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(request: Request, credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    if security.is_throttled(credentials.email):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts")
    user = db.query(models.AuthUser).filter_by(email=credentials.email).first()
    if not user or not security.verify_password(credentials.password, user.password_hash):
        security.register_failed_attempt(credentials.email)
        raise HTTPException(status_code=400, detail="Invalid credentials")
    security.clear_failed_attempts(credentials.email)
    access_token = security.create_access_token({"sub": str(user.id)})
    refresh_token = str(uuid4())
    rt = models.RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expires_days),
    )
    db.add(rt)
    db.commit()
    audit.log_event(
        db,
        "login",
        user.id,
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
    )
    return schemas.TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(data: schemas.RefreshRequest, db: Session = Depends(get_db)):
    token_row = db.query(models.RefreshToken).filter_by(token=data.refresh_token).first()
    if not token_row or token_row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    access_token = security.create_access_token({"sub": str(token_row.user_id)})
    return schemas.TokenResponse(access_token=access_token, refresh_token=data.refresh_token)


@router.post("/forgot-password")
def forgot_password(data: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.AuthUser).filter_by(email=data.email).first()
    if not user:
        return {"message": "ok"}
    token = str(uuid4())
    pr = models.PasswordReset(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(pr)
    db.commit()
    audit.log_event(db, "forgot-password", user.id)
    return {"message": "ok"}


@router.post("/reset-password")
def reset_password(data: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    pr = db.query(models.PasswordReset).filter_by(token=data.token, used=False).first()
    if not pr or pr.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid token")
    user = db.query(models.AuthUser).filter_by(id=pr.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    user.password_hash = security.hash_password(data.password)
    pr.used = True
    db.commit()
    audit.log_event(db, "reset-password", user.id)
    return {"message": "ok"}


@router.get("/me", response_model=schemas.UserRead)
def me(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = security.decode_token(credentials.credentials)
        user_id = payload.get("sub")
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    user = db.get(models.AuthUser, UUID(str(user_id)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
