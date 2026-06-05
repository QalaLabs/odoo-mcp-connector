"""Webhook endpoints for lead capture."""

from __future__ import annotations
import hashlib
import hmac
import json
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

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


class LeadClassifier:
    """Classify incoming leads by type."""

    PERSONAL_EMAIL_DOMAINS = {
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "aol.com", "icloud.com", "mail.com", "protonmail.com",
    }

    B2C_KEYWORDS = ["personal", "individual", "private", "home"]

    B2B_KEYWORDS = ["company", "business", "corporate", "enterprise", "llc", "inc"]

    SUPPORT_KEYWORDS = [
        "help", "support", "issue", "problem", "broken", "error",
        "not working", "bug", "fix", "urgent", "asap", "emergency",
    ]

    DEALER_KEYWORDS = [
        "dealer", "distributor", "franchise", "wholesale", "reseller",
        "agent", "broker", "partner program",
    ]

    def classify(self, contact: ContactData) -> dict:
        """Classify lead type and return assignment data."""
        lead_type = "lead"
        team_id = None
        tag_ids = []
        priority = "2"

        company = contact.company or ""
        email = contact.email or ""
        message = contact.message.lower()
        combined = f"{company} {email} {message}".lower()

        if any(kw in combined for kw in self.SUPPORT_KEYWORDS):
            lead_type = "lead"
            tag_ids.append(self._get_or_create_tag("Support"))
            priority = "3"

        elif any(kw in combined for kw in self.DEALER_KEYWORDS):
            lead_type = "lead"
            tag_ids.append(self._get_or_create_tag("Dealer"))
            priority = "2"

        elif email:
            domain = email.split("@")[-1] if "@" in email else ""
            is_personal = domain in self.PERSONAL_EMAIL_DOMAINS

            if company or not is_personal:
                lead_type = "opportunity"
                tag_ids.append(self._get_or_create_tag("B2B"))
                priority = "3"
            else:
                lead_type = "lead"
                tag_ids.append(self._get_or_create_tag("B2C"))

        return {
            "lead_type": lead_type,
            "team_id": team_id,
            "tag_ids": tag_ids,
            "priority": priority,
        }

    def _get_or_create_tag(self, tag_name: str) -> int:
        """Placeholder for tag lookup - returns 0, implement with actual Odoo lookup."""
        return 0


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP handler for webhook requests."""

    def log_message(self, format, *args):
        """Suppress default logging."""
        logger.info(format % args)

    def do_POST(self):
        """Handle POST requests."""
        if self.path == "/webhook/contact":
            self._handle_contact_webhook()
        elif self.path == "/health":
            self._handle_health()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_contact_webhook(self):
        """Handle incoming contact form webhook."""
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
        """Verify request authentication."""
        config = self.server.config

        if config.api_key:
            auth = self.headers.get("Authorization", "")
            expected = f"Bearer {config.api_key}"
            return auth == expected

        if config.hmac_secret:
            signature = self.headers.get("X-Signature", "")
            expected = hmac.new(
                config.hmac_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected)

        return True

    def _parse_contact(self, data: dict) -> ContactData:
        """Parse incoming contact data."""
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
        """Process lead through classifier and create in Odoo."""
        classifier = LeadClassifier()
        classification = classifier.classify(contact)

        if self.server.odoo_connection:
            conn = self.server.odoo_connection

            partner_id = None
            if contact.email:
                partners = conn.search("res.partner", [["email", "=", contact.email]])
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
                "tag_ids": [(6, 0, classification["tag_ids"])] if classification["tag_ids"] else [],
            }
            if partner_id:
                values["partner_id"] = partner_id

            lead_id = conn.create("crm.lead", values)

            if contact.message:
                conn.call_method("crm.lead", "message_post", args=[[lead_id]], kwargs={
                    "body": f"[Website Contact Form]\n\n{contact.message}",
                    "subtype": "comment",
                })

            from datetime import timedelta
            deadline = datetime.now() + timedelta(hours=24)
            try:
                conn.create("mail.activity", {
                    "res_id": lead_id,
                    "res_model_id": conn.call_method("ir.model", "search", args=[["model", "=", "crm.lead"]]),
                    "activity_type_id": 1,
                    "date_deadline": deadline.date().isoformat(),
                    "summary": f"Follow-up: {contact.name}",
                })
            except Exception:
                pass

            return {"lead_id": lead_id, "classification": classification}

        return {"lead_id": None, "classification": classification}

    def _handle_health(self):
        """Health check endpoint."""
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
