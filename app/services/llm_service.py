import logging

from app.services.validation_service import validate_invoice_data

logger = logging.getLogger(__name__)

import json
from openai import OpenAI

from app.schemas.invoice import InvoiceData
from app.services.prompts import INVOICE_EXTRACTION_PROMPT
from app.core.config import OPENAI_KEY,OPENAI_MODEL, MAX_LLM_INPUT_CHARS

client = OpenAI(api_key=OPENAI_KEY)
openai_version = OPENAI_MODEL

MAX_CHARS = MAX_LLM_INPUT_CHARS

def extract_invoice_data(raw_text: str) -> InvoiceData:

    if len(raw_text) > MAX_CHARS:
        raw_text = raw_text[:MAX_CHARS]
        logger.warning(
        f"Input text truncated from "
        f"{len(raw_text)} to "
        f"{MAX_LLM_INPUT_CHARS} chars ong. Truncated to {MAX_CHARS} characters")

    prompt = INVOICE_EXTRACTION_PROMPT + raw_text
    try:
        response = client.chat.completions.create(
            model=openai_version,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        content = response.choices[0].message.content

        parsed = json.loads(content)

        data = InvoiceData(**parsed)

        data = validate_invoice_data(data)

        return data

    except Exception as e:
        raise ValueError(f"LLM parsing failed: {str(e)}")

def fix_line_items(items):
    fixed = []

    for item in items:
        qty = float(item.quantity)
        price = float(item.unit_price)

        expected = round(qty * price, 2)

        # if mismatch, fix amount
        if abs(expected - item.amount) > 0.01:
            item.amount = expected
            item.confidence *= 0.9

        if not item.source_text:
            item.source_text = None

        fixed.append(item)

    return fixed

def test_openai():
    response = client.chat.completions.create(
        model=openai_version,
        messages=[
            {
                "role": "user",
                "content": "Reply with: OpenAI connection successful"
            }
        ]
    )
    return response.choices[0].message.content