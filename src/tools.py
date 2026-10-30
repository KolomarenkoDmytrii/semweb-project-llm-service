"""MCP tool definitions wrapping chemistry API endpoints."""

import httpx
import logging
from typing import Any
# from mcp.server.models import Tool
from mcp.types import Tool
from pydantic import BaseModel, Field

from .config import settings

logger = logging.getLogger(__name__)

# CHEMISTRY_API_BASE = "http://localhost:8000"

# Tool schemas for MCP
class SubstanceInput(BaseModel):
    substance: str = Field(
        description="Substance name, QID, or Wikidata URL (e.g., 'water', 'Q283', 'https://www.wikidata.org/wiki/Q283')"
    )

class ReactionInput(BaseModel):
    substance: str = Field(
        description="First substance name, QID, or Wikidata URL"
    )
    other_substance: str = Field(
        description="Second substance name, QID, or Wikidata URL"
    )

class MixtureInput(BaseModel):
    mixture: str = Field(
        description="Mixture name or ID (e.g., 'seawater', 'Q14383')"
    )

# HTTP client for API calls
async def _call_api(endpoint: str, params: dict) -> dict[str, Any]:
    """Call chemistry API endpoint."""
    url = f"{settings.CHEMISTRY_API_BASE}{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"API call failed to {url}: {e}")
        return {"error": str(e), "endpoint": endpoint, "params": params}

# Tool implementations
async def ask_reaction(substance: str, other_substance: str) -> dict[str, Any]:
    """
    Query possible reactions between two substances.
    
    Args:
        substance: First substance (name, QID, or Wikidata URL)
        other_substance: Second substance (name, QID, or Wikidata URL)
    
    Returns:
        Reaction information from Wikidata/Rhea
    """
    params = {
        "substance": substance,
        "other_substance": other_substance
    }
    return await _call_api("/api/v1/ask/reaction", params)

async def ask_chemical_properties(substance: str) -> dict[str, Any]:
    """
    Retrieve chemical properties of a substance.
    
    Args:
        substance: Substance name or ID
    
    Returns:
        Chemical properties (molecular formula, mass, structure, etc.)
    """
    params = {"substance": substance}
    return await _call_api("/api/v1/ask/chemical-properties", params)

async def ask_substance_kind(substance: str) -> dict[str, Any]:
    """
    Determine the kind/classification of a substance.
    
    Args:
        substance: Substance name or ID
    
    Returns:
        Substance classification (element, compound, mixture, etc.)
    """
    params = {"substance": substance}
    return await _call_api("/api/v1/ask/substance-kind", params)

async def ask_physical_properties(substance: str) -> dict[str, Any]:
    """
    Retrieve physical properties of a substance.
    
    Args:
        substance: Substance name or ID
    
    Returns:
        Physical properties (melting point, boiling point, density, etc.)
    """
    params = {"substance": substance}
    return await _call_api("/api/v1/ask/physical-properties", params)

async def ask_mixture_components(mixture: str) -> dict[str, Any]:
    """
    Get the components of a mixture.
    
    Args:
        mixture: Mixture name or ID
    
    Returns:
        List of components and their properties
    """
    params = {"mixture": mixture}
    return await _call_api("/api/v1/ask/mixture-components", params)

# MCP tool definitions
def get_mcp_tools() -> list[Tool]:
    """Return list of MCP tool definitions."""
    return [
        Tool(
            name="ask_reaction",
            description="Query possible reactions between two substances. Use this when the user asks about reactions, interactions, or what happens when substances mix.",
            inputSchema={
                "type": "object",
                "properties": {
                    "substance": {
                        "type": "string",
                        "description": "First substance (name, QID like 'Q283', or Wikidata URL)"
                    },
                    "other_substance": {
                        "type": "string",
                        "description": "Second substance (name, QID, or Wikidata URL)"
                    }
                },
                "required": ["substance", "other_substance"]
            }
        ),
        Tool(
            name="ask_chemical_properties",
            description="Get chemical properties of a substance. Use this for molecular formula, molecular weight, chemical composition, or other chemical characteristics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "substance": {
                        "type": "string",
                        "description": "Substance name or ID (e.g., 'water', 'Q283')"
                    }
                },
                "required": ["substance"]
            }
        ),
        Tool(
            name="ask_substance_kind",
            description="Determine what kind of substance something is. Use this to classify substances (element, compound, mixture, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "substance": {
                        "type": "string",
                        "description": "Substance name or ID"
                    }
                },
                "required": ["substance"]
            }
        ),
        Tool(
            name="ask_physical_properties",
            description="Get physical properties of a substance. Use this for melting/boiling points, density, color, state of matter, or other physical characteristics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "substance": {
                        "type": "string",
                        "description": "Substance name or ID"
                    }
                },
                "required": ["substance"]
            }
        ),
        Tool(
            name="ask_mixture_components",
            description="Get the components of a mixture. Use this to find out what a mixture is made of.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mixture": {
                        "type": "string",
                        "description": "Mixture name or ID (e.g., 'seawater', 'Q14383')"
                    }
                },
                "required": ["mixture"]
            }
        )
    ]

# Tool dispatcher for LangChain
TOOL_FUNCTIONS = {
    "ask_reaction": ask_reaction,
    "ask_chemical_properties": ask_chemical_properties,
    "ask_substance_kind": ask_substance_kind,
    "ask_physical_properties": ask_physical_properties,
    "ask_mixture_components": ask_mixture_components,
}

