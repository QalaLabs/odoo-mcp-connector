"""CLI entry point for Odoo MCP Connector."""

from __future__ import annotations
import sys
import asyncio
import os


def main():
    """Main entry point."""
    try:
        from .server import run_server
        from .config import load_config
        from .logging_config import get_logger

        if not os.path.exists(".env"):
            print("Error: .env file not found")
            print("Copy .env.example to .env and configure your Odoo credentials")
            sys.exit(1)

        config = load_config()
        logger = get_logger()
        logger.info("Starting Odoo MCP Connector...")
        logger.info(f"Transport: {config.mcp_transport}")
        logger.info(f"URL: {config.url}")

        if config.mcp_transport == "stdio":
            asyncio.run(run_server(config))
        else:
            logger.error(f"Transport '{config.mcp_transport}' not fully implemented")
            logger.info("Use 'stdio' transport for Claude Desktop")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
