from app.ingestion.base import IngestionStrategy
from app.ingestion.excel_csv import CsvIngestionStrategy, ExcelIngestionStrategy
from app.ingestion.html_email import EmailIngestionStrategy, HtmlIngestionStrategy
from app.ingestion.image_standalone import StandaloneImageIngestionStrategy
from app.ingestion.plaintext import PlaintextIngestionStrategy

_EXTENSION_MAP: dict[str, tuple[str, IngestionStrategy]] = {
    ".xlsx": ("excel", ExcelIngestionStrategy()),
    ".xls": ("excel", ExcelIngestionStrategy()),
    ".csv": ("csv", CsvIngestionStrategy()),
    ".html": ("html", HtmlIngestionStrategy()),
    ".htm": ("html", HtmlIngestionStrategy()),
    ".eml": ("email", EmailIngestionStrategy()),
    ".txt": ("plaintext", PlaintextIngestionStrategy()),
    ".jpg": ("image", StandaloneImageIngestionStrategy()),
    ".jpeg": ("image", StandaloneImageIngestionStrategy()),
    ".png": ("image", StandaloneImageIngestionStrategy()),
    ".gif": ("image", StandaloneImageIngestionStrategy()),
}


class UnsupportedFileTypeError(ValueError):
    pass


def get_strategy_for_filename(filename: str) -> tuple[str, IngestionStrategy]:
    """Returns (upload_type, strategy) based on file extension. upload_type
    matches submission_batches.upload_type's allowed values."""
    lower_name = filename.lower()
    for extension, (upload_type, strategy) in _EXTENSION_MAP.items():
        if lower_name.endswith(extension):
            return upload_type, strategy
    raise UnsupportedFileTypeError(f"Unsupported file type for {filename!r}.")
