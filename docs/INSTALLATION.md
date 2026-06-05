# Installation Guide

## Prerequisites

- Python 3.10+
- UV package manager
- Odoo instance (14-19+)
- API key or user credentials

## Quick Install

### 1. Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Package

```bash
# Using uvx (run directly without install)
uvx odoo-mcp-connector

# Or install locally
pip install odoo-mcp-connector

# Or from source
git clone https://github.com/your-org/odoo-mcp-connector.git
cd odoo-mcp-connector
pip install -e .
```

## Claude Desktop Setup

1. Find your config file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the server configuration:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["odoo-mcp-connector"],
      "env": {
        "ODOO_URL": "https://your-odoo.odoo.com",
        "ODOO_API_KEY": "your-api-key-here",
        "ODOO_DB": "your-database-name"
      }
    }
  }
}
```

3. Restart Claude Desktop

## Claude Code Setup

Add to your project `.mcp.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["odoo-mcp-connector"],
      "env": {
        "ODOO_URL": "https://your-odoo.odoo.com",
        "ODOO_API_KEY": "your-api-key-here",
        "ODOO_DB": "your-database-name"
      }
    }
  }
}
```

Or use the CLI:

```bash
claude mcp add odoo \
  --env ODOO_URL=https://your-odoo.com \
  --env ODOO_API_KEY=your-key \
  -- uvx odoo-mcp-connector
```

## Generate Odoo API Key

1. Log in to your Odoo instance
2. Go to **Settings → Users & Companies → Users**
3. Select your user
4. Click **Preferences** tab
5. Under **API Keys**, click **New API Key**
6. Enter description, click **Generate**
7. Copy the key (shown only once)

## Docker Setup

```bash
# Build
docker build -t odoo-mcp-connector .

# Run
docker run --rm -i \
  -e ODOO_URL=https://your-odoo.com \
  -e ODOO_API_KEY=your-key \
  -e ODOO_DB=your-db \
  odoo-mcp-connector
```

For Odoo on localhost:
```bash
docker run --rm -i \
  -e ODOO_URL=http://host.docker.internal:8069 \
  -e ODOO_API_KEY=your-key \
  -e ODOO_DB=your-db \
  odoo-mcp-connector
```

## Verification

Ask Claude:
> "What models are available?"
> "Show me my recent CRM leads"
> "Check the server connection status"
