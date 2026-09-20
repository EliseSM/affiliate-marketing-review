"""add submissions.project_name

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-22

Free-text grouping label so resubmissions of the same marketing material can
be filtered together (see app/ingestion/excel_csv.py's project_name column
alias and the project_name form field on POST /submissions/batch).

Note: this migration does NOT add an "exported" status value anywhere -- the
submissions.status column is a plain String with no DB-level enum/check
constraint, so "exported" becoming a valid value (set by POST /exports) needed
no schema change, only an application-level change.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("submissions", sa.Column("project_name", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("submissions", "project_name")
