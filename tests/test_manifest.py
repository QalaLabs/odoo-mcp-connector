"""Unit tests for manifest.py generator."""

import json
from pathlib import Path
from manifest import parse_pyproject_toml, generate_manifest


def test_parse_pyproject_toml():
    """Test that metadata is parsed successfully from pyproject.toml."""
    metadata = parse_pyproject_toml()
    
    assert "name" in metadata
    assert metadata["name"] == "odoo-mcp-connector"
    assert "version" in metadata
    assert "description" in metadata


def test_generate_manifest():
    """Test that generate_manifest produces the correct structure."""
    manifest = generate_manifest()
    
    # Check top-level keys
    assert manifest["manifest_version"] == "0.4"
    assert manifest["name"] == "odoo-mcp-connector"
    assert manifest["display_name"] == "Odoo MCP Connector"
    assert manifest["author"]["name"] == "Qala Labs"
    
    # Check server config
    assert manifest["server"]["type"] == "python"
    assert manifest["server"]["entry_point"] == "mcp_server_odoo/__main__.py"
    assert manifest["server"]["mcp_config"]["command"] == "python"
    
    # Check user config fields
    user_config = manifest["user_config"]
    assert "odooUrl" in user_config
    assert "odooApiKey" in user_config
    assert "odooUser" in user_config
    assert "odooPassword" in user_config
    assert "odooDb" in user_config
    assert "yoloMode" in user_config
    
    # Check tools are extracted
    tools = manifest["tools"]
    assert len(tools) > 0
    # Check that first tool has name and description
    assert "name" in tools[0]
    assert "description" in tools[0]
    
    # Verify odoo_search_records is present
    tool_names = [t["name"] for t in tools]
    assert "odoo_search_records" in tool_names
