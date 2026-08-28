import pytest
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from app.services.scheduler import parse_time_expression, parse_interval_expression, BackgroundSchedulerService
from app.services.telegram_bot import TelegramBotService
from app.models.entities import User, CustomAgent, ScheduledTask, Wallet, Base

def test_time_expression_parser():
    now = datetime.now(timezone.utc)
    
    # Relative formats
    t1 = parse_time_expression("10s")
    assert t1 is not None
    assert 9 <= (t1 - now).total_seconds() <= 12

    t2 = parse_time_expression("15m")
    assert t2 is not None
    assert 14 * 60 <= (t2 - now).total_seconds() <= 16 * 60

    t3 = parse_time_expression("2h")
    assert t3 is not None
    assert 119 * 60 <= (t3 - now).total_seconds() <= 121 * 60

    t4 = parse_time_expression("1d")
    assert t4 is not None
    assert 23 * 3600 <= (t4 - now).total_seconds() <= 25 * 3600

    # Turkish relative formats
    t5 = parse_time_expression("30dakika")
    assert t5 is not None
    assert 29 * 60 <= (t5 - now).total_seconds() <= 31 * 60

    # Absolute HH:MM
    t6 = parse_time_expression("15:30")
    assert t6 is not None
    assert t6.hour == 15 and t6.minute == 30

    # Invalid string
    assert parse_time_expression("invalid_time_string") is None


def test_interval_expression_parser():
    assert parse_interval_expression("30s") == 30
    assert parse_interval_expression("15m") == 900
    assert parse_interval_expression("1h") == 3600
    assert parse_interval_expression("6h") == 21600
    assert parse_interval_expression("1d") == 86400
    assert parse_interval_expression("invalid") is None


@pytest.mark.asyncio
async def test_telegram_webhook_hybrid_flow():
    # Use fast in-memory SQLite engine
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        test_email = f"tg_user_{uuid.uuid4().hex[:6]}@example.com"
        test_chat_id = f"998877{uuid.uuid4().hex[:4]}"
        user = User(
            email=test_email,
            hashed_password="mock_hash",
            full_name="Telegram Test User",
            telegram_chat_id=test_chat_id,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        await db.flush()

        wallet = Wallet(user_id=user.id, balance_usd=10.0)
        db.add(wallet)
        await db.commit()

        # 1. Test /start menu
        update_start = {
            "message": {
                "chat": {"id": test_chat_id},
                "from": {"id": 123456, "first_name": "Tester"},
                "text": "/start"
            }
        }
        res_start = await TelegramBotService.process_webhook_update("mock_token", update_start, db)
        assert res_start["status"] == "ok"

        # 2. Test /remind command
        update_remind = {
            "message": {
                "chat": {"id": test_chat_id},
                "from": {"id": 123456},
                "text": "/remind 10m Ekip toplantısına katıl"
            }
        }
        res_remind = await TelegramBotService.process_webhook_update("mock_token", update_remind, db)
        assert res_remind["status"] == "ok"
        assert "task_id" in res_remind

        # 3. Test /track command (Recurring Web Search)
        update_track = {
            "message": {
                "chat": {"id": test_chat_id},
                "from": {"id": 123456},
                "text": "/track 1h Yapay Zeka Gelişmeleri"
            }
        }
        res_track = await TelegramBotService.process_webhook_update("mock_token", update_track, db)
        assert res_track["status"] == "ok"
        assert "task_id" in res_track

        # 4. Test /newbot command
        update_newbot = {
            "message": {
                "chat": {"id": test_chat_id},
                "from": {"id": 123456},
                "text": "/newbot Borsa Danışmanı | Borsa verilerini analiz et | evet | amazon.nova-micro-v1:0"
            }
        }
        res_newbot = await TelegramBotService.process_webhook_update("mock_token", update_newbot, db)
        assert res_newbot["status"] == "ok"
        assert "agent_id" in res_newbot

        # 5. Test /agents list
        update_agents = {
            "message": {
                "chat": {"id": test_chat_id},
                "from": {"id": 123456},
                "text": "/agents"
            }
        }
        res_agents = await TelegramBotService.process_webhook_update("mock_token", update_agents, db)
        assert res_agents["status"] == "ok"
        assert res_agents["count"] >= 1

        # 6. Test /image command (Titan Image Generator)
        update_image = {
            "message": {
                "chat": {"id": test_chat_id},
                "from": {"id": 123456},
                "text": "/image Siberpunk neon şehir manzarası"
            }
        }
        res_image = await TelegramBotService.process_webhook_update("mock_token", update_image, db)
        assert res_image["status"] == "ok"
        assert res_image.get("image_generated") is True

        # 7. Test Smart Natural Language Reminder
        update_nl_remind = {
            "message": {
                "chat": {"id": test_chat_id},
                "from": {"id": 123456},
                "text": "15 dakika sonra bana su içmeyi hatırlat"
            }
        }
        res_nl = await TelegramBotService.process_webhook_update("mock_token", update_nl_remind, db)
        assert res_nl["status"] == "ok"
        assert "task_id" in res_nl

        # 8. Test Background Scheduler Task Execution
        expired_task = ScheduledTask(
            user_id=user.id,
            task_type="REMINDER",
            title="Test Zamanı Dolan Hatırlatıcı",
            payload={"chat_id": test_chat_id, "prompt": "Alarm testi"},
            schedule_type="ONCE",
            next_run_at=datetime.now(timezone.utc) - timedelta(seconds=10),
            status="ACTIVE"
        )
        db.add(expired_task)
        await db.commit()

        await BackgroundSchedulerService.process_due_tasks(db)
        await db.refresh(expired_task)
        assert expired_task.status == "COMPLETED"
        assert expired_task.run_count == 1
    
    await test_engine.dispose()
