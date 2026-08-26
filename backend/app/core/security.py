import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Any, Dict
import jwt
from passlib.context import CryptContext
import pyotp
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    safe_password = plain_password[:72]
    return pwd_context.verify(safe_password, hashed_password)


def get_password_hash(password: str) -> str:
    safe_password = password[:72]
    return pwd_context.hash(safe_password)


# JWT Tokens
def create_access_token(subject: str, role: str = "user", expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_jwt_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return {}


# API Key generation and hashing
def generate_api_key(prefix_label: str = "live") -> Tuple[str, str, str]:
    """
    Generates a secure API key in format: sk-<prefix_label>-<8_char_prefix><32_char_secret>
    Returns: (full_raw_key, prefix, sha256_hash)
    Raw key is NEVER stored in database, only prefix and sha256_hash.
    """
    random_prefix = secrets.token_hex(4)  # 8 chars
    random_secret = secrets.token_urlsafe(32)
    full_key = f"sk-{prefix_label}-{random_prefix}{random_secret}"
    prefix = f"sk-{prefix_label}-{random_prefix}"
    
    hashed_secret = hash_api_key(full_key)
    return full_key, prefix, hashed_secret


def hash_api_key(api_key: str) -> str:
    """Computes SHA-256 hash of API key for safe database lookup."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


# MFA / TOTP Helpers
def generate_mfa_secret() -> str:
    return pyotp.random_base32()


def get_mfa_provisioning_uri(secret: str, email: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=settings.PROJECT_NAME)


def verify_mfa_token(secret: str, token: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)
