import pytest
import asyncio
from app.services.memory_engine import MemoryOptimizer
from app.services.reasoning_engine import MinimalToolRegistry, ReActAgentRunner


def test_memory_token_estimation():
    text = "Hello world! This is a test of the 3-layer memory engine."
    tokens = MemoryOptimizer.estimate_tokens(text)
    assert tokens > 5


def test_memory_compression_sliding_window():
    # Construct 10 conversational turns
    messages = []
    for i in range(10):
        messages.append({"role": "user", "content": f"User query number {i}: What is the status of task {i}?"})
        messages.append({"role": "assistant", "content": f"Assistant response {i}: Task {i} completed successfully with high efficiency."})

    opt_msgs, summary_context, orig_tokens, opt_tokens = MemoryOptimizer.build_optimized_context(
        messages=messages,
        system_prompt="You are a smart assistant."
    )

    # Verbatim messages must be constrained to MAX_RAW_MESSAGES
    assert len(opt_msgs) == MemoryOptimizer.MAX_RAW_MESSAGES
    # Summary context must contain compressed older history
    assert "COMPRESSED MEMORY" in summary_context or "RECAP" in summary_context
    # Optimized tokens should be significantly lower than uncompressed
    assert opt_tokens < orig_tokens


def test_learnable_insights_extraction():
    user_text = "Benim adım Sahin. Lütfen bana kısa ve öz Türkçe yanıt ver."
    insights = MemoryOptimizer.extract_learnable_insights(user_text, "Anlaşıldı.")
    assert "Sahin" in insights
    assert "Kısa, öz" in insights or "Türkçe" in insights


@pytest.mark.asyncio
async def test_minimal_tool_math_execution():
    res = await MinimalToolRegistry.execute_tool("calculator_math", {"expression": "25 * 4 + 10"})
    assert "110" in res


@pytest.mark.asyncio
async def test_minimal_tool_reminder_execution():
    res = await MinimalToolRegistry.execute_tool("alarm_reminder", {"time_expr": "15m", "message": "Proje toplantısı"})
    assert "Hatırlatıcı Planlandı" in res
    assert "Proje toplantısı" in res


@pytest.mark.asyncio
async def test_react_reasoning_fast_math():
    # Direct math query fast-path
    async def mock_llm(p):
        return "FINAL_ANSWER: Mock answer"

    result = await ReActAgentRunner.run_reasoning_loop(
        user_input="150 * 2?",
        system_persona="Matematik uzmanısın.",
        llm_caller=mock_llm
    )

    assert "300" in result["answer"]
    assert len(result["steps"]) > 0
    assert result["steps"][0]["action"] == "calculator_math"
