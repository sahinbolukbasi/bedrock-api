import re
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger


class MemoryOptimizer:
    """
    3-Layer Memory & Token Optimization Engine for Bedrock LLM interactions.
    
    Layer 1: Short-term Memory (Sliding Context Window + Rolling Summary Compressor)
    Layer 2: Long-term Memory (User Preferences, System Instructions & Persistent Facts)
    Layer 3: Working Memory (Scratchpad for multi-step reasoning & task checkpoints)
    """

    MAX_RAW_MESSAGES = 6  # Keep last 6 messages verbatim
    SUMMARY_TRIGGER_COUNT = 8  # Trigger compression when message history exceeds 8
    ESTIMATED_CHARS_PER_TOKEN = 4

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Fast, conservative token estimation."""
        if not text:
            return 0
        return max(1, len(text) // cls.ESTIMATED_CHARS_PER_TOKEN)

    @classmethod
    def build_optimized_context(
        cls,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        long_term_memory: Optional[str] = None,
        working_scratchpad: Optional[str] = None,
        rolling_summary: Optional[str] = None,
        max_context_tokens: int = 4000
    ) -> Tuple[List[Dict[str, str]], str, int, int]:
        """
        Compresses and optimizes conversation history before passing to Bedrock.
        Returns:
            - optimized_messages: Formatted messages list
            - new_summary_context: Rolling summary if compressed
            - original_token_estimate: Tokens if sent uncompressed
            - optimized_token_estimate: Actual tokens after optimization
        """
        raw_text_total = "".join([m.get("content", "") for m in messages])
        original_tokens = cls.estimate_tokens(raw_text_total) + cls.estimate_tokens(system_prompt or "")

        # 1. Prepare Long-Term Memory & Working Scratchpad Header
        context_headers = []
        if system_prompt:
            context_headers.append(f"### SYSTEM INSTRUCTION & PERSONA:\n{system_prompt}")
        if long_term_memory:
            context_headers.append(f"### LONG-TERM USER KNOWLEDGE & PREFERENCES:\n{long_term_memory}")
        if working_scratchpad:
            context_headers.append(f"### ACTIVE WORKING SCRATCHPAD (TASK CONTEXT):\n{working_scratchpad}")

        # 2. Check if compression is needed
        optimized_messages: List[Dict[str, str]] = []
        updated_summary = rolling_summary or ""

        if len(messages) <= cls.MAX_RAW_MESSAGES:
            # Short conversation: keep all messages
            if rolling_summary:
                context_headers.append(f"### PREVIOUS CONVERSATION RECAP:\n{rolling_summary}")
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role in ("user", "assistant", "system"):
                    optimized_messages.append({"role": role, "content": content})
        else:
            # Long conversation: compress older messages into summary
            older_messages = messages[:-cls.MAX_RAW_MESSAGES]
            recent_messages = messages[-cls.MAX_RAW_MESSAGES:]

            # Incremental rolling compression
            older_summary_parts = []
            if rolling_summary:
                older_summary_parts.append(rolling_summary)

            for om in older_messages:
                r = om.get("role", "user")
                c = (om.get("content", "") or "").strip()
                if c:
                    snippet = c if len(c) < 150 else c[:140] + "..."
                    older_summary_parts.append(f"- {r.capitalize()}: {snippet}")

            # Keep summary concise
            updated_summary = "\n".join(older_summary_parts[-6:])
            context_headers.append(f"### PREVIOUS CONVERSATION RECAP (COMPRESSED MEMORY):\n{updated_summary}")

            for rm in recent_messages:
                role = rm.get("role", "user")
                content = rm.get("content", "")
                if role in ("user", "assistant", "system"):
                    optimized_messages.append({"role": role, "content": content})

        combined_system = "\n\n".join(context_headers)
        opt_text_total = "".join([m.get("content", "") for m in optimized_messages])
        optimized_tokens = cls.estimate_tokens(opt_text_total) + cls.estimate_tokens(combined_system)

        return optimized_messages, combined_system, original_tokens, optimized_tokens

    @classmethod
    def extract_learnable_insights(cls, user_text: str, assistant_response: str) -> Optional[str]:
        """
        Extracts user preferences, explicit corrections, or persistent facts.
        """
        raw = user_text.lower()
        insights = []
        
        # Explicit corrections: "aslında adım ...", "ben ... yazılımcıyım", "bana ... de"
        pref_match = re.search(r"(?:adım|ismim)\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)", raw)
        if pref_match:
            insights.append(f"Kullanıcı Adı: {pref_match.group(1).capitalize()}")

        if "türkçe yanıt ver" in raw or "türkçe konuş" in raw:
            insights.append("Dil Tercihi: Türkçe")
        elif "answer in english" in raw:
            insights.append("Language Preference: English")

        if "kısa ve öz" in raw or "detay verme" in raw:
            insights.append("Üslup: Kısa, öz ve net yanıtlar")
        elif "açıklamalı kod" in raw or "adım adım anlat" in raw:
            insights.append("Üslup: Açıklamalı ve adım adım anlatım")

        return "; ".join(insights) if insights else None
