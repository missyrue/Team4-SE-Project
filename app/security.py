"""Session handling + role checks shared by every router.

* create_session()   -> random token stored in the DB (logout can really end it)
* get_current_user() -> FastAPI dependency: 401 if not logged in      (OBS-SR-001)
* require_admin()    -> FastAPI dependency: 403 if not an admin       (OBS-SR-003)

Password hashing lives in app/passwords.py.
"""
import secrets
from datetime import timedelta

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app import config
from app.database import get_db
from app.models import SessionToken, User, utcnow


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(SessionToken(token=token, user_id=user.id))
    db.commit()
    return token


def get_bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    return authorization[7:].strip()


def get_current_user(token: str = Depends(get_bearer_token), db: Session = Depends(get_db)) -> User:
    session = db.get(SessionToken, token)
    if session is None or utcnow() - session.created_at > timedelta(hours=config.SESSION_HOURS):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user
