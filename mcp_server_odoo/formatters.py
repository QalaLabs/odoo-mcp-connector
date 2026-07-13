"""Formatting utilities for LLM-friendly output."""

from __future__ import annotations
from typing import Any, Optional
from datetime import datetime


def format_record(record: dict, model: str = None) -> str:
    """Format a single record for LLM display."""
    lines = []
    if model:
        lines.append(f"## {model}")
    
    for key, value in record.items():
        if key.startswith("_") or value is None:
            continue
        formatted_key = key.replace("_", " ").title()
        
        if isinstance(value, list) and value and isinstance(value[0], dict):
            lines.append(f"### {formatted_key}")
            for item in value[:5]:
                lines.append(format_record(item))
        elif isinstance(value, dict):
            lines.append(f"{formatted_key}: {value.get('display_name', value.get('id', 'N/A'))}")
        elif isinstance(value, (int, float, str)):
            lines.append(f"{formatted_key}: {value}")
    
    return "\n".join(lines)


def format_records(records: list[dict], model: str = None) -> str:
    """Format multiple records for LLM display."""
    if not records:
        return "No records found."
    
    lines = [f"## {model or 'Records'} ({len(records)} found)"]
    lines.append("")
    for i, record in enumerate(records, 1):
        display_name = record.get("display_name") or record.get("name") or f"ID: {record.get('id')}"
        lines.append(f"### {i}. {display_name}")
        for key, value in record.items():
            if key in ("id", "display_name") or value is None:
                continue
            formatted_key = key.replace("_", " ").title()
            if isinstance(value, (int, float, str)):
                lines.append(f"- {formatted_key}: {value}")
        lines.append("")
    
    return "\n".join(lines)


def format_search_result(result: dict, model: str = None) -> str:
    """Format search result for LLM display."""
    count = result.get("count", 0)
    records = result.get("records", [])
    
    lines = [f"## Search Results for {model or 'model'}"]
    lines.append(f"**Total: {count} records**")
    lines.append("")
    
    if records:
        lines.append(format_records(records, model))
    else:
        lines.append("No records match the search criteria.")
    
    return "\n".join(lines)


def format_field_info(fields: dict) -> str:
    """Format fields_get response for LLM display."""
    lines = ["## Model Fields"]
    
    for name, info in fields.items():
        field_type = info.get("type", "unknown")
        string = info.get("string", name)
        required = " (required)" if info.get("required") else ""
        readonly = " [readonly]" if info.get("readonly") else ""
        
        lines.append(f"- **{name}**{required}{readonly}")
        lines.append(f"  - Type: {field_type}")
        lines.append(f"  - Label: {string}")
        
        if info.get("help"):
            lines.append(f"  - Help: {info['help']}")
        
        if info.get("relation"):
            lines.append(f"  - Relation: {info['relation']}")
        
        if info.get("selection"):
            options = ", ".join(f"`{k}: {v}`" for k, v in info["selection"])
            lines.append(f"  - Options: {options}")
    
    return "\n".join(lines)


def format_error(error: str, code: str = None) -> str:
    """Format error for LLM display."""
    lines = ["## Error"]
    if code:
        lines.append(f"**Code:** {code}")
    lines.append(error)
    return "\n".join(lines)


def format_count(count: int, model: str) -> str:
    """Format count result."""
    return f"## Count\n**{count}** records in **{model}**"


def format_aggregate(result: list[dict], groupby: list[str]) -> str:
    """Format aggregation result for LLM display."""
    if not result:
        return "No aggregated data found."
    
    lines = ["## Aggregation Results"]
    if groupby:
        lines.append(f"Grouped by: {', '.join(groupby)}")
    lines.append("")
    
    for i, group in enumerate(result, 1):
        lines.append(f"### Group {i}")
        for key, value in group.items():
            if key.startswith("__"):
                agg_name = key.replace("__", "").replace("_", " ").title()
                lines.append(f"- {agg_name}: {value}")
            elif key.endswith("_count"):
                field = key.replace("_count", "")
                lines.append(f"- {field.title()} Count: {value}")
            else:
                lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        lines.append("")
    
    return "\n".join(lines)


def format_lead(lead: dict) -> str:
    """Format CRM lead for LLM display."""
    lines = ["## Lead"]
    lines.append(f"**Name:** {lead.get('name', 'N/A')}")
    lines.append(f"**Type:** {lead.get('type', 'N/A')}")
    lines.append(f"**Stage:** {lead.get('stage_id', (0, 'Unknown'))[1] if isinstance(lead.get('stage_id'), (list, tuple)) else 'N/A'}")
    lines.append(f"**Priority:** {lead.get('priority', 'N/A')}")
    lines.append("")
    
    contact_info = [
        ("Email", "email_from"),
        ("Phone", "phone"),
        ("Company", "partner_name"),
        ("Source", "source_id"),
    ]
    
    for label, field in contact_info:
        value = lead.get(field)
        if value:
            if isinstance(value, (list, tuple)) and len(value) > 1:
                value = value[1]
            lines.append(f"**{label}:** {value}")
    
    if lead.get("description"):
        lines.append("")
        lines.append("**Description:**")
        lines.append(lead["description"])
    
    return "\n".join(lines)


def format_channel_log(message: str, channel: str, direction: str) -> str:
    """Format channel message log."""
    return f"""## Channel Message Logged

- **Channel:** {channel}
- **Direction:** {direction}
- **Status:** Successfully logged
"""


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate long text for display."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
