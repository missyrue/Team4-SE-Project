"""Authentication & Authorization Service (SAD 3.4)

OBS-F-001  POST /api/auth/register
OBS-F-002  POST /api/auth/login
OBS-F-003  POST /api/auth/logout
OBS-SR-001 protected endpoints need a valid session (see app/security.py)
OBS-SR-002 passwords stored as salted hashes (see app/passwords.py)
OBS-SR-005 input validated + parameterised queries (SQLAlchemy)
"""
import re

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cart, SessionToken, User
from app.passwords import hash_password, verify_password
from app.security import create_session, get_bearer_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def _clean_email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 254 or not EMAIL_RE.match(value):
        raise ValueError("must be a valid email address")
    return value


class RegisterIn(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    fullName: str = Field(min_length=1, max_length=100)

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        return _clean_email(v)

    @field_validator("password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("must contain at least one letter and one digit")
        return v

    @field_validator("fullName")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = v.strip()
        if not v or CONTROL_CHARS.search(v):
            raise ValueError("must not be empty or contain control characters")
        return v


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)


@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    # Public registration ALWAYS creates a customer: nobody can sign up as admin.
    user = User(email=body.email, password_hash=hash_password(body.password), full_name=body.fullName, role="customer")
    db.add(user)
    db.flush()
    db.add(Cart(user_id=user.id))  # every customer owns one cart
    db.commit()
    return {"id": user.id, "email": user.email, "fullName": user.full_name, "role": user.role}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    # Same message for "unknown email" and "wrong password" so attackers learn nothing.
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": create_session(db, user), "role": user.role, "fullName": user.full_name}


@router.post("/logout", status_code=204)
def logout(token: str = Depends(get_bearer_token), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.get(SessionToken, token)
    if session:
        db.delete(session)
        db.commit()
    return Response(status_code=204)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "fullName": user.full_name, "role": user.role}
