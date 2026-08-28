import httpx
import re
import urllib.parse
from typing import List, Dict, Any, Optional
from loguru import logger

class WebSearchService:
    """
    Live Web Search and News Retrieval Service for AI Agents.
    Supports real-time topic searches, news extraction, and web summaries.
    """

    @classmethod
    async def search_news_and_web(cls, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Searches the live web/news for the given query and returns titles, snippets, and sources.
        Uses DuckDuckGo HTML & RSS feeds with resilient fallbacks.
        """
        results: List[Dict[str, str]] = []
        clean_query = query.strip()
        if not clean_query:
            return results

        encoded_query = urllib.parse.quote_plus(clean_query)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr,en;q=0.9"
        }

        # 1. Try DuckDuckGo Lite / HTML Search
        try:
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    text = resp.text
                    # Extract snippets with regex
                    # Links: <a class="result__snippet" ...>snippet</a> or <a class="result__url" ...>
                    link_matches = re.findall(r'<a class="result__url"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', text, re.IGNORECASE)
                    snippet_matches = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', text, re.DOTALL | re.IGNORECASE)
                    title_matches = re.findall(r'<a class="result__a"[^>]*>(.*?)</a>', text, re.DOTALL | re.IGNORECASE)

                    for i in range(min(max_results, len(title_matches))):
                        title = re.sub(r'<[^>]+>', '', title_matches[i]).strip()
                        snippet = re.sub(r'<[^>]+>', '', snippet_matches[i]).strip() if i < len(snippet_matches) else ""
                        raw_link = link_matches[i][0] if i < len(link_matches) else ""
                        
                        # Unpack uddg param if duckduckgo redirect url
                        if "uddg=" in raw_link:
                            try:
                                actual_url = urllib.parse.unquote(raw_link.split("uddg=")[1].split("&")[0])
                            except Exception:
                                actual_url = raw_link
                        else:
                            actual_url = raw_link

                        if title:
                            results.append({
                                "title": title,
                                "snippet": snippet or "İlgili web içeriği ve canlı haber detayı.",
                                "url": actual_url or f"https://duckduckgo.com/?q={encoded_query}"
                            })

                    if results:
                        logger.info(f"[WebSearchService] Found {len(results)} search results for '{clean_query}'")
                        return results
        except Exception as e:
            logger.warning(f"[WebSearchService] DuckDuckGo search attempt failed: {e}")

        # 2. Resilient Fallback: Google News RSS for News Queries
        try:
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=tr&gl=TR&ceid=TR:tr"
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get(rss_url, headers=headers)
                if resp.status_code == 200:
                    text = resp.text
                    items = re.findall(r'<item>(.*?)</item>', text, re.DOTALL | re.IGNORECASE)
                    for item in items[:max_results]:
                        t_match = re.search(r'<title>(.*?)</title>', item, re.DOTALL | re.IGNORECASE)
                        l_match = re.search(r'<link>(.*?)</link>', item, re.DOTALL | re.IGNORECASE)
                        d_match = re.search(r'<pubDate>(.*?)</pubDate>', item, re.DOTALL | re.IGNORECASE)

                        title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', t_match.group(1)).strip() if t_match else "Haber Başlığı"
                        link = l_match.group(1).strip() if l_match else ""
                        pub_date = d_match.group(1).strip() if d_match else ""

                        results.append({
                            "title": title,
                            "snippet": f"Yayın Tarihi: {pub_date}. Google News canlı kaynaklarından derlenmiştir.",
                            "url": link
                        })

                    if results:
                        logger.info(f"[WebSearchService] Found {len(results)} RSS news results for '{clean_query}'")
                        return results
        except Exception as e:
            logger.warning(f"[WebSearchService] Google News RSS attempt failed: {e}")

        return results

    @classmethod
    def format_search_context(cls, results: List[Dict[str, str]]) -> str:
        """
        Formats search results into a clean text block to be injected into the LLM system prompt.
        """
        if not results:
            return "İnternet aramasında ek sonuç bulunamadı."

        formatted = ["🌐 **CANLI İNTERNET & GÜNCEL HABER BİLGİLERİ (Real-Time Web Intelligence):**"]
        for idx, item in enumerate(results, 1):
            formatted.append(f"{idx}. **{item.get('title')}**")
            formatted.append(f"   • Özet: {item.get('snippet')}")
            formatted.append(f"   • Kaynak URL: {item.get('url')}")
        return "\n".join(formatted)
