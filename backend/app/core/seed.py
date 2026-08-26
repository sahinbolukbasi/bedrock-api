import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.entities import ModelCatalog, ModelPricing, User, Wallet
from app.core.security import get_password_hash
from app.core.config import settings
from loguru import logger

INITIAL_MODELS = [
    # --- Anthropic Claude Family ---
    {
        "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "name": "claude-3-5-sonnet-20241022",
        "display_name": "Anthropic Claude 3.5 Sonnet v2",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 200000,
        "capabilities": {"vision": True, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.003000"),
            "provider_out": Decimal("0.015000"),
            "customer_in": Decimal("0.003600"),
            "customer_out": Decimal("0.018000"),
            "margin": Decimal("20.00"),
        }
    },
    {
        "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",
        "name": "claude-3-5-haiku",
        "display_name": "Anthropic Claude 3.5 Haiku",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 200000,
        "capabilities": {"vision": True, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.000800"),
            "provider_out": Decimal("0.004000"),
            "customer_in": Decimal("0.001000"),
            "customer_out": Decimal("0.005000"),
            "margin": Decimal("25.00"),
        }
    },
    {
        "model_id": "anthropic.claude-3-opus-20240229-v1:0",
        "name": "claude-3-opus",
        "display_name": "Anthropic Claude 3 Opus",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 200000,
        "capabilities": {"vision": True, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.015000"),
            "provider_out": Decimal("0.075000"),
            "customer_in": Decimal("0.018000"),
            "customer_out": Decimal("0.090000"),
            "margin": Decimal("20.00"),
        }
    },
    {
        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
        "name": "claude-3-sonnet",
        "display_name": "Anthropic Claude 3 Sonnet",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 200000,
        "capabilities": {"vision": True, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.003000"),
            "provider_out": Decimal("0.015000"),
            "customer_in": Decimal("0.003600"),
            "customer_out": Decimal("0.018000"),
            "margin": Decimal("20.00"),
        }
    },

    # --- Amazon Nova Family ---
    {
        "model_id": "amazon.nova-pro-v1:0",
        "name": "nova-pro",
        "display_name": "Amazon Nova Pro",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 300000,
        "capabilities": {"vision": True, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.000800"),
            "provider_out": Decimal("0.003200"),
            "customer_in": Decimal("0.001000"),
            "customer_out": Decimal("0.004000"),
            "margin": Decimal("25.00"),
        }
    },
    {
        "model_id": "amazon.nova-lite-v1:0",
        "name": "nova-lite",
        "display_name": "Amazon Nova Lite",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 300000,
        "capabilities": {"vision": True, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.000060"),
            "provider_out": Decimal("0.000240"),
            "customer_in": Decimal("0.000080"),
            "customer_out": Decimal("0.000300"),
            "margin": Decimal("33.00"),
        }
    },
    {
        "model_id": "amazon.nova-micro-v1:0",
        "name": "nova-micro",
        "display_name": "Amazon Nova Micro",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 128000,
        "capabilities": {"vision": False, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.000035"),
            "provider_out": Decimal("0.000140"),
            "customer_in": Decimal("0.000050"),
            "customer_out": Decimal("0.000180"),
            "margin": Decimal("40.00"),
        }
    },

    # --- Meta Llama Family ---
    {
        "model_id": "meta.llama3-3-70b-instruct-v1:0",
        "name": "llama-3.3-70b",
        "display_name": "Meta Llama 3.3 70B Instruct",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 128000,
        "capabilities": {"vision": False, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.000720"),
            "provider_out": Decimal("0.000720"),
            "customer_in": Decimal("0.000900"),
            "customer_out": Decimal("0.000900"),
            "margin": Decimal("25.00"),
        }
    },
    {
        "model_id": "meta.llama3-1-405b-instruct-v1:0",
        "name": "llama-3.1-405b",
        "display_name": "Meta Llama 3.1 405B Instruct",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 128000,
        "capabilities": {"vision": False, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.002400"),
            "provider_out": Decimal("0.002400"),
            "customer_in": Decimal("0.003000"),
            "customer_out": Decimal("0.003000"),
            "margin": Decimal("25.00"),
        }
    },
    {
        "model_id": "meta.llama3-1-70b-instruct-v1:0",
        "name": "llama-3.1-70b",
        "display_name": "Meta Llama 3.1 70B Instruct",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 128000,
        "capabilities": {"vision": False, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.000720"),
            "provider_out": Decimal("0.000720"),
            "customer_in": Decimal("0.000900"),
            "customer_out": Decimal("0.000900"),
            "margin": Decimal("25.00"),
        }
    },
    {
        "model_id": "meta.llama3-1-8b-instruct-v1:0",
        "name": "llama-3.1-8b",
        "display_name": "Meta Llama 3.1 8B Instruct",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 128000,
        "capabilities": {"vision": False, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.000220"),
            "provider_out": Decimal("0.000220"),
            "customer_in": Decimal("0.000300"),
            "customer_out": Decimal("0.000300"),
            "margin": Decimal("36.00"),
        }
    },

    # --- Mistral AI Family ---
    {
        "model_id": "mistral.mistral-large-2407-v1:0",
        "name": "mistral-large-2407",
        "display_name": "Mistral Large 2 (24.07)",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 128000,
        "capabilities": {"vision": False, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.002000"),
            "provider_out": Decimal("0.006000"),
            "customer_in": Decimal("0.002500"),
            "customer_out": Decimal("0.007500"),
            "margin": Decimal("25.00"),
        }
    },
    {
        "model_id": "mistral.mistral-small-2402-v1:0",
        "name": "mistral-small",
        "display_name": "Mistral Small",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 32000,
        "capabilities": {"vision": False, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.000200"),
            "provider_out": Decimal("0.000600"),
            "customer_in": Decimal("0.000300"),
            "customer_out": Decimal("0.000800"),
            "margin": Decimal("33.00"),
        }
    },

    # --- Cohere Family ---
    {
        "model_id": "cohere.command-r-plus-v1:0",
        "name": "command-r-plus",
        "display_name": "Cohere Command R+",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 128000,
        "capabilities": {"vision": False, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.003000"),
            "provider_out": Decimal("0.015000"),
            "customer_in": Decimal("0.003600"),
            "customer_out": Decimal("0.018000"),
            "margin": Decimal("20.00"),
        }
    },
    {
        "model_id": "cohere.command-r-v1:0",
        "name": "command-r",
        "display_name": "Cohere Command R",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 128000,
        "capabilities": {"vision": False, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.000500"),
            "provider_out": Decimal("0.001500"),
            "customer_in": Decimal("0.000700"),
            "customer_out": Decimal("0.002000"),
            "margin": Decimal("33.00"),
        }
    },

    # --- Amazon Titan Text Family ---
    {
        "model_id": "amazon.titan-text-premier-v1:0",
        "name": "titan-text-premier",
        "display_name": "Amazon Titan Text Premier",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 32000,
        "capabilities": {"vision": False, "tools": True, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.000500"),
            "provider_out": Decimal("0.001500"),
            "customer_in": Decimal("0.000700"),
            "customer_out": Decimal("0.002000"),
            "margin": Decimal("33.00"),
        }
    },
    {
        "model_id": "amazon.titan-text-express-v1",
        "name": "titan-text-express",
        "display_name": "Amazon Titan Text Express",
        "provider": "BEDROCK",
        "type": "CHAT",
        "context_window": 8000,
        "capabilities": {"vision": False, "tools": False, "streaming": True},
        "pricing": {
            "provider_in": Decimal("0.000200"),
            "provider_out": Decimal("0.000600"),
            "customer_in": Decimal("0.000300"),
            "customer_out": Decimal("0.000800"),
            "margin": Decimal("33.00"),
        }
    },

    # --- Image Generation Models ---
    {
        "model_id": "amazon.titan-image-generator-v2:0",
        "name": "titan-image-v2",
        "display_name": "Amazon Titan Image Generator G1 v2",
        "provider": "BEDROCK",
        "type": "IMAGE",
        "context_window": 0,
        "capabilities": {"image_generation": True, "inpaint": True},
        "pricing": {
            "provider_in": Decimal("0.0"),
            "provider_out": Decimal("0.0"),
            "customer_in": Decimal("0.0"),
            "customer_out": Decimal("0.0"),
            "margin": Decimal("25.00"),
            "per_image_cost": Decimal("0.0400"),
            "per_image_charge": Decimal("0.0500"),
        }
    },
    {
        "model_id": "stability.stable-diffusion-xl-v1",
        "name": "sdxl-v1",
        "display_name": "Stability AI SDXL 1.0",
        "provider": "BEDROCK",
        "type": "IMAGE",
        "context_window": 0,
        "capabilities": {"image_generation": True},
        "pricing": {
            "provider_in": Decimal("0.0"),
            "provider_out": Decimal("0.0"),
            "customer_in": Decimal("0.0"),
            "customer_out": Decimal("0.0"),
            "margin": Decimal("25.00"),
            "per_image_cost": Decimal("0.0400"),
            "per_image_charge": Decimal("0.0500"),
        }
    }
]


