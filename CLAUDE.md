# Developer Guide

## Project Structure

```
odoo-mcp-connector/
├── mcp_server_odoo/       # Main package
│   ├── __init__.py        # Exports
│   ├── __main__.py        # CLI entry point
│   ├── server.py          # MCP server class
│   ├── tools.py           # All MCP tools (32 tools)
│   ├── odoo_connection.py # Odoo API client
│   ├── config.py          # Settings
│   ├── formatters.py      # LLM output formatting
│   ├── error_handling.py  # Custom exceptions
│   ├── error_sanitizer.py # Safe error messages
│   ├── performance.py     # Connection pool, rate limiter
│   ├── schemas.py         # Pydantic schemas
│   ├── resources.py       # MCP resources
│   ├── webhooks.py        # REST webhook endpoint (port 8080)
│   ├── channels.py        # WhatsApp/Email adapters
│   ├── lead_classifier.py # Lead type classification (B2C, B2B, support, dealer)
│   └── logging_config.py  # Structured logging
├── tests/                 # Unit tests
├── docs/                  # Documentation
└── skills/                # Octogent context (optional)
```

## Development

### Setup
```bash
# Create venv
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install
pip install -e ".[dev]"

# Test
pytest tests/ -v
```

### Adding New Tools

1. Add tool definition in `register_all_tools()` (tools.py)
2. Add handler function `_tool_name()`
3. Add case in `execute_tool()`

Example:
```python
# In register_all_tools():
Tool(
    name="my_new_tool",
    description="Does something",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
        },
        "required": ["param1"],
    },
),

# In execute_tool():
elif name == "my_new_tool":
    return await _my_new_tool(connection, arguments)

# Add handler:
async def _my_new_tool(conn, args):
    result = conn.some_method(args["param1"])
    return CallToolResult(content=[TextContent(type="text", text=str(result))])
```

### Code Style

- Line length: 100
- Use type hints
- docstrings for public functions
- No comments unless explaining "why"

### Testing

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_odoo_connection.py::TestFormatters -v

# With coverage
pytest tests/ --cov=mcp_server_odoo
```

## Architecture

- `server.py` - MCP protocol handler (imports Tool, Resource, ResourceTemplate, TextContent, CallToolResult from mcp.types)
- `tools.py` - Tool registry and execution (27 tools listed but 32 registered including create_draft_bill, post_after_approval, query_partners, get_invoices, update_crm_lead)
- `odoo_connection.py` - Odoo API abstraction (XML-RPC + JSON/2 auto-detect)
- `formatters.py` - LLM output formatting
- `error_sanitizer.py` - Safe error messages (redacts API keys/passwords)
- `config.py` - Pydantic settings (loads from .env or env vars: ODOO_URL, ODOO_API_KEY, ODOO_DB, etc.)
- `performance.py` - Connection pool, smart field selector, rate limiter
- `webhooks.py` - REST webhook endpoint for website contact forms (port 8080)
- `channels.py` - WhatsApp (Convertway) and Email (Gmail) adapters
- `schemas.py` - Pydantic input/output schemas
- `resources.py` - MCP resource definitions
- `logging_config.py` - Structured logging (JSON or text)
- `error_handling.py` - Custom exceptions

## Odoo API Notes

- Odoo 19+ uses JSON/2 API
- Odoo 14-18 uses XML-RPC
- Connection auto-detects version
- API keys require Odoo MCP module (or YOLO mode)

## Known Issues

- `TextResource` removed from mcp.types in mcp SDK 1.27.0 — use Resource instead
- `streamable-http` transport not fully implemented; falls back to stdio
- Config reads env vars directly in `__init__` (pydantic-settings case sensitivity workaround)

## License

MIT - See LICENSE file. Attribution to referenced projects required.
