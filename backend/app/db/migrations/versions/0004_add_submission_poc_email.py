"""add submissions.poc_email

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-21

Point-of-contact email for whoever owns a piece of marketing material, so a
reviewer knows who to follow up with. Populated at upload time either via an
excel/csv "poc_email" column (see app/ingestion/excel_csv.py) or the
poc_email form field on POST /submissions/batch for single-item uploads.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("submissions", sa.Column("poc_email", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("submissions", "poc_email")
