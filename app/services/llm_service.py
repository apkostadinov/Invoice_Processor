import logging

logger = logging.getLogger(__name__)

import json
from openai import OpenAI

from app.schemas.invoice_schema import InvoiceData
from app.services.prompts import INVOICE_EXTRACTION_PROMPT
from app.core.config import OPENAI_KEY,OPENAI_MODEL

client = OpenAI(api_key=OPENAI_KEY)
openai_version = OPENAI_MODEL

def extract_invoice_data(raw_text: str) -> InvoiceData:
    prompt = INVOICE_EXTRACTION_PROMPT + raw_text

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

    return InvoiceData(**parsed)

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