"""MCP tools registry and executor."""

from __future__ import annotations
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

from mcp.types import Tool, TextContent, CallToolResult
from .odoo_connection import OdooConnection
from .error_handling import OdooMCPError
from .error_sanitizer import sanitize_error
from .formatters import (
    format_records,
    format_search_result,
    format_field_info,
    format_count,
    format_lead,
    format_channel_log,
)
from .schemas import (
    SearchRecordsInput,
    GetRecordInput,
    CreateRecordInput,
    UpdateRecordInput,
    DeleteRecordInput,
    AggregateRecordsInput,
    PostMessageInput,
    LogChannelMessageInput,
    CreateLeadInput,
)

logger = logging.getLogger(__name__)


def register_all_tools(connection: OdooConnection) -> list[Tool]:
    """Register all available MCP tools."""
    tools = [
        Tool(
            name="search_records",
            description="Search for records in any Odoo model with domain filters, sorting, and pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Odoo model name (e.g., res.partner)"},
                    "domain": {"type": "array", "description": "Search domain filters"},
                    "fields": {"type": "array", "description": "Fields to return (null for smart selection)"},
                    "limit": {"type": "integer", "description": "Max records to return", "default": 10},
                    "offset": {"type": "integer", "description": "Records to skip", "default": 0},
                    "order": {"type": "string", "description": "Sort order (e.g., 'name asc')"},
                },
                "required": ["model"],
            },
        ),
        Tool(
            name="get_record",
            description="Retrieve a specific record by ID with smart field selection",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Odoo model name"},
                    "record_id": {"type": "integer", "description": "Record ID"},
                    "fields": {"type": "array", "description": "Fields to return"},
                },
                "required": ["model", "record_id"],
            },
        ),
        Tool(
            name="create_record",
            description="Create a new record in Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Odoo model name"},
                    "values": {"type": "object", "description": "Field values for the new record"},
                },
                "required": ["model", "values"],
            },
        ),
        Tool(
            name="update_record",
            description="Update an existing record",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Odoo model name"},
                    "record_id": {"type": "integer", "description": "Record ID to update"},
                    "values": {"type": "object", "description": "Field values to update"},
                },
                "required": ["model", "record_id", "values"],
            },
        ),
        Tool(
            name="delete_record",
            description="Delete a record from Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Odoo model name"},
                    "record_id": {"type": "integer", "description": "Record ID to delete"},
                },
                "required": ["model", "record_id"],
            },
        ),
        Tool(
            name="count_records",
            description="Count records matching domain criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Odoo model name"},
                    "domain": {"type": "array", "description": "Search domain filters"},
                },
                "required": ["model"],
            },
        ),
        Tool(
            name="list_models",
            description="List all models accessible via MCP",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_model_fields",
            description="Get field definitions and metadata for a model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Odoo model name"},
                },
                "required": ["model"],
            },
        ),
        Tool(
            name="aggregate_records",
            description="Server-side aggregation - group, sum, count without pulling raw rows",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Odoo model name"},
                    "domain": {"type": "array", "description": "Filter domain"},
                    "groupby": {"type": "array", "description": "Fields to group by"},
                    "aggregates": {"type": "array", "description": "Aggregations (e.g., amount:sum)"},
                },
                "required": ["model", "groupby"],
            },
        ),
        Tool(
            name="post_message",
            description="Post a message to a record's chatter (mail.thread)",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Odoo model name"},
                    "record_id": {"type": "integer", "description": "Record ID"},
                    "body": {"type": "string", "description": "Message body"},
                    "subtype": {"type": "string", "description": "note or comment", "default": "note"},
                    "body_is_html": {"type": "boolean", "description": "Body contains HTML", "default": False},
                },
                "required": ["model", "record_id", "body"],
            },
        ),
        Tool(
            name="log_channel_message",
            description="Log WhatsApp/email message to CRM lead as a note",
            inputSchema={
                "type": "object",
                "properties": {
                    "lead_id": {"type": "integer", "description": "Lead ID to attach message"},
                    "channel": {"type": "string", "description": "whatsapp or email"},
                    "direction": {"type": "string", "description": "inbound or outbound"},
                    "message": {"type": "string", "description": "Message content"},
                    "timestamp": {"type": "string", "description": "ISO timestamp"},
                    "from_number": {"type": "string", "description": "Phone/email address"},
                },
                "required": ["lead_id", "channel", "direction", "message"],
            },
        ),
        Tool(
            name="create_lead",
            description="Create a CRM lead with automatic follow-up task",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Lead name"},
                    "contact_name": {"type": "string"},
                    "email_from": {"type": "string"},
                    "phone": {"type": "string"},
                    "partner_name": {"type": "string", "description": "Company name"},
                    "lead_type": {"type": "string", "description": "lead or opportunity", "default": "lead"},
                    "pipeline_id": {"type": "integer"},
                    "team_id": {"type": "integer"},
                    "user_id": {"type": "integer"},
                    "priority": {"type": "string", "description": "1 (low) to 3 (high)", "default": "2"},
                    "tag_ids": {"type": "array", "items": {"type": "integer"}},
                    "source_id": {"type": "integer"},
                    "description": {"type": "string"},
                    "expected_revenue": {"type": "number"},
                    "scheduled_follow_up_hours": {"type": "integer", "description": "Hours until follow-up", "default": 24},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="search_leads",
            description="Search CRM leads and opportunities",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {"type": "array", "description": "Search filters"},
                    "fields": {"type": "array"},
                    "limit": {"type": "integer", "default": 10},
                },
            },
        ),
        Tool(
            name="create_invoice",
            description="Create a customer invoice",
            inputSchema={
                "type": "object",
                "properties": {
                    "partner_id": {"type": "integer", "description": "Customer ID"},
                    "move_type": {"type": "string", "description": "out_invoice, out_refund, in_invoice, in_refund"},
                    "date": {"type": "string", "description": "Invoice date"},
                    "invoice_line_ids": {"type": "array"},
                },
                "required": ["partner_id"],
            },
        ),
        Tool(
            name="search_invoices",
            description="Search customer invoices",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {"type": "array"},
                    "state": {"type": "string", "description": "draft, posted, paid, cancelled"},
                    "limit": {"type": "integer", "default": 10},
                },
            },
        ),
        Tool(
            name="create_purchase_order",
            description="Create a purchase order to vendor",
            inputSchema={
                "type": "object",
                "properties": {
                    "partner_id": {"type": "integer", "description": "Vendor ID"},
                    "date_order": {"type": "string"},
                    "order_line": {"type": "array"},
                    "notes": {"type": "string"},
                },
                "required": ["partner_id"],
            },
        ),
        Tool(
            name="get_stock_levels",
            description="Get product stock levels by location",
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Product ID"},
                    "location_id": {"type": "integer", "description": "Location ID"},
                },
            },
        ),
        Tool(
            name="create_expense",
            description="Create an expense report entry",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Expense description"},
                    "product_id": {"type": "integer", "description": "Expense category/product ID"},
                    "unit_amount": {"type": "number", "description": "Amount"},
                    "quantity": {"type": "number", "default": 1},
                    "date": {"type": "string"},
                    "employee_id": {"type": "integer"},
                    "description": {"type": "string"},
                },
                "required": ["name", "product_id", "unit_amount"],
            },
        ),
        Tool(
            name="server_info",
            description="Get server version and connection info",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]
    return tools


