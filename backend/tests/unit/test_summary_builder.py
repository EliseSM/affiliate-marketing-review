import uuid

from app.db.models.rubric_dimension import RubricDimension
from app.db.models.rule_definition import RuleDefinition
from app.evaluation.deterministic.dto import RuleOutcome
from app.evaluation.llm_judge.schema import DimensionScore, ExtractedClaim
from app.evaluation.summary_builder import build_run_summary


def _dimension(key: str, display_name: str) -> RubricDimension:
    return RubricDimension(
        id=uuid.uuid4(),
        key=key,
        display_name=display_name,
        description="",
        scoring_scale={},
        active=True,
        sort_order=0,
    )


def _rule(display_name: str) -> RuleDefinition:
    return RuleDefinition(
        id=uuid.uuid4(),
        rule_key=display_name.lower().replace(" ", "_"),
        display_name=display_name,
        description="",
        category="deterministic_now",
        severity="high",
        requires_product_terms=False,
        active=True,
        config=None,
    )


def test_summary_lists_reasons_for_failing_dimensions_and_rules():
    disclosure_dim = _dimension("disclosure", "Disclosure")
    passing_dim = _dimension("truthfulness", "Truthfulness")
    blocklist_rule = _rule("Prohibited phrase blocklist")

    summary = build_run_summary(
        overall_flag="fail",
        dimension_scores=[
            DimensionScore(dimension_key="disclosure", score=0, rationale="No disclosure found anywhere."),
            DimensionScore(dimension_key="truthfulness", score=2, rationale="Accurate."),
        ],
        rubric_by_key={"disclosure": disclosure_dim, "truthfulness": passing_dim},
        rule_outcomes=[
            RuleOutcome(
                rule_definition_id=blocklist_rule.id,
                rule_key=blocklist_rule.rule_key,
                result="fail",
                evidence={"matches": [{"phrase": "guaranteed approval"}]},
            )
        ],
        rule_defs_by_id={blocklist_rule.id: blocklist_rule},
        claims=[],
    )

    assert summary["outcome"] == "fail"
    assert any("Disclosure (0/2)" in reason for reason in summary["reasons"])
    assert any("guaranteed approval" in reason for reason in summary["reasons"])
    assert not any("Truthfulness" in reason for reason in summary["reasons"])
    assert summary["claims_to_verify"] == []


def test_summary_lists_claims_to_verify_on_a_passing_run():
    dim = _dimension("truthfulness", "Truthfulness")

    summary = build_run_summary(
        overall_flag="pass",
        dimension_scores=[DimensionScore(dimension_key="truthfulness", score=2, rationale="Accurate.")],
        rubric_by_key={"truthfulness": dim},
        rule_outcomes=[],
        rule_defs_by_id={},
        claims=[
            ExtractedClaim(
                claim_text="Rates range from 7.99% to 21.99% APR.",
                claim_type="apr",
                product_identifier="ClearPath Personal Loan",
                severity="low",
            )
        ],
    )

    assert summary["outcome"] == "pass"
    assert summary["reasons"] == []
    assert summary["claims_to_verify"] == [
        {
            "claim_text": "Rates range from 7.99% to 21.99% APR.",
            "claim_type": "apr",
            "product_identifier": "ClearPath Personal Loan",
            "severity": "low",
        }
    ]
