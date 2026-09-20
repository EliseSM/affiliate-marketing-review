"""seed product_terms with ClearPath Financial test-fixture products

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-19

Seeds the product_terms table (starts empty per the design doc) so the
apr_matches_product_terms deterministic rule has real data to check the
marketing-test-examples/ fixtures against, instead of always returning
not_applicable. Source of truth is app/db/seed_data.py (PRODUCT_TERMS_SEED).
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.db.seed_data import PRODUCT_TERMS_SEED

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


product_terms_table = sa.table(
    "product_terms",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("product_identifier", sa.String),
    sa.column("product_type", sa.String),
    sa.column("apr_min", sa.Numeric),
    sa.column("apr_max", sa.Numeric),
    sa.column("annual_fee", sa.Numeric),
    sa.column("eligibility_notes", sa.String),
    sa.column("source_document_ref", sa.String),
)


def upgrade() -> None:
    op.bulk_insert(
        product_terms_table,
        [
            {
                "id": uuid.uuid4(),
                "product_identifier": row["product_identifier"],
                "product_type": row["product_type"],
                "apr_min": row["apr_min"],
                "apr_max": row["apr_max"],
                "annual_fee": row["annual_fee"],
                "eligibility_notes": row["eligibility_notes"],
                "source_document_ref": row["source_document_ref"],
            }
            for row in PRODUCT_TERMS_SEED
        ],
    )


def downgrade() -> None:
    op.execute(
        product_terms_table.delete().where(
            product_terms_table.c.product_identifier.in_(
                [row["product_identifier"] for row in PRODUCT_TERMS_SEED]
            )
        )
    )
