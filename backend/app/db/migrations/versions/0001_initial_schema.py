"""initial schema + seed rubric_dimensions and rule_definitions

Revision ID: 0001
Revises:
Create Date: 2026-09-19

Seeding strategy: seed data lives in app/db/seed_data.py (the single source of
truth, mirrored from the guidelines doc) and is inserted directly in this
migration's upgrade() via SQLAlchemy Core inserts. Keeping seeding inside the
migration (rather than a separate script run after) guarantees the registry
tables are never empty after `alembic upgrade head`, which the deterministic
engine and LLM prompt builder both depend on.
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.db.seed_data import RUBRIC_DIMENSIONS, RULE_DEFINITIONS

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "submission_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("upload_type", sa.String(), nullable=False),
        sa.Column("uploaded_by_email", sa.String(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
    )

    op.create_table(
        "rubric_dimensions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(), nullable=False, unique=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("scoring_scale", postgresql.JSONB(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "rule_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_key", sa.String(), nullable=False, unique=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False, server_default="medium"),
        sa.Column("requires_product_terms", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("config", postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        "product_terms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_identifier", sa.String(), nullable=False, unique=True),
        sa.Column("product_type", sa.String(), nullable=False),
        sa.Column("apr_min", sa.Numeric(), nullable=True),
        sa.Column("apr_max", sa.Numeric(), nullable=True),
        sa.Column("annual_fee", sa.Numeric(), nullable=True),
        sa.Column("promo_terms", postgresql.JSONB(), nullable=True),
        sa.Column("eligibility_notes", sa.String(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("source_document_ref", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("submission_batches.id"),
            nullable=False,
        ),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=True),
        sa.Column("raw_text", sa.String(), nullable=False),
        sa.Column("raw_html", sa.String(), nullable=True),
        sa.Column("product_identifier", sa.String(), nullable=True),
        sa.Column("affiliate_partner", sa.String(), nullable=True),
        sa.Column("landing_url", sa.String(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(), nullable=False, server_default="ingested"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "submission_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "submission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("submissions.id"), nullable=False
        ),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("original_src", sa.String(), nullable=True),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
    )

    op.create_table(
        "evaluation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "submission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("submissions.id"), nullable=False
        ),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("llm_provider", sa.String(), nullable=True),
        sa.Column("deterministic_ruleset_version", sa.String(), nullable=True),
        sa.Column("overall_score", sa.Numeric(), nullable=True),
        sa.Column("overall_flag", sa.String(), nullable=True),
    )

    op.create_table(
        "llm_judge_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "evaluation_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluation_runs.id"),
            nullable=False,
        ),
        sa.Column(
            "rubric_dimension_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rubric_dimensions.id"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("rationale", sa.String(), nullable=False),
        sa.Column("evidence_refs", postgresql.JSONB(), nullable=True),
        sa.Column("raw_model_response", postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint("evaluation_run_id", "rubric_dimension_id", name="uq_run_dimension"),
    )

    op.create_table(
        "deterministic_check_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "evaluation_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluation_runs.id"),
            nullable=False,
        ),
        sa.Column(
            "rule_definition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rule_definitions.id"),
            nullable=False,
        ),
        sa.Column("result", sa.String(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
    )

    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "submission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("submissions.id"), nullable=False
        ),
        sa.Column(
            "evaluation_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluation_runs.id"),
            nullable=False,
        ),
        sa.Column("claim_text", sa.String(), nullable=False),
        sa.Column("claim_type", sa.String(), nullable=False, server_default="other"),
        sa.Column("product_identifier", sa.String(), nullable=True),
        sa.Column("source_reference", sa.String(), nullable=True),
        sa.Column("source_date", sa.Date(), nullable=True),
        sa.Column(
            "rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rule_definitions.id"), nullable=True
        ),
        sa.Column(
            "rubric_dimension_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rubric_dimensions.id"),
            nullable=True,
        ),
        sa.Column("severity", sa.String(), nullable=False, server_default="low"),
        sa.Column("evaluator_result", sa.String(), nullable=False, server_default="unverifiable"),
        sa.Column("human_review_status", sa.String(), nullable=False, server_default="unreviewed"),
    )

    # --- Seed rubric_dimensions (guidelines Section 12) and rule_definitions (Sections 8 & 13) ---
    rubric_table = sa.table(
        "rubric_dimensions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("key", sa.String),
        sa.column("display_name", sa.String),
        sa.column("description", sa.String),
        sa.column("scoring_scale", postgresql.JSONB),
        sa.column("active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        rubric_table,
        [
            {
                "id": uuid.uuid4(),
                "key": dim["key"],
                "display_name": dim["display_name"],
                "description": dim["description"],
                "scoring_scale": dim["scoring_scale"],
                "active": True,
                "sort_order": dim["sort_order"],
            }
            for dim in RUBRIC_DIMENSIONS
        ],
    )

    rule_table = sa.table(
        "rule_definitions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("rule_key", sa.String),
        sa.column("display_name", sa.String),
        sa.column("description", sa.String),
        sa.column("category", sa.String),
        sa.column("severity", sa.String),
        sa.column("requires_product_terms", sa.Boolean),
        sa.column("active", sa.Boolean),
        sa.column("config", postgresql.JSONB),
    )
    op.bulk_insert(
        rule_table,
        [
            {
                "id": uuid.uuid4(),
                "rule_key": rule["rule_key"],
                "display_name": rule["display_name"],
                "description": rule["description"],
                "category": rule["category"],
                "severity": rule["severity"],
                "requires_product_terms": rule["requires_product_terms"],
                "active": True,
                "config": rule["config"],
            }
            for rule in RULE_DEFINITIONS
        ],
    )


def downgrade() -> None:
    op.drop_table("claims")
    op.drop_table("deterministic_check_results")
    op.drop_table("llm_judge_results")
    op.drop_table("evaluation_runs")
    op.drop_table("submission_assets")
    op.drop_table("submissions")
    op.drop_table("product_terms")
    op.drop_table("rule_definitions")
    op.drop_table("rubric_dimensions")
    op.drop_table("submission_batches")
