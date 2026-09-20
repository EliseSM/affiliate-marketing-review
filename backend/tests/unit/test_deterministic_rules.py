from app.db.seed_data import PROHIBITED_PHRASES, RULE_DEFINITIONS
from app.evaluation.deterministic.dto import ProductTermsInput, SubmissionInput
from app.evaluation.deterministic.rules.disclosure_presence import check_disclosure_presence
from app.evaluation.deterministic.rules.product_terms_match import check_apr_matches_product_terms
from app.evaluation.deterministic.rules.prohibited_phrases import check_prohibited_phrases

DISCLOSURE_CONFIG = next(
    rule["config"] for rule in RULE_DEFINITIONS if rule["rule_key"] == "disclosure_presence"
)
PROHIBITED_CONFIG = {"phrases": PROHIBITED_PHRASES}


def _submission(text: str, html: str | None = None, product_identifier: str | None = None) -> SubmissionInput:
    return SubmissionInput(raw_text=text, raw_html=html, product_identifier=product_identifier)


def test_prohibited_phrases_fails_on_guaranteed_approval():
    submission = _submission("Guaranteed approval! Everyone qualifies, no matter your credit score.")

    result, evidence = check_prohibited_phrases(submission, PROHIBITED_CONFIG, None)

    assert result == "fail"
    matched_phrases = {m["phrase"] for m in evidence["matches"]}
    assert "guaranteed approval" in matched_phrases
    assert "everyone qualifies" in matched_phrases


def test_prohibited_phrases_passes_on_compliant_copy():
    submission = _submission(
        "Check whether you may qualify for a personal loan. Rates and terms vary by creditworthiness."
    )

    result, evidence = check_prohibited_phrases(submission, PROHIBITED_CONFIG, None)

    assert result == "pass"
    assert evidence["matches"] == []


def test_disclosure_presence_passes_when_disclosure_near_link():
    html = (
        "<p>We may receive compensation when you apply through this link.</p>"
        '<a href="https://example.com/apply">Apply Now</a>'
    )
    submission = _submission("placeholder text", html=html)

    result, _evidence = check_disclosure_presence(submission, DISCLOSURE_CONFIG, None)

    assert result == "pass"


def test_disclosure_presence_fails_when_no_disclosure_anywhere():
    html = "<p>This is the best card for everyone.</p>" '<a href="https://example.com/apply">Apply Now</a>'
    submission = _submission("placeholder text", html=html)

    result, evidence = check_disclosure_presence(submission, DISCLOSURE_CONFIG, None)

    assert result == "fail"
    assert "reason" in evidence


def test_disclosure_presence_not_applicable_without_any_link():
    submission = _submission("Just some educational content with no recommendation or link at all.")

    result, _evidence = check_disclosure_presence(submission, DISCLOSURE_CONFIG, None)

    assert result == "not_applicable"


CLEARPATH_PERSONAL_LOAN = ProductTermsInput(
    product_identifier="ClearPath Personal Loan", apr_min=7.99, apr_max=21.99, annual_fee=None
)
CLEARPATH_REWARDS_CARD = ProductTermsInput(
    product_identifier="ClearPath Rewards Card", apr_min=None, apr_max=None, annual_fee=0
)


def test_apr_check_not_applicable_without_product_identifier():
    submission = _submission("Get a 4.99% personal loan, available to every applicant.")

    result, evidence = check_apr_matches_product_terms(submission, None, None)

    assert result == "not_applicable"
    assert "product_identifier" in evidence["reason"]


def test_apr_check_not_applicable_when_product_not_in_table():
    submission = _submission(
        "Get a 4.99% personal loan.", product_identifier="Some Unlisted Loan"
    )

    result, _evidence = check_apr_matches_product_terms(submission, None, None)

    assert result == "not_applicable"


def test_apr_check_fails_on_invented_rate_below_range():
    # Mirrors marketing-test-examples/failing/web/02_invented_rate_no_conditions_personal_loan.html
    submission = _submission(
        "ClearPath Financial is offering a 4.99% personal loan, available to every applicant "
        "regardless of credit history.",
        product_identifier="ClearPath Personal Loan",
    )

    result, evidence = check_apr_matches_product_terms(submission, None, CLEARPATH_PERSONAL_LOAN)

    assert result == "fail"
    assert evidence["mismatches"][0]["claimed"] == 4.99


def test_apr_check_passes_on_rate_within_range():
    submission = _submission(
        "Rates on a ClearPath Personal Loan range from 7.99% to 21.99% depending on creditworthiness.",
        product_identifier="ClearPath Personal Loan",
    )

    result, _evidence = check_apr_matches_product_terms(submission, None, CLEARPATH_PERSONAL_LOAN)

    assert result == "pass"


def test_apr_check_ignores_dollar_amounts_that_are_not_annual_fee_claims():
    # Regression test: a loose regex previously treated ANY "$<number>" as an
    # annual-fee claim, which would have falsely flagged a $200 welcome bonus or
    # a $500 spend requirement against the card's $0 annual_fee.
    submission = _submission(
        "Sign up for the ClearPath Rewards Card and get a $200 welcome bonus after you spend "
        "$500 in qualifying purchases within 90 days. The card has a $0 annual fee.",
        product_identifier="ClearPath Rewards Card",
    )

    result, evidence = check_apr_matches_product_terms(submission, None, CLEARPATH_REWARDS_CARD)

    assert result == "pass"
    assert evidence["fee_claims_checked"] == [0.0]
