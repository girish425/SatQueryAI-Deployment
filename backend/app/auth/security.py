import os
import time
import hmac
import hashlib
import secrets
import base64
import json
from typing import Dict, Any, Optional

SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("AUTH_SECRET") or "satquery_ai_secret_key_2026_super_secure"
TOKEN_EXPIRY_SECONDS = 7 * 24 * 3600  # 7 days


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${key.hex()}"


def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a provided password against the stored salt$hash string."""
    try:
        if not stored_password or "$" not in stored_password:
            return False
        salt, key_hex = stored_password.split("$", 1)
        new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return hmac.compare_digest(key_hex, new_key.hex())
    except Exception:
        return False


def create_access_token(user_data: Dict[str, Any], expires_in: int = TOKEN_EXPIRY_SECONDS) -> str:
    """Create a signed URL-safe session token containing user payload and expiration."""
    payload = {
        **user_data,
        "exp": int(time.time()) + expires_in
    }
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip('=')
    
    signature = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify signature and return token payload if valid and unexpired."""
    try:
        if not token or "." not in token:
            return None
        payload_b64, signature = token.split(".", 1)
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
            
        # Re-pad base64
        padded = payload_b64 + '=' * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(padded.encode('utf-8')).decode('utf-8')
        payload = json.loads(payload_json)
        
        if payload.get("exp", 0) < int(time.time()):
            return None  # Expired
            
        return payload
    except Exception:
        return None
