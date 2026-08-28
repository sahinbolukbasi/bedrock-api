import json
import re
import time
import math
from typing import Dict, Any, List, Optional, Callable
from loguru import logger
from app.services.web_search import WebSearchService
from app.services.scheduler import parse_time_expression


class MinimalToolRegistry:
    """
    Focused, deterministic minimal toolset for Autonomous Bedrock Agents.
    Prevents tool-selection confusion and optimizes token consumption.
    """

    @classmethod
    def get_tool_definitions(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "web_search",
                "description": "Performs live internet search for current news, market data, sports, weather or real-time information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The concise search query string."}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "calculator_math",
                "description": "Calculates complex mathematical or financial expressions accurately (e.g., '150 * 1.18', 'sqrt(144) * 20').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Mathematical formula to evaluate."}
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "alarm_reminder",
                "description": "Schedules a reminder or alarm for the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_expr": {"type": "string", "description": "Time expression (e.g., '10m', '2h', '17:30')."},
                        "message": {"type": "string", "description": "Content of the reminder."}
                    },
                    "required": ["time_expr", "message"]
                }
            }
        ]

    @classmethod
    async def execute_tool(cls, tool_name: str, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Executes the specified tool safely with error isolation."""
        try:
            if tool_name == "web_search":
                query = arguments.get("query", "")
                if not query:
                    return "Hata: Arama sorgusu boş olamaz."
                results = await WebSearchService.search(query, max_results=3)
                if not results:
                    return f"'{query}' için canlı web araması sonucu bulunamadı."
                formatted = []
                for r in results:
                    formatted.append(f"• **{r.get('title')}**\n{r.get('body')}\nKaynak: {r.get('href')}")
                return "\n\n".join(formatted)

            elif tool_name == "calculator_math":
                expr = arguments.get("expression", "")
                # Safe eval with restricted globals
                safe_dict = {
                    "sqrt": math.sqrt, "pow": math.pow, "abs": abs,
                    "sin": math.sin, "cos": math.cos, "pi": math.pi
                }
                # Remove dangerous characters
                clean_expr = re.sub(r"[^0-9\+\-\*\/\.\(\)\s\%eE,a-zA-Z]", "", expr)
                result = eval(clean_expr, {"__builtins__": None}, safe_dict)
                return f"Matematiksel Hesaplama Sonucu: {result}"

            elif tool_name == "alarm_reminder":
                time_expr = arguments.get("time_expr", "")
                msg = arguments.get("message", "")
                target_time = parse_time_expression(time_expr)
                if not target_time:
                    return f"Hata: '{time_expr}' zaman ifadesi anlaşılamadı. (Örnekler: 10m, 2h, 15:30)"
                return f"✅ Hatırlatıcı Planlandı: '{msg}' zaman: {target_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"

            else:
                return f"Bilinmeyen araç: {tool_name}"
        except Exception as e:
            logger.warning(f"Tool execution failed for {tool_name}: {e}")
            return f"Araç çalıştırma hatası ({tool_name}): {str(e)}"


class ReActAgentRunner:
    """
    ReAct (Reason + Act) Autonomous Agent Engine.
    Executes: Thought -> Action -> Observation -> Reflection.
    Includes loop protection (max 4 steps) and self-correction.
    """

    MAX_REACT_STEPS = 4

    @classmethod
    async def run_reasoning_loop(
        cls,
        user_input: str,
        system_persona: str,
        llm_caller: Callable,
        autonomy_level: str = "AUTONOMOUS",
        context_memory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a step-by-step ReAct thought loop.
        """
        start_time = time.time()
        steps_trace = []
        working_scratchpad = context_memory or ""
        final_answer = ""
        current_input = user_input

        # Check if user input requires deterministic tool fast-path
        # E.g. Math or simple search
        math_pattern = re.match(r"^(\d+[\s\+\-\*\/\%\^\(\)\.]+\d+)\s*(\=|\?|hesapla)?$", user_input.strip())
        if math_pattern:
            calc_res = await MinimalToolRegistry.execute_tool("calculator_math", {"expression": math_pattern.group(1)})
            steps_trace.append({
                "step": 1,
                "thought": "Doğrudan matematiksel hesaplama algılandı, deterministik araç çalıştırılıyor.",
                "action": "calculator_math",
                "action_input": {"expression": math_pattern.group(1)},
                "observation": calc_res
            })
            return {
                "answer": calc_res,
                "steps": steps_trace,
                "autonomy_level": autonomy_level,
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }

        from app.services.semantic_memory import SemanticMemoryStore
        from app.services.bedrock_tools import BedrockToolRegistry

        # 1. Retrieve Semantically Relevant Long-Term Memories
        relevant_facts = SemanticMemoryStore.retrieve_relevant_facts(user_input, context_memory or "")
        memory_block = SemanticMemoryStore.format_retrieved_memory_block(relevant_facts)

        effective_system_persona = system_persona
        if memory_block:
            effective_system_persona += f"\n\n{memory_block}"

        # Multi-step ReAct reasoning
        for step_idx in range(1, cls.MAX_REACT_STEPS + 1):
            prompt = (
                f"{effective_system_persona}\n\n"
                f"### GÖREV:\n{user_input}\n\n"
                f"### ÇALIŞMA HAFIZASI & GEÇMİŞ ADIMLAR:\n{working_scratchpad}\n\n"
                "Aşağıdaki formatta düşün ve karar ver:\n"
                "THOUGHT: <Ne yapman gerektiğini ve hangi bilgiye veya araca ihtiyacın olduğunu adım adım düşün>\n"
                "ACTION: <web_search / python_interpreter / finance_market_data / schedule_reminder / NONE>\n"
                "ACTION_INPUT: <JSON parametreleri veya 'none'>\n"
                "FINAL_ANSWER: <Eğer tüm bilgiye sahipsen veya araç gerekmiyorsa nihai cevabı buraya yaz>"
            )

            llm_output = await llm_caller(prompt)
            thought_match = re.search(r"THOUGHT:\s*(.*?)(?=ACTION:|FINAL_ANSWER:|$)", llm_output, re.DOTALL | re.IGNORECASE)
            action_match = re.search(r"ACTION:\s*([a-zA-Z_]+)", llm_output, re.IGNORECASE)
            input_match = re.search(r"ACTION_INPUT:\s*(.*?)(?=FINAL_ANSWER:|$)", llm_output, re.DOTALL | re.IGNORECASE)
            answer_match = re.search(r"FINAL_ANSWER:\s*(.*)", llm_output, re.DOTALL | re.IGNORECASE)

            thought = thought_match.group(1).strip() if thought_match else "Gereksinim analiz ediliyor."
            action = action_match.group(1).strip().lower() if action_match else "none"
            raw_input = input_match.group(1).strip() if input_match else "{}"
            answer = answer_match.group(1).strip() if answer_match else None

            # If model provided a final answer and no action is requested
            if action in ("none", "null") or answer:
                final_answer = answer or llm_output
                steps_trace.append({
                    "step": step_idx,
                    "thought": thought,
                    "action": "NONE",
                    "action_input": {},
                    "observation": "Nihai yanıta ulaşıldı."
                })
                break

            # Parse tool input
            tool_args = {}
            try:
                clean_json = re.sub(r"^```json\s*|\s*```$", "", raw_input, flags=re.MULTILINE).strip()
                if clean_json.startswith("{") and clean_json.endswith("}"):
                    tool_args = json.loads(clean_json)
                elif action == "web_search":
                    tool_args = {"query": raw_input.strip("\"'")}
                elif action in ("python_interpreter", "calculator_math"):
                    tool_args = {"code": f"print({raw_input.strip()})"}
                elif action == "finance_market_data":
                    tool_args = {"symbol": raw_input.strip("\"'")}
            except Exception:
                tool_args = {"query": raw_input}

            # Execute tool via BedrockToolRegistry or MinimalToolRegistry
            if action in ("python_interpreter", "finance_market_data", "schedule_reminder"):
                tool_exec_res = await BedrockToolRegistry.execute_tool_call(action, tool_args)
                observation = tool_exec_res.get("result") or tool_exec_res.get("error") or str(tool_exec_res)
            else:
                observation = await MinimalToolRegistry.execute_tool(action, tool_args)

            steps_trace.append({
                "step": step_idx,
                "thought": thought,
                "action": action,
                "action_input": tool_args,
                "observation": observation
            })

            # Update working scratchpad
            working_scratchpad += (
                f"\n[Adım {step_idx}]\n"
                f"Düşünce: {thought}\n"
                f"Eylem: {action}({tool_args})\n"
                f"Gözlem: {observation}\n"
            )

        if not final_answer:
            # Reflection & Synthesize final summary from scratchpad
            synth_prompt = (
                f"{effective_system_persona}\n\n"
                f"Kullanıcı Sorusu: {user_input}\n"
                f"Toplanan Araştırma & Gözlem Verileri:\n{working_scratchpad}\n\n"
                "Lütfen toplanan tüm gözlemleri sentezleyerek kullanıcıya doğrudan, temiz ve kapsamlı bir nihai yanıt ver."
            )
            final_answer = await llm_caller(synth_prompt)

        return {
            "answer": final_answer,
            "steps": steps_trace,
            "scratchpad": working_scratchpad,
            "relevant_memories": [f.to_dict() for f in relevant_facts],
            "autonomy_level": autonomy_level,
            "execution_time_ms": int((time.time() - start_time) * 1000)
        }

