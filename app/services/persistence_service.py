from sqlalchemy.orm import Session

from app.db.models.invoice import InvoiceModel
from app.db.models.line_item import LineItemModel
from app.schemas.invoice import Invoice


def save_invoice(
    session: Session,
    invoice: Invoice,
    raw_text: str,
    extraction_method: str,
    llm_raw_response: str
):
    issuer_id = invoice.issuer.vat_id or invoice.issuer.company_id
    receiver_id = None
    if invoice.receiver:
        receiver_id = invoice.receiver.vat_id or invoice.receiver.company_id

    db_invoice = InvoiceModel(
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,

        issuer_name=invoice.issuer.name,
        issuer_vat_id=issuer_id,

        receiver_name=invoice.receiver.name if invoice.receiver else None,
        receiver_vat_id=receiver_id,

        currency=invoice.currency,
        total_amount=invoice.total_amount,

        raw_text=raw_text,
        extraction_method=extraction_method,
        llm_raw_response=llm_raw_response,
        warnings="\n".join(invoice.warnings) if invoice.warnings else None,
    )

    session.add(db_invoice)
    session.flush()

    db_invoice.line_items.clear()

    for item in invoice.line_items:

        if item.quantity <= 0 or item.unit_price < 0:
            continue

        db_invoice.line_items.append(
            LineItemModel(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
                category=item.category,
                confidence=item.confidence,
                source_text=item.source_text,
            )
        )

    session.refresh(db_invoice)

    return db_invoice
