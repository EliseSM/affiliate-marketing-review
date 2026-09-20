import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models.claim import Claim
from app.db.models.deterministic_check_result import DeterministicCheckResult
from app.db.models.evaluation_run import EvaluationRun
from app.db.models.llm_judge_result import LLMJudgeResult
from app.db.models.product_terms import ProductTerms
from app.db.models.rubric_dimension import RubricDimension
from app.db.models.rule_definition import RuleDefinition
from app.db.models.submission import Submission
from app.db.models.submission_asset import SubmissionAsset
from app.evaluation.deterministic.dto import ProductTermsInput, RuleOutcome, SubmissionInput
from app.evaluation.deterministic.engine import RuleEngine
from app.evaluation.llm_judge.provider_factory import get_provider
from app.evaluation.llm_judge.schema import DimensionScore, JudgeResult, RubricDimensionInfo
from app.evaluation.summary_builder import build_run_summary
from app.storage.supabase_storage import SupabaseStorage

logger = logging.getLogger(__name__)

# overall_flag rollup rule (documented here since it's not defined anywhere else):
#   - any LLM dimension scored 0, or any deterministic result == "fail"  -> "fail"
#   - else any LLM dimension scored 1, or any deterministic result == "warn" -> "needs_review"
#   - else -> "pass"
# This is intentionally conservative: a single hard failure anywhere fails the whole run.


def _compute_rollup(
    dimension_scores: list[DimensionScore], rule_outcomes: list[RuleOutcome]
) -> tuple[float | None, str]:
    if not dimension_scores and not rule_outcomes:
        return None, "needs_review"

    has_fail = any(score.score == 0 for score in dimension_scores) or any(
        outcome.result == "fail" for outcome in rule_outcomes
    )
    has_warn = any(score.score == 1 for score in dimension_scores) or any(
        outcome.result == "warn" for outcome in rule_outcomes
    )

    if has_fail:
        flag = "fail"
    elif has_warn:
        flag = "needs_review"
    else:
        flag = "pass"

    avg_score = (
        sum(score.score for score in dimension_scores) / len(dimension_scores)
        if dimension_scores
        else None
    )
    return avg_score, flag


async def _load_images(
    session: AsyncSession, submission_id: uuid.UUID, settings: Settings
) -> list[bytes]:
    result = await session.execute(
        select(SubmissionAsset).where(
            SubmissionAsset.submission_id == submission_id,
            SubmissionAsset.asset_type.in_(["inline_image", "standalone_image", "attachment"]),
        )
    )
    assets = result.scalars().all()[: settings.LLM_MAX_IMAGES_PER_SUBMISSION]

    storage = SupabaseStorage(settings)
    images: list[bytes] = []
    for asset in assets:
        try:
            images.append(
                await storage.download(bucket=settings.SUPABASE_ASSETS_BUCKET, path=asset.storage_path)
            )
        except Exception:  # noqa: BLE001 -- a single unreachable asset shouldn't fail the whole run
            logger.exception("Failed to download asset %s for LLM judging; skipping.", asset.id)
    return images


