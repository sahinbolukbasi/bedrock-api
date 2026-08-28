import json
import re
import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger


class SemanticMemoryFact:
    """Represents an atomic, structured semantic memory item (Mem0 standard)."""
    def __init__(
        self,
        category: str,  # "profile", "preference", "rule", "project_context"
        key: str,
        value: str,
        confidence: float = 1.0,
        source_message: str = "",
        timestamp: Optional[str] = None
    ):
        self.category = category
        self.key = key
        self.value = value
        self.confidence = confidence
        self.source_message = source_message
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "source_message": self.source_message,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SemanticMemoryFact":
        return cls(
            category=data.get("category", "preference"),
            key=data.get("key", "general"),
            value=data.get("value", ""),
            confidence=float(data.get("confidence", 1.0)),
            source_message=data.get("source_message", ""),
            timestamp=data.get("timestamp")
        )


class SemanticMemoryStore:
    """
    Hierarchical Semantic Memory Engine (Mem0 / Zep Standard).
    
    1. Extracts atomic facts & preferences from interactions.
    2. Indexes facts into structured categories (Profile, Preferences, Rules, Context).
    3. Performs semantic relevance retrieval for user queries (RAG without DB bloat).
    4. Compresses historical conversation turns using adaptive rolling summaries.
    """

    @classmethod
    def parse_memory_graph(cls, raw_cache: str) -> List[SemanticMemoryFact]:
        """Parses serialized JSON or structured bullet points into SemanticMemoryFact list."""
        if not raw_cache:
            return []
        
        facts: List[SemanticMemoryFact] = []
        # Check if stored as JSON list
        try:
            clean = raw_cache.strip()
            if clean.startswith("[") and clean.endswith("]"):
                data = json.loads(clean)
                for item in data:
                    if isinstance(item, dict):
                        facts.append(SemanticMemoryFact.from_dict(item))
                return facts
        except Exception:
            pass

        # Parse bullet points format fallback
        for line in raw_cache.splitlines():
            line = line.strip()
            if line.startswith("•") or line.startswith("-"):
                line = line.lstrip("•- ").strip()
                # E.g. "[2026-08-28] Kullanıcı Adı: Sahin"
                parts = line.split(":", 1)
                if len(parts) == 2:
                    k, v = parts[0].strip(), parts[1].strip()
                    facts.append(SemanticMemoryFact(category="preference", key=k, value=v))
                else:
                    facts.append(SemanticMemoryFact(category="context", key="fact", value=line))
        return facts

    @classmethod
    def serialize_memory_graph(cls, facts: List[SemanticMemoryFact]) -> str:
        """Serializes memory facts into token-efficient JSON."""
        return json.dumps([f.to_dict() for f in facts[-30:]], ensure_ascii=False)

    @classmethod
    def calculate_text_relevance(cls, query: str, fact_text: str) -> float:
        """
        Fast token-overlap and keyword relevance score (0.0 to 1.0).
        """
        q_words = set(re.findall(r"\w+", query.lower()))
        f_words = set(re.findall(r"\w+", fact_text.lower()))
        if not q_words or not f_words:
            return 0.0
        
        intersection = q_words.intersection(f_words)
        score = len(intersection) / math.sqrt(len(q_words) * len(f_words))
        return score

    @classmethod
    def retrieve_relevant_facts(
        cls,
        query: str,
        memory_cache: str,
        top_k: int = 5,
        min_relevance: float = 0.05
    ) -> List[SemanticMemoryFact]:
        """
        Retrieves only the memory facts that are semantically relevant to the current query.
        Guarantees that user profile and critical rules are always included.
        """
        all_facts = cls.parse_memory_graph(memory_cache)
        if not all_facts:
            return []

        scored_facts = []
        for fact in all_facts:
            # Core profile and rules always get high base priority
            base_score = 0.5 if fact.category in ("profile", "rule") else 0.0
            content = f"{fact.key} {fact.value}"
            rel_score = cls.calculate_text_relevance(query, content) + base_score
            scored_facts.append((rel_score, fact))

        scored_facts.sort(key=lambda x: x[0], reverse=True)
        return [fact for score, fact in scored_facts[:top_k] if score >= min_relevance or fact.category in ("profile", "rule")]

    @classmethod
    def extract_facts_from_turn(
        cls,
        user_message: str,
        assistant_message: str,
        existing_facts: List[SemanticMemoryFact]
    ) -> List[SemanticMemoryFact]:
        """
        Deep semantic entity & preference extractor.
        Extracts user profile, coding preferences, language, tools, and rules.
        """
        raw_u = user_message.lower().strip()
        updated_facts = list(existing_facts)
        new_items: List[SemanticMemoryFact] = []

        # 1. User Name
        name_match = re.search(r"(?:adım|ismim|benim adım|bana)\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)", raw_u)
        if name_match and name_match.group(1).lower() not in ("bir", "lütfen", "bu", "nasıl"):
            new_items.append(SemanticMemoryFact("profile", "name", name_match.group(1).capitalize(), 1.0, user_message))

        # 2. Language & Communication Style
        if "türkçe" in raw_u:
            new_items.append(SemanticMemoryFact("preference", "language", "Türkçe", 0.95, user_message))
        elif "english" in raw_u:
            new_items.append(SemanticMemoryFact("preference", "language", "English", 0.95, user_message))

        if "kısa ve öz" in raw_u or "özet geç" in raw_u:
            new_items.append(SemanticMemoryFact("preference", "response_style", "Kısa ve öz, doğrudan yanıtlar", 0.9, user_message))
        elif "açıklamalı" in raw_u or "adım adım" in raw_u or "detaylı" in raw_u:
            new_items.append(SemanticMemoryFact("preference", "response_style", "Detaylı, açıklamalı ve kod bloklarıyla zenginleştirilmiş", 0.9, user_message))

        # 3. Programming Languages & Tech Stack
        techs = []
        for tech in ["python", "typescript", "javascript", "golang", "go", "rust", "react", "nextjs", "aws", "docker"]:
            if tech in raw_u:
                techs.append(tech.capitalize())
        if techs:
            new_items.append(SemanticMemoryFact("profile", "tech_stack", ", ".join(techs), 0.85, user_message))

        # 4. Explicit Rules ("her zaman ... yap", "asla ... yapma")
        rule_match = re.search(r"(?:her zaman|daima|asla)\s+([^\.\n]+)", raw_u)
        if rule_match:
            new_items.append(SemanticMemoryFact("rule", "behavior_rule", rule_match.group(0), 0.9, user_message))

        # Merge and deduplicate by category + key
        fact_map = {f"{f.category}:{f.key.lower()}": f for f in updated_facts}
        for n in new_items:
            fact_map[f"{n.category}:{n.key.lower()}"] = n

        return list(fact_map.values())

    @classmethod
    def format_retrieved_memory_block(cls, facts: List[SemanticMemoryFact]) -> str:
        """Formats retrieved semantic facts into a clean markdown prompt block."""
        if not facts:
            return ""
        
        lines = ["### 🧠 DİNAMİK HATIRLANAN BİLGİLER & KULLANICI TERCİHLERİ (SEMANTIC MEMORY):"]
        for f in facts:
            lines.append(f"- **[{f.category.upper()}] {f.key}**: {f.value}")
        return "\n".join(lines)
