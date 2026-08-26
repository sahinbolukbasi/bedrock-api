import pytest
from app.core.security import (
    generate_api_key,
    hash_api_key,
    get_password_hash,
    verify_password,
    create_access_token,
    decode_jwt_token
)


def test_password_hashing():
    pwd = "SecurePassword123!"
    hashed = get_password_hash(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_flow():
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(user_id, role="user")
    payload = decode_jwt_token(token)
    assert payload.get("sub") == user_id
    assert payload.get("role") == "user"
    assert payload.get("type") == "access"


def test_api_key_generation_and_hashing():
    full_key, prefix, hashed_secret = generate_api_key(prefix_label="live")
    assert full_key.startswith("sk-live-")
    assert prefix.startswith("sk-live-")
    assert len(prefix) > 10
    assert hash_api_key(full_key) == hashed_secret
    # Ensure hashing the prefix alone fails
    assert hash_api_key(prefix) != hashed_secret
