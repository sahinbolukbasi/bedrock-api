import uuid
from decimal import Decimal
from typing import Dict, List, Optional
import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.entities import CreditPurchase, User
from app.services.credit_service import CreditService
from loguru import logger

stripe.api_key = settings.STRIPE_SECRET_KEY

# Predefined credit packages
CREDIT_PACKAGES: Dict[str, Dict] = {
    "tier_5": {"amount": Decimal("5.00"), "bonus": Decimal("0.00"), "total": Decimal("5.00"), "name": "Starter ($5)"},
    "tier_10": {"amount": Decimal("10.00"), "bonus": Decimal("0.50"), "total": Decimal("10.50"), "name": "Builder ($10 + 5% Bonus)"},
    "tier_25": {"amount": Decimal("25.00"), "bonus": Decimal("2.50"), "total": Decimal("27.50"), "name": "Pro ($25 + 10% Bonus)"},
    "tier_50": {"amount": Decimal("50.00"), "bonus": Decimal("7.50"), "total": Decimal("57.50"), "name": "Scale ($50 + 15% Bonus)"},
    "tier_100": {"amount": Decimal("100.00"), "bonus": Decimal("20.00"), "total": Decimal("120.00"), "name": "Enterprise ($100 + 20% Bonus)"},
}


class StripeService:
    @staticmethod
    def get_packages() -> List[Dict]:
        packages = []
        for pkg_id, details in CREDIT_PACKAGES.items():
            packages.append({
                "package_id": pkg_id,
                "name": details["name"],
                "amount_usd": details["amount"],
                "bonus_usd": details["bonus"],
                "total_credits": details["total"]
            })
        return packages

    @staticmethod
    async def create_checkout_session(
        db: AsyncSession,
        user: User,
        package_id: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, str]:
        pkg = CREDIT_PACKAGES.get(package_id)
        if not pkg:
            raise ValueError("Invalid credit package selected.")

        succ_url = success_url or "http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com/billing?payment=success"
        canc_url = cancel_url or "http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com/billing?payment=cancelled"

        # If Stripe key is in placeholder/mock mode, create a session on AWS ALB
        if settings.STRIPE_SECRET_KEY.startswith("sk_test_placeholder"):
            mock_session_id = f"cs_mock_{uuid.uuid4().hex}"
            purchase = CreditPurchase(
                user_id=user.id,
                stripe_session_id=mock_session_id,
                amount_usd=pkg["amount"],
                credits_added=pkg["total"],
                status="PENDING"
            )
            db.add(purchase)
            await db.commit()
            return {
                "checkout_url": f"http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com/billing/mock-checkout?session_id={mock_session_id}&pkg={package_id}",
                "session_id": mock_session_id
            }

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=user.email,
            client_reference_id=str(user.id),
            metadata={"package_id": package_id, "user_id": str(user.id)},
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Bedrock AI Gateway - {pkg['name']}",
                        "description": f"Adds ${pkg['total']} in AI generation credits.",
                    },
                    "unit_amount": int(pkg["amount"] * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=succ_url,
            cancel_url=canc_url,
        )

        purchase = CreditPurchase(
            user_id=user.id,
            stripe_session_id=session.id,
            amount_usd=pkg["amount"],
            credits_added=pkg["total"],
            status="PENDING"
        )
        db.add(purchase)
        await db.commit()

        return {
            "checkout_url": session.url,
            "session_id": session.id
        }

    @staticmethod
    async def handle_webhook_event(
        db: AsyncSession,
        payload_bytes: bytes,
        sig_header: str
    ) -> bool:
        """
        Verifies cryptographic signature from Stripe and idempotently applies credits.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload_bytes, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception as e:
            logger.error(f"Stripe webhook signature verification failed: {e}")
            raise ValueError(f"Webhook signature error: {e}")

        event_type = event.get("type")
        logger.info(f"Received Stripe webhook event: {event_type}")

        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            session_id = session.get("id")
            client_ref_id = session.get("client_reference_id")
            payment_intent = session.get("payment_intent")

            # Check purchase record
            stmt = select(CreditPurchase).where(CreditPurchase.stripe_session_id == session_id)
            res = await db.execute(stmt)
            purchase = res.scalar_one_or_none()

            if not purchase and client_ref_id:
                # Create purchase record if missing
                pkg_id = session.get("metadata", {}).get("package_id", "tier_10")
                pkg = CREDIT_PACKAGES.get(pkg_id, CREDIT_PACKAGES["tier_10"])
                purchase = CreditPurchase(
                    user_id=uuid.UUID(client_ref_id),
                    stripe_session_id=session_id,
                    stripe_payment_intent_id=payment_intent,
                    amount_usd=pkg["amount"],
                    credits_added=pkg["total"],
                    status="PENDING"
                )
                db.add(purchase)
                await db.flush()

            if purchase and purchase.status != "COMPLETED":
                purchase.status = "COMPLETED"
                purchase.stripe_payment_intent_id = payment_intent
                # Add credits to wallet atomically
                await CreditService.add_credits(
                    db=db,
                    user_id=purchase.user_id,
                    amount_usd=purchase.credits_added,
                    reference_id=session_id,
                    transaction_type="PURCHASE",
                    description=f"Stripe payment ({session_id[:14]}...)"
                )
                await db.commit()
                logger.info(f"Successfully credited ${purchase.credits_added} to user {purchase.user_id}")

        return True
