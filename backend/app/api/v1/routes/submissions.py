import uuid

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, SettingsDep
from app.api.v1.routes.converters import run_to_out
from app.db.models.deterministic_check_result import DeterministicCheckResult
from app.db.models.evaluation_run import EvaluationRun
from app.db.models.llm_judge_result import LLMJudgeResult
from app.db.models.submission import Submission
from app.db.models.submission_asset import SubmissionAsset
from app.db.models.submission_batch import SubmissionBatch
from app.evaluation.job_runner import BackgroundTasksJobRunner
from app.ingestion.factory import UnsupportedFileTypeError, get_strategy_for_filename
from app.schemas.submission import (
    SubmissionAssetOut,
    SubmissionDetailOut,
    SubmissionListItemOut,
    SubmissionUploadResultOut,
)
from app.storage.supabase_storage import SupabaseStorage

router = APIRouter(prefix="/submissions", tags=["submissions"])

# Allow-listed sort fields for GET /submissions. `sort` query values are either
# the bare field name (ascending) or "-field" (descending).
SORT_FIELDS = {
    "created_at": Submission.created_at,
    "project_name": Submission.project_name,
}


def _submission_to_list_item(submission: Submission, latest_run: EvaluationRun | None) -> SubmissionListItemOut:
    return SubmissionListItemOut(
        id=submission.id,
        content_type=submission.content_type,
        product_identifier=submission.product_identifier,
        affiliate_partner=submission.affiliate_partner,
        poc_email=submission.poc_email,
        project_name=submission.project_name,
        status=submission.status,
        created_at=submission.created_at,
        latest_run=run_to_out(latest_run),
    )


async def _latest_run_for(session: DbSession, submission_id: uuid.UUID) -> EvaluationRun | None:
    result = await session.execute(
        select(EvaluationRun)
        .options(
            selectinload(EvaluationRun.llm_judge_results).selectinload(LLMJudgeResult.rubric_dimension),
            selectinload(EvaluationRun.deterministic_check_results).selectinload(
                DeterministicCheckResult.rule_definition
            ),
            selectinload(EvaluationRun.claims),
        )
        .where(EvaluationRun.submission_id == submission_id)
        .order_by(EvaluationRun.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


@router.post("/batch", response_model=SubmissionUploadResultOut)
async def upload_batch(
    session: DbSession,
    settings: SettingsDep,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    product_identifier: str | None = Form(
        default=None,
        description=(
            "Optional override applied to every submission parsed from this file. Excel/CSV "
            "uploads can instead set this per-row via a 'product_identifier' column; this "
            "override exists for single-item formats (HTML/email/plaintext/image) which have no "
            "per-row column to read it from."
        ),
    ),
    poc_email: str | None = Form(
        default=None,
        description=(
            "Optional point-of-contact email for whoever owns this marketing material, so a "
            "reviewer knows who to follow up with. Applied to every submission parsed from this "
            "file. Excel/CSV uploads can instead set this per-row via a 'poc_email' column; this "
            "override exists for single-item formats (HTML/email/plaintext/image)."
        ),
    ),
    project_name: str | None = Form(
        default=None,
        description=(
            "Optional free-text grouping label so resubmissions of the same marketing material "
            "(e.g. an improved version after a failed review) can be filtered together. Applied "
            "to every submission parsed from this file. Excel/CSV uploads can instead set this "
            "per-row via a 'project_name' column; this override exists for single-item formats "
            "(HTML/email/plaintext/image)."
        ),
    ),
) -> SubmissionUploadResultOut:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    if poc_email and "@" not in poc_email:
        raise HTTPException(status_code=400, detail="poc_email must be a valid email address.")

    # Cheap early rejection using the size Starlette already tracked while
    # streaming the multipart body, before we buffer the whole thing.
    if file.size is not None and file.size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB upload limit.",
        )

    try:
        upload_type, strategy = get_strategy_for_filename(file.filename)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_bytes = await file.read()
    # Authoritative check in case `file.size` wasn't populated (e.g. a client
    # that doesn't send a Content-Length per part).
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB upload limit.",
        )

    parsed_submissions = strategy.parse(file_bytes, file.filename)

    storage = SupabaseStorage(settings)
    batch_id = uuid.uuid4()
    raw_storage_path = f"{batch_id}/{file.filename}"
    await storage.upload_file(
        bucket=settings.SUPABASE_RAW_UPLOADS_BUCKET,
        path=raw_storage_path,
        content=file_bytes,
        content_type=file.content_type or "application/octet-stream",
    )

    batch = SubmissionBatch(
        id=batch_id,
        original_filename=file.filename,
        storage_path=raw_storage_path,
        upload_type=upload_type,
        row_count=len(parsed_submissions),
    )
    session.add(batch)
    await session.flush()

    job_runner = BackgroundTasksJobRunner(background_tasks, settings)
    created: list[Submission] = []

    for parsed in parsed_submissions:
        submission = Submission(
            batch_id=batch.id,
            content_type=parsed.content_type,
            source_row_number=parsed.source_row_number,
            raw_text=parsed.raw_text,
            raw_html=parsed.raw_html,
            product_identifier=product_identifier or parsed.product_identifier,
            affiliate_partner=parsed.affiliate_partner,
            poc_email=poc_email or parsed.poc_email,
            project_name=project_name or parsed.project_name,
            landing_url=parsed.landing_url,
            metadata_=parsed.metadata,
        )
        session.add(submission)
        await session.flush()

        for asset_index, asset in enumerate(parsed.assets):
            asset_storage_path = f"{submission.id}/{asset_index}"
            if asset.content:
                await storage.upload_file(
                    bucket=settings.SUPABASE_ASSETS_BUCKET,
                    path=asset_storage_path,
                    content=asset.content,
                    content_type=asset.mime_type,
                )
            session.add(
                SubmissionAsset(
                    submission_id=submission.id,
                    asset_type=asset.asset_type,
                    storage_path=asset_storage_path if asset.content else (asset.original_src or ""),
                    original_src=asset.original_src,
                    mime_type=asset.mime_type,
                )
            )

        run = EvaluationRun(submission_id=submission.id, status="pending")
        session.add(run)
        await session.flush()

        job_runner.enqueue(run.id)
        created.append(submission)

    await session.commit()

    return SubmissionUploadResultOut(
        batch_id=batch.id,
        submissions=[_submission_to_list_item(s, None) for s in created],
    )


