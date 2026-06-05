"""Odoo connection layer supporting XML-RPC (14-18) and JSON/2 API (19+)."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from dataclasses import dataclass
import xmlrpc.client

import httpx
import requests

from .config import OdooConfig
from .error_handling import OdooConnectionError, AuthenticationError

logger = logging.getLogger(__name__)


@dataclass
class OdooVersion:
    """Odoo version information."""
    major: int
    minor: int
    api_type: Literal["json2", "xmlrpc"]


class OdooConnection:
    """Odoo connection client with auto-detect API selection."""

    def __init__(self, config: OdooConfig):
        self.config = config
        self.url = config.url
        self.db = config.database
        self.uid: Optional[int] = None
        self.api_type: Optional[Literal["json2", "xmlrpc"]] = None
        self._version: Optional[OdooVersion] = None
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        if config.api_key:
            self._session.headers["Authorization"] = f"Bearer {config.api_key}"

    def connect(self) -> None:
        """Establish connection to Odoo and detect version."""
        try:
            if self.config.api_key:
                self._connect_with_api_key()
            else:
                self._connect_with_password()
            self._detect_version()
        except Exception as e:
            raise OdooConnectionError(f"Failed to connect to Odoo: {e}") from e

    def _connect_with_api_key(self) -> None:
        """Authenticate using API key."""
        if not self.db:
            self.db = self._get_database_from_url()
        
        auth_data = {
            "db": self.db,
            "api_key": self.config.api_key,
        }
        try:
            response = self._session.post(
                f"{self.url}/api/account/2/token",
                json=auth_data,
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                self.uid = data.get("user_id")
                if self.api_type is None:
                    self.api_type = "json2"
            else:
                raise AuthenticationError("Invalid API key")
        except requests.RequestException:
            self.api_type = "xmlrpc"
            self.uid = self._xmlrpc_authenticate()

    def _connect_with_password(self) -> None:
        """Authenticate using username/password."""
        if not self.db:
            self.db = self._get_database_from_url()
        self.uid = self._xmlrpc_authenticate()

    def _xmlrpc_authenticate(self) -> int:
        """Authenticate via XML-RPC."""
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        uid = common.authenticate(
            self.db,
            self.config.user,
            self.config.password,
            {}
        )
        if not uid:
            raise AuthenticationError("Authentication failed")
        return uid

    def _get_database_from_url(self) -> str:
        """Extract database name from URL or list databases."""
        try:
            response = self._session.get(
                f"{self.url}/web/database/list",
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                databases = data.get("databases", [])
                if databases:
                    return databases[0]
        except Exception:
            pass
        raise OdooConnectionError("Could not determine database. Set ODOO_DB explicitly.")

    def _detect_version(self) -> None:
        """Detect Odoo version and select appropriate API."""
        try:
            response = self._session.get(
                f"{self.url}/web/webclient/version_info",
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                version = data.get("version", {})
                server_version = version.get("serverVersion", "0.0")
                parts = server_version.split(".")[:2]
                self._version = OdooVersion(
                    major=int(parts[0]) if parts[0].isdigit() else 0,
                    minor=int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
                    api_type=self.api_type or "json2",
                )
                if self._version.major >= 19:
                    self.api_type = "json2"
                else:
                    self.api_type = "xmlrpc"
        except Exception:
            self.api_type = "xmlrpc"
            self._version = OdooVersion(major=0, minor=0, api_type="xmlrpc")

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """Execute Odoo model method."""
        if self.api_type == "json2":
            return self._execute_json2(model, method, *args, **kwargs)
        return self._execute_xmlrpc(model, method, *args, **kwargs)

    def _execute_json2(self, model: str, method: str, *args, **kwargs) -> Any:
        """Execute via JSON/2 API (Odoo 19+)."""
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        if self.config.api_key:
            headers["X-Odoo-Database"] = self.db
        
        payload = {
            "params": {
                "args": args,
                "kwargs": kwargs,
            }
        }
        
        url = f"{self.url}/json/2/{model}/{method}"
        try:
            response = self._session.post(
                url,
                json=payload,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise OdooConnectionError(f"Odoo error: {data['error']}")
            return data.get("result")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Authentication failed") from e
            raise OdooConnectionError(f"HTTP error: {e}") from e

    def _execute_xmlrpc(self, model: str, method: str, *args, **kwargs) -> Any:
        """Execute via XML-RPC (Odoo 14-18)."""
        object_proxy = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        return object_proxy.execute_kw(
            self.db,
            self.uid,
            self.config.password or self.config.api_key,
            model,
            method,
            args,
            kwargs,
        )

    def search_read(
        self,
        model: str,
        domain: list = None,
        fields: list = None,
        limit: int = 10,
        offset: int = 0,
        order: str = None,
    ) -> list[dict]:
        """Search and read records."""
        domain = domain or []
        if fields is None:
            fields = ["id", "display_name"]
        elif fields == "__all__":
            fields = []
        
        kwargs: dict = {
            "domain": domain,
            "fields": fields,
            "limit": limit,
        }
        if offset:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order
        
        return self.execute(model, "search_read", [], kwargs)

    def search(self, model: str, domain: list = None, limit: int = None) -> list[int]:
        """Search for record IDs."""
        domain = domain or []
        kwargs: dict = {}
        if limit:
            kwargs["limit"] = limit
        return self.execute(model, "search", [domain], kwargs)

    def count(self, model: str, domain: list = None) -> int:
        """Count records matching domain."""
        domain = domain or []
        return self.execute(model, "search_count", [domain], {})

    def read(self, model: str, ids: list[int], fields: list = None) -> list[dict]:
        """Read specific records by IDs."""
        if fields is None:
            fields = ["id", "display_name"]
        elif fields == "__all__":
            fields = []
        return self.execute(model, "read", [ids], {"fields": fields})

    def create(self, model: str, values: dict) -> int:
        """Create a new record."""
        return self.execute(model, "create", [values], {})

    def write(self, model: str, ids: list[int], values: dict) -> bool:
        """Update existing records."""
        return self.execute(model, "write", [ids, values], {})

    def unlink(self, model: str, ids: list[int]) -> bool:
        """Delete records."""
        return self.execute(model, "unlink", [ids], {})

    def fields_get(self, model: str, attributes: list = None) -> dict:
        """Get field definitions for a model."""
        attrs = attributes or ["name", "type", "string", "help", "required", "readonly"]
        return self.execute(model, "fields_get", [], {"attributes": attrs})

    def call_method(self, model: str, method: str, args: list = None, kwargs: dict = None) -> Any:
        """Call arbitrary model method."""
        args = args or []
        kwargs = kwargs or {}
        return self.execute(model, method, args, kwargs)

    @property
    def version(self) -> OdooVersion:
        """Get Odoo version info."""
        if self._version is None:
            self._detect_version()
        return self._version or OdooVersion(major=0, minor=0, api_type="xmlrpc")


def create_connection(config: OdooConfig = None) -> OdooConnection:
    """Create and connect to Odoo instance."""
    if config is None:
        config = load_config()
    conn = OdooConnection(config)
    conn.connect()
    return conn


def load_config() -> OdooConfig:
    """Load config - import here to avoid circular import."""
    from .config import load_config as _load_config
    return _load_config()
