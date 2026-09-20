import io

from openpyxl import Workbook

from app.db.models.evaluation_run import EvaluationRun
from app.db.models.submission import Submission

COLUMNS = [
    "submission_id",
    "content_type",
    "project_name",
    "product_identifier",
    "affiliate_partner",
    "poc_email",
    "landing_url",
    "status",
    "overall_score",
    "overall_flag",
    "run_status",
    "created_at",
]


def build_submissions_workbook(rows: list[tuple[Submission, EvaluationRun | None]]) -> bytes:
    """Builds an .xlsx approximating the legacy Excel tracker's columns, so
    exported results slot directly into the existing manual review process."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Submissions"
    sheet.append(COLUMNS)

    for submission, run in rows:
        sheet.append(
            [
                str(submission.id),
                submission.content_type,
                submission.project_name or "",
                submission.product_identifier or "",
                submission.affiliate_partner or "",
                submission.poc_email or "",
                submission.landing_url or "",
                submission.status,
                float(run.overall_score) if run and run.overall_score is not None else "",
                run.overall_flag if run else "",
                run.status if run else "",
                submission.created_at.isoformat() if submission.created_at else "",
            ]
        )

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
