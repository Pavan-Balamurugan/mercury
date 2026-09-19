from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth import create_access_token, decode_access_token, hash_password, verify_password
from app.db import get_db
from app.models import User
from app.schemas import Token, UserCreate, UserLogin, UserOut
from app.sentinel_logger import log_event

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        log_event("WARN", "REGISTER_FAILED", f"Duplicate email registration attempt: {payload.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    log_event("INFO", "USER_REGISTERED", f"New user registered: {payload.email}", user_id=str(user.id))
    return user


@router.post("/auth/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        log_event("WARN", "LOGIN_FAILED", f"Failed login attempt for {payload.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user.id), user.role)
    log_event("INFO", "LOGIN_SUCCESS", f"User logged in: {payload.email}", user_id=str(user.id))
    return Token(access_token=token)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except Exception:
        log_event("WARN", "AUTH_TOKEN_INVALID", "Invalid or expired token presented")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user