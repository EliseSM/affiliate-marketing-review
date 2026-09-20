from fastapi import APIRouter

from app.api.v1.routes import evaluation_runs, exports, rubric, rules, submissions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(submissions.router)
api_router.include_router(evaluation_runs.router)
api_router.include_router(exports.router)
api_router.include_router(rubric.router)
api_router.include_router(rules.router)
