"""Comprehensive MCP protocol, schema validation, and error-handling tests.

Follows the MCP testing patterns:
1. Strict schema validation across all registered tools.
2. AI-like edge cases and malformed input handling.
3. Resource registration and URI resolution.
4. Error case resilience and security bounds.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import AnyUrl

from mcp_server_odoo.odoo_connection import OdooConnection
from mcp_server_odoo.resources import read_resource_uri, register_all_resources
from mcp_server_odoo.server import OdooMCPServer
from mcp_server_odoo.tools import WRITE_TOOLS, execute_tool, register_all_tools


@pytest.fixture
def mock_connection():
    """Mock connection with full interface."""
    conn = MagicMock(spec=OdooConnection)
    conn.url = "https://test.odoo.com"
    conn.db = "test_db"
    conn.uid = 1
    conn.api_type = "xmlrpc"

    config = MagicMock()
    config.url = "https://test.odoo.com"
    config.database = "test_db"
    config.yolo_mode = "true"
    conn.config = config

    conn.search_read = AsyncMock(return_value=[{"id": 1, "name": "Partner A"}])
    conn.count = AsyncMock(return_value=1)
    conn.read = AsyncMock(return_value=[{"id": 1, "name": "Partner A"}])
    conn.create = AsyncMock(return_value=101)
    conn.write = AsyncMock(return_value=True)
    conn.unlink = AsyncMock(return_value=True)
    conn.fields_get = AsyncMock(return_value={"name": {"type": "char", "string": "Name"}})
    conn.call_method = AsyncMock(return_value=[])

    return conn


def test_tool_schemas_validity_and_completeness(mock_connection):
    """Test that all tool definitions have complete, valid schemas and descriptions."""
    tools = register_all_tools(mock_connection)
    assert len(tools) >= 20

    for tool in tools:
        assert tool.name, "Tool must have a name"
        assert tool.description, f"Tool {tool.name} must have a description"
        assert len(tool.description) > 10, f"Tool {tool.name} description too short"
        assert tool.inputSchema is not None, f"Tool {tool.name} must have inputSchema"
        assert isinstance(tool.inputSchema, dict), f"Tool {tool.name} inputSchema must be dict"
        assert tool.inputSchema.get("type") == "object", f"Tool {tool.name} schema type must be 'object'"

        properties = tool.inputSchema.get("properties", {})
        required = tool.inputSchema.get("required", [])

        # Verify that all required fields are declared in properties
        for req_field in required:
            assert req_field in properties, (
                f"Tool {tool.name}: required field '{req_field}' missing from properties"
            )


def test_resources_registration_and_uris(mock_connection):
    """Test that resources are properly registered with valid AnyUrl URIs."""
    resources = register_all_resources(mock_connection)
    assert len(resources) > 0

    for resource in resources:
        assert isinstance(resource.uri, (str, AnyUrl))
        assert resource.name
        assert resource.description


@pytest.mark.asyncio
async def test_read_resource_server_info(mock_connection):
    """Test reading the odoo://info/server resource."""
    content = await read_resource_uri(mock_connection, "odoo://info/server")
    assert "Odoo MCP Server" in content
    assert "https://test.odoo.com" in content
    assert "test_db" in content


@pytest.mark.asyncio
async def test_read_resource_disconnected():
    """Test reading resource when disconnected."""
    content = await read_resource_uri(None, "odoo://info/server")
    assert "Not connected to Odoo" in content


@pytest.mark.asyncio
async def test_read_resource_invalid_format(mock_connection):
    """Test reading resource with invalid URI format."""
    content = await read_resource_uri(mock_connection, "odoo://invalid")
    assert "Invalid URI format" in content


@pytest.mark.asyncio
async def test_execute_unknown_tool(mock_connection):
    """Test calling an unknown tool returns error result gracefully."""
    result = await execute_tool(mock_connection, "non_existent_tool_xyz", {})
    assert result.isError
    assert "Unknown tool" in result.content[0].text


@pytest.mark.asyncio
async def test_execute_tool_with_malformed_ai_input(mock_connection):
    """Test calling a tool with invalid argument types caught by Pydantic validation."""
    # record_id expected to be int, passing string that cannot be int
    result = await execute_tool(
        mock_connection,
        "odoo_get_record",
        {"model": "res.partner", "record_id": "not-an-id"}
    )
    assert result.isError
    assert "Validation Error" in result.content[0].text


@pytest.mark.asyncio
async def test_execute_tool_missing_required_fields(mock_connection):
    """Test calling a tool without required fields."""
    result = await execute_tool(
        mock_connection,
        "odoo_create_record",
        {}  # missing model and values
    )
    assert result.isError
    assert "Validation Error" in result.content[0].text


@pytest.mark.asyncio
async def test_yolo_mode_blocks_all_write_tools(mock_connection):
    """Security test: verify that YOLO read-only and off modes block all write tools."""
    for mode in ["off", "read"]:
        mock_connection.config.yolo_mode = mode
        for write_tool in WRITE_TOOLS:
            result = await execute_tool(mock_connection, write_tool, {})
            assert result.isError, f"Tool {write_tool} was not blocked in yolo_mode={mode}"
            assert "YOLO read-only mode" in result.content[0].text


@pytest.mark.asyncio
async def test_server_initialization_options():
    """Verify that OdooMCPServer initialization creates valid initialization options."""
    server = OdooMCPServer()
    init_options = server._server.create_initialization_options()
    assert init_options.server_name == "odoo-mcp-connector"
