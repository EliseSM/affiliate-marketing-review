import base64
import binascii
import email
import re
from email.message import Message

from bs4 import BeautifulSoup

from app.ingestion.base import IngestionStrategy
from app.ingestion.dto import ParsedAsset, ParsedSubmission

_DATA_URI_PATTERN = re.compile(r"^data:(image/[\w.+-]+);base64,(.*)$", re.DOTALL)


def _extract_images_from_html(soup: BeautifulSoup) -> list[ParsedAsset]:
    assets: list[ParsedAsset] = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        match = _DATA_URI_PATTERN.match(src.strip())
        if match:
            mime_type, b64_data = match.group(1), match.group(2)
            try:
                content = base64.b64decode(b64_data, validate=True)
            except (binascii.Error, ValueError):
                continue
            assets.append(
                ParsedAsset(
                    asset_type="inline_image",
                    content=content,
                    mime_type=mime_type,
                    original_src=src[:120],
                )
            )
        elif src.startswith("http://") or src.startswith("https://"):
            # Per design doc Section 3: don't fetch external images during
            # ingestion (adds latency/failure modes to the upload request).
            # Record the reference only; the evaluation job or the LLM
            # provider (if it supports remote image URLs) can resolve it later.
            assets.append(
                ParsedAsset(
                    asset_type="referenced_image",
                    content=b"",
                    mime_type="application/octet-stream",
                    original_src=src,
                )
            )
    return assets


class HtmlIngestionStrategy(IngestionStrategy):
    def parse(self, file_bytes: bytes, filename: str) -> list[ParsedSubmission]:
        html = file_bytes.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text(separator="\n", strip=True)
        assets = _extract_images_from_html(soup)

        first_link = soup.find("a", href=True)
        landing_url = first_link["href"] if first_link else None

        return [
            ParsedSubmission(
                content_type="web_page",
                raw_text=text,
                raw_html=html,
                landing_url=landing_url,
                assets=assets,
            )
        ]


def _get_body_and_attachments(msg: Message) -> tuple[str, str | None, list[ParsedAsset]]:
    plain_text = ""
    html_text = None
    assets: list[ParsedAsset] = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()

            if content_type == "text/plain" and disposition != "attachment" and not plain_text:
                payload = part.get_payload(decode=True)
                if payload:
                    plain_text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
            elif content_type == "text/html" and disposition != "attachment" and html_text is None:
                payload = part.get_payload(decode=True)
                if payload:
                    html_text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
            elif content_type.startswith("image/"):
                payload = part.get_payload(decode=True)
                if payload:
                    assets.append(
                        ParsedAsset(
                            asset_type="attachment" if disposition == "attachment" else "inline_image",
                            content=payload,
                            mime_type=content_type,
                            original_src=part.get_filename(),
                        )
                    )
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            decoded = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
            if msg.get_content_type() == "text/html":
                html_text = decoded
            else:
                plain_text = decoded

    return plain_text, html_text, assets


class EmailIngestionStrategy(IngestionStrategy):
    def parse(self, file_bytes: bytes, filename: str) -> list[ParsedSubmission]:
        msg = email.message_from_bytes(file_bytes)
        plain_text, html_text, attachment_assets = _get_body_and_attachments(msg)

        html_assets: list[ParsedAsset] = []
        if html_text:
            soup = BeautifulSoup(html_text, "html.parser")
            html_assets = _extract_images_from_html(soup)
            if not plain_text:
                plain_text = soup.get_text(separator="\n", strip=True)

        return [
            ParsedSubmission(
                content_type="email",
                raw_text=plain_text,
                raw_html=html_text,
                metadata={"subject": msg.get("Subject", ""), "from": msg.get("From", "")},
                assets=attachment_assets + html_assets,
            )
        ]
