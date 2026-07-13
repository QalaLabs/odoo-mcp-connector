"""Pydantic schemas for MCP tool inputs/outputs."""

from __future__ import annotations
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


class DomainFilter(BaseModel):
    """Domain filter for Odoo searches."""
    field: str
    operator: str
    value: Any


class SearchRecordsInput(BaseModel):
    """Input for search_records tool."""
    model: str = Field(..., description="Odoo model name")
    domain: Optional[list[list]] = Field(default=None, description="Search domain")
    fields: Optional[list[str]] = Field(default=None, description="Fields to return")
    limit: int = Field(default=10, ge=1, le=100, description="Max records")
    offset: int = Field(default=0, ge=0, description="Records to skip")
    order: Optional[str] = Field(default=None, description="Sort order")


class GetRecordInput(BaseModel):
    """Input for get_record tool."""
    model: str = Field(..., description="Odoo model name")
    record_id: int = Field(..., description="Record ID")
    fields: Optional[list[str]] = Field(default=None, description="Fields to return")


class CreateRecordInput(BaseModel):
    """Input for create_record tool."""
    model: str = Field(..., description="Odoo model name")
    values: dict = Field(..., description="Field values")


class UpdateRecordInput(BaseModel):
    """Input for update_record tool."""
    model: str = Field(..., description="Odoo model name")
    record_id: int = Field(..., description="Record ID")
    values: dict = Field(..., description="Field values to update")


class DeleteRecordInput(BaseModel):
    """Input for delete_record tool."""
    model: str = Field(..., description="Odoo model name")
    record_id: int = Field(..., description="Record ID")


class AggregateRecordsInput(BaseModel):
    """Input for aggregate_records tool."""
    model: str = Field(..., description="Odoo model name")
    domain: Optional[list[list]] = Field(default=None, description="Filter domain")
    groupby: list[str] = Field(..., description="Group by fields")
    aggregates: Optional[list[str]] = Field(default=None, description="Aggregations e.g. amount:sum")


class PostMessageInput(BaseModel):
    """Input for post_message tool."""
    model: str = Field(..., description="Odoo model name")
    record_id: int = Field(..., description="Record ID")
    body: str = Field(..., description="Message body")
    subtype: str = Field(default="note", description="note or comment")
    body_is_html: bool = Field(default=False)


class LogChannelMessageInput(BaseModel):
    """Input for log_channel_message tool."""
    lead_id: int = Field(..., description="Lead ID to attach message")
    channel: str = Field(..., description="whatsapp or email")
    direction: str = Field(..., description="inbound or outbound")
    message: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp")
    from_number: Optional[str] = Field(default=None)


class CreateLeadInput(BaseModel):
    """Input for create_lead tool."""
    name: str = Field(..., description="Lead name")
    contact_name: Optional[str] = Field(default=None)
    email_from: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    partner_name: Optional[str] = Field(default=None, description="Company name")
    lead_type: str = Field(default="lead", description="lead or opportunity")
    pipeline_id: Optional[int] = Field(default=None)
    team_id: Optional[int] = Field(default=None)
    user_id: Optional[int] = Field(default=None)
    priority: str = Field(default="2", description="1 (low) to 3 (high)")
    tag_ids: Optional[list[int]] = Field(default=None)
    source_id: Optional[int] = Field(default=None, description="Source ID")
    description: Optional[str] = Field(default=None)
    expected_revenue: Optional[float] = Field(default=None)
    scheduled_follow_up_hours: int = Field(default=24)


class CreateInvoiceInput(BaseModel):
    """Input for create_invoice tool."""
    partner_id: int = Field(..., description="Customer ID")
    move_type: str = Field(default="out_invoice", description="out_invoice, out_refund, in_invoice, in_refund")
    date: Optional[str] = Field(default=None, description="Invoice date")
    invoice_line_ids: Optional[list[dict]] = Field(default=None, description="Line items")


class CreatePurchaseOrderInput(BaseModel):
    """Input for create_purchase_order tool."""
    partner_id: int = Field(..., description="Vendor ID")
    date_order: Optional[str] = Field(default=None)
    order_line: Optional[list[dict]] = Field(default=None)
    notes: Optional[str] = Field(default=None)


class CreateExpenseInput(BaseModel):
    """Input for create_expense tool."""
    name: str = Field(..., description="Expense description")
    product_id: int = Field(..., description="Product/expense category ID")
    unit_amount: float = Field(..., description="Amount")
    quantity: float = Field(default=1)
    date: Optional[str] = Field(default=None)
    employee_id: Optional[int] = Field(default=None)
    description: Optional[str] = Field(default=None)


