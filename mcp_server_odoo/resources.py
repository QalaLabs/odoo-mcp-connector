"""MCP resources for Odoo data access."""

from __future__ import annotations

from typing import Optional

from mcp.types import Resource
from pydantic import AnyUrl

from .formatters import format_count, format_field_info, format_records
from .odoo_connection import OdooConnection


def register_all_resources(connection: Optional[OdooConnection] = None) -> list[Resource]:
    """Register static resources."""
    return [
        Resource(
            uri=AnyUrl("odoo://info/server"),
            name="Server Info",
            description="Odoo MCP Server information",
            mimeType="text/plain",
        ),
    ]


async def read_resource_uri(connection: Optional[OdooConnection], uri: str) -> str:
    """Read a resource by URI."""
    if not connection:
        return "Not connected to Odoo"

    if uri.startswith("odoo://info/server"):
        return f"""## Odoo MCP Server

**Version:** 0.1.0
**URL:** {connection.url}
**Database:** {connection.db}
**API:** {connection.api_type}
"""

    parts = uri.replace("odoo://", "").split("/")
    if len(parts) < 2:
        return "Invalid URI format. Use: odoo://{model}/..."

    model = parts[0]
    action = parts[1] if len(parts) > 1 else "search"
    record_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None

    try:
        if action == "record" and record_id:
            records = await connection.read(model, [record_id])
            return format_records(records, model)
        elif action == "search":
            records = await connection.search_read(model, limit=10)
            return format_records(records, model)
        elif action == "count":
            count = await connection.count(model)
            return format_count(count, model)
        elif action == "fields":
            fields = await connection.fields_get(model)
            return format_field_info(fields)
        else:
            return f"Unknown action: {action}"
    except Exception as e:
        return f"Error: {str(e)}"

