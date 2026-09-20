import re
from typing import Optional

from app.evaluation.deterministic.dto import ProductTermsInput, RuleResult, SubmissionInput
from app.evaluation.deterministic.registry import register_rule

_APR_PATTERN = re.compile(r"(\d{1,2}(?:\.\d{1,2})?)\s*%")
# The trailing qualifier is required (not optional) so this only matches genuine
# annual-fee mentions, not every dollar figure in the content (loan amounts, bonus
# amounts, balances, etc. would otherwise be misread as an annual-fee claim).
_FEE_PATTERN = re.compile(r"\$(\d{1,4}(?:\.\d{2})?)\s*(?:annual\s+fee|per\s+year)", re.IGNORECASE)


@register_rule("apr_matches_product_terms")
def check_apr_matches_product_terms(
    submission: SubmissionInput, config: Optional[dict], product_terms: Optional[ProductTermsInput]
) -> tuple[RuleResult, dict]:
    """Genuinely best-effort v1 check: extracts bare APR/fee-looking numbers
    via regex and compares them to the product_terms table. Degrades to
    `not_applicable` whenever the product isn't in the table yet, or when the
    content doesn't reference a product_identifier at all -- this is expected
    until product_terms is populated, per the design doc."""
    if submission.product_identifier is None:
        return "not_applicable", {"reason": "Submission has no product_identifier to look up."}

    if product_terms is None:
        return "not_applicable", {
            "reason": f"No product_terms row found for {submission.product_identifier!r}.",
        }

    text = submission.raw_text or ""
    apr_claims = [float(m.group(1)) for m in _APR_PATTERN.finditer(text)]
    fee_claims = [float(m.group(1)) for m in _FEE_PATTERN.finditer(text)]

    mismatches = []

    if apr_claims and product_terms.apr_min is not None and product_terms.apr_max is not None:
        for claim in apr_claims:
            if not (product_terms.apr_min <= claim <= product_terms.apr_max):
                mismatches.append(
                    {
                        "claim_type": "apr",
                        "claimed": claim,
                        "expected_range": [product_terms.apr_min, product_terms.apr_max],
                    }
                )

    if fee_claims and product_terms.annual_fee is not None:
        for claim in fee_claims:
            if claim != float(product_terms.annual_fee):
                mismatches.append(
                    {
                        "claim_type": "annual_fee",
                        "claimed": claim,
                        "expected": float(product_terms.annual_fee),
                    }
                )

    if mismatches:
        return "fail", {"mismatches": mismatches}

    if not apr_claims and not fee_claims:
        return "not_applicable", {"reason": "No APR/fee-like claims found in content to check."}

    return "pass", {"apr_claims_checked": apr_claims, "fee_claims_checked": fee_claims}
