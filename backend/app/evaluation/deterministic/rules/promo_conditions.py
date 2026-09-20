from typing import Optional

from app.evaluation.deterministic.dto import ProductTermsInput, RuleResult, SubmissionInput
from app.evaluation.deterministic.registry import register_rule


@register_rule("promo_conditions_present")
def check_promo_conditions_present(
    submission: SubmissionInput, config: Optional[dict], product_terms: Optional[ProductTermsInput]
) -> tuple[RuleResult, dict]:
    """Presence-only heuristic (Section 13): if promotional language is used,
    some qualifying-condition language should be present too. Whether the
    conditions are actually *correct* and complete is a job for the LLM pass
    (promo_conditions_present is a `hybrid` rule per rule_definitions.category)."""
    config = config or {}
    promo_markers: list[str] = config.get("promo_markers", [])
    condition_markers: list[str] = config.get("condition_markers", [])

    haystack = (submission.raw_text or "").lower()

    has_promo = any(marker.lower() in haystack for marker in promo_markers)
    if not has_promo:
        return "not_applicable", {"reason": "No promotional/intro-offer language detected."}

    has_conditions = any(marker.lower() in haystack for marker in condition_markers)
    if has_conditions:
        return "pass", {"promo_markers_found": [m for m in promo_markers if m.lower() in haystack]}

    return "fail", {
        "reason": "Promotional language found without qualifying condition language nearby.",
        "promo_markers_found": [m for m in promo_markers if m.lower() in haystack],
    }
