# Configuration Guide

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `ODOO_URL` | Odoo instance URL |
| `ODOO_API_KEY` | API key for authentication |
| `ODOO_USER` | Username (if not using API key) |
| `ODOO_PASSWORD` | Password (if not using API key) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `ODOO_DB` | auto | Database name |
| `ODOO_LOCALE` | en_US | Language locale |
| `ODOO_YOLO` | off | YOLO mode (read-only dev) |
| `ODOO_MCP_TRANSPORT` | stdio | stdio or streamable-http |
| `ODOO_MCP_HOST` | localhost | HTTP host |
| `ODOO_MCP_PORT` | 8000 | HTTP port |
| `ODOO_MCP_DEFAULT_LIMIT` | 10 | Default record limit |
| `ODOO_MCP_MAX_LIMIT` | 100 | Max record limit |
| `ODOO_MCP_LOG_LEVEL` | INFO | DEBUG, INFO, WARNING, ERROR |

## .env File

Create a `.env` file in the project root:

```bash
ODOO_URL=https://mycompany.odoo.com
ODOO_API_KEY=your_api_key_here
ODOO_DB=mycompany
ODOO_MCP_LOG_LEVEL=INFO
```

## YOLO Mode

YOLO mode bypasses MCP security for development/testing:

```bash
# Read-only (safe for demos)
ODOO_YOLO=read

# Full access (DANGEROUS)
ODOO_YOLO=true
```

Never use YOLO mode in production!

## HTTP Transport

For remote access via HTTP:

```bash
ODOO_MCP_TRANSPORT=streamable-http
ODOO_MCP_HOST=0.0.0.0
ODOO_MCP_PORT=8000
```

Access at: `http://localhost:8000/mcp/`

## MCP Client Config Examples

### Claude Desktop
```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["odoo-mcp-connector"],
      "env": {
        "ODOO_URL": "https://mycompany.odoo.com",
        "ODOO_API_KEY": "your_key",
        "ODOO_DB": "mycompany"
      }
    }
  }
}
```

### VS Code (Copilot)
```json
{
  "servers": {
    "odoo": {
      "type": "stdio",
      "command": "uvx",
      "args": ["odoo-mcp-connector"],
      "env": {
        "ODOO_URL": "https://mycompany.odoo.com",
        "ODOO_API_KEY": "your_key"
      }
    }
  }
}
```

### Cursor
```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["odoo-mcp-connector"],
      "env": {
        "ODOO_URL": "https://mycompany.odoo.com",
        "ODOO_API_KEY": "your_key"
      }
    }
  }
}
```
