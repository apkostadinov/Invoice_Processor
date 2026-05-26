from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from pathlib import Path
from contextlib import asynccontextmanager
import logging
from app.core.logging import setup_logging
from collections import defaultdict

from app.core.config import validate_settings
from app.core.exceptions import (
    DomainError,
    LLMParseError,
    OCRProcessingError,
    PersistenceError,
    ValidationError,
)
from app.db.init_db import init_db
from app.db.models import InvoiceModel
from app.db.session import SessionLocal

from app.services.llm_service import extract_invoice_data
from app.services.document_extractor import extract_document_text
from app.services.llm_service import test_openai
from app.services.persistence_service import save_invoice
from app.services.report_service import generate_invoice_report
from app.schemas.response import InvoiceDetailResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_settings()
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

setup_logging()

ALLOWED_UPLOAD_EXTENSIONS = {".pdf"}

@app.exception_handler(OCRProcessingError)
async def handle_ocr_error(_, exc: OCRProcessingError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(LLMParseError)
async def handle_llm_error(_, exc: LLMParseError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(ValidationError)
async def handle_validation_error(_, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(PersistenceError)
async def handle_persistence_error(_, exc: PersistenceError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


@app.exception_handler(DomainError)
async def handle_domain_error(_, exc: DomainError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )

def validate_upload(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing file name"
        )

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

@app.post("/api/invoices/test_upload")
async def upload_invoice(file: UploadFile = File(...)):
    validate_upload(file)

    uploads_dir = Path("app/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    file_path = uploads_dir / file.filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    text, source = extract_document_text(file_path)

    return {
        "status": "uploaded",
        "filename": file.filename,
        "extraction_method": source,
        "raw_text_length": len(text),
        "preview": text[:500]
    }

@app.post("/api/invoices/extract")
async def extract_invoice(file: UploadFile = File(...)):
    validate_upload(file)

    file_path = f"app/uploads/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    raw_text, source = extract_document_text(file_path)
    structured, llm_raw_response = extract_invoice_data(raw_text)

    session = SessionLocal()

    try:
        db_invoice = save_invoice(
            session=session,
            invoice=structured,
            raw_text=raw_text,
            extraction_method=source,
            llm_raw_response=llm_raw_response
        )

        session.commit()

        return {
            "invoice_id": db_invoice.id,
            "status": "saved",
            "warnings": structured.warnings
        }

    except Exception as e:
        logger.exception("Database persistence failed")
        session.rollback()
        raise PersistenceError(f"Failed to persist invoice: {str(e)}") from e

    finally:
        session.close()

@app.get("/api/invoices/{invoice_id}/report")
def generate_report(invoice_id: int):

    session = SessionLocal()

    try:
        try:
            pdf_path = generate_invoice_report(
                session=session,
                invoice_id=invoice_id
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.exception("Report generation failed")
            raise PersistenceError(f"Failed to generate report: {str(e)}") from e

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"invoice_{invoice_id}_report.pdf"
        )

    finally:
        session.close()


@app.get("/api/invoices")
def list_invoices():
    session = SessionLocal()

    try:
        rows = (
            session.query(InvoiceModel.id)
            .order_by(InvoiceModel.id.asc())
            .all()
        )
        ids = [row[0] for row in rows]

        return {
            "count": len(ids),
            "invoice_ids": ids
        }
    finally:
        session.close()


@app.get("/api/invoices/{invoice_id}", response_model=InvoiceDetailResponse)
def get_invoice(invoice_id: int):
    session = SessionLocal()

    try:
        invoice = (
            session.query(InvoiceModel)
            .filter(InvoiceModel.id == invoice_id)
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        summary = defaultdict(float)

        for item in invoice.line_items:
            summary[item.category] += item.amount

        return InvoiceDetailResponse(
            id=invoice.id,

            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,

            issuer={
                "name": invoice.issuer_name,
                "vat_id": invoice.issuer_vat_id
            },

            receiver={
                "name": invoice.receiver_name,
                "vat_id": invoice.receiver_vat_id
            },

            currency=invoice.currency,
            total_amount=invoice.total_amount,

            line_items=[
                {
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "amount": item.amount,
                    "category": item.category,
                    "confidence": item.confidence,
                    "source_text": item.source_text
                }
                for item in invoice.line_items
            ],

            summary=dict(summary),

            expense_summary=invoice.expense_summary,

            warnings=(invoice.warnings.split("\n") if invoice.warnings else [])
        )
    finally:
        session.close()



@app.get("/test-openai")
def openai_test():
    result = test_openai()

    return {
        "response": result
    }
