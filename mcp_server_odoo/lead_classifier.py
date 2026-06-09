"""Lead classification for multi-channel CRM intake."""

from __future__ import annotations
from typing import Optional


# Tag name constants for Odoo crm.tag model
TAG_SUPPORT = "Support"
TAG_DEALER = "Dealer/Distributor"
TAG_B2B = "B2B"
TAG_B2C = "B2C"
TAG_T6_PENDING_PAYMENT = "T6 - Pending Payment Workflow"

PERSONAL_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "aol.com", "icloud.com", "mail.com", "protonmail.com",
    "live.com", "msn.com", "yandex.com", "zoho.com",
}

DEALER_KEYWORDS = [
    "dealer", "distributor", "franchise", "wholesale", "reseller",
    "agent", "broker", "partner program", "retail partner",
]

SUPPORT_KEYWORDS = [
    "help", "support", "issue", "problem", "broken", "error",
    "not working", "bug", "fix", "urgent", "asap", "emergency",
    "complaint", "damage", "refund", "return",
]


def classify_lead(
    name: str = "",
    email: str = "",
    phone: str = "",
    company: str = "",
    message: str = "",
    source: str = "api",
) -> dict:
    """Classify a lead and return assignment data.

    Returns:
        dict with keys: lead_type, team_id, tag_ids, priority, tag_names
    """
    lead_type = "lead"
    team_id = None
    tag_ids = []
    priority = "2"

    company = company or ""
    email = email or ""
    message = message.lower()
    combined = f"{company} {email} {message}".lower()

    if any(kw in combined for kw in SUPPORT_KEYWORDS):
        lead_type = "lead"
        priority = "3"

    elif any(kw in combined for kw in DEALER_KEYWORDS):
        lead_type = "lead"
        priority = "2"

    elif email and "@" in email:
        domain = email.split("@")[-1].lower()
        is_personal = domain in PERSONAL_EMAIL_DOMAINS

        if company or not is_personal:
            lead_type = "opportunity"
            priority = "3"
        else:
            lead_type = "lead"

    return {
        "lead_type": lead_type,
        "team_id": team_id,
        "tag_ids": tag_ids,
        "priority": priority,
    }


def get_tags_for_type(lead_type: str, source: str = "") -> list[str]:
    """Return tag name list based on classification result."""
    tags = []
    if lead_type == "opportunity":
        tags.append(TAG_B2B)
        tags.append(TAG_T6_PENDING_PAYMENT)
    elif lead_type == "lead":
        tags.append(TAG_B2C)
    return tags


def get_team_for_type(lead_type: str) -> Optional[int]:
    """Return default team ID by lead type.
    
    Override with ODOO_TEAM_B2B, ODOO_TEAM_B2C, ODOO_TEAM_SUPPORT env vars.
    """
    import os
    var = os.environ.get({
        "opportunity": "ODOO_TEAM_B2B",
        "lead": "ODOO_TEAM_B2C",
    }.get(lead_type, ""))
    if not var:
        return None
    try:
        return int(var)
    except (ValueError, TypeError):
        return None
