"""
Domain Interfaces (Ports) for AWS Bedrock AI Gateway.
Adheres to Dependency Inversion Principle (DIP) and Clean Architecture standards.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class ISecretsManager(ABC):
    """Abstract interface for Secrets Management and Key Vault adapters."""

    @abstractmethod
    def get_secret(self, secret_key: str, secret_name: Optional[str] = None, default: Optional[str] = None) -> Optional[str]:
        """Retrieves a secret value dynamically from secure vault or environment."""
        pass


class IEmailService(ABC):
    """Abstract interface for transactional email dispatchers."""

    @abstractmethod
    async def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Sends an HTML email to the specified recipient."""
        pass

    @abstractmethod
    async def send_verification_code(self, to_email: str, code: str, full_name: Optional[str] = None) -> bool:
        """Sends a 6-digit OTP email verification code."""
        pass


class IBotService(ABC):
    """Abstract interface for external chat bot channels (Telegram, Slack, etc.)."""

    @abstractmethod
    async def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown", reply_markup: Optional[Dict[str, Any]] = None) -> bool:
        """Sends a formatted message to a target chat."""
        pass

    @abstractmethod
    async def generate_pairing_code(self, user_id: Any) -> str:
        """Generates a secure pairing token for bidirectional account linking."""
        pass
