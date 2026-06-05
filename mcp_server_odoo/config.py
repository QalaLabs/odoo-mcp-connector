"""Configuration management for Odoo MCP Connector."""

from __future__ import annotations

import os
from typing import Optional, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env(name: str, default: str = None) -> Optional[str]:
    """Get environment variable."""
    return os.environ.get(name, default)


class OdooConfig(BaseSettings):
    """Odoo connection and MCP server configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    url: str = Field(
        default="https://demo.odoo.com",
        description="Odoo instance URL",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (recommended)",
    )
    user: Optional[str] = Field(
        default=None,
        description="Username (required if not using API key)",
    )
    password: Optional[str] = Field(
        default=None,
        description="Password (required if not using API key)",
    )
    database: Optional[str] = Field(
        default=None,
        description="Database name (auto-detected if not set)",
    )
    locale: str = Field(
        default="en_US",
        description="Language/locale for Odoo responses",
    )
    yolo_mode: Literal["off", "read", "true"] = Field(
        default="off",
        description="YOLO mode - bypasses MCP security (DEV ONLY)",
    )

    mcp_transport: Literal["stdio", "streamable-http"] = Field(
        default="stdio",
        description="MCP transport type",
    )
    mcp_host: str = Field(
        default="localhost",
        description="Host to bind for HTTP transport",
    )
    mcp_port: int = Field(
        default=8000,
        description="Port to bind for HTTP transport",
    )
    mcp_default_limit: int = Field(
        default=10,
        description="Default number of records returned per search",
    )
    mcp_max_limit: int = Field(
        default=100,
        description="Maximum allowed record limit per request",
    )
    mcp_max_smart_fields: int = Field(
        default=15,
        description="Maximum fields returned by smart field selection",
    )
    mcp_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Log level",
    )
    mcp_log_json: bool = Field(
        default=False,
        description="Enable structured JSON log output",
    )
    mcp_log_file: Optional[str] = Field(
        default=None,
        description="Path for rotating log file",
    )
    mcp_enable_method_calls: bool = Field(
        default=False,
        description="Enable call_model_method tool (requires YOLO=true)",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "ODOO_URL" in os.environ:
            self.url = os.environ["ODOO_URL"]
        if "ODOO_API_KEY" in os.environ:
            self.api_key = os.environ["ODOO_API_KEY"]
        if "ODOO_USER" in os.environ:
            self.user = os.environ["ODOO_USER"]
        if "ODOO_PASSWORD" in os.environ:
            self.password = os.environ["ODOO_PASSWORD"]
        if "ODOO_DB" in os.environ:
            self.database = os.environ["ODOO_DB"]
        if "ODOO_LOCALE" in os.environ:
            self.locale = os.environ["ODOO_LOCALE"]
        if "ODOO_YOLO" in os.environ:
            self.yolo_mode = os.environ["ODOO_YOLO"]
        if "ODOO_MCP_TRANSPORT" in os.environ:
            self.mcp_transport = os.environ["ODOO_MCP_TRANSPORT"]
        if "ODOO_MCP_HOST" in os.environ:
            self.mcp_host = os.environ["ODOO_MCP_HOST"]
        if "ODOO_MCP_PORT" in os.environ:
            self.mcp_port = int(os.environ["ODOO_MCP_PORT"])
        if "ODOO_MCP_LOG_LEVEL" in os.environ:
            self.mcp_log_level = os.environ["ODOO_MCP_LOG_LEVEL"]

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        if v:
            return v.rstrip("/")
        return v

    @property
    def auth_method(self) -> Literal["api_key", "password"]:
        """Return the authentication method being used."""
        if self.api_key:
            return "api_key"
        return "password"


def load_config() -> OdooConfig:
    """Load configuration from environment variables."""
    return OdooConfig()
