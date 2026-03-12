"""
MCP Tools Router - Connect to external tools via Model Context Protocol
"""
from fastapi import APIRouter, HTTPException
from models.schemas import MCPToolRequest, WorkspaceAction
from services.mcp_service import mcp_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mcp", tags=["MCP Tools"])


@router.post("/query")
async def mcp_query(
    prompt: str,
    server_url: str,
    server_label: str = "custom",
    model: str = "general",
):
    """Query using a custom MCP server"""
    try:
        result = await mcp_service.connect_custom_server(
            server_url=server_url,
            prompt=prompt,
            server_label=server_label,
            model=model,
        )
        return result
    except Exception as e:
        logger.error(f"MCP query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace")
async def workspace_query(action: WorkspaceAction):
    """Query Google Workspace (Gmail, Calendar, Drive)"""
    try:
        services = action.parameters.get("services", [
            "google_mail", "google_calendar", "google_drive"
        ])
        result = await mcp_service.workspace_query(
            query=action.action,
            services=services,
        )
        return result
    except Exception as e:
        logger.error(f"Workspace error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers")
async def list_servers():
    """List available MCP servers"""
    return mcp_service.get_available_servers()