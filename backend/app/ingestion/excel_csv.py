import csv
import io
from typing import Optional

from openpyxl import load_workbook

from app.ingestion.base import IngestionStrategy
from app.ingestion.dto import ParsedSubmission

# Known column-header aliases from legacy Excel trackers, lowercased. Any
# column not matched here is preserved verbatim in ParsedSubmission.metadata
# so bulk uploads with inconsistent headers never silently lose data.
COLUMN_ALIASES: dict[str, list[str]] = {
    "content_type": ["content_type", "content type", "type"],
    "raw_text": ["raw_text", "content", "body", "copy", "text"],
    "product_identifier": ["product_identifier", "product", "product id", "product_id"],
    "affiliate_partner": ["affiliate_partner", "partner", "affiliate", "publisher"],
    "landing_url": ["landing_url", "url", "link"],
    "poc_email": [
        "poc_email",
        "poc email",
        "point of contact",
        "point of contact email",
        "owner_email",
        "owner email",
        "contact_email",
        "contact email",
        "submitter_email",
    ],
    "project_name": [
        "project_name",
        "project name",
        "project",
        "material group",
        "campaign group",
    ],
}

DEFAULT_CONTENT_TYPE = "web_page"


def _normalize_headers(headers: list[str]) -> dict[str, int]:
    """Maps canonical field name -> column index, based on COLUMN_ALIASES."""
    lower_headers = [h.strip().lower() if h else "" for h in headers]
    mapping: dict[str, int] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_headers:
                mapping[canonical] = lower_headers.index(alias)
                break
    return mapping


def _row_to_submission(
    headers: list[str], row: list[Optional[str]], mapping: dict[str, int], row_number: int
) -> ParsedSubmission:
    def get(field: str) -> Optional[str]:
        idx = mapping.get(field)
        if idx is None or idx >= len(row):
            return None
        value = row[idx]
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    metadata = {}
    mapped_indices = set(mapping.values())
    for idx, header in enumerate(headers):
        if idx not in mapped_indices and idx < len(row) and row[idx] not in (None, ""):
            metadata[header or f"column_{idx}"] = row[idx]

    return ParsedSubmission(
        content_type=get("content_type") or DEFAULT_CONTENT_TYPE,
        raw_text=get("raw_text") or "",
        source_row_number=row_number,
        product_identifier=get("product_identifier"),
        affiliate_partner=get("affiliate_partner"),
        landing_url=get("landing_url"),
        poc_email=get("poc_email"),
        project_name=get("project_name"),
        metadata=metadata,
    )


class ExcelIngestionStrategy(IngestionStrategy):
    def parse(self, file_bytes: bytes, filename: str) -> list[ParsedSubmission]:
        workbook = load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
        sheet = workbook.active
        rows_iter = sheet.iter_rows(values_only=True)

        try:
            headers = [str(h) if h is not None else "" for h in next(rows_iter)]
        except StopIteration:
            return []

        mapping = _normalize_headers(headers)
        submissions = []
        for row_number, row in enumerate(rows_iter, start=2):  # row 1 is the header
            if row is None or all(v is None for v in row):
                continue
            submissions.append(_row_to_submission(headers, list(row), mapping, row_number))
        return submissions


class CsvIngestionStrategy(IngestionStrategy):
    def parse(self, file_bytes: bytes, filename: str) -> list[ParsedSubmission]:
        text = file_bytes.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return []

        headers = rows[0]
        mapping = _normalize_headers(headers)
        submissions = []
        for row_number, row in enumerate(rows[1:], start=2):
            if not any(cell.strip() for cell in row if cell):
                continue
            submissions.append(_row_to_submission(headers, row, mapping, row_number))
        return submissions
