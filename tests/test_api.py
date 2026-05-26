from pathlib import Path

import pytest
import app.main as main_module
import app.services.report_service as report_service
from app.db.models.invoice import InvoiceModel
from app.schemas.company import Company
from app.schemas.invoice import Invoice
from app.schemas.line_item import LineItem


def _seed_invoice(session, invoice_number: str) -> InvoiceModel:
    invoice = InvoiceModel(
        invoice_number=invoice_number,
        invoice_date="2026-05-26",
        issuer_name="Issuer Ltd",
        issuer_vat_id="BG123",
        receiver_name="Receiver OOD",
        receiver_vat_id="BG456",
        currency="BGN",
        total_amount=42.0,
        extraction_method="pdf",
    )
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice


def test_health_returns_ok(client_and_session_factory):
    client, _ = client_and_session_factory
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_extract_rejects_non_pdf_upload(client_and_session_factory):
    client, _ = client_and_session_factory
    response = client.post(
        "/api/invoices/extract",
        files={"file": ("not_invoice.txt", b"test", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are supported"


def test_list_invoices_returns_empty_state(client_and_session_factory):
    client, _ = client_and_session_factory
    response = client.get("/api/invoices")
    assert response.status_code == 200
    assert response.json() == {"count": 0, "invoice_ids": []}


def test_list_invoices_returns_all_ids_sorted(client_and_session_factory):
    client, session_factory = client_and_session_factory
    with session_factory() as session:
        _seed_invoice(session, "INV-2")
        _seed_invoice(session, "INV-1")

    response = client.get("/api/invoices")
    assert response.status_code == 200
    assert response.json() == {"count": 2, "invoice_ids": [1, 2]}


def test_get_invoice_not_found_returns_404(client_and_session_factory):
    client, _ = client_and_session_factory
    response = client.get("/api/invoices/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


def test_generate_report_not_found_returns_404(client_and_session_factory):
    client, _ = client_and_session_factory
    response = client.get("/api/invoices/999/report")
    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


def _mock_invoice_payload() -> Invoice:
    return Invoice(
        invoice_number="DEMO-900",
        invoice_date="2026-05-25",
        issuer=Company(name="Fresh Foods PLC", vat_id="BG111222333"),
        receiver=Company(name="North Office OOD", vat_id="BG444555666"),
        currency="BGN",
        total_amount=94.2,
        line_items=[
            LineItem(description="Milk", quantity=2, unit_price=3.2, amount=6.4, category="Dairy", confidence=0.95, source_text="Milk 2 x 3.20"),
            LineItem(description="Bread", quantity=2, unit_price=2.4, amount=4.8, category="Bakery", confidence=0.95, source_text="Bread 2 x 2.40"),
            LineItem(description="Yogurt", quantity=4, unit_price=1.8, amount=7.2, category="Dairy", confidence=0.95, source_text="Yogurt 4 x 1.80"),
            LineItem(description="Coffee", quantity=1, unit_price=12.5, amount=12.5, category="Beverages", confidence=0.95, source_text="Coffee 1 x 12.50"),
            LineItem(description="Water", quantity=6, unit_price=1.1, amount=6.6, category="Beverages", confidence=0.95, source_text="Water 6 x 1.10"),
            LineItem(description="Cheese", quantity=2, unit_price=6.8, amount=13.6, category="Dairy", confidence=0.95, source_text="Cheese 2 x 6.80"),
            LineItem(description="Tomatoes", quantity=3, unit_price=2.7, amount=8.1, category="Vegetables", confidence=0.95, source_text="Tomatoes 3 x 2.70"),
            LineItem(description="Soap", quantity=2, unit_price=5.4, amount=10.8, category="Household", confidence=0.95, source_text="Soap 2 x 5.40"),
            LineItem(description="Towels", quantity=2, unit_price=12.1, amount=24.2, category="Household", confidence=0.95, source_text="Towels 2 x 12.10"),
        ],
        expense_summary="Office grocery and household supplies."
    )


def test_extract_persists_invoice_and_items(client_and_session_factory, monkeypatch):
    client, _ = client_and_session_factory
    mocked_invoice = _mock_invoice_payload()

    monkeypatch.setattr(
        main_module,
        "extract_document_text",
        lambda _: ("RAW OCR TEXT", "ocr"),
    )
    monkeypatch.setattr(
        main_module,
        "extract_invoice_data",
        lambda _: (mocked_invoice, '{"ok": true}'),
    )

    response = client.post(
        "/api/invoices/extract",
        files={"file": ("invoice.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "saved"
    assert isinstance(body["invoice_id"], int)

    details = client.get(f"/api/invoices/{body['invoice_id']}")
    assert details.status_code == 200
    detail_body = details.json()
    assert detail_body["invoice_number"] == "DEMO-900"
    assert detail_body["currency"] == "BGN"
    assert len(detail_body["line_items"]) == 9
    assert detail_body["summary"]["Dairy"] == pytest.approx(27.2)


def test_generate_report_for_saved_invoice(
    client_and_session_factory,
    monkeypatch,
    tmp_path: Path
):
    client, _ = client_and_session_factory
    mocked_invoice = _mock_invoice_payload()

    monkeypatch.setattr(
        main_module,
        "extract_document_text",
        lambda _: ("RAW OCR TEXT", "ocr"),
    )
    monkeypatch.setattr(
        main_module,
        "extract_invoice_data",
        lambda _: (mocked_invoice, '{"ok": true}'),
    )
    monkeypatch.setattr(report_service, "REPORTS_DIR", tmp_path)

    create_response = client.post(
        "/api/invoices/extract",
        files={"file": ("invoice.pdf", b"%PDF-1.4", "application/pdf")},
    )
    invoice_id = create_response.json()["invoice_id"]

    report_response = client.get(f"/api/invoices/{invoice_id}/report")
    assert report_response.status_code == 200
    assert report_response.headers["content-type"] == "application/pdf"

    expected_file = tmp_path / f"invoice_{invoice_id}.pdf"
    assert expected_file.exists()
