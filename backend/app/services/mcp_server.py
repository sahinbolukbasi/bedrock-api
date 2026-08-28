from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from loguru import logger
from app.services.bedrock_tools import BedrockToolRegistry


class StatefulMCPServer:
    """
    Model Context Protocol (MCP) Stateful Server implementation.
    Maintains tool registration, protocol handshakes, and persistent session context.
    """

    _sessions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def initialize_session(cls, session_id: str, client_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initializes a new stateful MCP session."""
        session = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "client_info": client_info or {},
            "context_variables": {},
            "execution_count": 0
        }
        cls._sessions[session_id] = session
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        return cls._sessions.get(session_id)

    @classmethod
    def update_session_context(cls, session_id: str, key: str, value: Any) -> None:
        if session_id in cls._sessions:
            cls._sessions[session_id]["context_variables"][key] = value

    @classmethod
    def list_mcp_tools(cls) -> List[Dict[str, Any]]:
        """Returns standard MCP tool definitions."""
        config = BedrockToolRegistry.get_bedrock_tool_config()
        mcp_tools = []
        for t in config.get("tools", []):
            spec = t.get("toolSpec", {})
            mcp_tools.append({
                "name": spec.get("name"),
                "description": spec.get("description"),
                "inputSchema": spec.get("inputSchema", {}).get("json", {})
            })
        return mcp_tools

    @classmethod
    async def call_mcp_tool(cls, session_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calls a tool within an active stateful MCP session context."""
        session = cls.get_session(session_id)
        if not session:
            cls.initialize_session(session_id)

        cls._sessions[session_id]["execution_count"] += 1
        result = await BedrockToolRegistry.execute_tool_call(tool_name, arguments)
        return {
            "session_id": session_id,
            "tool": tool_name,
            "result": result
        }
