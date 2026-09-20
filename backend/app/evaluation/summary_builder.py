"""Builds the structured, human-readable evaluation_runs.summary payload.

Called once from app/evaluation/pipeline.py right after the deterministic and
LLM-judge passes complete, using only data already computed in that request --
never called again later. This is what guarantees the frontend can display
"why a run failed" / "what claims to double-check" from already-stored data
instead of regenerating an explanation whenever a user opens the dropdown.
"""

import uuid

from app.db.models.rubric_dimension import RubricDimension
from app.db.models.rule_definition import RuleDefinition
from app.evaluation.deterministic.dto import RuleOutcome
from app.evaluation.llm_judge.schema import DimensionScore, ExtractedClaim


def _format_evidence(evidence: dict) -> str:
    if not evidence:
        return "no additional evidence recorded"

    reason = evidence.get("reason")
    if reason:
        return reason

    matches = evidence.get("matches")
    if matches:
        phrases = sorted({m.get("phrase", "") for m in matches if m.get("phrase")})
        if phrases:
            return f"matched prohibited phrase(s): {', '.join(phrases)}"

    mismatches = evidence.get("mismatches")
    if mismatches:
        parts = []
        for mismatch in mismatches:
            if mismatch.get("claim_type") == "apr":
                expected_range = mismatch.get("expected_range", [None, None])
                parts.append(
                    f"stated APR {mismatch.get('claimed')}% is outside the expected "
                    f"{expected_range[0]}%-{expected_range[1]}% range"
                )
            elif mismatch.get("claim_type") == "annual_fee":
                parts.append(
                    f"stated annual fee ${mismatch.get('claimed')} does not match the "
                    f"expected ${mismatch.get('expected')}"
                )
            else:
                parts.append(str(mismatch))
        return "; ".join(parts)

    return str(evidence)


def build_run_summary(
    *,
    overall_flag: str,
    dimension_scores: list[DimensionScore],
    rubric_by_key: dict[str, RubricDimension],
    rule_outcomes: list[RuleOutcome],
    rule_defs_by_id: dict[uuid.UUID, RuleDefinition],
    claims: list[ExtractedClaim],
) -> dict:
    reasons: list[str] = []

    for score in dimension_scores:
        if score.score < 2:
            dimension = rubric_by_key.get(score.dimension_key)
            label = dimension.display_name if dimension else score.dimension_key
            reasons.append(f"{label} ({score.score}/2): {score.rationale}")

    for outcome in rule_outcomes:
        if outcome.result in ("fail", "warn"):
            rule_def = rule_defs_by_id.get(outcome.rule_definition_id)
            label = rule_def.display_name if rule_def else outcome.rule_key
            reasons.append(f"{label} ({outcome.result}): {_format_evidence(outcome.evidence)}")

    claims_to_verify = [
        {
            "claim_text": claim.claim_text,
            "claim_type": claim.claim_type,
            "product_identifier": claim.product_identifier,
            "severity": claim.severity,
        }
        for claim in claims
    ]

    return {
        "outcome": overall_flag,
        "reasons": reasons,
        "claims_to_verify": claims_to_verify,
    }
