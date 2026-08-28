import asyncio
import re
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger

from app.models.entities import CustomAgent, AgentExecutionLog, Wallet, ModelCatalog, User, ScheduledTask
from app.services.email_service import EmailService
from app.services.web_search import WebSearchService
from app.providers.router import provider_router
from app.domain.schemas import ChatCompletionRequest, ChatMessage


def parse_time_expression(time_str: str) -> Optional[datetime]:
    """
    Deterministically parses user time expressions into a timezone-aware UTC datetime.
    Supports:
    - Relative offsets: "10s", "30s", "5m", "15min", "2h", "1hour", "1d", "2days"
    - Absolute daily time: "15:30", "09:00", "23:45" (schedules for today if in future, else tomorrow)
    - Date + Time: "2026-08-28 16:30", "28.08.2026 16:30"
    """
    if not time_str:
        return None
    raw = time_str.strip().lower()
    now_utc = datetime.now(timezone.utc)

    # 1. Relative Seconds/Minutes/Hours/Days
    rel_match = re.match(r"^(\d+)\s*(s|sec|secs|saniye|m|min|mins|dakika|dk|h|hr|hrs|saat|d|day|days|gun|gün)$", raw)
    if rel_match:
        val = int(rel_match.group(1))
        unit = rel_match.group(2)
        if unit in ("s", "sec", "secs", "saniye"):
            return now_utc + timedelta(seconds=val)
        elif unit in ("m", "min", "mins", "dakika", "dk"):
            return now_utc + timedelta(minutes=val)
        elif unit in ("h", "hr", "hrs", "saat"):
            return now_utc + timedelta(hours=val)
        elif unit in ("d", "day", "days", "gun", "gün"):
            return now_utc + timedelta(days=val)

    # 2. HH:MM (e.g. 15:30)
    time_match = re.match(r"^(\d{1,2}):(\d{2})$", raw)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            target = now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now_utc:
                target += timedelta(days=1)
            return target

    # 3. YYYY-MM-DD HH:MM or DD.MM.YYYY HH:MM
    dt_match_iso = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})$", raw)
    if dt_match_iso:
        y, m, d, hh, mm = map(int, dt_match_iso.groups())
        return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)

    dt_match_tr = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})$", raw)
    if dt_match_tr:
        d, m, y, hh, mm = map(int, dt_match_tr.groups())
        return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)

    return None


def parse_interval_expression(interval_str: str) -> Optional[int]:
    """
    Parses recurring intervals like "30m", "1h", "6h", "1d" into seconds.
    """
    if not interval_str:
        return None
    raw = interval_str.strip().lower()
    match = re.match(r"^(\d+)\s*(s|sec|m|min|dakika|dk|h|hr|saat|d|day|gun|gün)$", raw)
    if not match:
        return None
    val = int(match.group(1))
    unit = match.group(2)
    if unit in ("s", "sec"):
        return max(10, val)
    elif unit in ("m", "min", "dakika", "dk"):
        return val * 60
    elif unit in ("h", "hr", "saat"):
        return val * 3600
    elif unit in ("d", "day", "gun", "gün"):
        return val * 86400
    return None


