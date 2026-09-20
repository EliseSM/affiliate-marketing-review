import re
from typing import Optional

from app.evaluation.deterministic.dto import ProductTermsInput, RuleResult, SubmissionInput
from app.evaluation.deterministic.registry import register_rule


def _phrase_pattern(phrase: str) -> re.Pattern:
    # Word-boundary-aware, case-insensitive; phrases may contain internal
    # spaces/hyphens which \b still handles correctly since they aren't word chars.
    escaped = re.escape(phrase)
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


@register_rule("prohibited_phrase_blocklist")
def check_prohibited_phrases(
    submission: SubmissionInput, config: Optional[dict], product_terms: Optional[ProductTermsInput]
) -> tuple[RuleResult, dict]:
    phrases: list[str] = (config or {}).get("phrases", [])
    haystack = submission.raw_text or ""

    matches = []
    for phrase in phrases:
        pattern = _phrase_pattern(phrase)
        for match in pattern.finditer(haystack):
            matches.append({"phrase": phrase, "matched_text": match.group(0), "offset": match.start()})

    if matches:
        return "fail", {"matches": matches}
    return "pass", {"matches": []}