@router.get("", response_model=list[SubmissionListItemOut])
async def list_submissions(
    session: DbSession,
    status: str | None = Query(default=None),
    exclude_status: str | None = Query(
        default=None,
        description=(
            "Excludes submissions with this status. Used by the frontend's 'Active' tab to hide "
            "submissions with status='exported' without needing a dedicated tab query param."
        ),
    ),
    content_type: str | None = Query(default=None),
    overall_flag: str | None = Query(default=None),
    project_name: str | None = Query(
        default=None, description="Case-insensitive exact match, for grouping resubmissions."
    ),
    sort: str = Query(
        default="-created_at",
        description=f"Bare field name for ascending, '-field' for descending. Allowed fields: {', '.join(SORT_FIELDS)}.",
    ),
) -> list[SubmissionListItemOut]:
    stmt = select(Submission)
    if status:
        stmt = stmt.where(Submission.status == status)
    if exclude_status:
        stmt = stmt.where(Submission.status != exclude_status)
    if content_type:
        stmt = stmt.where(Submission.content_type == content_type)
    if project_name:
        stmt = stmt.where(func.lower(Submission.project_name) == project_name.lower())

    sort_column = SORT_FIELDS.get(sort.lstrip("-"))
    if sort_column is not None:
        stmt = stmt.order_by(sort_column.desc() if sort.startswith("-") else sort_column.asc())

    result = await session.execute(stmt)
    submissions = result.scalars().all()

    items = []
    for submission in submissions:
        latest_run = await _latest_run_for(session, submission.id)
        if overall_flag and (latest_run is None or latest_run.overall_flag != overall_flag):
            continue
        items.append(_submission_to_list_item(submission, latest_run))
    return items


@router.get("/{submission_id}", response_model=SubmissionDetailOut)
async def get_submission(session: DbSession, submission_id: uuid.UUID) -> SubmissionDetailOut:
    submission = await session.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found.")

    latest_run = await _latest_run_for(session, submission_id)

    assets_result = await session.execute(
        select(SubmissionAsset).where(SubmissionAsset.submission_id == submission_id)
    )
    assets = assets_result.scalars().all()

    return SubmissionDetailOut(
        id=submission.id,
        content_type=submission.content_type,
        product_identifier=submission.product_identifier,
        affiliate_partner=submission.affiliate_partner,
        poc_email=submission.poc_email,
        project_name=submission.project_name,
        status=submission.status,
        created_at=submission.created_at,
        latest_run=run_to_out(latest_run),
        raw_text=submission.raw_text,
        raw_html=submission.raw_html,
        landing_url=submission.landing_url,
        metadata=submission.metadata_,
        assets=[SubmissionAssetOut.model_validate(a) for a in assets],
    )
