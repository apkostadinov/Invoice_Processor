from pdf2image import convert_from_path
import pytesseract
import logging
# import pytesseract

logger = logging.getLogger(__name__)

#pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

def extract_text_with_ocr(pdf_path: str) -> str:
    logger.info(f"OCR started for: {pdf_path}")

    images = convert_from_path(pdf_path)

    text_pages = []

    for i, img in enumerate(images):
        logger.debug(f"OCR processing page {i+1}")
        img = img.convert("L")
        img = img.resize((img.width * 2, img.height * 2))
        text = pytesseract.image_to_string(
            img,
            lang="bul+eng"
        )
        text_pages.append(text)

    result = "\n".join(text_pages)

    logger.info(f"OCR finished | chars={len(result)}")

    return result