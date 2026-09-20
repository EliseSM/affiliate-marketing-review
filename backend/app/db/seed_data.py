"""Canonical seed data sourced directly from
reference-docs/affiliate_marketing_guidelines_consumer_financial_services.md.

Kept as plain Python data (not hardcoded in the Alembic migration file itself)
so the same source of truth can be reused by the migration's data-seeding step
and by any future re-seed/reset script.
"""

RUBRIC_DIMENSIONS: list[dict] = [
    {
        "key": "truthfulness",
        "display_name": "Truthfulness",
        "description": "Claims must accurately describe the product and be free of false or unsupported material claims.",
        "scoring_scale": {
            "0": "Contains false/unsupported material claims.",
            "1": "Minor imprecision or missing qualification.",
            "2": "Claims are accurate and supported.",
        },
        "sort_order": 1,
    },
    {
        "key": "disclosure",
        "display_name": "Disclosure",
        "description": "The affiliate relationship must be disclosed clearly, conspicuously, and near the relevant content.",
        "scoring_scale": {
            "0": "Affiliate relationship is missing or misleading.",
            "1": "Disclosure exists but is weak/poorly placed.",
            "2": "Clear, conspicuous, understandable disclosure near relevant content.",
        },
        "sort_order": 2,
    },
    {
        "key": "product_terms",
        "display_name": "Product terms",
        "description": "Stated product terms and conditions (APR, fees, rewards, etc.) must be current and accurate.",
        "scoring_scale": {
            "0": "Material terms are wrong or invented.",
            "1": "Mostly correct but missing important conditions.",
            "2": "Current terms and conditions are accurately represented.",
        },
        "sort_order": 3,
    },
    {
        "key": "no_guarantees",
        "display_name": "No guarantees",
        "description": "Content must not guarantee approval, rates, or outcomes that cannot be legally supported.",
        "scoring_scale": {
            "0": "Guarantees approval/rates/outcomes.",
            "1": "Ambiguous certainty or overly strong language.",
            "2": "Appropriately communicates uncertainty and eligibility.",
        },
        "sort_order": 4,
    },
    {
        "key": "evidence_grounding",
        "display_name": "Evidence grounding",
        "description": "Material claims should be traceable to appropriate, retrievable evidence.",
        "scoring_scale": {
            "0": "Claims lack evidence or contradict sources.",
            "1": "Evidence exists but coverage is incomplete.",
            "2": "Material claims are traceable to appropriate evidence.",
        },
        "sort_order": 5,
    },
    {
        "key": "fairness",
        "display_name": "Fairness",
        "description": "Recommendation logic must not use prohibited/sensitive characteristics or discriminatory steering.",
        "scoring_scale": {
            "0": "Uses prohibited/sensitive characteristics or discriminatory steering.",
            "1": "Potential proxy or inconsistent treatment.",
            "2": "Uses legitimate product-fit criteria consistently.",
        },
        "sort_order": 6,
    },
    {
        "key": "consumer_clarity",
        "display_name": "Consumer clarity",
        "description": "Content should be clear, balanced, and understandable to an ordinary consumer.",
        "scoring_scale": {
            "0": "Materially misleading or confusing.",
            "1": "Generally understandable but important caveat is easy to miss.",
            "2": "Clear, balanced, consumer-understandable presentation.",
        },
        "sort_order": 7,
    },
    {
        "key": "affiliate_integrity",
        "display_name": "Affiliate integrity",
        "description": "Compensation and ranking methodology must be transparent and must not drive deceptive claims.",
        "scoring_scale": {
            "0": "Compensation drives deceptive claims/ranking.",
            "1": "Compensation relationship or ranking methodology is unclear.",
            "2": "Compensation and ranking methodology are transparent.",
        },
        "sort_order": 8,
    },
]

# Guidelines Section 8 — Prohibited or high-risk language library.
PROHIBITED_PHRASES: list[str] = [
    "guaranteed approval",
    "guaranteed acceptance",
    "everyone qualifies",
    "no matter your credit score",
    "guaranteed lowest rate",
    "guaranteed best rate",
    "instant approval guaranteed",
    "guaranteed savings",
    "guaranteed credit-score increase",
    "guaranteed credit score increase",
    "risk-free borrowing",
    "risk free borrowing",
    "no downside",
    "free money",
    "guaranteed mortgage approval",
    "this loan is right for you",
    "this card is right for you",
    "the best product for everyone",
    "act now or you will lose your chance",
]

