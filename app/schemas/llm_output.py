from pydantic import BaseModel
from app.schemas.invoice import Invoice

class LLMInvoiceOutput(BaseModel):
    invoice: Invoice
    confidence_score: float