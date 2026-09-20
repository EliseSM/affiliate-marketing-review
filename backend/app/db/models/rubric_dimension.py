from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin

if TYPE_CHECKING:
    from app.db.models.claim import Claim
    from app.db.models.llm_judge_result import LLMJudgeResult


class RubricDimension(UUIDPKMixin, Base):
    """Registry table seeded from guidelines Section 12. Rows are data, not code,
    so a new rubric dimension can be added without a code change."""

    __tablename__ = "rubric_dimensions"

    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    scoring_scale: Mapped[dict] = mapped_column(JSONB, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    llm_judge_results: Mapped[list["LLMJudgeResult"]] = relationship(back_populates="rubric_dimension")
    claims: Mapped[list["Claim"]] = relationship(back_populates="rubric_dimension")
