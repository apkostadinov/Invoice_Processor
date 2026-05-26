import logging

from app.services.validation_service import validate_invoice_data

import json
from json import JSONDecodeError
from openai import OpenAI

from app.schemas.invoice import Invoice
from app.services.prompts import INVOICE_EXTRACTION_PROMPT
from app.core.config import OPENAI_KEY,OPENAI_MODEL, MAX_LLM_INPUT_CHARS

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_KEY)
openai_version = OPENAI_MODEL

MAX_CHARS = MAX_LLM_INPUT_CHARS

def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in LLM response")
    return text[start:end + 1]


def _parse_invoice_response(content: str) -> Invoice:
    try:
        parsed = json.loads(content)
    except JSONDecodeError:
        parsed = json.loads(_extract_json_object(content))
    return Invoice(**parsed)


def _request_invoice_json(prompt: str, use_json_mode: bool) -> str:
    params = {
        "model": openai_version,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    if use_json_mode:
        params["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**params)
    return response.choices[0].message.content or ""


def extract_invoice_data(raw_text: str) -> tuple[Invoice, str]:
    if len(raw_text) > MAX_CHARS:
        original_len = len(raw_text)
        raw_text = raw_text[:MAX_CHARS]
        logger.warning(
            f"Input text truncated from {original_len} "
            f"to {MAX_CHARS} characters"
        )

    prompt = INVOICE_EXTRACTION_PROMPT + raw_text
    attempts = [
        (prompt, True),
        (
            prompt + "\n\nReturn strictly one valid JSON object only.",
            False
        ),
    ]
    last_error = None

    for attempt_index, (attempt_prompt, use_json_mode) in enumerate(attempts, start=1):
        try:
            content = _request_invoice_json(attempt_prompt, use_json_mode)
            data = _parse_invoice_response(content)
            data = validate_invoice_data(data)
            return data, content
        except Exception as exc:
            last_error = exc
            logger.warning(
                "LLM extraction attempt %s failed: %s",
                attempt_index,
                str(exc),
            )

    raise ValueError(f"LLM parsing failed after retries: {str(last_error)}")

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
