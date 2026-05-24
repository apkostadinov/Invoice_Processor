from pydantic import BaseModel
from typing import List, Optional


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float
    category: str
    confidence: float = 1.0


class Company(BaseModel):
    name: str
    company_id: Optional[str] = None


class InvoiceData(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None

    issuer: Company
    receiver: Optional[Company] = None

    currency: str
    total_amount: float

    line_items: List[LineItem]

    expense_summary: str

