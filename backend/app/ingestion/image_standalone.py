import mimetypes

from app.ingestion.base import IngestionStrategy
from app.ingestion.dto import ParsedAsset, ParsedSubmission


class StandaloneImageIngestionStrategy(IngestionStrategy):
    def parse(self, file_bytes: bytes, filename: str) -> list[ParsedSubmission]:
        mime_type, _ = mimetypes.guess_type(filename)
        asset = ParsedAsset(
            asset_type="standalone_image",
            content=file_bytes,
            mime_type=mime_type or "application/octet-stream",
            original_src=filename,
        )
        return [
            ParsedSubmission(
                content_type="ad_copy",
                raw_text="",
                assets=[asset],
            )
        ]
