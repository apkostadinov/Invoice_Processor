from sqlalchemy.orm import Session

from app.db.models.invoice import InvoiceModel
from app.db.models.line_item import LineItemModel
from app.schemas.invoice import Invoice


def save_invoice(session: Session, invoice: Invoice, raw_text: str, extraction_method: str):
    db_invoice = InvoiceModel(
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,

        issuer_name=invoice.issuer.name,
        issuer_vat_id=invoice.issuer.vat_id,

        receiver_name=invoice.receiver.name if invoice.receiver else None,
        receiver_vat_id=invoice.receiver.vat_id if invoice.receiver else None,

        currency=invoice.currency,
        total_amount=invoice.total_amount,

        raw_text=raw_text,
        extraction_method=extraction_method,
    )

    session.add(db_invoice)
    session.flush()  # IMPORTANT: gets invoice ID before commit

    line_items = []

    for item in invoice.line_items:
        db_item = LineItemModel(
            invoice_id=db_invoice.id,

            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            amount=item.amount,
            category=item.category,

            confidence=item.confidence,
            source_text=item.source_text,
        )

        line_items.append(db_item)

    session.add_all(line_items)

    return db_invoice