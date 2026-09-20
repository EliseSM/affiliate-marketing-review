from typing import Optional

from app.evaluation.deterministic.dto import ProductTermsInput, RuleResult, SubmissionInput
from app.evaluation.deterministic.registry import register_rule


@register_rule("disclosure_presence")
def check_disclosure_presence(
    submission: SubmissionInput, config: Optional[dict], product_terms: Optional[ProductTermsInput]
) -> tuple[RuleResult, dict]:
    config = config or {}
    disclosure_markers: list[str] = config.get("disclosure_markers", [])
    link_markers: list[str] = config.get("link_markers", [])
    proximity_chars: int = config.get("proximity_chars", 400)

    haystack = (submission.raw_html or submission.raw_text or "").lower()

    link_positions = [haystack.find(marker.lower()) for marker in link_markers]
    link_positions = [pos for pos in link_positions if pos != -1]

    if not link_positions:
        # No recommendation/link markers found at all -- nothing to attach a
        # disclosure to, so this check doesn't apply to this piece of content.
        return "not_applicable", {"reason": "No recommendation/link markers found in content."}

    disclosure_positions = [haystack.find(marker.lower()) for marker in disclosure_markers]
    disclosure_positions = [pos for pos in disclosure_positions if pos != -1]

    if not disclosure_positions:
        return "fail", {"reason": "No affiliate disclosure language found anywhere in the content."}

    for link_pos in link_positions:
        for disc_pos in disclosure_positions:
            if abs(link_pos - disc_pos) <= proximity_chars:
                return "pass", {
                    "link_offset": link_pos,
                    "disclosure_offset": disc_pos,
                    "distance": abs(link_pos - disc_pos),
                }

    return "warn", {
        "reason": "Disclosure language found but not within proximity of any recommendation/link.",
        "link_positions": link_positions,
        "disclosure_positions": disclosure_positions,
    }