# ClearPath Financial product terms -- source of truth for the
# apr_matches_product_terms deterministic rule. These values are chosen to match
# the accurate claims made in marketing-test-examples/passing/ and to conflict
# with the invented claim in marketing-test-examples/failing/web/02 (a 4.99%
# personal loan advertised as universally available). See
# marketing-test-examples/CLAIMS.md for which fixture files these correspond to.
PRODUCT_TERMS_SEED: list[dict] = [
    {
        "product_identifier": "ClearPath Personal Loan",
        "product_type": "personal_loan",
        "apr_min": 7.99,
        "apr_max": 21.99,
        "annual_fee": None,
        "eligibility_notes": (
            "Rate, term, and loan amount depend on the applicant's credit profile, income, and "
            "requested amount. Rate-check uses a soft credit inquiry; a hard inquiry occurs only "
            "on formal application."
        ),
        "source_document_ref": "test-fixture-seed",
    },
    {
        "product_identifier": "ClearPath Rewards Card",
        "product_type": "credit_card",
        "apr_min": None,
        "apr_max": None,
        "annual_fee": 0,
        "eligibility_notes": (
            "$0 annual fee for the first year, $95/year thereafter (the annual_fee value here "
            "reflects the promotional first-year rate; the naive single-value deterministic check "
            "cannot represent both tiers at once -- see CLAIMS.md). Welcome bonus: $200 after $500 "
            "in qualifying purchases within the first 90 days of account opening."
        ),
        "source_document_ref": "test-fixture-seed",
    },
    {
        "product_identifier": "ClearPath Mortgage",
        "product_type": "mortgage",
        "apr_min": 6.25,
        "apr_max": 7.5,
        "annual_fee": None,
        "eligibility_notes": (
            "Estimated rate assumes a $300,000 loan amount, 30-year fixed term, 20% down payment, "
            "and a credit score of 740 or higher. Actual rate depends on loan amount, term, down "
            "payment, credit profile, property location, and market conditions at rate lock."
        ),
        "source_document_ref": "test-fixture-seed",
    },
]

RULE_DEFINITIONS: list[dict] = [
    {
        "rule_key": "prohibited_phrase_blocklist",
        "display_name": "Prohibited phrase blocklist",
        "description": "Flags language from the guidelines Section 8 prohibited/high-risk phrase library.",
        "category": "deterministic_now",
        "severity": "high",
        "requires_product_terms": False,
        "config": {"phrases": PROHIBITED_PHRASES},
    },
    {
        "rule_key": "disclosure_presence",
        "display_name": "Affiliate disclosure presence",
        "description": "Checks that disclosure-like language appears near a recommendation/link, per Section 13.",
        "category": "deterministic_now",
        "severity": "high",
        "requires_product_terms": False,
        "config": {
            "disclosure_markers": ["compensat", "affiliate link", "may earn", "paid partner", "sponsored"],
            "link_markers": ["<a ", "apply now", "learn more", "get started", "see rates"],
            "proximity_chars": 400,
        },
    },
    {
        "rule_key": "promo_conditions_present",
        "display_name": "Promotional conditions present",
        "description": "Checks that promotional/intro offers are accompanied by qualifying conditions (Section 13).",
        "category": "hybrid",
        "severity": "medium",
        "requires_product_terms": False,
        "config": {
            "promo_markers": ["intro", "promo", "0% apr", "welcome bonus", "sign-up bonus", "sign up bonus"],
            "condition_markers": ["spend", "within", "days", "months", "qualifying purchase", "terms apply"],
        },
    },
    {
        "rule_key": "prequalification_not_approval",
        "display_name": "Prequalification not described as approval",
        "description": "Flags language that conflates prequalification with approval/commitment (Section 6, 13).",
        "category": "hybrid",
        "severity": "critical",
        "requires_product_terms": False,
        "config": {
            "prequalification_markers": ["prequalif", "pre-qualif", "preapprov", "pre-approv"],
            "overreach_markers": ["guarantee", "guaranteed", "you are approved", "you're approved", "final approval"],
        },
    },
    {
        "rule_key": "apr_matches_product_terms",
        "display_name": "APR/fee claims match product terms",
        "description": "Cross-checks stated APR/fee claims against the product_terms table (Section 13). "
        "Returns not_applicable if the product is not yet in the table.",
        "category": "requires_product_terms",
        "severity": "high",
        "requires_product_terms": True,
        "config": None,
    },
]
