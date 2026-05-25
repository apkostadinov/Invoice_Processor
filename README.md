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

## Output Files

Uploaded PDFs are saved in `app/uploads/`.
Generated reports are saved in `app/reports/`.

## Sample Invoices

Place test invoices in `samples/`.
The repository includes:
`samples/sample_invoice_demo.pdf`
`samples/sample_invoice_demo_2.pdf`
`samples/sample_invoice_demo_3.pdf`
