"""Module for channel integrations (WhatsApp, Email, etc.)."""

from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ChannelAdapter:
    """Base adapter for channel integrations."""

    def __init__(self, odoo_connection):
        self.conn = odoo_connection

    def process_inbound(self, data: dict) -> int:
        """Process inbound message, return lead ID."""
        raise NotImplementedError


class WhatsAppAdapter(ChannelAdapter):
    """WhatsApp channel via Convertway."""

    def process_inbound(self, data: dict) -> int:
        """Process inbound WhatsApp message."""
        phone = data.get("from", data.get("phone", ""))
        message = data.get("message", data.get("text", ""))
        timestamp = data.get("timestamp", "")

        lead_id = self._find_or_create_lead(phone)

        if lead_id and message:
            body = f"""[WhatsApp - INBOUND]
From: {phone}
Time: {timestamp}

{message}"""

            self.conn.call_method(
                "crm.lead",
                "message_post",
                args=[[lead_id]],
                kwargs={"body": body, "subtype": "comment"}
            )

        return lead_id

    def _find_or_create_lead(self, phone: str) -> Optional[int]:
        """Find existing lead or create new by phone."""
        leads = self.conn.search("crm.lead", [["phone", "=", phone]], limit=1)
        if leads:
            return leads[0]

        return None


class EmailAdapter(ChannelAdapter):
    """Email channel via Gmail MCP."""

    def process_inbound(self, data: dict) -> int:
        """Process inbound email."""
        sender = data.get("from", data.get("sender", ""))
        subject = data.get("subject", "No Subject")
        body = data.get("body", data.get("text", ""))
        thread_id = data.get("thread_id", "")

        email = self._extract_email(sender)

        lead_id = self._find_or_create_lead(email)

        if lead_id and body:
            formatted_body = f"""[Email - INBOUND]
From: {sender}
Subject: {subject}
Thread: {thread_id}

{body}"""

            self.conn.call_method(
                "crm.lead",
                "message_post",
                args=[[lead_id]],
                kwargs={"body": formatted_body, "subtype": "comment"}
            )

        return lead_id

    def _extract_email(self, sender: str) -> Optional[str]:
        """Extract email address from sender string."""
        if "<" in sender and ">" in sender:
            return sender.split("<")[1].split(">")[0].strip()
        if "@" in sender:
            return sender.strip()
        return None

    def _find_or_create_lead(self, email: str) -> Optional[int]:
        """Find existing lead or create new by email."""
        if not email:
            return None

        leads = self.conn.search("crm.lead", [["email_from", "=", email]], limit=1)
        if leads:
            return leads[0]

        return None


def get_channel_adapter(channel: str, odoo_connection) -> Optional[ChannelAdapter]:
    """Get adapter for channel."""
    if channel.lower() == "whatsapp":
        return WhatsAppAdapter(odoo_connection)
    elif channel.lower() in ("email", "gmail"):
        return EmailAdapter(odoo_connection)
    return None
