from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class LineItemModel(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)

    invoice_id = Column(Integer, ForeignKey("invoices.id"))

    description = Column(String, nullable=False)

    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)

    category = Column(String, nullable=False)

    confidence = Column(Float, default=1.0)
    source_text = Column(String, nullable=True)

    invoice = relationship(
        "InvoiceModel",
        back_populates="line_items"
    )