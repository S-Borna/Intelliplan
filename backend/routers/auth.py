"""Authentication endpoints — login, register, session management."""

import json
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Customer, Notification, UserRole, hash_password, verify_password
from backend.schemas import UserRegister, UserLogin, UserOut, TokenOut

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# Simple token store (demo — in production use JWT or Redis)
_tokens: dict[str, str] = {}  # token -> user_id


def create_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    _tokens[token] = user_id
    return token


def get_current_user(db: Session, token: str) -> User | None:
    user_id = _tokens.get(token)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency: extract and validate user from Authorization header."""
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else auth
    if not token:
        raise HTTPException(401, "Not authenticated")
    user = get_current_user(db, token)
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user


def require_handler(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency: require handler or admin role."""
    user = require_user(request, db)
    if user.role not in (UserRole.HANDLER, UserRole.ADMIN):
        raise HTTPException(403, "Handler access required")
    return user


@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    # If customer role, link to or create customer record
    customer_id = data.customer_id
    if data.role == "customer" and not customer_id:
        # Create a customer record automatically
        customer = Customer(
            name=data.full_name,
            company=data.full_name.split()[0] + " AB",
            email=data.email,
        )
        db.add(customer)
        db.flush()
        customer_id = customer.id

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        customer_id=customer_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id)
    return TokenOut(token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password."""
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_token(user.id)
    return TokenOut(token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(require_user)):
    """Get current user profile."""
    return UserOut.model_validate(user)


@router.post("/logout")
def logout(request: Request):
    """Logout — invalidate token."""
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else auth
    _tokens.pop(token, None)
    return {"ok": True}
