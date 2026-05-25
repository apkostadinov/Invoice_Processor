import logging

from app.schemas.invoice import Invoice

logger = logging.getLogger(__name__)

MAX_REASONABLE_PRICE = 100000

def clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, value))



def validate_invoice_data(data: Invoice) -> Invoice:
    warnings = []

    validate_line_items(data, warnings)
    validate_invoice_total(data, warnings)

    data.warnings = warnings
    return data


def validate_line_items(data: Invoice, warnings: list):
    for item in data.line_items:

        # -------------------------
        # Quantity sanity
        # -------------------------
        if item.quantity <= 0:
            logger.warning(
                f"Invalid quantity for item "
                f"{item.description}: {item.quantity}"
            )
            warnings.append(
                f"Invalid quantity corrected for {item.description}"
            )
            item.quantity = 1.0
            item.confidence = clamp_confidence(
                item.confidence * 0.7
            )

        # -------------------------
        # OCR anomaly detection
        # -------------------------
        if item.unit_price > MAX_REASONABLE_PRICE:

            logger.warning(
                f"Suspicious unit price detected "
                f"for item {item.description}: "
                f"{item.unit_price}"
            )

            item.confidence = clamp_confidence(
                item.confidence * 0.5
            )

        # -------------------------
        # Amount consistency
        # -------------------------
        expected_amount = round(
            item.quantity * item.unit_price,
            2
        )

        if abs(expected_amount - item.amount) > 0.01:

            logger.warning(
                f"Correcting amount for "
                f"{item.description}: "
                f"{item.amount} -> {expected_amount}"
            )

            warnings.append(
                f"Suspicious unit price detected: {item.description}"
            )

            item.amount = expected_amount
            item.confidence = clamp_confidence(
                item.confidence * 0.9
            )


def validate_invoice_total(data: Invoice, warnings: list):

    calculated_total = round(
        sum(item.amount for item in data.line_items),
        2
    )

    if abs(calculated_total - data.total_amount) > 0.05:

        logger.warning(
            f"Invoice total mismatch: "
            f"invoice={data.total_amount} "
            f"calculated={calculated_total}"
        )

        warnings.append(
            f"Invoice total corrected from "
            f"{data.total_amount}"
        )

        # trust line items more than total
        data.total_amount = calculated_total