async def seed_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Seed Admin User
        admin_stmt = select(User).where(User.email == settings.ADMIN_EMAIL)
        admin_res = await db.execute(admin_stmt)
        admin_user = admin_res.scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                full_name="Platform Super Admin",
                role="admin",
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            await db.flush()

            admin_wallet = Wallet(user_id=admin_user.id, balance_usd=Decimal("1000.000000"))
            db.add(admin_wallet)
            logger.info(f"Created admin user: {settings.ADMIN_EMAIL}")
        else:
            # Sync admin password and active status on every startup
            admin_user.hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
            admin_user.role = "admin"
            admin_user.is_active = True
            admin_user.is_verified = True
            logger.info(f"Synchronized admin user credentials for: {settings.ADMIN_EMAIL}")

        # Seed Models & Pricing
        for m_data in INITIAL_MODELS:
            stmt = select(ModelCatalog).where(ModelCatalog.model_id == m_data["model_id"])
            res = await db.execute(stmt)
            model_obj = res.scalar_one_or_none()

            if not model_obj:
                model_obj = ModelCatalog(
                    model_id=m_data["model_id"],
                    name=m_data["name"],
                    display_name=m_data["display_name"],
                    provider=m_data["provider"],
                    type=m_data["type"],
                    context_window=m_data["context_window"],
                    capabilities=m_data["capabilities"],
                    is_enabled=True,
                    region=settings.AWS_REGION
                )
                db.add(model_obj)
                await db.flush()

                p_data = m_data["pricing"]
                pricing_obj = ModelPricing(
                    model_id=model_obj.id,
                    provider_input_price_per_1k=p_data["provider_in"],
                    provider_output_price_per_1k=p_data["provider_out"],
                    customer_input_price_per_1k=p_data["customer_in"],
                    customer_output_price_per_1k=p_data["customer_out"],
                    margin_percent=p_data["margin"],
                    per_image_cost_usd=p_data.get("per_image_cost", Decimal("0.04")),
                    per_image_charge_usd=p_data.get("per_image_charge", Decimal("0.05"))
                )
                db.add(pricing_obj)
                logger.info(f"Seeded model: {m_data['display_name']}")

        await db.commit()
        logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_database())
