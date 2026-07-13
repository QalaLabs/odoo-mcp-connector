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
from pydantic import ValidationError as PydanticValidationError
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
    CreateInvoiceInput,
    CreatePurchaseOrderInput,
    CreateExpenseInput,
    CountRecordsInput,
    GetModelFieldsInput,
    SearchLeadsInput,
    SearchInvoicesInput,
    GetStockLevelsInput,
    CreateDraftBillInput,
    PostAfterApprovalInput,
    QueryPartnersInput,
    GetInvoicesInput,
    UpdateCrmLeadInput,
    ConfigureConnectionInput,
)
from .error_handling import OdooMCPError, YOLOAccessError

logger = logging.getLogger(__name__)


def register_all_tools(connection: OdooConnection) -> list[Tool]:
    """Register all available MCP tools."""
    tools = [
        Tool(
            name="odoo_search_records",
            description="Search for records in any Odoo model with domain filters, sorting, and pagination",
            inputSchema=SearchRecordsInput.model_json_schema(),
        ),
        Tool(
            name="odoo_get_record",
            description="Get a single record by ID with specific fields",
            inputSchema=GetRecordInput.model_json_schema(),
        ),
        Tool(
            name="odoo_create_record",
            description="Create a new record in any Odoo model",
            inputSchema=CreateRecordInput.model_json_schema(),
        ),
        Tool(
            name="odoo_update_record",
            description="Update one or more existing records in any Odoo model",
            inputSchema=UpdateRecordInput.model_json_schema(),
        ),
        Tool(
            name="odoo_delete_record",
            description="Delete one or more records in any Odoo model",
            inputSchema=DeleteRecordInput.model_json_schema(),
        ),
        Tool(
            name="odoo_count_records",
            description="Count records in a model matching domain filters",
            inputSchema=CountRecordsInput.model_json_schema(),
        ),
        Tool(
            name="odoo_list_models",
            description="List all available Odoo model names and descriptions",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="odoo_get_model_fields",
            description="Get field definitions and types for a specific Odoo model",
            inputSchema=GetModelFieldsInput.model_json_schema(),
        ),
        Tool(
            name="odoo_aggregate_records",
            description="Perform group by, sum, avg, or count aggregation on Odoo records",
            inputSchema=AggregateRecordsInput.model_json_schema(),
        ),
        Tool(
            name="odoo_post_message",
            description="Post a message to a record chatter (mail.thread)",
            inputSchema=PostMessageInput.model_json_schema(),
        ),
        Tool(
            name="odoo_log_channel_message",
            description="Log an inbound/outbound email or WhatsApp message to a lead's chatter",
            inputSchema=LogChannelMessageInput.model_json_schema(),
        ),
        Tool(
            name="odoo_create_lead",
            description="Create a new CRM lead with automatic type classification and scheduled follow-up activity",
            inputSchema=CreateLeadInput.model_json_schema(),
        ),
        Tool(
            name="odoo_search_leads",
            description="Search CRM leads and opportunities",
            inputSchema=SearchLeadsInput.model_json_schema(),
        ),
        Tool(
            name="odoo_create_invoice",
            description="Create a customer invoice with line items",
            inputSchema=CreateInvoiceInput.model_json_schema(),
        ),
        Tool(
            name="odoo_search_invoices",
            description="Search account invoices/moves",
            inputSchema=SearchInvoicesInput.model_json_schema(),
        ),
        Tool(
            name="odoo_create_purchase_order",
            description="Create a vendor purchase order with lines",
            inputSchema=CreatePurchaseOrderInput.model_json_schema(),
        ),
        Tool(
            name="odoo_get_stock_levels",
            description="Get physical stock levels for products",
            inputSchema=GetStockLevelsInput.model_json_schema(),
        ),
        Tool(
            name="odoo_create_expense",
            description="Create an employee expense report entry",
            inputSchema=CreateExpenseInput.model_json_schema(),
        ),
        Tool(
            name="odoo_server_info",
            description="Get server version and connection info",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="odoo_create_draft_bill",
            description="Create a draft vendor/customer bill (account.move)",
            inputSchema=CreateDraftBillInput.model_json_schema(),
        ),
        Tool(
            name="odoo_post_after_approval",
            description="Post/validate a draft invoice (change state to posted)",
            inputSchema=PostAfterApprovalInput.model_json_schema(),
        ),
        Tool(
            name="odoo_query_partners",
            description="Search customers/vendors/partners",
            inputSchema=QueryPartnersInput.model_json_schema(),
        ),
        Tool(
            name="odoo_get_invoices",
            description="Get invoice by ID with full details",
            inputSchema=GetInvoicesInput.model_json_schema(),
        ),
        Tool(
            name="odoo_update_crm_lead",
            description="Update CRM lead stage, team, or assignee",
            inputSchema=UpdateCrmLeadInput.model_json_schema(),
        ),
        Tool(
            name="odoo_configure_connection",
            description="Configure Odoo connection parameters at runtime",
            inputSchema=ConfigureConnectionInput.model_json_schema(),
        ),
    ]
    return tools



