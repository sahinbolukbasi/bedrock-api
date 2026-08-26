import uuid
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.errors import GatewayAPIException
from app.api.deps import get_current_user
from app.domain.schemas import (
    WalletResponse,
    WalletTransactionItem,
    CreditPackageItem,
    CheckoutSessionRequest,
    CheckoutSessionResponse
)
from app.models.entities import User, Wallet, WalletTransaction
from app.services.credit_service import CreditService
from app.services.stripe_service import StripeService

router = APIRouter()


@router.get("", response_model=WalletResponse)
async def get_wallet_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    wallet = await CreditService.get_or_create_wallet(db, current_user.id)
    return wallet


@router.get("/transactions", response_model=List[WalletTransactionItem])
async def list_transactions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    wallet = await CreditService.get_or_create_wallet(db, current_user.id)
    stmt = (
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/packages", response_model=List[CreditPackageItem])
async def list_credit_packages():
    return StripeService.get_packages()


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout(
    body: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        res = await StripeService.create_checkout_session(
            db=db,
            user=current_user,
            package_id=body.package_id,
            success_url=body.success_url,
            cancel_url=body.cancel_url
        )
        return res
    except Exception as e:
        raise GatewayAPIException(status_code=400, message=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Receives and processes verified Stripe webhook events.
    Guaranteed idempotent credit additions.
    """
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    payload_bytes = await request.body()
    try:
        await StripeService.handle_webhook_event(db, payload_bytes, stripe_signature)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dev-fund")
async def dev_fund_wallet(
    amount: Decimal = Decimal("10.00"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Development endpoint to quickly add test credits to current user wallet without Stripe setup.
    """
    tx_ref = f"dev_fund_{uuid.uuid4().hex[:8]}"
    wallet, tx = await CreditService.add_credits(
        db=db,
        user_id=current_user.id,
        amount_usd=amount,
        reference_id=tx_ref,
        transaction_type="BONUS",
        description=f"Developer Test Credits (${amount})"
    )
    return {
        "message": f"Successfully added ${amount} in test credits.",
        "new_balance": float(wallet.balance_usd)
    }


from fastapi.responses import Response

@router.get("/export/transactions.csv")
async def export_my_transactions_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    wallet = await CreditService.get_or_create_wallet(db, current_user.id)
    stmt = (
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(500)
    )
    res = await db.execute(stmt)
    txs = res.scalars().all()

    csv_lines = ["Transaction ID,Type,Amount USD,Balance After USD,Description,Reference ID,Date"]
    for t in txs:
        csv_lines.append(
            f'"{t.id}","{t.type}","{float(t.amount_usd):.4f}","{float(t.balance_after):.4f}","{t.description or ""}","{t.reference_id or ""}","{t.created_at}"'
        )

    csv_data = "\n".join(csv_lines)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=my_bedrock_spending_report.csv"}
    )

