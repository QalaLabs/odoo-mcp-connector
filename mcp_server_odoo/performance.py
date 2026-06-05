"""Performance optimizations for Odoo MCP Connector."""

from __future__ import annotations
from typing import Optional, Any
from functools import lru_cache
import threading
import time

from .odoo_connection import OdooConnection


class ConnectionPool:
    """Simple connection pool for multi-threaded access."""

    def __init__(self, config, max_size: int = 5):
        self.config = config
        self.max_size = max_size
        self._pool: list[OdooConnection] = []
        self._lock = threading.Lock()
        self._created = 0

    def acquire(self) -> OdooConnection:
        """Acquire a connection from the pool."""
        with self._lock:
            if self._pool:
                return self._pool.pop()
            if self._created >= self.max_size:
                raise RuntimeError("Connection pool exhausted")
            self._created += 1
        
        conn = OdooConnection(self.config)
        conn.connect()
        return conn

    def release(self, conn: OdooConnection) -> None:
        """Return a connection to the pool."""
        with self._lock:
            if len(self._pool) < self.max_size:
                self._pool.append(conn)
                return
            self._created -= 1


class SmartFieldSelector:
    """Select most relevant fields per model."""

    ESSENTIAL_FIELDS = {"id", "display_name", "name", "active"}

    BUSINESS_FIELDS = {
        "res.partner": ["email", "phone", "street", "city", "country_id", "company_type"],
        "crm.lead": ["type", "stage_id", "user_id", "partner_id", "priority", "probability"],
        "sale.order": ["partner_id", "state", "date_order", "amount_total", "user_id"],
        "account.move": ["partner_id", "state", "invoice_date", "amount_total", "move_type"],
        "product.product": ["name", "list_price", "standard_price", "qty_available", "type"],
        "stock.picking": ["partner_id", "state", "scheduled_date", "picking_type_id"],
        "hr.expense": ["name", "product_id", "unit_amount", "quantity", "state"],
    }

    SKIP_FIELD_TYPES = {"binary", "html", "reference", "one2many"}

    SKIP_FIELD_NAMES = {
        "message_partner_ids", "message_follower_ids", "message_ids",
        "activity_ids", "access_token", "password", "__last_update",
    }

    def select_fields(self, model: str, fields: list = None, max_fields: int = 15) -> list:
        """Select optimal fields for a model."""
        if fields and fields != ["__all__"]:
            return fields
        
        if fields == ["__all__"]:
            return []
        
        selected = list(self.ESSENTIAL_FIELDS)
        
        business = self.BUSINESS_FIELDS.get(model, [])
        selected.extend(business)
        
        return list(set(selected))[:max_fields]

    def should_skip_field(self, field_name: str, field_type: str) -> bool:
        """Check if field should be skipped."""
        if field_name in self.SKIP_FIELD_NAMES:
            return True
        if field_type in self.SKIP_FIELD_TYPES:
            return True
        if field_name.startswith("x_studio_"):
            return True
        return False


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls: int = 100, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window = window_seconds
        self._calls: list[float] = []
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        """Check if call is allowed."""
        with self._lock:
            now = time.time()
            self._calls = [t for t in self._calls if now - t < self.window]
            
            if len(self._calls) >= self.max_calls:
                return False
            
            self._calls.append(now)
            return True

    def wait_time(self) -> float:
        """Get seconds until next call allowed."""
        with self._lock:
            if len(self._calls) < self.max_calls:
                return 0
            oldest = min(self._calls)
            return max(0, self.window - (time.time() - oldest))
