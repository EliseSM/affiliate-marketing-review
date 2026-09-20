from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.db.models.submission import Submission

# upload_type allowed values: excel | csv | html | email | plaintext | image


class SubmissionBatch(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "submission_batches"

    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    upload_type: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_by_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    submissions: Mapped[list["Submission"]] = relationship(back_populates="batch")
