from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPKMixin

# product_type allowed values: personal_loan | credit_card | mortgage
# Starts empty; populated/maintained by the compliance team. Deterministic checks
# that depend on this table (see rule_definitions.requires_product_terms) return
# `not_applicable` for any product_identifier not found here.


class ProductTerms(UUIDPKMixin, Base):
    __tablename__ = "product_terms"

    product_identifier: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    product_type: Mapped[str] = mapped_column(String, nullable=False)
    apr_min: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    apr_max: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    annual_fee: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    promo_terms: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    eligibility_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source_document_ref: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
