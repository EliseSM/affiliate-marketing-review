"""Shared ORM -> API-schema conversion, used by both submissions.py and
evaluation_runs.py so the two routes can never drift out of sync on this
shape again. Callers must eager-load evaluation_run.llm_judge_results ->
.rubric_dimension, evaluation_run.deterministic_check_results ->
.rule_definition, and evaluation_run.claims before calling this -- it only
reads already-loaded relationship attributes, never lazy-loads.
"""

from app.db.models.evaluation_run import EvaluationRun
from app.schemas.submission import (
    ClaimOut,
    DeterministicCheckResultOut,
    EvaluationRunOut,
    LLMJudgeResultOut,
)


def run_to_out(run: EvaluationRun | None) -> EvaluationRunOut | None:
    if run is None:
        return None
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
        judge_results=[
            LLMJudgeResultOut(
                dimension_key=result.rubric_dimension.key,
                display_name=result.rubric_dimension.display_name,
                score=result.score,
                rationale=result.rationale,
            )
            for result in run.llm_judge_results
        ],
        deterministic_results=[
            DeterministicCheckResultOut(
                rule_key=result.rule_definition.rule_key,
                display_name=result.rule_definition.display_name,
                result=result.result,
                evidence=result.evidence,
            )
            for result in run.deterministic_check_results
        ],
        claims=[ClaimOut.model_validate(claim) for claim in run.claims],
    )
