import pytest
import uuid
from app.domain.schemas import (
    ConversationCreateRequest,
    ConversationResponse,
    ConversationMessageCreateRequest,
    ConversationMessageResponse
)


def test_conversation_schemas_and_lifecycle():
    # 1. Create conversation request
    conv_req = ConversationCreateRequest(
        title="Python Mülakat Hazırlığı",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        system_prompt="Kıdemli Python Geliştirici persona",
        temperature=0.7
    )
    assert conv_req.title == "Python Mülakat Hazırlığı"
    assert conv_req.temperature == 0.7

    # 2. Conversation response validation
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()
    conv_res = ConversationResponse(
        id=conv_id,
        user_id=user_id,
        title=conv_req.title,
        model_id=conv_req.model_id,
        system_prompt=conv_req.system_prompt,
        temperature=conv_req.temperature,
        created_at=None,
        updated_at=None
    )
    assert conv_res.id == conv_id
    assert conv_res.title == "Python Mülakat Hazırlığı"

    # 3. Message schema validation
    msg_req = ConversationMessageCreateRequest(
        role="user",
        content="Python'da GIL nedir?"
    )
    assert msg_req.role == "user"
    assert "GIL" in msg_req.content

    msg_res = ConversationMessageResponse(
        id=uuid.uuid4(),
        conversation_id=conv_id,
        role="assistant",
        content="Global Interpreter Lock (GIL), CPython'da aynı anda sadece bir iş parçacığının Python bytecode çalıştırmasını sağlayan mekanizmadır.",
        tokens=35,
        cost_usd=None,
        created_at=None
    )
    assert msg_res.role == "assistant"
    assert msg_res.tokens == 35
