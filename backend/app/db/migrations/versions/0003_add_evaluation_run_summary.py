"""add evaluation_runs.summary

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-20

Adds a structured, human-readable summary column populated once by the
evaluation pipeline (app/evaluation/summary_builder.py) at evaluation time --
{"outcome": str, "reasons": list[str], "claims_to_verify": list[dict]} -- so
the frontend can display why a run failed or what claims to double-check on a
passing run without generating anything on demand.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evaluation_runs", sa.Column("summary", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("evaluation_runs", "summary")
