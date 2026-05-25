from pydantic import BaseModel
from typing import Optional


class Company(BaseModel):
    name: str
    vat_id: Optional[str] = None
    company_id: Optional[str] = None
