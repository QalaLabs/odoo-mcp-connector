"""Sanitize Odoo error messages for safe client responses."""

from __future__ import annotations
import re
import logging

logger = logging.getLogger(__name__)

SENSITIVE_PATTERNS = [
    (re.compile(r"api_key[:\s]*[a-zA-Z0-9]+", re.IGNORECASE), "api_key: [REDACTED]"),
    (re.compile(r"password[:\s]*[^\s,}]+", re.IGNORECASE), "password: [REDACTED]"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9]+"), "Bearer [REDACTED]"),
    (re.compile(r"/xmlrpc/[a-zA-Z0-9]+"), "/xmlrpc/[REDACTED]"),
    (re.compile(r"Database:\s*[a-zA-Z0-9_]+", re.IGNORECASE), "Database: [REDACTED]"),
    (re.compile(r"login[:\s]*[^\s,}]+", re.IGNORECASE), "login: [REDACTED]"),
    (re.compile(r"token[:\s]*[a-zA-Z0-9]+", re.IGNORECASE), "token: [REDACTED]"),
    (re.compile(r"secret[:\s]*[^\s,}]+", re.IGNORECASE), "secret: [REDACTED]"),
]

STACK_TRACE_PATTERNS = [
    r"Traceback \(most recent call last\)",
    r"File \".*\", line \d+",
    r"    \w+ = ",
    r"^AttributeError:",
    r"^ValueError:",
    r"^KeyError:",
    r"^TypeError:",
]


def sanitize_error(error: Exception) -> str:
    """Sanitize error message for client response."""
    message = str(error)
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    if any(p in message for p in ["Traceback", "File \""]):
        message = sanitize_stack_trace(message)
    return message


def sanitize_stack_trace(full_trace: str) -> str:
    """Remove stack trace details, keep only the error message."""
    lines = full_trace.split("\n")
    clean_lines = []
    for line in lines:
        is_stack_trace = any(re.search(p, line) for p in STACK_TRACE_PATTERNS)
        if is_stack_trace:
            continue
        clean_lines.append(line)
    return "\n".join(clean_lines).strip()


def format_odoo_error(odoo_error: dict) -> str:
    """Format Odoo RPC error for client response."""
    if isinstance(odoo_error, dict):
        name = odoo_error.get("name", "")
        message = odoo_error.get("message", str(odoo_error))
        if "Access Error" in name or "AccessError" in name:
            return "Access denied. Check permissions."
        if "ValidationError" in name:
            return f"Validation error: {message}"
        if "NotFoundError" in name or "missing record" in message.lower():
            return "Record not found."
        if "UserError" in name:
            return message
        return sanitize_error(Exception(message))
    return sanitize_error(Exception(str(odoo_error)))


def is_safe_to_expose(error: Exception) -> bool:
    """Check if error can be safely exposed to client."""
    unsafe_keywords = [
        "api_key", "password", "secret", "token", "credential",
        "bearer", "authentication", "authorization",
    ]
    message_lower = str(error).lower()
    return not any(kw in message_lower for kw in unsafe_keywords)
