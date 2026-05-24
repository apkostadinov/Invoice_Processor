from fastapi import FastAPI, UploadFile, File
from app.db.init_db import init_db
from app.db.database import SessionLocal
from app.models.invoice import Invoice
from app.services.document_extractor import extract_document_text
from app.services.llm_service import test_openai
from app.core.logging import setup_logging
import logging
from app.services.llm_service import extract_invoice_data


import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

app = FastAPI()

setup_logging()

@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/invoices/extract")
async def extract_invoice(file: UploadFile = File(...)):

    file_path = f"app/uploads/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    raw_text, source = extract_document_text(file_path)

    structured_data = extract_invoice_data(raw_text)

    return {
        "filename": file.filename,

        "extraction_source": source,

        "raw_text_length": len(raw_text),

        "raw_text_preview": raw_text[:1000],

        "line_item_count": len(structured_data.line_items),

        "line_items": structured_data.line_items,

        "structured_data": structured_data
    }

@app.post("/api/invoices")
async def upload_invoice(file: UploadFile = File(...)):
    uploads_dir = Path("app/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    file_path = uploads_dir / file.filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    text, source = extract_document_text(file_path)

    db = SessionLocal()

    invoice = Invoice(
        filename=file.filename,
        raw_text=text,
        extraction_method=source)

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    db.close()

    return {
        "message": "Invoice uploaded",
        "invoice_id": invoice.id,
        "filename": invoice.filename,
        "text_length": len(text)
    }



@app.get("/test-openai")
def openai_test():
    result = test_openai()

    return {
        "response": result
    }