class AgentAutonomousEngine:
    """
    Autonomous Execution, Live Web Search, Scheduling, and Multi-Channel Engine for AI Agents.
    1. Real-Time Web & News Intelligence (DuckDuckGo / RSS scraping)
    2. Multi-Channel Push (Telegram Bot Direct Message, AWS SNS SMS, Email)
    3. Self-Improving Reflection & Continual Memory Cache
    """

    @classmethod
    async def run_agent(
        cls,
        agent: CustomAgent,
        input_text: str,
        trigger_type: str,
        db: AsyncSession,
        override_prompt: Optional[str] = None,
        telegram_chat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"[AgentEngine] Executing agent '{agent.name}' (ID: {agent.id}) via {trigger_type}")

        # 1. Fetch user & wallet
        u_stmt = select(User).where(User.id == agent.user_id)
        u_res = await db.execute(u_stmt)
        user_obj = u_res.scalar_one_or_none()

        wallet_stmt = select(Wallet).where(Wallet.user_id == agent.user_id)
        w_res = await db.execute(wallet_stmt)
        wallet = w_res.scalar_one_or_none()

        # 2. Web Search & Live News Gathering (if enabled in tools_config or query asks for it)
        tools = agent.tools_config or {}
        search_results: List[Dict[str, str]] = []
        web_context_str = ""

        needs_search = (
            tools.get("web_search") or 
            any(k in input_text.lower() for k in ["haber", "news", "güncel", "fiyat", "borsa", "hava", "ara", "search", "son dakika"])
        )

        if needs_search:
            try:
                search_query = input_text.replace("/news", "").replace("/haber", "").replace("/search", "").strip()
                if not search_query:
                    search_query = "Gündem ve teknoloji son dakika haberleri"
                search_results = await WebSearchService.search_news_and_web(search_query, max_results=4)
                if search_results:
                    web_context_str = WebSearchService.format_search_context(search_results)
            except Exception as search_err:
                logger.warning(f"[AgentEngine] Web search failed: {search_err}")

        # 3. 3-Layer Memory Optimization
        from app.services.memory_engine import MemoryOptimizer
        from app.services.reasoning_engine import ReActAgentRunner

        learned_cache = agent.learned_memory_cache or ""
        base_prompt = override_prompt or agent.system_prompt
        goal_text = getattr(agent, "goal_definition", "")
        if goal_text:
            base_prompt += f"\n\n### HEDEF & BAŞARI KRİTERİ:\n{goal_text}"

        autonomy_lvl = getattr(agent, "autonomy_level", "AUTONOMOUS")

        # 4. LLM Caller definition for ReAct Engine
        provider = provider_router.get_provider("BEDROCK")
        dummy_model = ModelCatalog(
            model_id=agent.model_id or "amazon.nova-micro-v1:0",
            name=agent.model_id or "nova-micro",
            display_name=agent.model_id or "Amazon Nova Micro",
            provider="BEDROCK"
        )

        async def bedrock_react_caller(prompt_text: str) -> str:
            req = ChatCompletionRequest(
                model=agent.model_id or "amazon.nova-micro-v1:0",
                messages=[
                    ChatMessage(role="user", content=prompt_text)
                ],
                temperature=0.4,
                max_tokens=1500
            )
            try:
                resp, _, _ = await provider.generate_chat(req, dummy_model)
                return resp.choices[0].message.content
            except Exception as e:
                logger.warning(f"[AgentEngine] ReAct call note: {e}")
                # Fallback to direct heuristic / search if available
                if search_results:
                    return "\n".join([f"• {r['title']}: {r['snippet']}" for r in search_results])
                return f"Görev analiz edildi: {input_text}"

        # 5. Run ReAct Reasoning Loop
        reasoning_result = await ReActAgentRunner.run_reasoning_loop(
            user_input=input_text,
            system_persona=base_prompt,
            llm_caller=bedrock_react_caller,
            autonomy_level=autonomy_lvl,
            context_memory=learned_cache
        )

        output_text = reasoning_result.get("answer", "")
        steps_trace = reasoning_result.get("steps", [])

        # 6. Extract Learnable Insights & Update Long-term Memory
        new_insight = MemoryOptimizer.extract_learnable_insights(input_text, output_text)
        if not new_insight:
            new_insight = f"Görev: {input_text[:40]} -> Sonuç: {output_text[:60]}"

        current_mem = agent.learned_memory_cache or ""
        updated_mem = f"{current_mem}\n• [{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}] {new_insight}".strip()
        agent.learned_memory_cache = updated_mem[-2000:]
        agent.total_runs += 1
        agent.last_run_at = datetime.now(timezone.utc)


        # 6. Multi-Channel Dispatch
        # A. Telegram Dispatch
        target_chat_id = telegram_chat_id or (user_obj.telegram_chat_id if user_obj else None) or tools.get("telegram_chat_id")
        telegram_dispatched = False

        if (tools.get("telegram") or tools.get("telegram_notify") or target_chat_id) and target_chat_id:
            from app.services.telegram_bot import TelegramBotService
            tg_text = (
                f"🤖 *{agent.name} Bildirimi*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"{output_text}\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ _Tetikleme: {trigger_type} · Model: {agent.model_id}_"
            )
            asyncio.create_task(TelegramBotService.send_message(
                bot_token=tools.get("telegram_bot_token"),
                chat_id=str(target_chat_id),
                text=tg_text
            ))
            telegram_dispatched = True

        # B. Email Dispatch
        email_dispatched = False
        if (tools.get("email") or tools.get("email_notifications")) and user_obj and user_obj.email:
            subject = f"🤖 AI Ajan Raporu: {agent.name}"
            html = f"""
            <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; rounded: 12px;">
              <h2 style="color: #4f46e5; margin-top: 0;">🤖 {agent.name} Raporu</h2>
              <p><strong>Model:</strong> {agent.model_id} | <strong>Tetikleme:</strong> {trigger_type}</p>
              <div style="background: #0f172a; color: #f8fafc; padding: 16px; border-radius: 8px; font-size: 14px; line-height: 1.6; white-space: pre-wrap;">
                {output_text}
              </div>
              <p style="font-size: 11px; color: #94a3b8; margin-top: 16px;">AWS Bedrock AI Gateway Otonom Ajan Servisi</p>
            </div>
            """
            asyncio.create_task(EmailService.send_email_async(user_obj.email, subject, html))
            email_dispatched = True

        # 7. Deduct Micro-Fee & Record Execution Log
        cost_usd = Decimal("0.001500")
        if wallet and wallet.balance_usd >= cost_usd:
            wallet.balance_usd -= cost_usd

        log_entry = AgentExecutionLog(
            agent_id=agent.id,
            trigger_type=trigger_type,
            input_text=input_text,
            output_text=output_text,
            learned_insight=new_insight,
            status="COMPLETED",
            cost_usd=cost_usd
        )
        db.add(log_entry)
        await db.commit()

        return {
            "status": "COMPLETED",
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "output": output_text,
            "web_search_used": bool(search_results),
            "search_results_count": len(search_results),
            "channels_triggered": {
                "telegram": telegram_dispatched,
                "email": email_dispatched
            },
            "total_runs": agent.total_runs
        }


