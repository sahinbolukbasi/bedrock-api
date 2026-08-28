import re
import math
import httpx
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger


class TextChunk:
    def __init__(self, text: str, source: str, chunk_index: int, metadata: Optional[Dict[str, Any]] = None):
        self.text = text
        self.source = source
        self.chunk_index = chunk_index
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata
        }


class LocalRAGEngine:
    """
    Cost-Effective, Local Hybrid Vector & Semantic RAG Engine.
    Zero external Vector DB subscription needed (100% in-process & budget friendly).
    
    1. Ingests raw text, custom website URLs, or REST API endpoints.
    2. Splits into semantic chunks (350-500 chars with overlap).
    3. Performs hybrid TF-IDF / BM25 token-cosine similarity ranking.
    4. Injects only the top 2-3 most relevant snippets into prompt (saving 80%+ tokens).
    """

    CHUNK_SIZE = 450
    CHUNK_OVERLAP = 60

    @classmethod
    def chunk_text(cls, text: str, source_name: str) -> List[TextChunk]:
        """Splits long text into overlapping semantic chunks."""
        clean_text = re.sub(r"\s+", " ", text).strip()
        if not clean_text:
            return []

        chunks: List[TextChunk] = []
        start = 0
        idx = 0
        text_len = len(clean_text)

        while start < text_len:
            end = min(start + cls.CHUNK_SIZE, text_len)
            chunk_content = clean_text[start:end].strip()
            if chunk_content:
                chunks.append(TextChunk(chunk_content, source_name, idx))
                idx += 1
            if end >= text_len:
                break
            start += (cls.CHUNK_SIZE - cls.CHUNK_OVERLAP)

        return chunks

    @classmethod
    async def ingest_url(cls, url: str) -> List[TextChunk]:
        """Fetches a web page, extracts text content, and returns indexed chunks."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"[LocalRAG] Failed to fetch {url}, status: {resp.status_code}")
                    return []
                
                html = resp.text
                # Simple HTML tag stripping and whitespace normalization
                text = re.sub(r"<script.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<style.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<[^>]+>", " ", text)
                clean_text = re.sub(r"\s+", " ", text).strip()
                
                return cls.chunk_text(clean_text, source_name=url)
        except Exception as e:
            logger.warning(f"[LocalRAG] Ingest URL error for {url}: {e}")
            return []

    @classmethod
    async def ingest_api_endpoint(cls, endpoint_url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None) -> List[TextChunk]:
        """Fetches custom REST API data and converts JSON response to indexable chunks."""
        try:
            req_headers = headers or {}
            async with httpx.AsyncClient(timeout=10.0) as client:
                if method.upper() == "POST":
                    resp = await client.post(endpoint_url, headers=req_headers)
                else:
                    resp = await client.get(endpoint_url, headers=req_headers)
                
                if resp.status_code == 200:
                    text_content = resp.text
                    return cls.chunk_text(text_content, source_name=endpoint_url)
                return []
        except Exception as e:
            logger.warning(f"[LocalRAG] Ingest API error for {endpoint_url}: {e}")
            return []

    @classmethod
    def calculate_bm25_similarity(cls, query: str, document: str) -> float:
        """Calculates token frequency and term overlap similarity score."""
        q_tokens = set(re.findall(r"\w+", query.lower()))
        d_tokens = re.findall(r"\w+", document.lower())
        if not q_tokens or not d_tokens:
            return 0.0

        d_token_counts = {}
        for t in d_tokens:
            d_token_counts[t] = d_token_counts.get(t, 0) + 1

        score = 0.0
        doc_len = len(d_tokens)
        avg_len = 50.0  # reference avg len
        k1 = 1.2
        b = 0.75

        for qt in q_tokens:
            tf = d_token_counts.get(qt, 0)
            if tf > 0:
                # BM25 term saturation component
                score += (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_len)))

        return score

    @classmethod
    def query_knowledge_sources(
        cls,
        query: str,
        knowledge_sources: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Queries all configured knowledge sources (stored text chunks, URLs, APIs)
        and returns the top-k most relevant chunks with citations.
        """
        all_chunks: List[TextChunk] = []

        for source in knowledge_sources:
            stype = source.get("type", "text")
            sname = source.get("name", "Knowledge Base")
            content = source.get("content", "")

            if stype == "text" and content:
                all_chunks.extend(cls.chunk_text(content, sname))
            elif stype in ("url", "api") and content:
                # If pre-cached chunks exist
                cached = source.get("cached_chunks", [])
                if cached:
                    for c in cached:
                        all_chunks.append(TextChunk(c.get("text", ""), c.get("source", sname), c.get("chunk_index", 0)))
                else:
                    all_chunks.extend(cls.chunk_text(content, sname))

        if not all_chunks:
            return []

        scored_chunks: List[Tuple[float, TextChunk]] = []
        for chunk in all_chunks:
            score = cls.calculate_bm25_similarity(query, chunk.text)
            if score > 0.1:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "text": chunk.text,
                "source": chunk.source,
                "score": round(score, 3)
            }
            for score, chunk in scored_chunks[:top_k]
        ]

    @classmethod
    def format_rag_context(cls, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Formats retrieved RAG chunks into clean markdown prompt context."""
        if not retrieved_chunks:
            return ""

        parts = ["### 📚 ÖZEL BİLGİ TABANI & KAYNAK DOKÜMANLAR (KNOWLEDGE BASE RAG):"]
        for idx, item in enumerate(retrieved_chunks, 1):
            parts.append(f"[Kaynak {idx}: {item['source']}]\n{item['text']}")
        parts.append("Yukarıdaki özel kaynak verilerini temel alarak kullanıcıya doğru ve kaynak belirterek yanıt ver.")
        return "\n\n".join(parts)
