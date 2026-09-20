import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.db.models.evaluation_run import EvaluationRun
    from app.db.models.rubric_dimension import RubricDimension


class LLMJudgeResult(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "llm_judge_results"
    __table_args__ = (
        UniqueConstraint("evaluation_run_id", "rubric_dimension_id", name="uq_run_dimension"),
    )

    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_runs.id"), nullable=False
    )
    rubric_dimension_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rubric_dimensions.id"), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0, 1, or 2
    rationale: Mapped[str] = mapped_column(String, nullable=False)
    evidence_refs: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    raw_model_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    evaluation_run: Mapped["EvaluationRun"] = relationship(back_populates="llm_judge_results")
    rubric_dimension: Mapped["RubricDimension"] = relationship(back_populates="llm_judge_results")
