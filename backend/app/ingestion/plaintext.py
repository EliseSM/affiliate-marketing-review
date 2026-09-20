from app.ingestion.base import IngestionStrategy
from app.ingestion.dto import ParsedSubmission


class PlaintextIngestionStrategy(IngestionStrategy):
    def parse(self, file_bytes: bytes, filename: str) -> list[ParsedSubmission]:
        text = file_bytes.decode("utf-8", errors="replace")
        return [ParsedSubmission(content_type="ad_copy", raw_text=text)]
