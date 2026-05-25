from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class InvoiceModel(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    invoice_number = Column(String, nullable=True, index=True)
    invoice_date = Column(String, nullable=True)

    issuer_name = Column(String, nullable=False)
    issuer_vat_id = Column(String, nullable=True)

    receiver_name = Column(String, nullable=True)
    receiver_vat_id = Column(String, nullable=True)

    currency = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)

    filename = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.now)
    raw_text = Column(Text, nullable=True)
    extraction_method = Column(String, nullable=True)
    llm_raw_response = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)

    # relationship
    line_items = relationship(
        "LineItemModel",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
