"""init schema

Revision ID: 0001_init_schema
Revises: 
Create Date: 2026-05-26 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_init_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sa.String(), nullable=True),
        sa.Column("invoice_date", sa.String(), nullable=True),
        sa.Column("issuer_name", sa.String(), nullable=False),
        sa.Column("issuer_vat_id", sa.String(), nullable=True),
        sa.Column("receiver_name", sa.String(), nullable=True),
        sa.Column("receiver_vat_id", sa.String(), nullable=True),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("extraction_method", sa.String(), nullable=True),
        sa.Column("llm_raw_response", sa.Text(), nullable=True),
        sa.Column("expense_summary", sa.Text(), nullable=True),
        sa.Column("warnings", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_invoices_id"), "invoices", ["id"], unique=False)
    op.create_index(
        op.f("ix_invoices_invoice_number"),
        "invoices",
        ["invoice_number"],
        unique=False,
    )

    op.create_table(
        "line_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source_text", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_line_items_id"), "line_items", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_line_items_id"), table_name="line_items")
    op.drop_table("line_items")

    op.drop_index(op.f("ix_invoices_invoice_number"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_id"), table_name="invoices")
    op.drop_table("invoices")
