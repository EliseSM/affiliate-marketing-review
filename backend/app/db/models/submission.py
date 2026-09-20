import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.db.models.claim import Claim
    from app.db.models.evaluation_run import EvaluationRun
    from app.db.models.submission_asset import SubmissionAsset
    from app.db.models.submission_batch import SubmissionBatch

# content_type allowed values: web_page | email | ad_copy
# status allowed values: ingested | evaluating | evaluated | error


class Submission(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "submissions"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submission_batches.id"), nullable=False
    )
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    source_row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    raw_text: Mapped[str] = mapped_column(String, nullable=False)
    raw_html: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    product_identifier: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    affiliate_partner: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    landing_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Point-of-contact email for whoever owns this piece of marketing material,
    # so a reviewer knows who to follow up with. Captured at upload time (see
    # POST /submissions/batch and the excel/csv poc_email column alias).
    poc_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ingested")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    batch: Mapped["SubmissionBatch"] = relationship(back_populates="submissions")
    assets: Mapped[list["SubmissionAsset"]] = relationship(back_populates="submission")
    evaluation_runs: Mapped[list["EvaluationRun"]] = relationship(back_populates="submission")
    claims: Mapped[list["Claim"]] = relationship(back_populates="submission")
