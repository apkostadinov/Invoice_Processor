# Smart Receipt Analyzer

Python service that extracts data from invoice PDFs with OCR and LLM parsing, stores structured output in PostgreSQL, and generates expense report PDFs.

## Requirements

Docker and Docker Compose.

## Setup

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_KEY` in `.env`.
3. Start all services.

```bash
docker compose up --build
```

If you change SQLAlchemy models after a previous run, reset the database volume so new columns are applied:

```bash
docker compose down -v
docker compose up --build
```

## API

Health check:

```bash
GET /health
```

Upload only endpoint for OCR preview without DB persistence:

```bash
POST /api/invoices/test_upload
Content-Type: multipart/form-data
file=<invoice.pdf>
```

Main endpoint that processes and persists invoice data:

```bash
POST /api/invoices/extract
Content-Type: multipart/form-data
file=<invoice.pdf>
```

List all saved invoice IDs (useful for report generation):

```bash
GET /api/invoices
```

Notes:
`/api/invoices/test_upload` is a debug helper endpoint and does not save a receipt row in the database.
`/api/invoices/extract` is the production flow for assignment requirements and stores parsed data and line items.

Get invoice details:

```bash
GET /api/invoices/{invoice_id}
```

Generate and download report PDF:

```bash
GET /api/invoices/{invoice_id}/report
```

## Suggested Workflows

### 1) Standard processing + reporting flow

1. Upload and extract with `POST /api/invoices/extract`.
2. Capture returned `invoice_id`.
3. Fetch full details via `GET /api/invoices/{invoice_id}`.
4. Generate report via `GET /api/invoices/{invoice_id}/report`.

### 2) Batch processing flow

1. Process multiple PDFs through `POST /api/invoices/extract`.
2. Call `GET /api/invoices` to get all available IDs.
3. Loop through IDs and call `GET /api/invoices/{invoice_id}/report` for each.

### 3) Debug OCR/parse before persistence

1. Use `POST /api/invoices/test_upload` to verify extraction quality.
2. When extraction preview looks correct, switch to `POST /api/invoices/extract` to persist data.

## Output Files

Uploaded PDFs are saved in `app/uploads/`.
Generated reports are saved in `app/reports/`.

## Sample Invoices

Place test invoices in `samples/`.
The repository includes:
`samples/sample_invoice_demo.pdf`
`samples/sample_invoice_demo_2.pdf`
`samples/sample_invoice_demo_3.pdf`

## Tested Invoice Types

- Digital/text PDFs with selectable text (preferred path).
- Scanned/image PDFs that require OCR fallback.
- Multi-line-item retail-style invoices with 8+ items.
- Invoices with issuer/receiver IDs in VAT or company ID format.

## Known Limitations

- Very low-quality scans (skew, blur, heavy noise) may reduce OCR quality and line-item accuracy.
- Complex layouts (multi-column tables, overlapping stamps, rotated pages) may produce partial extraction.
- LLM output quality depends on OCR text quality; severe OCR corruption can lead to misclassification.
- Extremely long invoices are truncated to `MAX_LLM_INPUT_CHARS` before sending to the LLM.
- Current extraction supports PDF input only.
