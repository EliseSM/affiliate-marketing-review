from pathlib import Path

from app.ingestion.excel_csv import CsvIngestionStrategy
from app.ingestion.factory import get_strategy_for_filename
from app.ingestion.html_email import HtmlIngestionStrategy
from app.ingestion.plaintext import PlaintextIngestionStrategy

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_csv_ingestion_parses_one_submission_per_row():
    file_bytes = (FIXTURES_DIR / "sample.csv").read_bytes()

    submissions = CsvIngestionStrategy().parse(file_bytes, "sample.csv")

    assert len(submissions) == 2

    first = submissions[0]
    assert first.content_type == "web_page"
    assert "5.99% APR" in first.raw_text
    assert first.product_identifier == "personal-loan-a"
    assert first.affiliate_partner == "BestRatesCo"
    assert first.landing_url == "https://example.com/apply"
    assert first.metadata.get("campaign") == "spring-promo"
    assert first.poc_email == "marketer@bestratesco.example"

    second = submissions[1]
    assert second.content_type == "email"
    assert "Guaranteed approval" in second.raw_text
    assert second.poc_email is None


def test_html_ingestion_extracts_text_inline_image_and_landing_url():
    file_bytes = (FIXTURES_DIR / "sample.html").read_bytes()

    submissions = HtmlIngestionStrategy().parse(file_bytes, "sample.html")

    assert len(submissions) == 1
    submission = submissions[0]
    assert submission.content_type == "web_page"
    assert "5.99% to 24.99% APR" in submission.raw_text
    assert submission.landing_url == "https://example.com/apply"

    assert len(submission.assets) == 1
    asset = submission.assets[0]
    assert asset.asset_type == "inline_image"
    assert asset.mime_type == "image/png"
    assert len(asset.content) > 0


def test_plaintext_ingestion_returns_single_submission():
    file_bytes = (FIXTURES_DIR / "sample.txt").read_bytes()

    submissions = PlaintextIngestionStrategy().parse(file_bytes, "sample.txt")

    assert len(submissions) == 1
    assert "competitive rate" in submissions[0].raw_text


def test_factory_dispatches_by_extension():
    upload_type, strategy = get_strategy_for_filename("report.CSV")
    assert upload_type == "csv"
    assert isinstance(strategy, CsvIngestionStrategy)

    upload_type, strategy = get_strategy_for_filename("landing.html")
    assert upload_type == "html"
    assert isinstance(strategy, HtmlIngestionStrategy)
