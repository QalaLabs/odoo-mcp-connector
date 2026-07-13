# Odoo MCP Connector Rules & Project Memory

This file serves as the project memory and style guide for the Odoo MCP Connector.

## Project Context
- **Odoo MCP Connector**: An MCP server that exposes 25+ tools to communicate with Odoo ERP instances.
- **Connection Transport**: Defaults to `stdio` JSON-RPC.
- **Authentication**: Supports `api_key` or `password` authentication with auto-detection for XML-RPC (v14-18) and JSON/2 API (v19+).

## Key Files & Tools
- [manifest.py](file:///e:/Odoo%20connector/manifest.py): Dynamic manifest generator that parses `pyproject.toml` and extracts tool schemas using `mcp_server_odoo.tools.register_all_tools(None)`. Run this script using `python manifest.py` to regenerate `manifest.json`.
- [server.py](file:///e:/Odoo%20connector/mcp_server_odoo/server.py): Contains the core `OdooMCPServer` wrapper. To prevent connection failure crashes, always pass the server instance (`self`) to `execute_tool` instead of `self._connection`.
- [tools.py](file:///e:/Odoo%20connector/mcp_server_odoo/tools.py): The main tool registry and execution block.

## Environment & Build Rules
- **Git Push / GitHub Actions Auth**: If push/pull commands fail with invalid credential errors on this repository, temporarily unset the `GITHUB_TOKEN` environment variable (e.g., `$env:GITHUB_TOKEN=$null` in PowerShell) to allow the local CLI `keyring` credentials to be used.
- **Standard Error Logging**: Ensure all server and library logs are strictly redirected to `sys.stderr` to prevent stdio transport corruption on the JSON-RPC stream. Use `logging.basicConfig(level=..., stream=sys.stderr, force=True)` to force this configuration.
- **Python Version Compatibility**: Do not use nested double/single quotes within f-strings in a way that breaks Python versions older than 3.12 (e.g. use helper variables or escaped quotes).
- **Run Tests**: Always run `pytest` to verify changes before staging or committing:
  ```bash
  pytest
  ```
