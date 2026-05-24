import logging
from app.schemas.invoice_schema import InvoiceData

logger = logging.getLogger(__name__)

def validate_invoice_data(data: InvoiceData) -> InvoiceData:
    for item in data.line_items:

        expected_amount = round(
            item.quantity * item.unit_price,
            2
        )

        # tolerance for floating point errors
        if abs(expected_amount - item.amount) > 0.01:
            logger.warning(
                f"Corrected item amount "
                f"from {item.amount} "
                f"to {expected_amount}"
            )

            item.amount = expected_amount

            # lower confidence if corrected
            item.confidence *= 0.9



    return data
'''
#TODO
sum(items) ≈ invoice total
all prices use same currency
quantity > 0
unit_price = 999999 → likely OCR error
'''