class BackgroundSchedulerService:
    """
    Production Async Background Scheduler for:
    - One-off and recurring Reminders
    - Periodic Web Search and Live News Tracking
    - Scheduled Agent Cron executions
    """

    _is_running: bool = False
    _scheduler_task: Optional[asyncio.Task] = None

    @classmethod
    async def start(cls):
        """Starts the background scheduler loop."""
        if cls._is_running:
            return
        cls._is_running = True
        cls._scheduler_task = asyncio.create_task(cls._loop())
        logger.info("[BackgroundSchedulerService] Background scheduler worker started.")

    @classmethod
    async def stop(cls):
        """Stops the background scheduler loop cleanly."""
        cls._is_running = False
        if cls._scheduler_task:
            cls._scheduler_task.cancel()
            try:
                await cls._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("[BackgroundSchedulerService] Background scheduler worker stopped.")

    @classmethod
    async def _loop(cls):
        from app.core.database import AsyncSessionLocal
        while cls._is_running:
            try:
                async with AsyncSessionLocal() as db:
                    await cls.process_due_tasks(db)
            except Exception as e:
                logger.error(f"[BackgroundSchedulerService] Error in scheduler loop: {e}")
            await asyncio.sleep(10)  # Check every 10 seconds

    @classmethod
    async def process_due_tasks(cls, db: AsyncSession):
        """Fetches and executes all ACTIVE tasks where next_run_at <= now()."""
        now = datetime.now(timezone.utc)
        stmt = select(ScheduledTask).where(
            ScheduledTask.status == "ACTIVE",
            ScheduledTask.next_run_at <= now
        )
        res = await db.execute(stmt)
        due_tasks = res.scalars().all()

        for task in due_tasks:
            try:
                if task.task_type == "REMINDER":
                    await cls._execute_reminder(task, db)
                elif task.task_type == "WEB_SEARCH_TRACKER":
                    await cls._execute_web_tracker(task, db)
                elif task.task_type == "AGENT_CRON":
                    await cls._execute_agent_cron(task, db)
            except Exception as task_err:
                logger.error(f"[BackgroundSchedulerService] Failed executing task {task.id}: {task_err}")

    @classmethod
    async def _execute_reminder(cls, task: ScheduledTask, db: AsyncSession):
        from app.services.telegram_bot import TelegramBotService
        chat_id = task.payload.get("chat_id")
        title = task.title
        created_str = task.created_at.strftime("%H:%M") if task.created_at else ""

        if chat_id:
            msg = (
                f"⏰ *ZAMAN DOLDU! HATIRLATICI:* 🔔\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 *{title}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 _Kurulma Saati: {created_str} UTC_"
            )
            await TelegramBotService.send_message(
                bot_token=None,
                chat_id=str(chat_id),
                text=msg
            )

        task.status = "COMPLETED"
        task.last_run_at = datetime.now(timezone.utc)
        task.run_count += 1
        await db.commit()
        logger.info(f"[BackgroundSchedulerService] Reminder executed for chat_id={chat_id}: {title}")

    @classmethod
    async def _execute_web_tracker(cls, task: ScheduledTask, db: AsyncSession):
        from app.services.telegram_bot import TelegramBotService
        chat_id = task.payload.get("chat_id")
        query = task.payload.get("search_query") or task.title
        interval = task.interval_seconds or 3600

        # Perform live search
        results = await WebSearchService.search_news_and_web(query, max_results=3)
        now = datetime.now(timezone.utc)

        if results and chat_id:
            bullet_points = "\n".join([f"• *{r['title']}*\n  _{r['snippet'][:120]}..._\n  🔗 [Haberi Oku]({r['url']})" for r in results])
            msg = (
                f"🌐 *Canlı Web & Haber Takipçisi Bildirimi* 📡\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 *Takip Edilen Konu:* `{query}`\n\n"
                f"{bullet_points}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏰ _Sonraki Tarama: {(now + timedelta(seconds=interval)).strftime('%H:%M')} UTC_"
            )
            await TelegramBotService.send_message(
                bot_token=None,
                chat_id=str(chat_id),
                text=msg
            )
            task.last_result_summary = str([r["title"] for r in results])

        task.last_run_at = now
        task.run_count += 1
        task.next_run_at = now + timedelta(seconds=interval)
        await db.commit()
        logger.info(f"[BackgroundSchedulerService] Web tracker executed for '{query}', next run at {task.next_run_at}")

    @classmethod
    async def _execute_agent_cron(cls, task: ScheduledTask, db: AsyncSession):
        agent_id = task.payload.get("agent_id")
        chat_id = task.payload.get("chat_id")
        prompt = task.payload.get("prompt") or task.title
        interval = task.interval_seconds or 86400

        if agent_id:
            a_stmt = select(CustomAgent).where(CustomAgent.id == agent_id)
            a_res = await db.execute(a_stmt)
            agent = a_res.scalar_one_or_none()
            if agent:
                await AgentAutonomousEngine.run_agent(
                    agent=agent,
                    input_text=prompt,
                    trigger_type="SCHEDULE_CRON",
                    db=db,
                    telegram_chat_id=str(chat_id) if chat_id else None
                )

        now = datetime.now(timezone.utc)
        task.last_run_at = now
        task.run_count += 1
        task.next_run_at = now + timedelta(seconds=interval)
        await db.commit()

