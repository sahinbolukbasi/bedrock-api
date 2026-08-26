from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Tuple
from app.domain.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ImageGenerationRequest,
    ImageGenerationResponse
)
from app.models.entities import ModelCatalog


class IModelProvider(ABC):
    """Abstract interface for all model providers (Bedrock, OpenAI, Anthropic direct, etc.)"""

    @abstractmethod
    async def generate_chat(
        self,
        request: ChatCompletionRequest,
        model_entity: ModelCatalog
    ) -> Tuple[ChatCompletionResponse, int, int]:
        """
        Executes a non-streaming chat completion.
        Returns: (ChatCompletionResponse, input_tokens, output_tokens)
        """
        pass

    @abstractmethod
    async def stream_chat(
        self,
        request: ChatCompletionRequest,
        model_entity: ModelCatalog
    ) -> AsyncGenerator[Tuple[ChatCompletionChunk, int, int], None]:
        """
        Streams chat completion tokens in real-time.
        Yields: (ChatCompletionChunk, input_tokens_delta, output_tokens_delta)
        """
        pass

    @abstractmethod
    async def generate_image(
        self,
        request: ImageGenerationRequest,
        model_entity: ModelCatalog
    ) -> ImageGenerationResponse:
        """Executes an image generation request."""
        pass
