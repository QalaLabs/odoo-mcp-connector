"""Custom exceptions for Odoo MCP Connector."""


class OdooMCPError(Exception):
    """Base exception for Odoo MCP errors."""

    def __init__(self, message: str, code: str = "ODOO_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(OdooMCPError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTH_ERROR")


class PermissionError(OdooMCPError):
    """Permission denied."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code="PERMISSION_ERROR")


class ValidationError(OdooMCPError):
    """Validation failed."""

    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, code="VALIDATION_ERROR")


class NotFoundError(OdooMCPError):
    """Record not found."""

    def __init__(self, model: str, record_id: int = None):
        msg = f"Record not found in {model}"
        if record_id:
            msg += f" (ID: {record_id})"
        super().__init__(msg, code="NOT_FOUND")


class ConnectionError(OdooMCPError):
    """Connection to Odoo failed."""

    def __init__(self, message: str = "Failed to connect to Odoo"):
        super().__init__(message, code="CONNECTION_ERROR")


class OdooConnectionError(OdooMCPError):
    """General Odoo connection error."""
    pass


class InvalidModelError(OdooMCPError):
    """Invalid model name."""

    def __init__(self, model: str):
        super().__init__(f"Invalid or inaccessible model: {model}", code="INVALID_MODEL")


class YOLOAccessError(OdooMCPError):
    """Operation blocked in YOLO read-only mode."""

    def __init__(self, operation: str):
        super().__init__(
            f"Operation '{operation}' blocked in YOLO read-only mode",
            code="YOLO_ACCESS_ERROR"
        )
