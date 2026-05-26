from app.services.pdf_text_extractor import extract_text_from_pdf
from app.services.ocr_service import extract_text_with_ocr

from app.core.exceptions import OCRProcessingError
import logging
import time

logger = logging.getLogger(__name__)

def extract_document_text(pdf_path: str) -> tuple[str, str]:
    """
    Returns:
    (text, source)
    source = "pdf" or "ocr"
    """

    logger.info(f"Starting extraction for: {pdf_path}")

    start = time.time()

    try:
        text = extract_text_from_pdf(pdf_path)
    except Exception as exc:
        raise OCRProcessingError(f"PDF text extraction failed: {str(exc)}") from exc

    duration = time.time() - start

    logger.info(f"PDF text extraction took {duration:.2f}s")

    if text and len(text.strip()) > 100:
        logger.info("Used PDF text extraction (fast path)")
        logger.info(f"Extracted characters: {len(text)}")
        return text, "pdf"

    logger.warning("PDF extraction failed or empty → switching to OCR")
    duration = time.time() - start
    # fallback
    try:
        ocr_text = extract_text_with_ocr(pdf_path)
    except Exception as exc:
        raise OCRProcessingError(f"OCR fallback failed: {str(exc)}") from exc

    logger.info("Used OCR extraction (slow path)")
    logger.info(f"OCR extracted characters: {len(ocr_text)}")

    duration = time.time() - start
    logger.info(f"OCR extraction took {duration:.2f}s")

    return ocr_text, "ocr"