async def execute_tool(
    connection: OdooConnection,
    name: str,
    arguments: dict
) -> CallToolResult:
    """Execute a tool by name."""
    try:
        if not connection:
            return CallToolResult(
                content=[TextContent(type="text", text="Not connected to Odoo")],
                isError=True,
            )

        if name == "search_records":
            return await _search_records(connection, arguments)
        elif name == "get_record":
            return await _get_record(connection, arguments)
        elif name == "create_record":
            return await _create_record(connection, arguments)
        elif name == "update_record":
            return await _update_record(connection, arguments)
        elif name == "delete_record":
            return await _delete_record(connection, arguments)
        elif name == "count_records":
            return await _count_records(connection, arguments)
        elif name == "list_models":
            return await _list_models(connection, arguments)
        elif name == "get_model_fields":
            return await _get_model_fields(connection, arguments)
        elif name == "aggregate_records":
            return await _aggregate_records(connection, arguments)
        elif name == "post_message":
            return await _post_message(connection, arguments)
        elif name == "log_channel_message":
            return await _log_channel_message(connection, arguments)
        elif name == "create_lead":
            return await _create_lead(connection, arguments)
        elif name == "search_leads":
            return await _search_leads(connection, arguments)
        elif name == "create_invoice":
            return await _create_invoice(connection, arguments)
        elif name == "search_invoices":
            return await _search_invoices(connection, arguments)
        elif name == "create_purchase_order":
            return await _create_purchase_order(connection, arguments)
        elif name == "get_stock_levels":
            return await _get_stock_levels(connection, arguments)
        elif name == "create_expense":
            return await _create_expense(connection, arguments)
        elif name == "server_info":
            return await _server_info(connection, arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True,
            )
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {sanitize_error(e)}")],
            isError=True,
        )


