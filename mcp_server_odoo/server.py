"""MCP Server for Odoo ERP."""

from __future__ import annotations
import logging
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    Resource,
    ResourceTemplate,
    TextContent,
    CallToolResult,
)

from .config import OdooConfig
from .odoo_connection import OdooConnection, create_connection
from .tools import register_all_tools
from .resources import register_all_resources
from .logging_config import setup_logging, get_logger


class OdooMCPServer:
    """Main MCP server class for Odoo integration."""

    def __init__(self, config: OdooConfig = None):
        self.config = config or OdooConfig()
        self.logger = setup_logging(self.config)
        self._server = Server("odoo-mcp-connector")
        self._connection: Optional[OdooConnection] = None
        
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Setup server request handlers."""
        @self._server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available MCP tools."""
            return register_all_tools(self._connection)

        @self._server.call_tool()
        async def call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool calls."""
            from .tools import execute_tool
            try:
                result = await execute_tool(self._connection, name, arguments)
                return result
            except Exception as e:
                self.logger.error(f"Tool error: {name}", exc_info=True)
                from .error_sanitizer import sanitize_error
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {sanitize_error(e)}")],
                    isError=True,
                )

        @self._server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources."""
            return register_all_resources(self._connection)

        @self._server.list_resource_templates()
        async def list_resource_templates() -> list[ResourceTemplate]:
            """List resource templates."""
            return [
                ResourceTemplate(
                    uriTemplate="odoo://{model}/record/{id}",
                    name="Record by ID",
                    description="Get a specific record by ID",
                    mimeType="text/plain",
                ),
                ResourceTemplate(
                    uriTemplate="odoo://{model}/search",
                    name="Search Records",
                    description="Search records with default settings",
                    mimeType="text/plain",
                ),
                ResourceTemplate(
                    uriTemplate="odoo://{model}/count",
                    name="Count Records",
                    description="Count all records in a model",
                    mimeType="text/plain",
                ),
                ResourceTemplate(
                    uriTemplate="odoo://{model}/fields",
                    name="Model Fields",
                    description="Get field definitions for a model",
                    mimeType="text/plain",
                ),
            ]

        @self._server.read_resource()
        async def read_resource(uri: Any) -> str:
            """Read a resource."""
            from .resources import read_resource_uri
            return await read_resource_uri(self._connection, str(uri))

    def connect(self) -> None:
        """Connect to Odoo."""
        try:
            self._connection = create_connection(self.config)
            self.logger.info(f"Connected to Odoo {self._connection.url}")
            self.logger.info(f"Using API: {self._connection.api_type}")
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            raise

    async def run(self) -> None:
        """Run the MCP server."""
        self.connect()
        self.logger.info("Starting Odoo MCP Server...")
        
        options = self.config.model_dump()
        async with stdio_server() as (read_stream, write_stream):
            await self._server.run(
                read_stream,
                write_stream,
                options,
            )


def create_server(config: OdooConfig = None) -> OdooMCPServer:
    """Create server instance."""
    return OdooMCPServer(config)


async def run_server(config: OdooConfig = None) -> None:
    """Run the server."""
    server = OdooMCPServer(config)
    await server.run()
