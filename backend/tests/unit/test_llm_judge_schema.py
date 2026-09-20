import pytest

from app.evaluation.llm_judge.schema import (
    DimensionScore,
    IncompleteJudgeResultError,
    JudgeResult,
    RubricDimensionInfo,
    validate_dimension_coverage,
)

DIMENSIONS = [
    RubricDimensionInfo(key="truthfulness", display_name="Truthfulness", description="", scoring_scale={}),
    RubricDimensionInfo(key="disclosure", display_name="Disclosure", description="", scoring_scale={}),
]


def test_validate_dimension_coverage_passes_when_all_dimensions_scored():
    result = JudgeResult(
        dimension_scores=[
            DimensionScore(dimension_key="truthfulness", score=2, rationale="ok"),
            DimensionScore(dimension_key="disclosure", score=2, rationale="ok"),
        ]
    )

    validate_dimension_coverage(result, DIMENSIONS)  # should not raise


def test_validate_dimension_coverage_raises_when_a_dimension_is_missing():
    result = JudgeResult(
        dimension_scores=[DimensionScore(dimension_key="truthfulness", score=2, rationale="ok")]
    )

    with pytest.raises(IncompleteJudgeResultError, match="disclosure"):
        validate_dimension_coverage(result, DIMENSIONS)


def test_validate_dimension_coverage_ignores_extra_unknown_dimensions():
    # An unrecognized dimension_key is handled elsewhere (pipeline.py logs and
    # discards it) -- coverage validation only cares that nothing expected is missing.
    result = JudgeResult(
        dimension_scores=[
            DimensionScore(dimension_key="truthfulness", score=2, rationale="ok"),
            DimensionScore(dimension_key="disclosure", score=2, rationale="ok"),
            DimensionScore(dimension_key="some_future_dimension", score=1, rationale="ok"),
        ]
    )

    validate_dimension_coverage(result, DIMENSIONS)  # should not raise