async def _search_records(conn: OdooConnection, args: dict) -> CallToolResult:
    """Search for records."""
    records = conn.search_read(
        model=args["model"],
        domain=args.get("domain"),
        fields=args.get("fields"),
        limit=args.get("limit", 10),
        offset=args.get("offset", 0),
        order=args.get("order"),
    )
    count = conn.count(args["model"], args.get("domain"))
    result = {"records": records, "count": count}
    text = format_search_result(result, args["model"])
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _get_record(conn: OdooConnection, args: dict) -> CallToolResult:
    """Get a single record."""
    records = conn.read(
        args["model"],
        [args["record_id"]],
        args.get("fields"),
    )
    if not records:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Record {args['record_id']} not found")],
            isError=True,
        )
    text = format_records(records, args["model"])
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _create_record(conn: OdooConnection, args: dict) -> CallToolResult:
    """Create a record."""
    record_id = conn.create(args["model"], args["values"])
    return CallToolResult(content=[TextContent(type="text", text=f"Created {args['model']} with ID: {record_id}")])


async def _update_record(conn: OdooConnection, args: dict) -> CallToolResult:
    """Update a record."""
    conn.write(args["model"], [args["record_id"]], args["values"])
    return CallToolResult(content=[TextContent(type="text", text=f"Updated {args['model']} ID: {args['record_id']}")])


async def _delete_record(conn: OdooConnection, args: dict) -> CallToolResult:
    """Delete a record."""
    conn.unlink(args["model"], [args["record_id"]])
    return CallToolResult(content=[TextContent(type="text", text=f"Deleted {args['model']} ID: {args['record_id']}")])


async def _count_records(conn: OdooConnection, args: dict) -> CallToolResult:
    """Count records."""
    count = conn.count(args["model"], args.get("domain"))
    text = format_count(count, args["model"])
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _list_models(conn: OdooConnection, args: dict) -> CallToolResult:
    """List models."""
    models = ["crm.lead", "account.move", "sale.order", "purchase.order", "stock.picking", "hr.expense", "res.partner"]
    text = "## Available Models\n\n" + "\n".join(f"- {m}" for m in models)
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _get_model_fields(conn: OdooConnection, args: dict) -> CallToolResult:
    """Get model fields."""
    fields = conn.fields_get(args["model"])
    text = format_field_info(fields)
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _aggregate_records(conn: OdooConnection, args: dict) -> CallToolResult:
    """Aggregate records."""
    result = conn.call_method(
        args["model"],
        "read_group",
        args=[],
        kwargs={
            "domain": args.get("domain", []),
            "fields": args.get("aggregates", ["__count"]),
            "groupby": args.get("groupby", []),
        },
    )
    from .formatters import format_aggregate
    text = format_aggregate(result, args.get("groupby", []))
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _post_message(conn: OdooConnection, args: dict) -> CallToolResult:
    """Post message to chatter."""
    conn.call_method(
        args["model"],
        "message_post",
        args=[[args["record_id"]]],
        kwargs={
            "body": args["body"],
            "subtype": args.get("subtype", "note"),
        },
    )
    return CallToolResult(content=[TextContent(type="text", text="Message posted successfully")])


