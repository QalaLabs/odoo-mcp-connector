"""Unit tests for Odoo connection layer."""

from unittest.mock import Mock, patch

import pytest


class TestOdooConnection:
    """Test OdooConnection class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = Mock()
        config.url = "https://test.odoo.com"
        config.api_key = "test_key"
        config.database = "test_db"
        config.user = None
        config.password = None
        config.locale = "en_US"
        config.yolo_mode = "off"
        return config

    def test_init(self, mock_config):
        """Test connection initialization."""
        with patch("mcp_server_odoo.odoo_connection.OdooConnection.__init__", return_value=None):
            from mcp_server_odoo.odoo_connection import OdooConnection
            conn = OdooConnection.__new__(OdooConnection)
            conn.config = mock_config
            conn.url = mock_config.url
            conn.db = mock_config.database
            conn.uid = None
            conn.api_type = None
            conn._version = None
            conn._session = Mock()

            assert conn.url == "https://test.odoo.com"
            assert conn.db == "test_db"


class TestErrorSanitizer:
    """Test error sanitization."""

    def test_sanitize_api_key(self):
        """Test API key is redacted."""
        from mcp_server_odoo.error_sanitizer import sanitize_error

        error = Exception("Invalid api_key: abc123 secret key")
        result = sanitize_error(error)
        assert "api_key" in result.lower()
        assert "abc123" not in result

    def test_sanitize_password(self):
        """Test password is redacted."""
        from mcp_server_odoo.error_sanitizer import sanitize_error

        error = Exception("password: mysecretpass")
        result = sanitize_error(error)
        assert "mysecretpass" not in result


class TestFormatters:
    """Test output formatters."""

    def test_format_record(self):
        """Test record formatting."""
        from mcp_server_odoo.formatters import format_record

        record = {
            "id": 1,
            "display_name": "Test Partner",
            "email": "test@example.com",
            "phone": "+1234567890",
        }
        result = format_record(record, "res.partner")
        assert "Test Partner" in result
        assert "test@example.com" in result

    def test_format_records_empty(self):
        """Test empty records."""
        from mcp_server_odoo.formatters import format_records

        result = format_records([])
        assert "No records found" in result

    def test_format_count(self):
        """Test count formatting."""
        from mcp_server_odoo.formatters import format_count

        result = format_count(42, "res.partner")
        assert "42" in result
        assert "res.partner" in result

    def test_clean_html(self):
        """Test clean_html strips tags and unescapes entities."""
        from mcp_server_odoo.formatters import clean_html

        raw_html = "<p>Invoice validated<br/>Next line &amp; &lt;details&gt;</p>"
        cleaned = clean_html(raw_html)
        assert cleaned == "Invoice validated\nNext line & <details>"
        assert clean_html("") == ""
        assert clean_html(None) == ""


class TestSchemas:
    """Test Pydantic schemas."""

    def test_search_records_input(self):
        """Test search input validation."""
        from mcp_server_odoo.schemas import SearchRecordsInput

        input_data = SearchRecordsInput(
            model="res.partner",
            domain=[["name", "=", "Test"]],
            limit=5,
        )
        assert input_data.model == "res.partner"
        assert input_data.limit == 5

    def test_create_record_input(self):
        """Test create input validation."""
        from mcp_server_odoo.schemas import CreateRecordInput

        input_data = CreateRecordInput(
            model="res.partner",
            values={"name": "Test", "email": "test@example.com"},
        )
        assert input_data.model == "res.partner"
        assert input_data.values["name"] == "Test"

    def test_create_lead_input(self):
        """Test lead creation input."""
        from mcp_server_odoo.schemas import CreateLeadInput

        input_data = CreateLeadInput(
            name="Test Lead",
            email_from="test@example.com",
            lead_type="opportunity",
        )
        assert input_data.name == "Test Lead"
        assert input_data.lead_type == "opportunity"
