"""
mcp_server.py
Main MCP Server implementation for Agent365
Provides tools for AI model management and health checks
"""

import os
from typing import Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from dataverse_metadata_v2 import get_access_token, fetch_metadata, parse_cr_aimodels
from normalizer import normalize_ai_model

# Initialize MCP Server
mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "intertechnumberlogythailand"),
    version="1.0.0",
)


# ── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool
def health_check() -> dict:
    """Check MCP server health and connectivity."""
    try:
        token = get_access_token()
        return {
            "status": "ok",
            "service": "agent365-mcp",
            "version": "1.0.0",
            "dataverse_authenticated": bool(token),
            "message": "Server is healthy and Dataverse is accessible"
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "agent365-mcp",
            "message": f"Health check failed: {str(e)}",
            "dataverse_authenticated": False
        }


@mcp.tool
def get_ai_model(model_id: str) -> dict:
    """
    Retrieve an AI model configuration from Microsoft Dataverse.
    
    Args:
        model_id: The unique identifier (cr_aimodelid) of the AI model
        
    Returns:
        Dictionary containing normalized AI model data
    """
    try:
        import requests
        
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
        }
        
        dataverse_env = os.getenv("DATAVERSE_ENV")
        # Fetch entity set name from metadata
        xml = fetch_metadata()
        schema = parse_cr_aimodels(xml)
        entity_set = schema.get("entity_set", "cr_aimodelses")
        
        url = f"{dataverse_env}/api/data/v9.2/{entity_set}({model_id})"
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        
        record = resp.json()
        normalized = normalize_ai_model(record)
        
        return {
            "success": True,
            "data": normalized.model_dump(),
            "model_id": model_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model_id": model_id
        }


@mcp.tool
def list_ai_models(top: int = 10, skip: int = 0) -> dict:
    """
    List AI models from Dataverse with pagination.
    
    Args:
        top: Number of records to retrieve (max 100)
        skip: Number of records to skip
        
    Returns:
        List of AI models with metadata
    """
    try:
        import requests
        
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
        }
        
        dataverse_env = os.getenv("DATAVERSE_ENV")
        xml = fetch_metadata()
        schema = parse_cr_aimodels(xml)
        entity_set = schema.get("entity_set", "cr_aimodelses")
        
        # Build query
        select_fields = ",".join([p["logical_name"] for p in schema.get("properties", [])[:10]])
        url = f"{dataverse_env}/api/data/v9.2/{entity_set}?$select={select_fields}&$top={min(top, 100)}&$skip={skip}"
        
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        models = [normalize_ai_model(record).model_dump() for record in data.get("value", [])]
        
        return {
            "success": True,
            "count": len(models),
            "models": models,
            "pagination": {
                "top": top,
                "skip": skip
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "count": 0,
            "models": []
        }


@mcp.tool
def get_schema() -> dict:
    """
    Retrieve the cr_aimodels entity schema from Dataverse.
    
    Returns:
        Complete entity schema with properties and navigation properties
    """
    try:
        xml = fetch_metadata()
        schema = parse_cr_aimodels(xml)
        
        if "error" in schema:
            return {
                "success": False,
                "error": schema.get("error"),
                "hint": schema.get("hint")
            }
        
        return {
            "success": True,
            "schema": schema
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ── Server Startup ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("MCP_SERVER_PORT", 8000))
    print(f"""
    ╔════════════════════════════════════════════════╗
    ║  Agent365 MCP Server                           ║
    ║  Starting on port {port}                          ║
    ║  Dataverse: {os.getenv('DATAVERSE_ENV', 'Not set'):<28} ║
    ╚════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "mcp_server:mcp",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