async def _log_channel_message(conn: OdooConnection, args: dict) -> CallToolResult:
    """Log WhatsApp/email message to lead."""
    ts = args.get("timestamp", datetime.now().isoformat())
    body = f"""[{args['channel'].upper()} - {args['direction'].upper()}]
Timestamp: {ts}
From: {args.get('from_number', 'N/A')}

{args['message']}"""
    
    conn.call_method(
        "crm.lead",
        "message_post",
        args=[[args["lead_id"]]],
        kwargs={
            "body": body,
            "subtype": "comment" if args["direction"] == "inbound" else "note",
        },
    )
    text = format_channel_log(args["message"], args["channel"], args["direction"])
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _create_lead(conn: OdooConnection, args: dict) -> CallToolResult:
    """Create CRM lead with follow-up task."""
    values = {
        "name": args["name"],
        "type": args.get("lead_type", "lead"),
        "priority": args.get("priority", "2"),
    }
    
    for field in ("contact_name", "email_from", "phone", "partner_name", "description",
                 "pipeline_id", "team_id", "user_id", "expected_revenue"):
        if args.get(field):
            values[field] = args[field]
    
    if args.get("tag_ids"):
        values["tag_ids"] = [(6, 0, args["tag_ids"])]
    
    lead_id = conn.create("crm.lead", values)
    
    follow_up_hours = args.get("scheduled_follow_up_hours", 24)
    deadline = datetime.now() + timedelta(hours=follow_up_hours)
    
    try:
        activity_vals = {
            "res_id": lead_id,
            "res_model_id": conn.call_method("ir.model", "search", args=[["model", "=", "crm.lead"]]),
            "activity_type_id": 1,
            "date_deadline": deadline.date().isoformat(),
            "summary": f"Follow-up: {args['name']}",
            "note": f"First follow-up for new {args.get('lead_type', 'lead')} lead",
        }
        conn.create("mail.activity", activity_vals)
    except Exception as e:
        logger.warning(f"Could not create follow-up activity: {e}")
    
    text = f"""## Lead Created

**ID:** {lead_id}
**Name:** {args['name']}
**Type:** {args.get('lead_type', 'lead')}
**Follow-up Scheduled:** {deadline.isoformat()}"""
    
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _search_leads(conn: OdooConnection, args: dict) -> CallToolResult:
    """Search CRM leads."""
    domain = args.get("domain", [])
    if not domain:
        domain = []
    domain.insert(0, ["type", "in", ["lead", "opportunity"]])
    
    records = conn.search_read(
        "crm.lead",
        domain=domain,
        fields=args.get("fields"),
        limit=args.get("limit", 10),
    )
    text = format_records(records, "CRM Leads")
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _create_invoice(conn: OdooConnection, args: dict) -> CallToolResult:
    """Create invoice."""
    values = {
        "partner_id": args["partner_id"],
        "move_type": args.get("move_type", "out_invoice"),
    }
    if args.get("date"):
        values["date"] = args["date"]
    if args.get("invoice_line_ids"):
        values["invoice_line_ids"] = args["invoice_line_ids"]
    
    invoice_id = conn.create("account.move", values)
    return CallToolResult(content=[TextContent(type="text", text=f"Created invoice ID: {invoice_id}")])


async def _search_invoices(conn: OdooConnection, args: dict) -> CallToolResult:
    """Search invoices."""
    domain = args.get("domain", [])
    state = args.get("state")
    if state:
        domain.append(["state", "=", state])
    if not any("move_type" in str(d) for d in domain):
        domain.append(["move_type", "=", "out_invoice"])
    
    records = conn.search_read(
        "account.move",
        domain=domain,
        limit=args.get("limit", 10),
    )
    text = format_records(records, "Invoices")
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _create_purchase_order(conn: OdooConnection, args: dict) -> CallToolResult:
    """Create purchase order."""
    values = {"partner_id": args["partner_id"]}
    if args.get("date_order"):
        values["date_order"] = args["date_order"]
    if args.get("order_line"):
        values["order_line"] = args["order_line"]
    if args.get("notes"):
        values["notes"] = args["notes"]
    
    po_id = conn.create("purchase.order", values)
    return CallToolResult(content=[TextContent(type="text", text=f"Created purchase order ID: {po_id}")])


async def _get_stock_levels(conn: OdooConnection, args: dict) -> CallToolResult:
    """Get stock levels."""
    domain = []
    if args.get("product_id"):
        domain.append(["product_id", "=", args["product_id"]])
    if args.get("location_id"):
        domain.append(["location_id", "=", args["location_id"]])
    
    quants = conn.search_read(
        "stock.quant",
        domain=domain,
        fields=["product_id", "location_id", "quantity", "reserved_quantity"],
    )
    text = format_records(quants, "Stock Levels")
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _create_expense(conn: OdooConnection, args: dict) -> CallToolResult:
    """Create expense."""
    values = {
        "name": args["name"],
        "product_id": args["product_id"],
        "unit_amount": args["unit_amount"],
        "quantity": args.get("quantity", 1),
    }
    if args.get("date"):
        values["date"] = args["date"]
    if args.get("employee_id"):
        values["employee_id"] = args["employee_id"]
    if args.get("description"):
        values["description"] = args["description"]
    
    expense_id = conn.create("hr.expense", values)
    return CallToolResult(content=[TextContent(type="text", text=f"Created expense ID: {expense_id}")])


async def _server_info(conn: OdooConnection, args: dict) -> CallToolResult:
    """Get server info."""
    version = conn.version
    text = f"""## Odoo Connection Info

**URL:** {conn.url}
**Database:** {conn.db}
**API Type:** {version.api_type}
**Version:** {version.major}.{version.minor}
**User ID:** {conn.uid}"""
    return CallToolResult(content=[TextContent(type="text", text=text)])
