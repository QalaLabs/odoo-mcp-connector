"""Channel integrations for WhatsApp (Convertway) and Email (Gmail)."""

from __future__ import annotations
import logging
from typing import Optional
from datetime import datetime, timedelta

from .lead_classifier import classify_lead, get_tags_for_type, get_team_for_type
from .odoo_connection import run_sync

logger = logging.getLogger(__name__)


class ChannelAdapter:
    """Base adapter for channel integrations."""

    def __init__(self, odoo_connection):
        self.conn = odoo_connection

    def _ensure_tag(self, tag_name: str) -> Optional[int]:
        """Look up or create a crm.tag by name."""
        existing = run_sync(self.conn.search("crm.tag", [["name", "=", tag_name]], limit=1))
        if existing:
            return existing[0]
        return run_sync(self.conn.create("crm.tag", {"name": tag_name}))

    def _resolve_tags(self, tag_names: list[str]) -> list[int]:
        return [self._ensure_tag(t) for t in tag_names if t]

    def _schedule_follow_up(self, lead_id: int, name: str, hours: int = 24):
        """Create a mail.activity for follow-up."""
        try:
            model_ids = run_sync(self.conn.search("ir.model", [["model", "=", "crm.lead"]], limit=1))
            res_model_id = model_ids[0] if model_ids else False
            deadline = datetime.now() + timedelta(hours=hours)
            run_sync(self.conn.create("mail.activity", {
                "res_id": lead_id,
                "res_model_id": res_model_id,
                "activity_type_id": 1,
                "date_deadline": deadline.date().isoformat(),
                "summary": f"Follow-up: {name}",
                "note": f"First follow-up for new lead from channel",
            }))
        except Exception as e:
            logger.warning(f"Could not schedule follow-up: {e}")

    def _post_message(self, lead_id: int, body: str):
        """Post a message to lead chatter."""
        try:
            run_sync(self.conn.call_method(
                "crm.lead", "message_post",
                args=[[lead_id]],
                kwargs={"body": body, "subtype": "comment"},
            ))
        except Exception as e:
            logger.warning(f"Could not post message to lead {lead_id}: {e}")


class WhatsAppAdapter(ChannelAdapter):
    """WhatsApp channel via Convertway."""

    def process_inbound(self, data: dict) -> Optional[int]:
        phone = data.get("from", data.get("phone", ""))
        message = data.get("message", data.get("text", ""))
        name = data.get("name", data.get("profile_name", phone))
        timestamp = data.get("timestamp", "")

        classification = classify_lead(
            name=name, phone=phone, message=message, source="whatsapp"
        )
        tag_names = get_tags_for_type(classification["lead_type"])
        tag_ids = self._resolve_tags(tag_names)

        lead = self._find_by_phone(phone)
        if lead:
            lead_id = lead
        else:
            partner_id = self._find_or_create_partner(name=name, phone=phone)
            values = {
                "name": message[:100] if message else f"WhatsApp enquiry - {phone}",
                "contact_name": name,
                "phone": phone,
                "type": classification["lead_type"],
                "priority": classification["priority"],
                "tag_ids": [(6, 0, tag_ids)] if tag_ids else [],
            }
            team_id = get_team_for_type(classification["lead_type"])
            if team_id:
                values["team_id"] = team_id
            if partner_id:
                values["partner_id"] = partner_id
            lead_id = run_sync(self.conn.create("crm.lead", values))
            self._schedule_follow_up(lead_id, name)

        body = f"""[WhatsApp - INBOUND]
From: {name} ({phone})
Time: {timestamp}

{message}"""
        self._post_message(lead_id, body)
        return lead_id

    def _find_by_phone(self, phone: str) -> Optional[int]:
        if not phone:
            return None
        leads = run_sync(self.conn.search("crm.lead", [["phone", "=", phone]], limit=1))
        return leads[0] if leads else None

    def _find_or_create_partner(self, name: str, phone: str) -> Optional[int]:
        if not phone:
            return None
        partners = run_sync(self.conn.search("res.partner", [["phone", "=", phone]], limit=1))
        if partners:
            return partners[0]
        return run_sync(self.conn.create("res.partner", {
            "name": name, "phone": phone, "company_type": "person",
        }))


class EmailAdapter(ChannelAdapter):
    """Email channel via Gmail MCP."""

    def process_inbound(self, data: dict) -> Optional[int]:
        sender = data.get("from", data.get("sender", ""))
        subject = data.get("subject", "No Subject")
        body = data.get("body", data.get("text", ""))
        thread_id = data.get("thread_id", "")

        email = self._extract_email(sender)
        name = self._extract_name(sender) or email or "Unknown"

        classification = classify_lead(
            name=name, email=email or "", message=f"{subject} {body}", source="email"
        )
        tag_names = get_tags_for_type(classification["lead_type"])
        tag_ids = self._resolve_tags(tag_names)

        lead = self._find_by_email(email) if email else None
        if lead:
            lead_id = lead
        else:
            partner_id = self._find_or_create_partner(name=name, email=email) if email else None
            values = {
                "name": subject[:100],
                "contact_name": name,
                "email_from": email,
                "description": body,
                "type": classification["lead_type"],
                "priority": classification["priority"],
                "tag_ids": [(6, 0, tag_ids)] if tag_ids else [],
            }
            team_id = get_team_for_type(classification["lead_type"])
            if team_id:
                values["team_id"] = team_id
            if partner_id:
                values["partner_id"] = partner_id
            lead_id = run_sync(self.conn.create("crm.lead", values))
            self._schedule_follow_up(lead_id, name)

        formatted_body = f"""[Email - INBOUND]
From: {sender}
Subject: {subject}
Thread: {thread_id}

{body}"""
        self._post_message(lead_id, formatted_body)
        return lead_id

    def _extract_email(self, sender: str) -> Optional[str]:
        if not sender:
            return None
        if "<" in sender and ">" in sender:
            return sender.split("<")[1].split(">")[0].strip()
        if "@" in sender:
            return sender.strip()
        return None

    def _extract_name(self, sender: str) -> Optional[str]:
        if not sender:
            return None
        if "<" in sender and ">" in sender:
            return sender.split("<")[0].strip().strip('"')
        return None

    def _find_by_email(self, email: str) -> Optional[int]:
        if not email:
            return None
        leads = run_sync(self.conn.search("crm.lead", [["email_from", "=", email]], limit=1))
        return leads[0] if leads else None

    def _find_or_create_partner(self, name: str, email: str) -> Optional[int]:
        if not email:
            return None
        partners = run_sync(self.conn.search("res.partner", [["email", "=", email]], limit=1))
        if partners:
            return partners[0]
        return run_sync(self.conn.create("res.partner", {
            "name": name, "email": email, "company_type": "person",
        }))


def get_channel_adapter(channel: str, odoo_connection) -> Optional[ChannelAdapter]:
    """Get adapter for channel."""
    if channel.lower() == "whatsapp":
        return WhatsAppAdapter(odoo_connection)
    elif channel.lower() in ("email", "gmail"):
        return EmailAdapter(odoo_connection)
    return None

