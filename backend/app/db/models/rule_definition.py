from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin

if TYPE_CHECKING:
    from app.db.models.claim import Claim
    from app.db.models.deterministic_check_result import DeterministicCheckResult

# category allowed values: deterministic_now | requires_product_terms | hybrid
# severity allowed values: low | medium | high | critical


class RuleDefinition(UUIDPKMixin, Base):
    """Registry table for deterministic checks (guidelines Sections 8 & 13). Rows
    are data; the matching check logic lives in app/evaluation/deterministic/rules,
    keyed by rule_key. Adding a rule = write a function + insert a row here."""

    __tablename__ = "rule_definitions"

    rule_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False, default="medium")
    requires_product_terms: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    deterministic_check_results: Mapped[list["DeterministicCheckResult"]] = relationship(
        back_populates="rule_definition"
    )
    claims: Mapped[list["Claim"]] = relationship(back_populates="rule")
