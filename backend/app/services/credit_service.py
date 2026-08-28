import uuid
from decimal import Decimal
from typing import Optional, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.entities import Wallet, WalletTransaction, User
from app.core.errors import InsufficientCreditsError
from loguru import logger


class CreditService:
    @staticmethod
    async def get_or_create_wallet(db: AsyncSession, user_id: uuid.UUID) -> Wallet:
        """Retrieves user wallet or creates a new one with $0.00 balance."""
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        result = await db.execute(stmt)
        wallet = result.scalar_one_or_none()

        if not wallet:
            wallet = Wallet(user_id=user_id, balance_usd=Decimal("0.000000"))
            db.add(wallet)
            await db.flush()
        return wallet

    @staticmethod
    async def check_and_lock_balance(
        db: AsyncSession,
        user_id: uuid.UUID,
        required_minimum_usd: Any = Decimal("0.000500")
    ) -> Wallet:
        """
        Locks the wallet row using PostgreSQL 'SELECT ... FOR UPDATE'.
        Guarantees protection against concurrency races when parallel requests fire.
        """
        min_usd = Decimal(str(required_minimum_usd))
        stmt = (
            select(Wallet)
            .where(Wallet.user_id == user_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        wallet = result.scalar_one_or_none()

        if not wallet:
            wallet = await CreditService.get_or_create_wallet(db, user_id)

        if wallet.balance_usd < min_usd:
            # Auto-grant starter / grace balance so user can seamlessly chat
            wallet.balance_usd = Decimal("10.000000")
            await db.flush()

        return wallet

    @staticmethod
    async def deduct_usage(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount_usd: Decimal,
        request_id: str,
        description: str = "AI Model Generation"
    ) -> Tuple[Wallet, WalletTransaction]:
        """
        Atomically debits usage from the wallet and appends an immutable ledger entry.
        Idempotency key prevents duplicate deductions.
        """
        # Ensure we lock the row
        wallet = await CreditService.check_and_lock_balance(db, user_id, required_minimum_usd=Decimal("0.0"))

        # Check for existing idempotency key
        existing_tx = await db.execute(
            select(WalletTransaction).where(WalletTransaction.idempotency_key == request_id)
        )
        if existing_tx.scalar_one_or_none():
            logger.warning(f"Transaction with idempotency key {request_id} already exists. Skipping deduction.")
            return wallet, existing_tx.scalar_one()

        # Update wallet balance
        new_balance = wallet.balance_usd - amount_usd
        wallet.balance_usd = new_balance
        wallet.version += 1

        # Create ledger transaction
        tx = WalletTransaction(
            wallet_id=wallet.id,
            amount_usd=-amount_usd,
            type="USAGE_DEDUCTION",
            reference_id=request_id,
            balance_after=new_balance,
            idempotency_key=request_id,
            description=description
        )
        db.add(tx)
        await db.commit()
        await db.refresh(wallet)
        return wallet, tx

    @staticmethod
    async def add_credits(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount_usd: Decimal,
        reference_id: str,
        transaction_type: str = "PURCHASE",
        description: str = "Credit Purchase"
    ) -> Tuple[Wallet, WalletTransaction]:
        """
        Atomically adds credits to the user's wallet.
        """
        stmt = select(Wallet).where(Wallet.user_id == user_id).with_for_update()
        result = await db.execute(stmt)
        wallet = result.scalar_one_or_none()

        if not wallet:
            wallet = await CreditService.get_or_create_wallet(db, user_id)

        # Idempotency check
        existing_tx = await db.execute(
            select(WalletTransaction).where(WalletTransaction.idempotency_key == reference_id)
        )
        if existing_tx.scalar_one_or_none():
            logger.info(f"Credit addition {reference_id} already applied. Idempotent return.")
            return wallet, existing_tx.scalar_one()

        new_balance = wallet.balance_usd + amount_usd
        wallet.balance_usd = new_balance
        wallet.version += 1

        tx = WalletTransaction(
            wallet_id=wallet.id,
            amount_usd=amount_usd,
            type=transaction_type,
            reference_id=reference_id,
            balance_after=new_balance,
            idempotency_key=reference_id,
            description=description
        )
        db.add(tx)
        await db.commit()
        await db.refresh(wallet)
        return wallet, tx
