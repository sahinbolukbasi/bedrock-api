from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    generate_mfa_secret,
    get_mfa_provisioning_uri,
    verify_mfa_token
)
from app.core.errors import AuthenticationError, GatewayAPIException
from app.api.deps import get_current_user
from app.domain.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserProfileResponse,
    MFASetupResponse,
    MFAVerifyRequest
)
from app.models.entities import User, Wallet
from app.services.credit_service import CreditService

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register_user(body: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if email exists
    stmt = select(User).where(User.email == body.email.lower())
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise GatewayAPIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="An account with this email already exists."
        )

    # Create new user
    user = User(
        email=body.email.lower(),
        hashed_password=get_password_hash(body.password),
        full_name=body.full_name,
        role="user",
        is_verified=True  # Auto-verified in development
    )
    db.add(user)
    await db.flush()

    # Create default wallet with $1.00 starter gift credits!
    wallet = Wallet(user_id=user.id, balance_usd=1.00)
    db.add(wallet)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(str(user.id), role=user.role)
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        email=user.email,
        role=user.role,
        mfa_required=False
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(body: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == body.email.lower())
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password.")

    if not user.is_active:
        raise AuthenticationError("This account is currently suspended.")

    # MFA Check
    if user.mfa_enabled:
        if not body.mfa_code:
            return TokenResponse(
                access_token="",
                refresh_token="",
                user_id=user.id,
                email=user.email,
                role=user.role,
                mfa_required=True
            )
        if not verify_mfa_token(user.mfa_secret, body.mfa_code):
            raise AuthenticationError("Invalid 2FA/MFA security code.")

    access_token = create_access_token(str(user.id), role=user.role)
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        email=user.email,
        role=user.role,
        mfa_required=False
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = generate_mfa_secret()
    current_user.mfa_secret = secret
    await db.commit()
    uri = get_mfa_provisioning_uri(secret, current_user.email)
    return MFASetupResponse(secret=secret, provisioning_uri=uri)


@router.post("/mfa/verify")
async def verify_mfa(body: MFAVerifyRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.mfa_secret:
        raise GatewayAPIException(status_code=400, message="MFA has not been initiated. Call /mfa/setup first.")

    if not verify_mfa_token(current_user.mfa_secret, body.code):
        raise AuthenticationError("Invalid verification code.")

    current_user.mfa_enabled = True
    await db.commit()
    return {"message": "Two-Factor Authentication successfully enabled."}
