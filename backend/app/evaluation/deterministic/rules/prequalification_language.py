from typing import Optional

from app.evaluation.deterministic.dto import ProductTermsInput, RuleResult, SubmissionInput
from app.evaluation.deterministic.registry import register_rule


@register_rule("prequalification_not_approval")
def check_prequalification_not_approval(
    submission: SubmissionInput, config: Optional[dict], product_terms: Optional[ProductTermsInput]
) -> tuple[RuleResult, dict]:
    """Cheap keyword co-occurrence pass (Section 6/13): flags content that
    mentions prequalification alongside language that overreaches into
    guaranteed/final approval. The genuinely semantic distinction (e.g. subtle
    phrasing that implies approval without these exact words) is left to the
    LLM pass -- this rule is a hybrid check, not a full solution."""
    config = config or {}
    prequalification_markers: list[str] = config.get("prequalification_markers", [])
    overreach_markers: list[str] = config.get("overreach_markers", [])

    haystack = (submission.raw_text or "").lower()

    has_prequalification = any(marker.lower() in haystack for marker in prequalification_markers)
    if not has_prequalification:
        return "not_applicable", {"reason": "No prequalification/preapproval language detected."}

    overreach_hits = [marker for marker in overreach_markers if marker.lower() in haystack]
    if overreach_hits:
        return "fail", {
            "reason": "Prequalification language co-occurs with approval/guarantee language.",
            "overreach_markers_found": overreach_hits,
        }

    return "pass", {}
