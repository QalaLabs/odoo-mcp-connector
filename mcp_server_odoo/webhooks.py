"""Webhook endpoints for lead capture from website contact forms."""

from __future__ import annotations
import hashlib
import hmac
import json
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

from .lead_classifier import classify_lead, get_tags_for_type, get_team_for_type

logger = logging.getLogger(__name__)


@dataclass
class WebhookConfig:
    """Webhook server configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    api_key: Optional[str] = None
    hmac_secret: Optional[str] = None
    odoo_config: Optional[dict] = None


@dataclass
class ContactData:
    """Parsed contact form data."""
    source: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    message: str
    metadata: dict


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP handler for webhook requests."""

    def log_message(self, format, *args):
        logger.info(format % args)

    def do_POST(self):
        if self.path == "/webhook/contact":
            self._handle_contact_webhook()
        elif self.path == "/health":
            self._handle_health()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_contact_webhook(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            if not self._verify_auth(body):
                self.send_response(401)
                self.end_headers()
                return

            data = json.loads(body)
            contact = self._parse_contact(data)
            result = self._process_lead(contact)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "lead_id": result.get("lead_id"),
                "classification": result.get("classification"),
            }).encode())

        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _verify_auth(self, body: bytes) -> bool:
        config = self.server.config
        if config.api_key:
            auth = self.headers.get("Authorization", "")
            return auth == f"Bearer {config.api_key}"
        if config.hmac_secret:
            signature = self.headers.get("X-Signature", "")
            expected = hmac.new(
                config.hmac_secret.encode(), body, hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected)
        return True

    def _parse_contact(self, data: dict) -> ContactData:
        contact = data.get("contact", {})
        return ContactData(
            source=data.get("source", "webhook"),
            name=contact.get("name", "Unknown"),
            email=contact.get("email"),
            phone=contact.get("phone"),
            company=contact.get("company"),
            message=contact.get("message", ""),
            metadata=data.get("metadata", {}),
        )

    def _process_lead(self, contact: ContactData) -> dict:
        classification = classify_lead(
            name=contact.name,
            email=contact.email or "",
            phone=contact.phone or "",
            company=contact.company or "",
            message=contact.message,
            source=contact.source,
        )

        if not self.server.odoo_connection:
            return {"lead_id": None, "classification": classification}

        conn = self.server.odoo_connection
        tag_names = get_tags_for_type(classification["lead_type"])
        tag_ids = []
        for t in tag_names:
            existing = conn.search("crm.tag", [["name", "=", t]], limit=1)
            if existing:
                tag_ids.append(existing[0])
            else:
                tag_ids.append(conn.create("crm.tag", {"name": t}))

        partner_id = None
        if contact.email:
            partners = conn.search("res.partner", [["email", "=", contact.email]], limit=1)
            if not partners:
                partner_id = conn.create("res.partner", {
                    "name": contact.name,
                    "email": contact.email,
                    "phone": contact.phone,
                    "company_type": "company" if contact.company else "person",
                })
            else:
                partner_id = partners[0]

        values = {
            "name": contact.message[:100] if contact.message else contact.name,
            "contact_name": contact.name,
            "email_from": contact.email,
            "phone": contact.phone,
            "partner_name": contact.company,
            "description": contact.message,
            "type": classification["lead_type"],
            "priority": classification["priority"],
            "tag_ids": [(6, 0, tag_ids)] if tag_ids else [],
        }
        team_id = get_team_for_type(classification["lead_type"])
        if team_id:
            values["team_id"] = team_id
        if partner_id:
            values["partner_id"] = partner_id

        lead_id = conn.create("crm.lead", values)

        if contact.message:
            conn.call_method("crm.lead", "message_post", args=[[lead_id]], kwargs={
                "body": f"[Website Contact Form]\n\n{contact.message}",
                "subtype": "comment",
            })

        deadline = datetime.now() + timedelta(hours=24)
        try:
            model_ids = conn.search("ir.model", [["model", "=", "crm.lead"]], limit=1)
            conn.create("mail.activity", {
                "res_id": lead_id,
                "res_model_id": model_ids[0] if model_ids else False,
                "activity_type_id": 1,
                "date_deadline": deadline.date().isoformat(),
                "summary": f"Follow-up: {contact.name}",
            })
        except Exception:
            pass

        return {"lead_id": lead_id, "classification": classification}

    def _handle_health(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')


class WebhookServer(HTTPServer):
    """Custom HTTP server for webhooks."""

    def __init__(self, config: WebhookConfig):
        super().__init__((config.host, config.port), WebhookHandler)
        self.config = config
        self.odoo_connection = None


def start_webhook_server(config: WebhookConfig, odoo_conn=None):
    """Start the webhook server."""
    server = WebhookServer(config)
    server.odoo_connection = odoo_conn
    logger.info(f"Starting webhook server on {config.host}:{config.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down webhook server")
        server.shutdown()
