import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.models.evaluation_run import EvaluationRun
from app.db.models.submission import Submission
from app.export.xlsx_builder import build_submissions_workbook
from app.schemas.export import ExportRequest

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("")
async def export_submissions(session: DbSession, body: ExportRequest) -> StreamingResponse:
    result = await session.execute(select(Submission).where(Submission.id.in_(body.submission_ids)))
    submissions = result.scalars().all()

    rows: list[tuple[Submission, EvaluationRun | None]] = []
    for submission in submissions:
        run_result = await session.execute(
            select(EvaluationRun)
            .where(EvaluationRun.submission_id == submission.id)
            .order_by(EvaluationRun.created_at.desc())
            .limit(1)
        )
        rows.append((submission, run_result.scalars().first()))

    workbook_bytes = build_submissions_workbook(rows)

    return StreamingResponse(
        io.BytesIO(workbook_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=affiliate-review-export.xlsx"},
    )
