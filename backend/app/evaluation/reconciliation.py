import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.config import Settings
from app.db.models.evaluation_run import EvaluationRun
from app.db.session import async_session_factory
from app.evaluation.job_runner import execute_now

logger = logging.getLogger(__name__)


async def _sweep_once(settings: Settings) -> None:
    stale_before = datetime.now(timezone.utc) - timedelta(seconds=settings.RUN_STALE_THRESHOLD_SECONDS)

    async with async_session_factory() as session:
        result = await session.execute(
            select(EvaluationRun).where(
                EvaluationRun.status.in_(["pending", "running"]),
                EvaluationRun.created_at < stale_before,
            )
        )
        stale_runs = result.scalars().all()
        stale_run_ids = [run.id for run in stale_runs]

    for run_id in stale_run_ids:
        logger.warning("Reconciliation sweep re-enqueuing stale evaluation run %s.", run_id)
        try:
            await execute_now(run_id, settings)
        except Exception:  # noqa: BLE001 -- one stuck run must not kill the sweep loop
            logger.exception("Reconciliation retry failed for run %s.", run_id)


async def reconciliation_loop(settings: Settings) -> None:
    """Started as an asyncio background task at FastAPI startup. Covers the
    case where the backend process restarts mid-job: a run stuck in
    pending/running past RUN_STALE_THRESHOLD_SECONDS gets retried from scratch
    (known v1 limitation -- see design doc Section 1)."""
    while True:
        try:
            await _sweep_once(settings)
        except Exception:  # noqa: BLE001 -- the sweep loop itself must never die
            logger.exception("Reconciliation sweep iteration failed.")
        await asyncio.sleep(settings.RECONCILIATION_SWEEP_INTERVAL_SECONDS)
