import uuid
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.db.models.evaluation_run import EvaluationRun
    from app.db.models.rubric_dimension import RubricDimension
    from app.db.models.rule_definition import RuleDefinition
    from app.db.models.submission import Submission

# claim_type allowed values: apr | fee | reward | eligibility | approval_odds | savings | other
# severity allowed values: low | medium | high | critical
# evaluator_result allowed values: supported | unsupported | contradicted | unverifiable
# human_review_status allowed values: unreviewed | confirmed | dismissed


class Claim(UUIDPKMixin, TimestampMixin, Base):
    """Implements the guidelines Section 16 model:
    claim -> product -> source -> source_date -> rule_id -> severity -> evaluator_result -> human_review_status.
    Populated by both the deterministic engine (rule_id set) and the LLM judge (rubric_dimension_id set)."""

    __tablename__ = "claims"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False
    )
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_runs.id"), nullable=False
    )
    claim_text: Mapped[str] = mapped_column(String, nullable=False)
    claim_type: Mapped[str] = mapped_column(String, nullable=False, default="other")
    product_identifier: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rule_definitions.id"), nullable=True
    )
    rubric_dimension_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rubric_dimensions.id"), nullable=True
    )
    severity: Mapped[str] = mapped_column(String, nullable=False, default="low")
    evaluator_result: Mapped[str] = mapped_column(String, nullable=False, default="unverifiable")
    human_review_status: Mapped[str] = mapped_column(String, nullable=False, default="unreviewed")

    submission: Mapped["Submission"] = relationship(back_populates="claims")
    evaluation_run: Mapped["EvaluationRun"] = relationship(back_populates="claims")
    rule: Mapped[Optional["RuleDefinition"]] = relationship(back_populates="claims")
    rubric_dimension: Mapped[Optional["RubricDimension"]] = relationship(back_populates="claims")
