from pydantic import BaseModel
from typing import List, Optional

from app.schemas.company import Company
from app.schemas.line_item import LineItem


class Invoice(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None

    issuer: Company
    receiver: Company

    currency: str
    total_amount: float

    line_items: List[LineItem]

    warnings: List[str] = []
    expense_summary: Optional[str] = None


InvoiceData = Invoice
