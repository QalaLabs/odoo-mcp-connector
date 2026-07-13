#!/usr/bin/env python3
"""Script to generate manifest.json for the Odoo MCP Connector."""

import json
import os
import sys
from pathlib import Path

# Add project root to sys.path to enable importing local package
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

try:
    from mcp_server_odoo.tools import register_all_tools
except ImportError as e:
    print(f"Error: Could not import mcp_server_odoo tools. Make sure you run this script from the project root. Detail: {e}", file=sys.stderr)
    sys.exit(1)


def parse_pyproject_toml() -> dict:
    """Simple parser for pyproject.toml to extract project metadata."""
    metadata = {}
    toml_path = project_root / "pyproject.toml"
    if not toml_path.exists():
        return metadata

    in_project_section = False
    with open(toml_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Ignore comments and empty lines
            if not line or line.startswith("#"):
                continue
            if line == "[project]":
                in_project_section = True
                continue
            elif line.startswith("[") and line.endswith("]"):
                in_project_section = False
                continue

            if in_project_section and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key in ("name", "version", "description"):
                    metadata[key] = val
    return metadata


def generate_manifest() -> dict:
    """Generate the manifest dict."""
    metadata = parse_pyproject_toml()
    
    name = metadata.get("name", "odoo-mcp-connector")
    version = metadata.get("version", "0.1.0")
    description = metadata.get("description", "MCP server for Odoo ERP - Claude AI integration")
    
    # Get tools
    try:
        raw_tools = register_all_tools(None)
        tools = [{"name": t.name, "description": t.description} for t in raw_tools]
    except Exception as e:
        print(f"Warning: Could not dynamically extract tools: {e}. Outputting empty tools list.", file=sys.stderr)
        tools = []

    manifest = {
        "$schema": "https://raw.githubusercontent.com/anthropics/mcpb/main/schemas/mcpb-manifest-v0.4.schema.json",
        "manifest_version": "0.4",
        "name": name,
        "display_name": "Odoo MCP Connector",
        "version": version,
        "description": description,
        "author": {
            "name": "Qala Labs",
            "email": "hello@qalalabs.com",
            "url": "https://github.com/QalaLabs"
        },
        "repository": {
            "type": "git",
            "url": f"https://github.com/QalaLabs/{name}.git"
        },
        "homepage": f"https://github.com/QalaLabs/{name}#readme",
        "support": f"https://github.com/QalaLabs/{name}/issues",
        "license": "MIT",
        "server": {
            "type": "python",
            "entry_point": "mcp_server_odoo/__main__.py",
            "mcp_config": {
                "command": "python",
                "args": ["-m", "mcp_server_odoo"],
                "env": {
                    "ODOO_URL": "${user_config.odooUrl}",
                    "ODOO_API_KEY": "${user_config.odooApiKey}",
                    "ODOO_USER": "${user_config.odooUser}",
                    "ODOO_PASSWORD": "${user_config.odooPassword}",
                    "ODOO_DB": "${user_config.odooDb}",
                    "ODOO_YOLO": "${user_config.yoloMode}"
                }
            }
        },
        "user_config": {
            "odooUrl": {
                "type": "string",
                "title": "Odoo URL",
                "description": "The URL of your Odoo instance (e.g. https://mycompany.odoo.com)",
                "required": True
            },
            "odooApiKey": {
                "type": "string",
                "title": "API Key",
                "description": "Odoo API key for authentication (recommended)",
                "sensitive": True,
                "required": False
            },
            "odooUser": {
                "type": "string",
                "title": "Username",
                "description": "Odoo username/login (required if API key is not used)",
                "required": False
            },
            "odooPassword": {
                "type": "string",
                "title": "Password",
                "description": "Odoo password (required if API key is not used)",
                "sensitive": True,
                "required": False
            },
            "odooDb": {
                "type": "string",
                "title": "Database Name",
                "description": "Odoo database name (will be auto-detected if not specified)",
                "required": False
            },
            "yoloMode": {
                "type": "string",
                "title": "YOLO Mode",
                "description": "Bypasses safety checks. Allowed values: off, read, true",
                "default": "off",
                "required": False
            }
        },
        "tools": tools
    }
    
    return manifest


def main():
    manifest = generate_manifest()
    
    if len(sys.argv) > 1 and sys.argv[1] in ("--print", "-p"):
        print(json.dumps(manifest, indent=2))
    else:
        output_path = project_root / "manifest.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")
        print(f"Manifest successfully generated and saved to {output_path}")


if __name__ == "__main__":
    main()
