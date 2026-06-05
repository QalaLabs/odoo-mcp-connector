# Developer Guide

## Project Structure

```
odoo-mcp-connector/
├── mcp_server_odoo/       # Main package
│   ├── __init__.py        # Exports
│   ├── server.py          # MCP server class
│   ├── tools.py           # All MCP tools
│   ├── odoo_connection.py # Odoo API client
│   ├── config.py          # Settings
│   └── ...
├── tests/                 # Unit tests
├── docs/                  # Documentation
└── tentacles/             # Octogent context (optional)
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

- `server.py` - MCP protocol handler
- `tools.py` - Tool registry and execution
- `odoo_connection.py` - Odoo API abstraction
- `formatters.py` - LLM output formatting
- `error_sanitizer.py` - Safe error messages

## Odoo API Notes

- Odoo 19+ uses JSON/2 API
- Odoo 14-18 uses XML-RPC
- Connection auto-detects version
- API keys require Odoo MCP module (or YOLO mode)

## License

MIT - See LICENSE file. Attribution to referenced projects required.
