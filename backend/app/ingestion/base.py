from abc import ABC, abstractmethod

from app.ingestion.dto import ParsedSubmission


class IngestionStrategy(ABC):
    @abstractmethod
    def parse(self, file_bytes: bytes, filename: str) -> list[ParsedSubmission]:
        """Parse an uploaded file into one or more ParsedSubmission objects.
        Excel/CSV strategies return one per row; single-content strategies
        (HTML/email/plaintext/image) return exactly one."""
        raise NotImplementedError
