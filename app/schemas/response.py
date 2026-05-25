from pydantic import BaseModel
from typing import List, Optional, Dict

from app.schemas.line_item import LineItem
from app.schemas.company import Company

class InvoiceDetailResponse(BaseModel):
    id: int

    invoice_number: Optional[str]
    invoice_date: Optional[str]

    issuer: Company
    receiver: Optional[Company] = None

    currency: str
    total_amount: float

    line_items: List[LineItem]

    summary: Dict[str, float]

    expense_summary: Optional[str] = None

    warnings: List[str] = []
