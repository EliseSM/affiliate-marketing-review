from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedAsset:
    asset_type: str  # inline_image | referenced_image | standalone_image | attachment
    content: bytes
    mime_type: str
    original_src: Optional[str] = None


@dataclass
class ParsedSubmission:
    content_type: str  # web_page | email | ad_copy
    raw_text: str
    raw_html: Optional[str] = None
    source_row_number: Optional[int] = None
    product_identifier: Optional[str] = None
    affiliate_partner: Optional[str] = None
    poc_email: Optional[str] = None
    landing_url: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    assets: list[ParsedAsset] = field(default_factory=list)
