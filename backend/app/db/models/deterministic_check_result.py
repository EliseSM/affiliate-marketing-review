import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.db.models.evaluation_run import EvaluationRun
    from app.db.models.rule_definition import RuleDefinition

# result allowed values: pass | fail | warn | not_applicable


class DeterministicCheckResult(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "deterministic_check_results"

    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_runs.id"), nullable=False
    )
    rule_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rule_definitions.id"), nullable=False
    )
    result: Mapped[str] = mapped_column(String, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    evaluation_run: Mapped["EvaluationRun"] = relationship(back_populates="deterministic_check_results")
    rule_definition: Mapped["RuleDefinition"] = relationship(back_populates="deterministic_check_results")
