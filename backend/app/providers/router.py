from typing import Dict
from app.providers.base import IModelProvider
from app.providers.bedrock import AWSBedrockProvider
from app.core.errors import ProviderError

class ProviderRouter:
    """Manages provider instances and routes requests dynamically."""

    def __init__(self):
        self._providers: Dict[str, IModelProvider] = {
            "BEDROCK": AWSBedrockProvider(),
        }

    def get_provider(self, provider_name: str = "BEDROCK") -> IModelProvider:
        provider = self._providers.get(provider_name.upper())
        if not provider:
            raise ProviderError(f"Provider '{provider_name}' is not supported or configured.")
        return provider

provider_router = ProviderRouter()