async def run_evaluation(run_id: uuid.UUID, session: AsyncSession, settings: Settings) -> None:
    """Orchestrates the deterministic rule engine and the LLM-as-judge pass for
    one evaluation run, persists all results, and computes the run's overall
    rollup. This is the seam where the two independent evaluation paths meet
    (design doc Section 3) -- it should stay a thin orchestrator."""
    run = await session.get(EvaluationRun, run_id)
    if run is None:
        logger.error("run_evaluation called with unknown run_id=%s", run_id)
        return

    submission = await session.get(Submission, run.submission_id)
    if submission is None:
        run.status = "failed"
        run.error_message = f"Submission {run.submission_id} not found."
        await session.commit()
        return

    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    submission.status = "evaluating"
    await session.commit()

    try:
        rule_defs = (
            (await session.execute(select(RuleDefinition).where(RuleDefinition.active.is_(True))))
            .scalars()
            .all()
        )

        product_terms_row = None
        if submission.product_identifier:
            product_terms_row = (
                await session.execute(
                    select(ProductTerms).where(
                        ProductTerms.product_identifier == submission.product_identifier
                    )
                )
            ).scalar_one_or_none()

        submission_input = SubmissionInput(
            raw_text=submission.raw_text,
            raw_html=submission.raw_html,
            product_identifier=submission.product_identifier,
        )
        product_terms_input = (
            ProductTermsInput(
                product_identifier=product_terms_row.product_identifier,
                apr_min=float(product_terms_row.apr_min) if product_terms_row.apr_min is not None else None,
                apr_max=float(product_terms_row.apr_max) if product_terms_row.apr_max is not None else None,
                annual_fee=(
                    float(product_terms_row.annual_fee) if product_terms_row.annual_fee is not None else None
                ),
            )
            if product_terms_row
            else None
        )

        rule_outcomes = RuleEngine().run(submission_input, rule_defs, product_terms_input)
        for outcome in rule_outcomes:
            session.add(
                DeterministicCheckResult(
                    evaluation_run_id=run.id,
                    rule_definition_id=outcome.rule_definition_id,
                    result=outcome.result,
                    evidence=outcome.evidence,
                )
            )

        rubric_rows = (
            (
                await session.execute(
                    select(RubricDimension)
                    .where(RubricDimension.active.is_(True))
                    .order_by(RubricDimension.sort_order)
                )
            )
            .scalars()
            .all()
        )
        rubric_by_key = {dim.key: dim for dim in rubric_rows}
        rubric_infos = [
            RubricDimensionInfo(
                key=dim.key,
                display_name=dim.display_name,
                description=dim.description,
                scoring_scale=dim.scoring_scale,
            )
            for dim in rubric_rows
        ]

        prohibited_rule = next(
            (rule for rule in rule_defs if rule.rule_key == "prohibited_phrase_blocklist"), None
        )
        prohibited_phrases: list[str] = (
            (prohibited_rule.config or {}).get("phrases", []) if prohibited_rule else []
        )

        images = await _load_images(session, submission.id, settings)

        provider = get_provider(settings)
        judge_result: JudgeResult = await provider.judge(
            text=submission.raw_text,
            images=images,
            rubric_dimensions=rubric_infos,
            prohibited_phrases=prohibited_phrases,
        )

        for score in judge_result.dimension_scores:
            dimension = rubric_by_key.get(score.dimension_key)
            if dimension is None:
                logger.warning("LLM returned unknown dimension_key=%s; discarding.", score.dimension_key)
                continue
            session.add(
                LLMJudgeResult(
                    evaluation_run_id=run.id,
                    rubric_dimension_id=dimension.id,
                    score=score.score,
                    rationale=score.rationale,
                )
            )

        for claim in judge_result.claims:
            session.add(
                Claim(
                    submission_id=submission.id,
                    evaluation_run_id=run.id,
                    claim_text=claim.claim_text,
                    claim_type=claim.claim_type,
                    product_identifier=claim.product_identifier,
                    source_reference=claim.source_reference,
                    source_date=claim.source_date,
                    severity=claim.severity,
                    evaluator_result=claim.evaluator_result,
                )
            )

        # Deterministic rules that found a concrete mismatch also contribute a claim
        # row, satisfying the Section 16 model from both evaluation paths.
        for outcome in rule_outcomes:
            if outcome.result == "fail" and outcome.evidence:
                rule_def = next((r for r in rule_defs if r.id == outcome.rule_definition_id), None)
                session.add(
                    Claim(
                        submission_id=submission.id,
                        evaluation_run_id=run.id,
                        claim_text=f"Deterministic rule '{outcome.rule_key}' failed.",
                        claim_type="other",
                        product_identifier=submission.product_identifier,
                        rule_id=outcome.rule_definition_id,
                        severity=rule_def.severity if rule_def else "medium",
                        evaluator_result="unsupported",
                    )
                )

        overall_score, overall_flag = _compute_rollup(judge_result.dimension_scores, rule_outcomes)
        run.overall_score = overall_score
        run.overall_flag = overall_flag
        run.summary = build_run_summary(
            overall_flag=overall_flag,
            dimension_scores=judge_result.dimension_scores,
            rubric_by_key=rubric_by_key,
            rule_outcomes=rule_outcomes,
            rule_defs_by_id={rule.id: rule for rule in rule_defs},
            claims=judge_result.claims,
        )
        run.llm_provider = f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}"
        run.deterministic_ruleset_version = "v1"
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        submission.status = "evaluated"
        await session.commit()

    except Exception as exc:  # noqa: BLE001 -- must always leave the run in a terminal state
        logger.exception("Evaluation run %s failed.", run_id)
        # If the try block failed partway through a flush (e.g. a duplicate-key
        # error on insert), the session's transaction is already rolled back at
        # the DB level and any objects touched since the last commit are in an
        # inconsistent in-memory state. Committing again without first calling
        # rollback() here would raise PendingRollbackError instead of ever
        # persisting "failed", leaving the run stuck in "running" forever.
        await session.rollback()
        run = await session.get(EvaluationRun, run_id)
        if run is not None:
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            submission = await session.get(Submission, run.submission_id)
            if submission is not None:
                submission.status = "error"
        await session.commit()