WRITE_TOOLS = {
    "create_record",
    "update_record",
    "delete_record",
    "post_message",
    "log_channel_message",
    "create_lead",
    "create_invoice",
    "create_purchase_order",
    "create_expense",
    "create_draft_bill",
    "post_after_approval",
    "update_crm_lead",
}

TOOL_SCHEMAS = {
    "search_records": SearchRecordsInput,
    "get_record": GetRecordInput,
    "create_record": CreateRecordInput,
    "update_record": UpdateRecordInput,
    "delete_record": DeleteRecordInput,
    "count_records": CountRecordsInput,
    "get_model_fields": GetModelFieldsInput,
    "aggregate_records": AggregateRecordsInput,
    "post_message": PostMessageInput,
    "log_channel_message": LogChannelMessageInput,
    "create_lead": CreateLeadInput,
    "search_leads": SearchLeadsInput,
    "create_invoice": CreateInvoiceInput,
    "search_invoices": SearchInvoicesInput,
    "create_purchase_order": CreatePurchaseOrderInput,
    "get_stock_levels": GetStockLevelsInput,
    "create_expense": CreateExpenseInput,
    "create_draft_bill": CreateDraftBillInput,
    "post_after_approval": PostAfterApprovalInput,
    "query_partners": QueryPartnersInput,
    "get_invoices": GetInvoicesInput,
    "update_crm_lead": UpdateCrmLeadInput,
    "configure_connection": ConfigureConnectionInput,
}


