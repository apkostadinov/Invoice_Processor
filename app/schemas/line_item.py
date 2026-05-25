from pydantic import BaseModel
from typing import Optional


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float
    category: str

    confidence: float = 1.0
    source_text: Optional[str] = None