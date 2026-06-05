"""Odoo MCP Connector - MCP server for Odoo ERP integration.

This MCP server enables AI assistants to interact with Odoo ERP through
natural language, supporting CRUD operations across CRM, Accounting,
Sales, Purchase, Inventory, and Expenses modules.

Based on concepts from:
- mcp-server-odoo (ivnvxd) - MPL-2.0
- odoo-mcp-pro (Pantalytics) - Elastic 2.0  
- claude-odoo-api (bmya) - MIT
"""

__version__ = "0.1.0"
__author__ = "Developer"
__license__ = "MIT"

from .config import OdooConfig, load_config
from .odoo_connection import OdooConnection, OdooConnectionError, create_connection
from .server import OdooMCPServer
from .error_handling import (
    OdooMCPError,
    AuthenticationError,
    PermissionError,
    ValidationError,
    NotFoundError,
)
from .schemas import (
    SearchResult,
    RecordData,
    ModelInfo,
    FieldInfo,
)

__all__ = [
    "__version__",
    "OdooMCPServer",
    "OdooConfig",
    "load_config",
    "OdooConnection",
    "OdooConnectionError",
    "create_connection",
    "OdooMCPError",
    "AuthenticationError",
    "PermissionError",
    "ValidationError",
    "NotFoundError",
    "SearchResult",
    "RecordData",
    "ModelInfo",
    "FieldInfo",
]
