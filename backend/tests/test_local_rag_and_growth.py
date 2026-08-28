import pytest
from app.services.local_rag import LocalRAGEngine
from app.services.agent_growth import AgentGrowthEngine, AgentEvolutionStage


def test_local_rag_chunking():
    sample_text = (
        "Bedrock Gateway is a high-performance AI API system. "
        "It provides unified access to Amazon Nova, Anthropic Claude, and Meta Llama models. "
        "It includes 3-layer memory optimization and cost-effective local RAG."
    )
    chunks = LocalRAGEngine.chunk_text(sample_text, "TestDoc")
    assert len(chunks) > 0
    assert chunks[0].source == "TestDoc"
    assert "Bedrock Gateway" in chunks[0].text


def test_local_rag_similarity_and_retrieval():
    sources = [
        {
            "type": "text",
            "name": "AWS Bedrock Pricing",
            "content": "Amazon Nova Micro costs $0.000035 per 1K input tokens and $0.00014 per 1K output tokens."
        },
        {
            "type": "text",
            "name": "Frontend Guide",
            "content": "The frontend is built with Next.js 14, Tailwind CSS, and Lucide icons."
        }
    ]

    # Query for Bedrock pricing
    results = LocalRAGEngine.query_knowledge_sources("Amazon Nova Micro pricing token cost", sources, top_k=1)
    assert len(results) == 1
    assert results[0]["source"] == "AWS Bedrock Pricing"
    assert "Nova Micro" in results[0]["text"]

    formatted = LocalRAGEngine.format_rag_context(results)
    assert "KNOWLEDGE BASE RAG" in formatted
    assert "AWS Bedrock Pricing" in formatted


def test_living_agent_growth_and_levels():
    # Level 1: Novice
    lvl, stage, _, _, _ = AgentGrowthEngine.calculate_level_and_stage(50)
    assert lvl == 1
    assert "Yenidoğan" in stage

    # Level 2: Apprentice
    lvl2, stage2, _, _, _ = AgentGrowthEngine.calculate_level_and_stage(250)
    assert lvl2 == 2
    assert "Çırak" in stage2

    # Level 3: Specialist
    lvl3, stage3, _, _, _ = AgentGrowthEngine.calculate_level_and_stage(600)
    assert lvl3 == 3
    assert "Uzman" in stage3

    # Level 4: Master
    lvl4, stage4, _, _, _ = AgentGrowthEngine.calculate_level_and_stage(1500)
    assert lvl4 == 4
    assert "Üstat" in stage4


def test_agent_xp_award_and_milestones():
    growth = AgentGrowthEngine.award_xp(
        current_xp=90,
        xp_gain=30,  # 90 + 30 = 120 -> Level 2 level-up!
        reason="Web araştırması ve canlı veri işleme",
        growth_history=[]
    )
    assert growth["new_xp"] == 120
    assert growth["level"] == 2
    assert growth["leveled_up"] is True
    assert len(growth["growth_history"]) > 0
    assert growth["growth_history"][-1]["type"] == "LEVEL_UP"


def test_agent_dynamic_iq_score():
    iq = AgentGrowthEngine.calculate_iq_score(
        total_runs=10,
        memory_fact_count=8,
        knowledge_source_count=3,
        level=2
    )
    # 85 (base) + 20 (runs) + 24 (facts) + 15 (knowledge) + 20 (level) = 164
    assert iq >= 140
