"""Vendor-agnostic structured-output contract for the LLM-as-judge pass.

dimension_scores is a list keyed by dimension `key`, not fixed named fields,
so adding a 9th rubric dimension to the `rubric_dimensions` table requires
zero changes to this schema or to any code that consumes it.
"""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

ClaimType = Literal["apr", "fee", "reward", "eligibility", "approval_odds", "savings", "other"]
Severity = Literal["low", "medium", "high", "critical"]
EvaluatorResult = Literal["supported", "unsupported", "contradicted", "unverifiable"]


class RubricDimensionInfo(BaseModel):
    """What the prompt builder / provider needs to know about one rubric dimension.
    Mirrors app.db.models.rubric_dimension.RubricDimension without an ORM dependency."""

    key: str
    display_name: str
    description: str
    scoring_scale: dict[str, str]


class DimensionScore(BaseModel):
    dimension_key: str = Field(description="Must match a RubricDimensionInfo.key supplied in the prompt.")
    score: int = Field(ge=0, le=2, description="0 = Fail, 1 = Partial, 2 = Pass.")
    rationale: str


class ExtractedClaim(BaseModel):
    claim_text: str
    claim_type: ClaimType = "other"
    product_identifier: Optional[str] = None
    source_reference: Optional[str] = None
    source_date: Optional[date] = None
    severity: Severity = "low"
    evaluator_result: EvaluatorResult = "unverifiable"


class JudgeResult(BaseModel):
    dimension_scores: list[DimensionScore]
    claims: list[ExtractedClaim] = Field(default_factory=list)


class IncompleteJudgeResultError(ValueError):
    """Raised when the LLM omits a score for one or more active rubric
    dimensions. A missing dimension isn't just an incomplete audit trail --
    pipeline._compute_rollup only inspects dimensions that were actually
    returned, so a real violation on an omitted dimension would silently
    never fail the run. Providers should treat this the same as a schema
    validation failure and retry."""


def validate_dimension_coverage(
    result: JudgeResult, rubric_dimensions: list[RubricDimensionInfo]
) -> None:
    expected = {dim.key for dim in rubric_dimensions}
    returned = {score.dimension_key for score in result.dimension_scores}
    missing = expected - returned
    if missing:
        raise IncompleteJudgeResultError(
            f"LLM response is missing a score for rubric dimension(s): {', '.join(sorted(missing))}"
        )
