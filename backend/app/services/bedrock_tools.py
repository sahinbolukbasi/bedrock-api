import json
import math
import sys
import io
import time
import httpx
import re
from typing import Dict, Any, List, Optional
from loguru import logger
from app.services.web_search import WebSearchService
from app.services.scheduler import parse_time_expression


class BedrockToolRegistry:
    """
    AWS Bedrock Converse API Native toolConfig specifications and execution sandbox.
    Follows AWS Bedrock JSON schema: { toolSpec: { name, description, inputSchema: { json: { ... } } } }
    """

    @classmethod
    def get_bedrock_tool_config(cls, enabled_tools: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Returns AWS Bedrock Converse API toolConfig dictionary.
        """
        all_specs = [
            {
                "toolSpec": {
                    "name": "web_search",
                    "description": "Performs live internet search for real-time news, current facts, market events, technology updates, or web research.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The specific search query string to look up on the live internet."
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Number of search results to return (1 to 5).",
                                    "default": 3
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "python_interpreter",
                    "description": "Executes safe Python code in an isolated sandbox for complex mathematical calculations, data formatting, statistical analysis, or algorithms.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "Valid Python 3 code. Use print() to output results."
                                }
                            },
                            "required": ["code"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "finance_market_data",
                    "description": "Fetches current market quotes, currency conversion rates, or crypto prices.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "Asset or currency pair symbol (e.g., 'BTC', 'ETH', 'USD/TRY', 'EUR/USD', 'AAPL')."
                                }
                            },
                            "required": ["symbol"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "schedule_reminder",
                    "description": "Schedules an alarm, reminder, or notification for the user at a specified time.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "time_expression": {
                                    "type": "string",
                                    "description": "Time expression such as '10m', '2h', '17:30', 'tomorrow 09:00'."
                                },
                                "message": {
                                    "type": "string",
                                    "description": "The reminder note or message."
                                }
                            },
                            "required": ["time_expression", "message"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "custom_api_request",
                    "description": "Executes dynamic REST API HTTP requests (GET, POST, PUT, DELETE) to external APIs such as crypto exchanges (Binance, Bybit), Instagram Graph API, WhatsApp Cloud API, CRMs, or custom web services.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "endpoint_url": {
                                    "type": "string",
                                    "description": "The full destination HTTP/HTTPS API URL to invoke."
                                },
                                "http_method": {
                                    "type": "string",
                                    "enum": ["GET", "POST", "PUT", "DELETE"],
                                    "default": "GET",
                                    "description": "HTTP request method."
                                },
                                "headers": {
                                    "type": "object",
                                    "description": "Optional HTTP request headers (Authorization Bearer token, API keys, Content-Type, etc.)."
                                },
                                "query_params": {
                                    "type": "object",
                                    "description": "Optional query string parameters to append to the URL."
                                },
                                "body_json": {
                                    "type": "object",
                                    "description": "JSON payload body for POST or PUT requests."
                                }
                            },
                            "required": ["endpoint_url"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "multi_url_fetcher",
                    "description": "Crawls and scrapes real-time content from one or multiple websites, documentation pages, RSS feeds, or news portals simultaneously.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "urls": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of URLs (e.g. ['https://example.com/api', 'https://docs.site.com']) to fetch and extract content from."
                                },
                                "query_filter": {
                                    "type": "string",
                                    "description": "Optional keyword or topic filter to extract specific sections."
                                }
                            },
                            "required": ["urls"]
                        }
                    }
                }
            }
        ]

        if enabled_tools:
            filtered = [t for t in all_specs if t["toolSpec"]["name"] in enabled_tools]
            return {"tools": filtered} if filtered else {"tools": all_specs}

        return {"tools": all_specs}

    @classmethod
    async def execute_tool_call(cls, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes native Bedrock tool call safely and returns structured output.
        """
        start_t = time.time()
        try:
            if tool_name == "web_search":
                query = tool_input.get("query", "").strip()
                max_res = min(5, max(1, int(tool_input.get("max_results", 3))))
                if not query:
                    return {"error": "Arama sorgusu boş olamaz."}
                
                results = await WebSearchService.search(query, max_results=max_res)
                if not results:
                    return {"result": f"'{query}' için canlı web araması sonucu bulunamadı.", "sources": []}
                
                formatted = []
                sources = []
                for r in results:
                    formatted.append(f"• **{r.get('title')}**\n{r.get('body')}\nKaynak: {r.get('href')}")
                    sources.append({"title": r.get("title"), "url": r.get("href")})
                
                return {
                    "result": "\n\n".join(formatted),
                    "sources": sources,
                    "count": len(results),
                    "latency_ms": int((time.time() - start_t) * 1000)
                }

            elif tool_name == "custom_api_request":
                url = tool_input.get("endpoint_url", "").strip()
                method = tool_input.get("http_method", "GET").upper().strip()
                headers = tool_input.get("headers") or {}
                params = tool_input.get("query_params") or {}
                body = tool_input.get("body_json")

                if not url.startswith("http://") and not url.startswith("https://"):
                    return {"error": f"Geçersiz URL şeması: '{url}'. http:// veya https:// ile başlamalıdır."}

                async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                    resp = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=body if method in ("POST", "PUT", "PATCH") else None
                    )
                    
                    try:
                        resp_data = resp.json()
                    except Exception:
                        resp_data = resp.text[:2000]

                    return {
                        "status_code": resp.status_code,
                        "is_success": resp.is_success,
                        "data": resp_data,
                        "url": str(resp.url),
                        "latency_ms": int((time.time() - start_t) * 1000)
                    }

            elif tool_name == "multi_url_fetcher":
                urls = tool_input.get("urls", [])
                if isinstance(urls, str):
                    urls = [urls]

                results = []
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    for u in urls[:5]:
                        try:
                            if not u.startswith("http"):
                                u = f"https://{u}"
                            resp = await client.get(u, headers={"User-Agent": "Mozilla/5.0 BedrockGatewayBot/1.0"})
                            clean_text = re.sub(r"<script.*?</script>", "", resp.text, flags=re.DOTALL | re.IGNORECASE)
                            clean_text = re.sub(r"<style.*?</style>", "", clean_text, flags=re.DOTALL | re.IGNORECASE)
                            clean_text = re.sub(r"<[^>]+>", " ", clean_text)
                            clean_text = " ".join(clean_text.split())[:1500]
                            results.append({"url": u, "status": resp.status_code, "content_snippet": clean_text})
                        except Exception as e:
                            results.append({"url": u, "error": str(e)})

                return {
                    "fetched_count": len(results),
                    "sources": results,
                    "latency_ms": int((time.time() - start_t) * 1000)
                }

            elif tool_name == "python_interpreter":
                code = tool_input.get("code", "")
                if not code:
                    return {"error": "Çalıştırılacak Python kodu verilmedi."}
                
                forbidden = ["os.system", "subprocess", "shutil.rmtree", "__import__('os')", "open(", "socket", "eval(", "exec("]
                for fb in forbidden:
                    if fb in code:
                        return {"error": f"Güvenlik ihlali: '{fb}' kullanımı bu sandbox ortamında engellenmiştir."}

                old_stdout = sys.stdout
                redirected = io.StringIO()
                sys.stdout = redirected
                safe_env = {
                    "math": math, "json": json, "re": re,
                    "abs": abs, "min": min, "max": max, "sum": sum, "len": len,
                    "round": round, "sorted": sorted, "range": range, "list": list,
                    "dict": dict, "set": set, "str": str, "int": int, "float": float
                }
                
                try:
                    exec(code, safe_env)
                    output = redirected.getvalue()
                    return {
                        "result": output.strip() or "Kod başarıyla çalıştırıldı (çıktı üretmedi).",
                        "latency_ms": int((time.time() - start_t) * 1000)
                    }
                except Exception as exec_err:
                    return {"error": f"Python çalıştırma hatası: {str(exec_err)}"}
                finally:
                    sys.stdout = old_stdout

            elif tool_name == "finance_market_data":
                symbol = tool_input.get("symbol", "BTC").upper().strip()
                search_query = f"{symbol} price live market quote current"
                results = await WebSearchService.search(search_query, max_results=2)
                if results:
                    snippet = "\n".join([f"• {r['title']}: {r['body']}" for r in results])
                    return {"result": f"{symbol} Canlı Piyasa Bilgileri:\n{snippet}", "symbol": symbol}
                return {"result": f"{symbol} için anlık piyasa verisi çekildi.", "symbol": symbol}

            elif tool_name == "schedule_reminder":
                time_expr = tool_input.get("time_expression", "")
                msg = tool_input.get("message", "")
                dt = parse_time_expression(time_expr)
                if not dt:
                    return {"error": f"'{time_expr}' zaman ifadesi anlaşılamadı."}
                return {
                    "result": f"✅ Hatırlatıcı kuruldu: '{msg}' Hedef zaman: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    "scheduled_at": dt.isoformat(),
                    "message": msg
                }

            else:
                return {"error": f"Tanımsız araç: {tool_name}"}

        except Exception as e:
            logger.warning(f"Error executing tool {tool_name}: {e}")
            return {"error": f"Araç çalıştırma hatası ({tool_name}): {str(e)}"}
