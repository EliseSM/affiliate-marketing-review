import logging
import uuid
from abc import ABC, abstractmethod

from fastapi import BackgroundTasks

from app.config import Settings, get_settings
from app.db.session import async_session_factory
from app.evaluation.pipeline import run_evaluation

logger = logging.getLogger(__name__)


class JobRunner(ABC):
    """Seam for how evaluation runs are executed. v1 uses FastAPI
    BackgroundTasks (see BackgroundTasksJobRunner); swapping to a real queue
    (Celery/RQ/Arq) later means implementing this interface, with no changes
    to pipeline.py or the API routes that call enqueue()."""

    @abstractmethod
    def enqueue(self, run_id: uuid.UUID) -> None:
        raise NotImplementedError


async def _execute(run_id: uuid.UUID, settings: Settings) -> None:
    async with async_session_factory() as session:
        await run_evaluation(run_id, session, settings)


class BackgroundTasksJobRunner(JobRunner):
    def __init__(self, background_tasks: BackgroundTasks, settings: Settings | None = None) -> None:
        self._background_tasks = background_tasks
        self._settings = settings or get_settings()

    def enqueue(self, run_id: uuid.UUID) -> None:
        self._background_tasks.add_task(_execute, run_id, self._settings)


async def execute_now(run_id: uuid.UUID, settings: Settings | None = None) -> None:
    """Used by the reconciliation sweep and the manual retry endpoint, where
    there's no live BackgroundTasks/request context to attach to."""
    await _execute(run_id, settings or get_settings())
