"""Unit tests for Odoo MCP tools execution, validation, and security."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from mcp.types import CallToolResult, TextContent

from mcp_server_odoo.tools import (
    register_all_tools,
    execute_tool,
    WRITE_TOOLS,
)
from mcp_server_odoo.odoo_connection import OdooConnection


@pytest.fixture
def mock_connection():
    """Create a mock OdooConnection."""
    conn = MagicMock(spec=OdooConnection)
    conn.url = "https://test.odoo.com"
    conn.db = "test_db"
    conn.uid = 1
    conn.api_type = "xmlrpc"
    
    # Mock config
    config = MagicMock()
    config.url = "https://test.odoo.com"
    config.database = "test_db"
    config.user = "test_user"
    config.password = "test_pass"
    config.api_key = "test_key"
    config.yolo_mode = "true"
    conn.config = config

    # Mock async connection methods
    conn.search_read = AsyncMock(return_value=[{"id": 1, "display_name": "Test Partner"}])
    conn.count = AsyncMock(return_value=1)
    conn.read = AsyncMock(return_value=[{"id": 1, "display_name": "Test Partner"}])
    conn.create = AsyncMock(return_value=42)
    conn.write = AsyncMock(return_value=True)
    conn.unlink = AsyncMock(return_value=True)
    conn.fields_get = AsyncMock(return_value={"name": {"type": "char", "string": "Name"}})
    conn.call_method = AsyncMock(return_value=[])
    
    # Mock version info
    version = MagicMock()
    version.major = 18
    version.minor = 0
    version.api_type = "xmlrpc"
    conn.version = version

    return conn


@pytest.fixture
def mock_server(mock_connection):
    """Create a mock OdooMCPServer."""
    server = MagicMock()
    server.config = mock_connection.config
    server._connection = mock_connection
    server.connect = AsyncMock()
    return server


def test_register_all_tools(mock_connection):
    """Test that all tools are registered successfully with schemas."""
    tools = register_all_tools(mock_connection)
    tool_names = [t.name for t in tools]
    
    assert "odoo_search_records" in tool_names
    assert "odoo_get_record" in tool_names
    assert "odoo_create_record" in tool_names
    assert "odoo_update_record" in tool_names
    assert "odoo_delete_record" in tool_names
    assert "odoo_configure_connection" in tool_names
    assert "odoo_get_invoice_activity" in tool_names
    assert "odoo_get_record_activity" in tool_names


@pytest.mark.asyncio
async def test_execute_tool_prefixed_and_unprefixed(mock_connection):
    """Test execute_tool handles both prefixed (odoo_*) and unprefixed names."""
    args = {"model": "res.partner", "domain": [], "limit": 5}
    
    # Prefixed
    result_prefixed = await execute_tool(mock_connection, "odoo_search_records", args)
    assert not result_prefixed.isError
    mock_connection.search_read.assert_called_once_with(
        model="res.partner",
        domain=[],
        fields=None,
        limit=5,
        offset=0,
        order=None,
    )
    
    # Unprefixed
    mock_connection.search_read.reset_mock()
    result_unprefixed = await execute_tool(mock_connection, "search_records", args)
    assert not result_unprefixed.isError
    mock_connection.search_read.assert_called_once()


@pytest.mark.asyncio
async def test_execute_tool_validation_success(mock_connection):
    """Test tool execution with valid arguments."""
    args = {"model": "res.partner", "record_id": 1, "fields": ["name"]}
    result = await execute_tool(mock_connection, "odoo_get_record", args)
    
    assert not result.isError
    mock_connection.read.assert_called_once_with("res.partner", [1], ["name"])
    assert "Test Partner" in result.content[0].text


@pytest.mark.asyncio
async def test_execute_tool_validation_failure(mock_connection):
    """Test tool execution with invalid arguments returns validation error."""
    # Negative limit is invalid (schema has limit ge=1)
    args = {"model": "res.partner", "limit": -5}
    result = await execute_tool(mock_connection, "odoo_search_records", args)
    
    assert result.isError
    assert "Validation Error" in result.content[0].text
    mock_connection.search_read.assert_not_called()


@pytest.mark.asyncio
async def test_execute_tool_yolo_mode_blocked(mock_connection):
    """Test write tools are blocked when yolo_mode is read or off."""
    for mode in ("off", "read"):
        mock_connection.config.yolo_mode = mode
        args = {"model": "res.partner", "values": {"name": "Blocked Partner"}}
        
        result = await execute_tool(mock_connection, "odoo_create_record", args)
        assert result.isError
        assert "blocked in YOLO" in result.content[0].text
        mock_connection.create.assert_not_called()


@pytest.mark.asyncio
async def test_execute_tool_yolo_mode_allowed(mock_connection):
    """Test write tools are allowed when yolo_mode is true."""
    mock_connection.config.yolo_mode = "true"
    args = {"model": "res.partner", "values": {"name": "Allowed Partner"}}
    
    result = await execute_tool(mock_connection, "odoo_create_record", args)
    assert not result.isError
    mock_connection.create.assert_called_once_with("res.partner", {"name": "Allowed Partner"})


@pytest.mark.asyncio
async def test_configure_connection_success(mock_server):
    """Test configure_connection tool updates configuration and connects."""
    args = {
        "url": "https://new.odoo.com",
        "database": "new_db",
        "api_key": "new_key",
        "yolo_mode": "read",
    }
    
    result = await execute_tool(mock_server, "odoo_configure_connection", args)
    assert not result.isError
    
    assert mock_server.config.url == "https://new.odoo.com"
    assert mock_server.config.database == "new_db"
    assert mock_server.config.api_key == "new_key"
    assert mock_server.config.yolo_mode == "read"
    mock_server.connect.assert_called_once()
    assert "Connection Configured Successfully" in result.content[0].text


@pytest.mark.asyncio
async def test_execute_tool_disconnected():
    """Test executing a tool when there is no connection returns error CallToolResult."""
    # Test passing None as connection directly
    result = await execute_tool(None, "odoo_search_records", {"model": "res.partner"})
    assert result.isError
    assert "Not connected to Odoo" in result.content[0].text

    # Test passing a mock server that has no connection and fails to connect
    mock_server = MagicMock()
    mock_server._server = MagicMock()
    mock_server._connection = None
    mock_server.connect = AsyncMock(side_effect=Exception("Failed to connect"))
    
    result_server = await execute_tool(mock_server, "odoo_search_records", {"model": "res.partner"})
    assert result_server.isError
    assert "Not connected to Odoo" in result_server.content[0].text
    mock_server.connect.assert_called_once()


@pytest.mark.asyncio
async def test_get_invoice_activity_combined(mock_connection):
    """Test get_invoice_activity combines mail.activity, mail.message, and mail.tracking.value."""
    # Setup mock returns based on model
    async def mock_search_read(model, domain=None, fields=None, limit=None, offset=0, order=None):
        if model == "mail.activity":
            return [
                {
                    "id": 10,
                    "activity_type_id": [1, "To-Do"],
                    "summary": "Follow up payment",
                    "date_deadline": "2026-09-05",
                    "user_id": [2, "Operations"],
                    "state": "planned",
                    "note": "<p>Call customer regarding invoice</p>",
                }
            ]
        elif model == "mail.message":
            return [
                {
                    "id": 101,
                    "date": "2026-08-31 15:45:00",
                    "author_id": [2, "Delhi Accounts"],
                    "body": "<p>Invoice validated</p>",
                    "subject": False,
                    "tracking_value_ids": [501],
                },
                {
                    "id": 102,
                    "date": "2026-08-31 15:40:00",
                    "author_id": [2, "Delhi Accounts"],
                    "body": "",
                    "subject": False,
                    "tracking_value_ids": [502],
                },
                {
                    "id": 103,
                    "date": "2026-08-31 13:28:00",
                    "author_id": [3, "Operations"],
                    "body": "<p>This journal entry has been created from: <a href='#'>SO2013815</a></p>",
                    "subject": False,
                    "tracking_value_ids": [],
                },
            ]
        elif model == "mail.tracking.value":
            return [
                {
                    "id": 501,
                    "mail_message_id": [101, "Message 101"],
                    "field_desc": "Status",
                    "old_value_char": "Draft",
                    "new_value_char": "Posted",
                },
                {
                    "id": 502,
                    "mail_message_id": [102, "Message 102"],
                    "field_desc": "Status",
                    "old_value_char": "Posted",
                    "new_value_char": "Draft",
                },
            ]
        return []

    mock_connection.search_read = AsyncMock(side_effect=mock_search_read)
    mock_connection.read = AsyncMock(return_value=[{"id": 1234, "display_name": "INV/2026/0001"}])

    result = await execute_tool(mock_connection, "odoo_get_invoice_activity", {"invoice_id": 1234})
    assert not result.isError
    text = result.content[0].text

    # Header check
    assert "Activity Timeline for account.move #1234 (INV/2026/0001)" in text

    # Scheduled activity check
    assert "Scheduled Activities (1 pending)" in text
    assert "[To-Do]" in text
    assert "Follow up payment" in text
    assert "**Assigned to:** Operations" in text
    assert "**Due:** 2026-09-05 (Planned)" in text
    assert "Call customer regarding invoice" in text

    # Chatter history & tracking checks matching chatter UI
    assert "Chatter History & Audit Log" in text
    assert "[2026-08-31 15:45:00] Delhi Accounts" in text
    assert "Invoice validated" in text
    assert "• Draft → Posted (Status)" in text

    assert "[2026-08-31 15:40:00] Delhi Accounts" in text
    assert "• Posted → Draft (Status)" in text

    assert "[2026-08-31 13:28:00] Operations" in text
    assert "This journal entry has been created from: SO2013815" in text


@pytest.mark.asyncio
async def test_get_record_activity_generic(mock_connection):
    """Test get_record_activity works for any model like crm.lead."""
    mock_connection.search_read = AsyncMock(return_value=[])
    mock_connection.read = AsyncMock(return_value=[{"id": 45, "display_name": "Acme Lead"}])

    result = await execute_tool(
        mock_connection,
        "odoo_get_record_activity",
        {"model": "crm.lead", "record_id": 45},
    )
    assert not result.isError
    text = result.content[0].text
    assert "Activity Timeline for crm.lead #45 (Acme Lead)" in text
    assert "No activity or chatter messages recorded." in text

