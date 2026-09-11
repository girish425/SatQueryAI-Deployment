import re
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr

from backend.app.database.mongodb import db_manager
from backend.app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Dependency to extract authenticated user from Authorization header."""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    payload = decode_access_token(token)
    if not payload or "user_id" not in payload:
        return None
    return payload


@router.post("/register")
async def register_user(req: RegisterRequest):
    """Register a new user account with secure password hashing."""
    email = req.email.strip().lower()
    if not email or "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")
    if not req.full_name.strip():
        raise HTTPException(status_code=400, detail="Please provide your full name.")

    # Check if user already exists
    existing = db_manager.get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    pwd_hash = hash_password(req.password)
    user_doc = db_manager.create_user(
        email=email,
        password_hash=pwd_hash,
        full_name=req.full_name.strip()
    )

    user_payload = {
        "user_id": user_doc["user_id"],
        "email": user_doc["email"],
        "full_name": user_doc["full_name"]
    }
    token = create_access_token(user_payload)

    return {
        "status": "success",
        "message": "Account created successfully.",
        "token": token,
        "user": user_payload
    }


@router.post("/login")
async def login_user(req: LoginRequest):
    """Authenticate user credentials and return a signed session token."""
    email = req.email.strip().lower()
    user = db_manager.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(user.get("password_hash", ""), req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user_payload = {
        "user_id": user["user_id"],
        "email": user["email"],
        "full_name": user.get("full_name", email.split("@")[0].title())
    }
    token = create_access_token(user_payload)

    return {
        "status": "success",
        "message": "Logged in successfully.",
        "token": token,
        "user": user_payload
    }


@router.get("/me")
async def get_my_profile(current_user: Optional[dict] = Depends(get_current_user)):
    """Retrieve profile of the currently logged-in user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required or token expired.")
    return {
        "status": "success",
        "user": current_user
    }
