# Odoo MCP Connector

MCP server enabling AI assistants (Claude Desktop/Code, Copilot, Cursor) to interact with Odoo ERP through natural language.

## Features

- **Full Odoo Integration**: CRM, Accounting, Sales, Purchase, Inventory, Expenses
- **Multi-version Support**: Odoo 14-18 (XML-RPC) and Odoo 19+ (JSON/2 API)
- **Natural Language Interface**: Ask questions, create records, update data
- **Multi-channel Lead Capture**: Webhooks, WhatsApp, Email integration
- **Smart Field Selection**: Auto-selects relevant fields per model
- **LLM-optimized Output**: Hierarchical text formatting

## Quick Start

### 1. Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Configure Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["odoo-mcp-connector"],
      "env": {
        "ODOO_URL": "https://your-odoo.com",
        "ODOO_API_KEY": "your-api-key",
        "ODOO_DB": "your-database"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `ODOO_URL` | Yes | Odoo instance URL |
| `ODOO_API_KEY` | Yes* | API key (recommended) |
| `ODOO_USER` | Yes* | Username |
| `ODOO_PASSWORD` | Yes* | Password |
| `ODOO_DB` | No | Database name (auto-detected) |
| `ODOO_MCP_LOG_LEVEL` | No | DEBUG, INFO, WARNING, ERROR |

## Available Tools

### Core CRUD
- `search_records` - Search with filters
- `get_record` - Get by ID
- `create_record` - Create new record
- `update_record` - Update record
- `delete_record` - Delete record
- `count_records` - Count matching records
- `list_models` - List available models
- `get_model_fields` - Get model field definitions

### CRM
- `create_lead` - Create lead with auto follow-up
- `search_leads` - Search CRM leads
- `log_channel_message` - Log WhatsApp/email to lead
- `post_message` - Post to record chatter

### Accounting
- `create_invoice` - Create customer invoice
- `search_invoices` - Search invoices
- `aggregate_records` - Group/sum/count

### Sales
- `search_records` (sale.order)

### Purchase
- `create_purchase_order` - Create vendor PO

### Inventory
- `get_stock_levels` - Get product stock

### Expenses
- `create_expense` - Create expense entry

## Example Usage

**Search for leads:**
> "Show me all open B2B leads from this week"

**Create a lead:**
> "Create a new opportunity for Acme Corp with expected revenue $50,000"

**Create an invoice:**
> "Create an invoice for customer ID 5 with product 'Consulting' for $1,000"

**Get stock:**
> "What's the stock level for product ID 42?"

## Development

```bash
# Clone
git clone https://github.com/your-org/odoo-mcp-connector.git
cd odoo-mcp-connector

# Create venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run server
python -m mcp_server_odoo
```

## Docker

```bash
docker build -t odoo-mcp-connector .
docker run --rm -i \
  -e ODOO_URL=https://your-odoo.com \
  -e ODOO_API_KEY=your-key \
  -e ODOO_DB=your-db \
  odoo-mcp-connector
```

## License

MIT License - See LICENSE file for details.

This project is based on concepts and patterns from:
- [mcp-server-odoo](https://github.com/ivnvxd/mcp-server-odoo) by ivnvxd (MPL-2.0)
- [odoo-mcp-pro](https://github.com/pantalytics/odoo-mcp-pro) by Pantalytics (Elastic 2.0)
- [claude-odoo-api](https://github.com/bmya/claude-odoo-api) by bmya (MIT)

The Model Context Protocol is an open standard by Anthropic.
Odoo is a registered trademark of Odoo S.A.
