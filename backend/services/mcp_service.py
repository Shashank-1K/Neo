"""
MCP Service - Model Context Protocol for connecting to external tools
"""
from typing import Dict, List, Optional
from services.groq_client import groq_service
import logging

logger = logging.getLogger(__name__)


class MCPService:
    """
    MCP (Model Context Protocol) Integration:
    - Connect to remote MCP servers
    - Google Workspace (Gmail, Calendar, Drive)
    - GitHub, Slack, Notion, databases
    - Any MCP-compatible service
    """

    # Pre-configured MCP server URLs
    KNOWN_SERVERS = {
        "google_mail": {
            "url": "https://mcp.google.com/gmail",
            "description": "Read and search emails",
            "requires_auth": True,
        },
        "google_calendar": {
            "url": "https://mcp.google.com/calendar",
            "description": "View calendar events",
            "requires_auth": True,
        },
        "google_drive": {
            "url": "https://mcp.google.com/drive",
            "description": "Search and access files",
            "requires_auth": True,
        },
    }

    async def call_with_mcp(
        self,
        prompt: str,
        mcp_servers: List[Dict],
        model: str = "general",
        system_prompt: str = "",
    ) -> dict:
        """
        Make an LLM call with MCP tool servers connected.
        The model can discover and use tools from the MCP servers.
        """
        from config import settings
        from api_key_manager import key_manager
        import httpx
        import time

        api_key = await key_manager.get_key("chat")
        model_id = settings.MODELS.get(model, model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build MCP tools configuration
        tools = []
        for server in mcp_servers:
            tools.append({
                "type": "mcp",
                "server_label": server.get("label", "mcp_server"),
                "server_url": server["url"],
                "require_approval": server.get("require_approval", "never"),
            })

        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": 4096,
            "tools": tools,
        }

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/responses",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()

            latency = (time.time() - start_time) * 1000
            await key_manager.report_success(api_key)

            # Extract text from response
            output_text = ""
            tools_used = []
            if "output" in result:
                for item in result["output"]:
                    if item.get("type") == "message":
                        for content in item.get("content", []):
                            if content.get("type") == "output_text":
                                output_text += content.get("text", "")
                    elif item.get("type") == "mcp_call":
                        tools_used.append(item.get("name", "unknown"))

            return {
                "content": output_text or str(result),
                "tools_used": tools_used,
                "latency_ms": latency,
                "model": model_id,
                "raw_response": result,
            }

        except Exception as e:
            await key_manager.report_failure(api_key, "429" in str(e))
            raise

    async def workspace_query(
        self,
        query: str,
        services: List[str] = None,
        model: str = "general",
    ) -> dict:
        """
        Query Google Workspace services.
        Note: Requires MCP server URLs to be configured and authenticated.
        """
        if services is None:
            services = ["google_mail", "google_calendar", "google_drive"]

        mcp_servers = []
        for svc in services:
            if svc in self.KNOWN_SERVERS:
                server_info = self.KNOWN_SERVERS[svc]
                mcp_servers.append({
                    "label": svc,
                    "url": server_info["url"],
                    "require_approval": "never",
                })

        if not mcp_servers:
            return {
                "content": "No configured MCP servers found for the requested services.",
                "tools_used": [],
                "latency_ms": 0,
                "model": "",
            }

        return await self.call_with_mcp(
            prompt=query,
            mcp_servers=mcp_servers,
            model=model,
            system_prompt="You are a workspace assistant with access to email, calendar, and file storage. Help the user with their request.",
        )

    async def connect_custom_server(
        self,
        server_url: str,
        prompt: str,
        server_label: str = "custom",
        model: str = "general",
    ) -> dict:
        """Connect to a custom MCP server"""
        return await self.call_with_mcp(
            prompt=prompt,
            mcp_servers=[{
                "label": server_label,
                "url": server_url,
                "require_approval": "never",
            }],
            model=model,
        )

    def get_available_servers(self) -> dict:
        """List all known MCP servers"""
        return self.KNOWN_SERVERS


# Singleton
mcp_service = MCPService()