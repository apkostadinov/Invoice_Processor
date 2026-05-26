from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
import logging
from app.core.logging import setup_logging
from collections import defaultdict

from app.db.init_db import init_db
from app.db.models import InvoiceModel
from app.db.base import Base
from app.db.session import engine
from app.db.session import SessionLocal

from app.services.llm_service import extract_invoice_data
from app.services.document_extractor import extract_document_text
from app.services.llm_service import test_openai
from app.services.persistence_service import save_invoice
from app.services.report_service import generate_invoice_report
from app.schemas.response import InvoiceDetailResponse

Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)

app = FastAPI()

setup_logging()

ALLOWED_UPLOAD_EXTENSIONS = {".pdf"}


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

@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/invoices/test_upload")
async def upload_invoice(file: UploadFile = File(...)):
    validate_upload(file)

    uploads_dir = Path("app/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    file_path = uploads_dir / file.filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        text, source = extract_document_text(file_path)
    except Exception as e:
        logger.exception("Upload extraction failed")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )

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

    try:
        raw_text, source = extract_document_text(file_path)
    except Exception as e:
        logger.exception("Document extraction failed")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )

    try:
        structured, llm_raw_response = extract_invoice_data(raw_text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("LLM processing failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM processing failed: {str(e)}"
        )

    if len(structured.line_items) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invoice must contain at least 8 line items"
        )

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

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        logger.exception("Database persistence failed")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist invoice: {str(e)}"
        )

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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate report: {str(e)}"
            )

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
