import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.db.models.claim import Claim
    from app.db.models.deterministic_check_result import DeterministicCheckResult
    from app.db.models.llm_judge_result import LLMJudgeResult
    from app.db.models.submission import Submission

# status allowed values: pending | running | completed | failed
# overall_flag allowed values: pass | needs_review | fail


class EvaluationRun(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_runs"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    llm_provider: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    deterministic_ruleset_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    overall_flag: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Structured, human-readable explanation of the outcome -- computed once in
    # app/evaluation/pipeline.py at evaluation time and persisted here, so the
    # frontend only ever displays already-stored data. Shape:
    # {"outcome": str, "reasons": list[str], "claims_to_verify": list[dict]}
    summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    submission: Mapped["Submission"] = relationship(back_populates="evaluation_runs")
    llm_judge_results: Mapped[list["LLMJudgeResult"]] = relationship(back_populates="evaluation_run")
    deterministic_check_results: Mapped[list["DeterministicCheckResult"]] = relationship(
        back_populates="evaluation_run"
    )
    claims: Mapped[list["Claim"]] = relationship(back_populates="evaluation_run")
