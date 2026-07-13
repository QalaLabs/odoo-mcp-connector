"""Logging configuration for Odoo MCP Connector."""

from __future__ import annotations
import logging
import sys
import json
from datetime import datetime
from typing import Optional

from .config import OdooConfig


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        return json.dumps(log_data)


def setup_logging(config: OdooConfig) -> logging.Logger:
    """Configure logging based on config."""
    log_level = getattr(logging, config.mcp_log_level, logging.INFO)
    
    # Configure root logger to output to stderr to prevent any library from printing to stdout
    logging.basicConfig(level=log_level, stream=sys.stderr, force=True)
    
    logger = logging.getLogger("mcp_server_odoo")
    logger.setLevel(log_level)
    
    logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    
    if config.mcp_log_json:
        handler.setFormatter(JSONFormatter())
    else:
        fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
    
    logger.addHandler(handler)
    
    # Silence verbose logs from requests and urllib3 to avoid cluttering stderr
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str = "mcp_server_odoo") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
