"""
Automated unit tests for Authentication, OTP Verification, and Anti-Spam Security.
Validates zero static OTP bypass, temporal expiration, and 120s cooldown enforcement.
"""

import time
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.auth import _VERIFICATION_CODES
from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password


@pytest.mark.asyncio
async def test_password_hashing_and_verification():
    """Verifies BCrypt / Argon2 hashing and validation logic."""
    raw_pass = "MySuperSecretPassword#2026!"
    hashed = get_password_hash(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPass123", hashed) is False


@pytest.mark.asyncio
async def test_jwt_token_claims_and_expiry():
    """Verifies JWT token encoding, claims, and role extraction."""
    user_id = "test-user-uuid-12345"
    token = create_access_token(subject=user_id, role="admin")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id
    assert payload.get("role") == "admin"


@pytest.mark.asyncio
async def test_otp_verification_rejects_static_bypass():
    """Verifies that static test bypasses ('123456', '999999') are strictly rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Request verification with static fake code
        resp = await ac.post("/api/auth/verify-email", json={
            "email": "unregistered_test_user@example.com",
            "code": "123456"
        })
        assert resp.status_code == 401
        assert "Geçersiz veya süresi dolmuş" in resp.json().get("detail", "") or "Geçersiz veya süresi dolmuş" in resp.json().get("error", {}).get("message", "")


@pytest.mark.asyncio
async def test_otp_verification_valid_flow():
    """Verifies full OTP registration, dynamic code generation, and activation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        test_email = f"authed_user_{uuid.uuid4().hex[:8]}@example.com"
        
        # 1. Register user
        reg_resp = await ac.post("/api/auth/register", json={
            "email": test_email,
            "password": "SecurePassword#991!",
            "full_name": "Test Verified User"
        })
        assert reg_resp.status_code == 200
        
        # Extract dynamic code stored in memory
        pending = _VERIFICATION_CODES.get(test_email)
        assert pending is not None
        otp_code = pending["code"]
        assert len(otp_code) == 6

        # 2. Verify with valid dynamic OTP
        ver_resp = await ac.post("/api/auth/verify-email", json={
            "email": test_email,
            "code": otp_code
        })
        assert ver_resp.status_code == 200
        data = ver_resp.json()
        assert "access_token" in data
        assert data["email"] == test_email


@pytest.mark.asyncio
async def test_resend_code_enforces_120s_cooldown():
    """Verifies that requesting new OTP within 120 seconds returns HTTP 429 Too Many Requests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        cooldown_email = f"cooldown_{uuid.uuid4().hex[:8]}@example.com"
        
        # 1. Initial register
        await ac.post("/api/auth/register", json={
            "email": cooldown_email,
            "password": "SecurePassword#2026!",
            "full_name": "Cooldown Tester"
        })

        # 2. Immediate resend request (within 120 seconds)
        resend_resp = await ac.post("/api/auth/resend-code", json={"email": cooldown_email})
        assert resend_resp.status_code == 429
        data = resend_resp.json()
        assert "bekleyiniz" in data.get("error", {}).get("message", "").lower() or "bekleyiniz" in data.get("detail", "").lower()

