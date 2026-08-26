import pytest
from decimal import Decimal
from app.domain.schemas import (
    ChatCompletionRequest,
    ChatMessage,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ImageGenerationRequest
)
from app.models.entities import ModelCatalog, ModelPricing
from app.providers.bedrock import AWSBedrockProvider


@pytest.mark.asyncio
async def test_bedrock_chat_generation_smart_fallback():
    """Tests non-streaming Bedrock chat completion returns valid 200 response with OpenAI schema."""
    provider = AWSBedrockProvider()
    model_entity = ModelCatalog(
        model_id="amazon.nova-micro-v1:0",
        name="nova-micro",
        display_name="Amazon Nova Micro",
        provider="BEDROCK",
        type="CHAT",
        is_enabled=True
    )
    model_entity.pricing = ModelPricing(
        customer_input_price_per_1k=Decimal("0.000035"),
        customer_output_price_per_1k=Decimal("0.000140")
    )

    request = ChatCompletionRequest(
        model="amazon.nova-micro-v1:0",
        messages=[
            ChatMessage(role="system", content="Sen uzman bir AI asistanısın."),
            ChatMessage(role="user", content="Python listelerini sıralamak için hangi yöntemler kullanılır?")
        ],
        temperature=0.7,
        max_tokens=500
    )

    response, in_tok, out_tok = await provider.generate_chat(request, model_entity)

    assert isinstance(response, ChatCompletionResponse)
    assert response.id.startswith("chatcmpl-")
    assert len(response.choices) > 0
    assert response.choices[0].message.role == "assistant"
    assert len(response.choices[0].message.content) > 20
    assert in_tok > 0
    assert out_tok > 0
    assert response.usage.total_tokens == in_tok + out_tok


@pytest.mark.asyncio
async def test_bedrock_chat_streaming_chunks():
    """Tests SSE streaming chunks yield valid delta content and final stop chunk."""
    provider = AWSBedrockProvider()
    model_entity = ModelCatalog(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        name="claude-3-haiku",
        display_name="Claude 3 Haiku",
        provider="BEDROCK",
        type="CHAT",
        is_enabled=True
    )
    model_entity.pricing = ModelPricing(
        customer_input_price_per_1k=Decimal("0.000250"),
        customer_output_price_per_1k=Decimal("0.001250")
    )

    request = ChatCompletionRequest(
        model="anthropic.claude-3-haiku-20240307-v1:0",
        messages=[
            ChatMessage(role="user", content="Merhaba! AWS Bedrock gateway test.")
        ],
        stream=True
    )

    chunks = []
    async for chunk, in_delta, out_delta in provider.stream_chat(request, model_entity):
        assert isinstance(chunk, ChatCompletionChunk)
        chunks.append(chunk)

    assert len(chunks) >= 2
    assert any(c.choices[0].delta.content for c in chunks if c.choices[0].delta)
    # The last chunk should have finish_reason == 'stop'
    assert chunks[-1].choices[0].finish_reason == "stop"


@pytest.mark.asyncio
async def test_bedrock_image_generation():
    """Tests Bedrock image generation with Amazon Titan Image Generator."""
    provider = AWSBedrockProvider()
    model_entity = ModelCatalog(
        model_id="amazon.titan-image-generator-v2:0",
        name="titan-image-generator-v2",
        display_name="Titan Image Generator G1 v2",
        provider="BEDROCK",
        type="IMAGE",
        is_enabled=True
    )
    model_entity.pricing = ModelPricing(
        per_image_charge_usd=Decimal("0.0500")
    )

    req = ImageGenerationRequest(
        model="amazon.titan-image-generator-v2:0",
        prompt="A futuristic AI cloud server datacenter in neon lights",
        n=1,
        size="1024x1024"
    )

    resp = await provider.generate_image(req, model_entity)
    assert len(resp.data) == 1
    assert resp.data[0].b64_json or resp.data[0].url
