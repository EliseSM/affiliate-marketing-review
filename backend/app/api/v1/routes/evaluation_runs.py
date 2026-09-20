import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, SettingsDep
from app.db.models.evaluation_run import EvaluationRun
from app.evaluation.job_runner import execute_now
from app.schemas.submission import DeterministicCheckResultOut, EvaluationRunOut, LLMJudgeResultOut

router = APIRouter(prefix="/evaluation-runs", tags=["evaluation-runs"])


@router.get("/{run_id}", response_model=EvaluationRunOut)
async def get_evaluation_run(session: DbSession, run_id: uuid.UUID) -> EvaluationRunOut:
    run = await session.get(
        EvaluationRun,
        run_id,
        options=[
            selectinload(EvaluationRun.llm_judge_results),
            selectinload(EvaluationRun.deterministic_check_results),
        ],
        # Forces a fresh reload (and re-application of the eager-load options
        # above) even if this session already has a stale, non-eager-loaded
        # copy of the run in its identity map -- which is exactly the case
        # right after retry_evaluation_run's execute_now() call, since that
        # runs the pipeline in its own separate session. Without this,
        # session.get() silently returns the cached object as-is, and
        # accessing its unloaded relationships below raises MissingGreenlet
        # (async SQLAlchemy forbids implicit lazy loading).
        populate_existing=True,
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")

    return EvaluationRunOut(
        id=run.id,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_message=run.error_message,
        llm_provider=run.llm_provider,
        overall_score=float(run.overall_score) if run.overall_score is not None else None,
        overall_flag=run.overall_flag,
        summary=run.summary,
        llm_judge_results=[LLMJudgeResultOut.model_validate(r) for r in run.llm_judge_results],
        deterministic_check_results=[
            DeterministicCheckResultOut.model_validate(r) for r in run.deterministic_check_results
        ],
    )


@router.post("/{run_id}/retry", response_model=EvaluationRunOut, status_code=202)
async def retry_evaluation_run(session: DbSession, settings: SettingsDep, run_id: uuid.UUID) -> EvaluationRunOut:
    previous_run = await session.get(EvaluationRun, run_id)
    if previous_run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")

    # A fresh EvaluationRun row is created rather than reusing run_id: the
    # child tables (llm_judge_results, deterministic_check_results, claims)
    # are insert-only and llm_judge_results has a unique constraint per
    # (evaluation_run_id, rubric_dimension_id), so re-running the same run_id
    # would collide with its own prior results on the second attempt.
    new_run = EvaluationRun(submission_id=previous_run.submission_id, status="pending")
    session.add(new_run)
    await session.commit()
    await session.refresh(new_run)

    await execute_now(new_run.id, settings)

    return await get_evaluation_run(session, new_run.id)