class RecordData(BaseModel):
    """Output record data."""
    id: int
    display_name: Optional[str] = None
    data: dict = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Output for search operations."""
    records: list[dict]
    count: int
    total: Optional[int] = None


class ModelInfo(BaseModel):
    """Model information."""
    model: str
    name: str
    fields: list[str]


class FieldInfo(BaseModel):
    """Field information."""
    name: str
    type: str
    string: str
    required: bool = False
    readonly: bool = False


class CreateRecordOutput(BaseModel):
    """Output for create operations."""
    id: int
    model: str


class UpdateRecordOutput(BaseModel):
    """Output for update/delete operations."""
    success: bool
    model: str
    record_ids: list[int]


class LeadOutput(BaseModel):
    """Output for lead operations."""
    id: int
    name: str
    type: str
    stage_id: int
    team_id: int
    user_id: Optional[int]
    tag_ids: list[int]


class InvoiceOutput(BaseModel):
    """Output for invoice operations."""
    id: int
    name: str
    partner_id: int
    state: str
    amount_total: float


class ErrorOutput(BaseModel):
    """Error output."""
    error: str
    code: str
    details: Optional[dict] = None


class CountRecordsInput(BaseModel):
    """Input for count_records tool."""
    model: str = Field(..., description="Odoo model name")
    domain: Optional[list[list]] = Field(default=None, description="Search domain filters")


class GetModelFieldsInput(BaseModel):
    """Input for get_model_fields tool."""
    model: str = Field(..., description="Odoo model name")
    attributes: Optional[list[str]] = Field(default=None, description="Field attributes to retrieve")


class SearchLeadsInput(BaseModel):
    """Input for search_leads tool."""
    domain: Optional[list[list]] = Field(default=None, description="Search domain filters")
    fields: Optional[list[str]] = Field(default=None, description="Fields to return")
    limit: int = Field(default=10, ge=1, le=100, description="Max records")


class SearchInvoicesInput(BaseModel):
    """Input for search_invoices tool."""
    domain: Optional[list[list]] = Field(default=None, description="Search domain filters")
    fields: Optional[list[str]] = Field(default=None, description="Fields to return")
    limit: int = Field(default=10, ge=1, le=100, description="Max records")


class GetStockLevelsInput(BaseModel):
    """Input for get_stock_levels tool."""
    product_ids: list[int] = Field(..., description="Product IDs to check stock for")
    location_id: Optional[int] = Field(default=None, description="Specific inventory location ID")


class CreateDraftBillInput(BaseModel):
    """Input for create_draft_bill tool."""
    partner_id: int = Field(..., description="Vendor/customer ID")
    move_type: str = Field(default="in_invoice", description="in_invoice (vendor), out_invoice (customer)")
    date: Optional[str] = Field(default=None, description="Bill date (YYYY-MM-DD)")
    invoice_line_ids: Optional[list[dict]] = Field(default=None, description="Invoice line items")
    ref: Optional[str] = Field(default=None, description="Vendor reference")


class PostAfterApprovalInput(BaseModel):
    """Input for post_after_approval tool."""
    invoice_id: int = Field(..., description="Invoice ID to post/validate")


class QueryPartnersInput(BaseModel):
    """Input for query_partners tool."""
    domain: Optional[list[list]] = Field(default=None, description="Search domain filters")
    limit: int = Field(default=10, ge=1, le=100, description="Max records")
    name: Optional[str] = Field(default=None, description="Quick search by name")
    email: Optional[str] = Field(default=None, description="Search by email")


class GetInvoicesInput(BaseModel):
    """Input for get_invoices tool."""
    invoice_id: int = Field(..., description="Invoice ID")


class UpdateCrmLeadInput(BaseModel):
    """Input for update_crm_lead tool."""
    lead_id: int = Field(..., description="Lead ID to update")
    stage_id: Optional[int] = Field(default=None, description="New stage ID")
    team_id: Optional[int] = Field(default=None, description="Sales team ID")
    user_id: Optional[int] = Field(default=None, description="Assign to user ID")
    priority: Optional[str] = Field(default=None, description="1 (low), 2 (medium), 3 (high)")


class ConfigureConnectionInput(BaseModel):
    """Input for configure_connection tool."""
    url: str = Field(..., description="Odoo instance URL")
    database: Optional[str] = Field(default=None, description="Database name")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    user: Optional[str] = Field(default=None, description="Username")
    password: Optional[str] = Field(default=None, description="Password")
    yolo_mode: Optional[Literal["off", "read", "true"]] = Field(default=None, description="YOLO mode setting")
