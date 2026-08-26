import pytest
from app.domain.schemas import AgentCreateRequest, AgentExecutionRequest
from app.providers.bedrock import AWSBedrockProvider
from app.models.entities import ModelCatalog


def test_agent_schema_and_prompts():
    agent_req = AgentCreateRequest(
        name="Finansal Rapor Ajanı",
        description="Şirket bilançolarını ve faturalarını analiz eder",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        system_prompt="Sen kıdemli bir Finans Analistisin. Verileri CSV ve tablo formatında incele.",
        has_email_tool=True,
        has_telegram_tool=False,
        telegram_webhook=None
    )
    assert agent_req.name == "Finansal Rapor Ajanı"
    assert agent_req.has_email_tool is True
    assert "Finans Analistisin" in agent_req.system_prompt

    exec_req = AgentExecutionRequest(
        task_input="Son 3 aylık sunucu maliyetlerimizi özetle",
        context_data={"q1_cost": 1200, "q2_cost": 950}
    )
    assert "maliyetlerimizi" in exec_req.task_input
    assert exec_req.context_data.get("q1_cost") == 1200


@pytest.mark.asyncio
async def test_agent_execution_with_bedrock():
    provider = AWSBedrockProvider()
    model = ModelCatalog(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        name="Claude 3.5 Sonnet",
        provider="Anthropic",
        type="CHAT",
        is_enabled=True
    )
    response_text = provider._generate_smart_response("python liste sırala", model.name)
    assert "sort" in response_text.lower() or "python" in response_text.lower()
