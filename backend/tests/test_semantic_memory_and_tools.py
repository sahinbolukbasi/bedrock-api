import pytest
import asyncio
from app.services.semantic_memory import SemanticMemoryFact, SemanticMemoryStore
from app.services.bedrock_tools import BedrockToolRegistry
from app.services.reasoning_engine import ReActAgentRunner


def test_semantic_fact_serialization():
    facts = [
        SemanticMemoryFact(category="profile", key="name", value="Sahin"),
        SemanticMemoryFact(category="preference", key="language", value="Türkçe"),
        SemanticMemoryFact(category="rule", key="code_style", value="Always use typed python")
    ]
    serialized = SemanticMemoryStore.serialize_memory_graph(facts)
    assert "Sahin" in serialized
    assert "Türkçe" in serialized

    parsed = SemanticMemoryStore.parse_memory_graph(serialized)
    assert len(parsed) == 3
    assert parsed[0].value == "Sahin"


def test_semantic_relevance_retrieval():
    facts = [
        SemanticMemoryFact(category="profile", key="name", value="Sahin"),
        SemanticMemoryFact(category="preference", key="tech_stack", value="Python, FastAPI, AWS Bedrock"),
        SemanticMemoryFact(category="context", key="database", value="PostgreSQL and Redis cache"),
        SemanticMemoryFact(category="context", key="vacation", value="Summer holiday in Antalya")
    ]
    cache = SemanticMemoryStore.serialize_memory_graph(facts)

    # Search for tech stack related query
    retrieved = SemanticMemoryStore.retrieve_relevant_facts(
        query="AWS Bedrock ve Python ile bir agent kuralım",
        memory_cache=cache,
        top_k=2
    )

    retrieved_keys = [f.key for f in retrieved]
    assert "name" in retrieved_keys or "tech_stack" in retrieved_keys


def test_fact_extraction_from_conversation():
    user_msg = "Benim adım Sahin, Python ve AWS üzerinde çalışıyorum. Bana her zaman kısa ve öz Türkçe yanıt ver."
    assistant_msg = "Memnun oldum Sahin Bey, talebiniz kaydedildi."
    
    extracted = SemanticMemoryStore.extract_facts_from_turn(user_msg, assistant_msg, [])
    keys = [f.key for f in extracted]
    assert "name" in keys
    assert "language" in keys
    assert "response_style" in keys


@pytest.mark.asyncio
async def test_bedrock_tool_config_generation():
    config = BedrockToolRegistry.get_bedrock_tool_config(["web_search", "python_interpreter"])
    assert "tools" in config
    tool_names = [t["toolSpec"]["name"] for t in config["tools"]]
    assert "web_search" in tool_names
    assert "python_interpreter" in tool_names


@pytest.mark.asyncio
async def test_python_interpreter_sandbox_execution():
    # Safe python calculation
    code = "x = [10, 20, 30]\nprint(f'Sum: {sum(x)}')"
    res = await BedrockToolRegistry.execute_tool_call("python_interpreter", {"code": code})
    assert "Sum: 60" in res.get("result", "")

    # Dangerous code rejection
    bad_code = "import os\nos.system('ls')"
    bad_res = await BedrockToolRegistry.execute_tool_call("python_interpreter", {"code": bad_code})
    assert "Güvenlik ihlali" in bad_res.get("error", "")


@pytest.mark.asyncio
async def test_react_engine_with_semantic_memory():
    facts = [
        SemanticMemoryFact(category="profile", key="name", value="Sahin"),
        SemanticMemoryFact(category="preference", key="role", value="DevOps Lead")
    ]
    cache = SemanticMemoryStore.serialize_memory_graph(facts)

    async def mock_llm(p):
        assert "Sahin" in p or "DevOps Lead" in p
        return "FINAL_ANSWER: Sayın Sahin, talebiniz DevOps standartlarında başarıyla yürütüldü."

    result = await ReActAgentRunner.run_reasoning_loop(
        user_input="Bana durumumu özetle",
        system_persona="Sen akıllı bir asistansın.",
        llm_caller=mock_llm,
        context_memory=cache
    )

    assert "Sahin" in result["answer"]
    assert len(result.get("relevant_memories", [])) > 0