async def execute_tool(
    connection: Any,
    name: str,
    arguments: dict
) -> CallToolResult:
    """Execute a tool by name."""
    try:
        tool_name = name
        if tool_name.startswith("odoo_"):
            tool_name = tool_name[5:]

        # Handle configure_connection first (needs server instance)
        if tool_name == "configure_connection":
            if hasattr(connection, "_server"):
                return await _configure_connection(connection, arguments)
            return CallToolResult(
                content=[TextContent(type="text", text="Server instance required for configuration")],
                isError=True,
            )

        # For all other tools, resolve server vs connection
        server = None
        if hasattr(connection, "_server"):
            server = connection
            connection = server._connection
            if not connection:
                # If we've got a server but no connection, try connecting first
                try:
                    await server.connect()
                    connection = server._connection
                except Exception:
                    pass
                if not connection:
                    return CallToolResult(
                        content=[TextContent(type="text", text="Not connected to Odoo")],
                        isError=True,
                    )

        # If connection is None, return a clean error
        if connection is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Not connected to Odoo")],
                isError=True,
            )

        # Check YOLO read-only/off mode for write operations
        if tool_name in WRITE_TOOLS:
            yolo = connection.config.yolo_mode
            if yolo in ("off", "read"):
                raise YOLOAccessError(tool_name)

        # Validate arguments using Pydantic schemas
        schema_model = TOOL_SCHEMAS.get(tool_name)
        validated_args = arguments
        if schema_model:
            try:
                model_instance = schema_model(**arguments)
                validated_args = model_instance.model_dump()
            except PydanticValidationError as ve:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Validation Error: {ve}")],
                    isError=True,
                )

        if tool_name == "search_records":
            return await _search_records(connection, validated_args)
        elif tool_name == "get_record":
            return await _get_record(connection, validated_args)
        elif tool_name == "create_record":
            return await _create_record(connection, validated_args)
        elif tool_name == "update_record":
            return await _update_record(connection, validated_args)
        elif tool_name == "delete_record":
            return await _delete_record(connection, validated_args)
        elif tool_name == "count_records":
            return await _count_records(connection, validated_args)
        elif tool_name == "list_models":
            return await _list_models(connection, validated_args)
        elif tool_name == "get_model_fields":
            return await _get_model_fields(connection, validated_args)
        elif tool_name == "aggregate_records":
            return await _aggregate_records(connection, validated_args)
        elif tool_name == "post_message":
            return await _post_message(connection, validated_args)
        elif tool_name == "log_channel_message":
            return await _log_channel_message(connection, validated_args)
        elif tool_name == "create_lead":
            return await _create_lead(connection, validated_args)
        elif tool_name == "search_leads":
            return await _search_leads(connection, validated_args)
        elif tool_name == "create_invoice":
            return await _create_invoice(connection, validated_args)
        elif tool_name == "search_invoices":
            return await _search_invoices(connection, validated_args)
        elif tool_name == "create_purchase_order":
            return await _create_purchase_order(connection, validated_args)
        elif tool_name == "get_stock_levels":
            return await _get_stock_levels(connection, validated_args)
        elif tool_name == "create_expense":
            return await _create_expense(connection, validated_args)
        elif tool_name == "server_info":
            return await _server_info(connection, validated_args)
        elif tool_name == "create_draft_bill":
            return await _create_draft_bill(connection, validated_args)
        elif tool_name == "post_after_approval":
            return await _post_after_approval(connection, validated_args)
        elif tool_name == "query_partners":
            return await _query_partners(connection, validated_args)
        elif tool_name == "get_invoices":
            return await _get_invoices(connection, validated_args)
        elif tool_name == "update_crm_lead":
            return await _update_crm_lead(connection, validated_args)
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
    records = await conn.search_read(
        model=args["model"],
        domain=args.get("domain"),
        fields=args.get("fields"),
        limit=args.get("limit", 10),
        offset=args.get("offset", 0),
        order=args.get("order"),
    )
    count = await conn.count(args["model"], args.get("domain"))
    result = {"records": records, "count": count}
    text = format_search_result(result, args["model"])
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _get_record(conn: OdooConnection, args: dict) -> CallToolResult:
    """Get a single record."""
    records = await conn.read(
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
    record_id = await conn.create(args["model"], args["values"])
    return CallToolResult(content=[TextContent(type="text", text=f"Created {args['model']} with ID: {record_id}")])


async def _update_record(conn: OdooConnection, args: dict) -> CallToolResult:
    """Update a record."""
    await conn.write(args["model"], [args["record_id"]], args["values"])
    return CallToolResult(content=[TextContent(type="text", text=f"Updated {args['model']} ID: {args['record_id']}")])


async def _delete_record(conn: OdooConnection, args: dict) -> CallToolResult:
    """Delete a record."""
    await conn.unlink(args["model"], [args["record_id"]])
    return CallToolResult(content=[TextContent(type="text", text=f"Deleted {args['model']} ID: {args['record_id']}")])


async def _count_records(conn: OdooConnection, args: dict) -> CallToolResult:
    """Count records."""
    count = await conn.count(args["model"], args.get("domain"))
    text = format_count(count, args["model"])
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _list_models(conn: OdooConnection, args: dict) -> CallToolResult:
    """List models."""
    models = ["crm.lead", "account.move", "sale.order", "purchase.order", "stock.picking", "hr.expense", "res.partner"]
    text = "## Available Models\n\n" + "\n".join(f"- {m}" for m in models)
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _get_model_fields(conn: OdooConnection, args: dict) -> CallToolResult:
    """Get model fields."""
    fields = await conn.fields_get(args["model"])
    text = format_field_info(fields)
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _aggregate_records(conn: OdooConnection, args: dict) -> CallToolResult:
    """Aggregate records."""
    result = await conn.call_method(
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
    await conn.call_method(
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
    
    await conn.call_method(
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
    
    lead_id = await conn.create("crm.lead", values)
    
    follow_up_hours = args.get("scheduled_follow_up_hours", 24)
    deadline = datetime.now() + timedelta(hours=follow_up_hours)
    
    try:
        res_model_id = await conn.call_method("ir.model", "search", args=[["model", "=", "crm.lead"]])
        activity_vals = {
            "res_id": lead_id,
            "res_model_id": res_model_id[0] if isinstance(res_model_id, list) and res_model_id else False,
            "activity_type_id": 1,
            "date_deadline": deadline.date().isoformat(),
            "summary": f"Follow-up: {args['name']}",
            "note": f"First follow-up for new {args.get('lead_type', 'lead')} lead",
        }
        await conn.create("mail.activity", activity_vals)
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
    
    records = await conn.search_read(
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
    
    invoice_id = await conn.create("account.move", values)
    return CallToolResult(content=[TextContent(type="text", text=f"Created invoice ID: {invoice_id}")])


async def _search_invoices(conn: OdooConnection, args: dict) -> CallToolResult:
    """Search invoices."""
    domain = args.get("domain", [])
    state = args.get("state")
    if state:
        domain.append(["state", "=", state])
    if not any("move_type" in str(d) for d in domain):
        domain.append(["move_type", "=", "out_invoice"])
    
    records = await conn.search_read(
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
    
    po_id = await conn.create("purchase.order", values)
    return CallToolResult(content=[TextContent(type="text", text=f"Created purchase order ID: {po_id}")])


async def _get_stock_levels(conn: OdooConnection, args: dict) -> CallToolResult:
    """Get stock levels."""
    domain = []
    if args.get("product_ids"):
        domain.append(["product_id", "in", args["product_ids"]])
    if args.get("location_id"):
        domain.append(["location_id", "=", args["location_id"]])
    
    quants = await conn.search_read(
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
    
    expense_id = await conn.create("hr.expense", values)
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


async def _create_draft_bill(conn: OdooConnection, args: dict) -> CallToolResult:
    """Create a draft bill."""
    values = {
        "partner_id": args["partner_id"],
        "move_type": args.get("move_type", "in_invoice"),
    }
    if args.get("date"):
        values["date"] = args["date"]
    if args.get("invoice_line_ids"):
        values["invoice_line_ids"] = args["invoice_line_ids"]
    if args.get("ref"):
        values["ref"] = args["ref"]
    bill_id = await conn.create("account.move", values)
    return CallToolResult(content=[TextContent(
        type="text", text=f"Created draft bill ID: {bill_id} ({args.get('move_type', 'in_invoice')})"
    )])


async def _post_after_approval(conn: OdooConnection, args: dict) -> CallToolResult:
    """Post a draft invoice."""
    invoice_id = args["invoice_id"]
    bill = await conn.read("account.move", [invoice_id], ["state", "name"])
    if not bill:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Invoice {invoice_id} not found")],
            isError=True,
        )
    state = bill[0].get("state")
    if state != "draft":
        return CallToolResult(content=[TextContent(
            type="text", text=f"Invoice {invoice_id} is already in state '{state}'. Cannot post."
        )])
    await conn.call_method("account.move", "action_post", args=[[invoice_id]])
    name = bill[0].get("name", invoice_id)
    return CallToolResult(content=[TextContent(
        type="text", text=f"Posted invoice {name} (ID: {invoice_id})"
    )])


async def _query_partners(conn: OdooConnection, args: dict) -> CallToolResult:
    """Search partners."""
    domain = args.get("domain", [])
    if args.get("name"):
        domain.append(["name", "ilike", args["name"]])
    if args.get("email"):
        domain.append(["email", "ilike", args["email"]])
    if not domain:
        domain = [["supplier_rank", ">", 0]]
    records = await conn.search_read(
        "res.partner",
        domain=domain,
        fields=["id", "name", "email", "phone", "company_type", "city"],
        limit=args.get("limit", 10),
    )
    count = await conn.count("res.partner", domain)
    text = format_search_result({"records": records, "count": count}, "Partners")
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _get_invoices(conn: OdooConnection, args: dict) -> CallToolResult:
    """Get invoice by ID."""
    records = await conn.read(
        "account.move",
        [args["invoice_id"]],
        ["id", "name", "state", "partner_id", "invoice_date", "amount_total",
         "amount_residual", "payment_state", "invoice_line_ids", "move_type", "ref"],
    )
    if not records:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Invoice {args['invoice_id']} not found")],
            isError=True,
        )
    rec = records[0]
    lines = [f"## Invoice: {rec.get('name', rec.get('id'))}"]
    lines.append(f"**State:** {rec.get('state', 'N/A')}")
    lines.append(f"**Type:** {rec.get('move_type', 'N/A')}")
    lines.append(f"**Partner ID:** {rec.get('partner_id', 'N/A')}")
    lines.append(f"**Date:** {rec.get('invoice_date', 'N/A')}")
    lines.append(f"**Total:** {rec.get('amount_total', 0)}")
    lines.append(f"**Residual:** {rec.get('amount_residual', 0)}")
    lines.append(f"**Payment State:** {rec.get('payment_state', 'N/A')}")
    if rec.get("ref"):
        lines.append(f"**Ref:** {rec['ref']}")
    text = "\n".join(lines)
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _update_crm_lead(conn: OdooConnection, args: dict) -> CallToolResult:
    """Update CRM lead."""
    lead_id = args["lead_id"]
    values = {}
    for field in ("stage_id", "team_id", "user_id", "priority"):
        if args.get(field):
            values[field] = args[field]
    if not values:
        return CallToolResult(
            content=[TextContent(type="text", text="No fields to update")],
            isError=True,
        )
    await conn.write("crm.lead", [lead_id], values)
    updated = ", ".join(f"{k}={v}" for k, v in values.items())
    return CallToolResult(content=[TextContent(
        type="text", text=f"Updated lead ID {lead_id}: {updated}"
    )])


async def _configure_connection(server: Any, arguments: dict) -> CallToolResult:
    """Configure Odoo connection parameters at runtime."""
    try:
        model_instance = ConfigureConnectionInput(**arguments)
        args = model_instance.model_dump()
    except PydanticValidationError as ve:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Validation Error: {ve}")],
            isError=True,
        )

    config = server.config
    if "url" in arguments:
        config.url = args["url"]
    if "database" in arguments:
        config.database = args["database"]
    if "api_key" in arguments:
        config.api_key = args["api_key"]
    if "user" in arguments:
        config.user = args["user"]
    if "password" in arguments:
        config.password = args["password"]
    if "yolo_mode" in arguments:
        config.yolo_mode = args["yolo_mode"]

    try:
        await server.connect()
        conn = server._connection
        if not conn:
            return CallToolResult(
                content=[TextContent(type="text", text="Failed to establish connection with new parameters")],
                isError=True,
            )
        
        version = conn.version
        text = f"""## Odoo Connection Configured Successfully

**URL:** {conn.url}
**Database:** {conn.db}
**API Type:** {version.api_type}
**Version:** {version.major}.{version.minor}
**User ID:** {conn.uid}
**YOLO Mode:** {config.yolo_mode}"""
        return CallToolResult(content=[TextContent(type="text", text=text)])
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Connection failed: {sanitize_error(e)}")],
            isError=True,
        )

