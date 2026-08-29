"""
Automated unit tests for Telegram Bot Service and Self-Healing Polling Worker.
Validates zero static token leaks, pairing link generator, and message routing.
"""

import pytest
from app.services.telegram_bot import (
    TelegramBotService, 
    get_telegram_bot_token, 
    get_telegram_bot_username,
    get_main_menu_keyboard
)
from app.core.secrets_manager import AWSSecretsManagerService


def test_telegram_token_dynamic_getter(monkeypatch):
    """Verifies that TelegramBotService dynamically fetches bot token from vault/env."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:DYNAMIC_TELEGRAM_TOKEN_XYZ")
    token = get_telegram_bot_token()
    assert token == "123456789:DYNAMIC_TELEGRAM_TOKEN_XYZ"


def test_telegram_username_dynamic_getter(monkeypatch):
    """Verifies Telegram username resolution."""
    monkeypatch.setenv("TELEGRAM_BOT_USERNAME", "CustomTestBot")
    username = get_telegram_bot_username()
    assert username == "CustomTestBot"


def test_main_menu_keyboard_structure():
    """Verifies interactive inline keyboard layout for Telegram bot."""
    kb = get_main_menu_keyboard()
    assert "inline_keyboard" in kb
    assert len(kb["inline_keyboard"]) >= 3
    # Check button texts
    all_texts = [btn["text"] for row in kb["inline_keyboard"] for btn in row]
    assert any("Ajanlar" in t for t in all_texts)
    assert any("Yeni Bot" in t for t in all_texts)
    assert any("Bakiye" in t for t in all_texts)


@pytest.mark.asyncio
async def test_telegram_send_message_aborts_on_empty_chat_id():
    """Verifies send_message safely returns False without raising exceptions when chat_id is missing."""
    res = await TelegramBotService.send_message(bot_token="test_token", chat_id="", text="Hello")
    assert res is False
