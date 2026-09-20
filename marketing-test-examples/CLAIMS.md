# Test Fixture Answer Key — ClearPath Financial

20 fictional affiliate marketing examples for **ClearPath Financial** (a fictional consumer financial services company), used to manually/end-to-end test the evaluation pipeline against `reference-docs/affiliate_marketing_guidelines_consumer_financial_services.md`. 10 are designed to **pass**; 10 are designed to **fail**, each on a different mechanism so they exercise different parts of the pipeline.

All fictional partner names (Summit Trust Bank, Harborview Lending) are invented for these fixtures and are not real companies.

**Verification note:** every deterministic-rule outcome listed below was confirmed by running the actual backend `RuleEngine` (`app/evaluation/deterministic/engine.py`) and ingestion strategies (`app/ingestion/factory.py`) against these exact files — not hand-predicted. The 5 rule keys referenced are the real ones seeded in `app/db/seed_data.py`. LLM-judge dimension outcomes are the *intended* result these examples are designed to elicit; they depend on the actual model's judgment at evaluation time and are not mechanically guaranteed the way the deterministic results are.

## Passing examples (expect `overall_flag = pass`)

All 10 pass every applicable deterministic rule (verified — no `fail`/`warn` outcomes anywhere in this group) and are written to be genuinely compliant, so a correctly functioning LLM judge should score all 8 rubric dimensions at 2.

| # | File | Product | Type | What it demonstrates | Guideline mechanism |
|---|------|---------|------|----------------------|----------------------|
| 1 | `passing/emails/01_disclosure_clarity_personal_loan.eml` | Personal loan | Email | Disclosure text ("We may receive compensation...") placed immediately next to the CTA link; soft-pull framing ("won't affect your credit score") | Section 2 (disclosure standards); `rule_key: disclosure_presence` → pass |
| 2 | `passing/emails/02_complete_promo_terms_credit_card.eml` | Credit card | Email | Welcome bonus stated with full conditions: $500 spend requirement, 90-day window | Section 5 (welcome bonus conditions); `rule_key: promo_conditions_present` → pass |
| 3 | `passing/emails/03_prequalification_distinction_mortgage.eml` | Mortgage | Email | Prequalification explicitly distinguished from approval/commitment to lend, without any overreach language | Section 6; `rule_key: prequalification_not_approval` → pass |
| 4 | `passing/emails/04_no_guarantee_language_personal_loan.eml` | Personal loan | Email | "May qualify" / rate depends on credit profile — no certainty language | Section 4; Rubric dimension: No guarantees = 2 (expected) |
| 5 | `passing/emails/05_accurate_fee_terms_credit_card.eml` | Credit card | Email | Annual fee schedule, rewards rate, foreign transaction fee, balance-transfer fee all stated accurately with conditions | Section 5; Rubric dimension: Product terms = 2 (expected) |
| 6 | `passing/web/01_transparent_comparison_personal_loan.html` | Personal loan | Web | Comparison table with stated methodology (APR, fees, funding time, min. credit score) + disclosure that compensation may affect ordering but not the terms shown | Section 7; Rubric dimension: Affiliate integrity = 2 (expected) |
| 7 | `passing/web/02_product_fit_criteria_credit_card.html` | Credit card | Web | Recommendation criteria based on stated spending/reward preferences and credit profile only — explicitly not on name/location/browsing history | Section 9; Rubric dimension: Fairness = 2 (expected) |
| 8 | `passing/web/03_rate_assumptions_mortgage.html` | Mortgage | Web | Rate estimate stated with full assumptions (loan amount, term, down payment, credit score) and excluded costs called out | Section 6 (Reg Z framing); Rubric dimension: Truthfulness = 2 (expected) |
| 9 | `passing/web/04_eligibility_transparency_mortgage.html` | Mortgage | Web | States geographic exclusions (NY, HI) and minimum credit score/documentation requirements up front; prequalification language present with no overreach | Section 1 (transparent limitations) + Section 6; `rule_key: prequalification_not_approval` → pass |
| 10 | `passing/web/05_substantiated_savings_credit_card.html` | Credit card | Web | Balance-transfer savings claim with a fully defined comparison (starting APR, balance, payment, term) and a "results will vary" caveat | Section 3 ("Savings" row); `rule_key: promo_conditions_present` → pass |

## Failing examples (expect `overall_flag = fail`)

Each example contains exactly one deliberate violation type. Where a `rule_key` is listed, the deterministic engine fails it directly (confirmed by running the engine against the file); where the mechanism is listed as "LLM-judged (no deterministic rule)", the deterministic layer returns all `pass`/`not_applicable` and detecting the violation depends entirely on the LLM-as-judge pass — these three are the most important fixtures for confirming the LLM layer is actually doing work beyond the blocklist/heuristics.

| # | File | Product | Type | Violation | Claim/language excerpt | Guideline mechanism |
|---|------|---------|------|-----------|--------------------------|----------------------|
| 1 | `failing/emails/01_guaranteed_approval_personal_loan.eml` | Personal loan | Email | Exact Section 8 blocklist phrase | "guaranteed approval on a personal loan up to $25,000" | Section 8 blocklist; `rule_key: prohibited_phrase_blocklist` → **fail** (matched "guaranteed approval") |
| 2 | `failing/web/01_missing_disclosure_credit_card.html` | Credit card | Web | No affiliate disclosure anywhere | Entire page has no disclosure language of any kind | Section 2; `rule_key: disclosure_presence` → **fail** ("No affiliate disclosure language found anywhere") |
| 3 | `failing/web/02_invented_rate_no_conditions_personal_loan.html` | Personal loan | Web | Specific rate presented as universally available, no qualifying conditions | "a 4.99% personal loan, available to every applicant regardless of credit history" | Section 3 (Rates/APR row); **LLM-judged** (no deterministic rule — `apr_matches_product_terms` returns `not_applicable` since `product_terms` is empty). Rubric dimensions: Truthfulness = 0, Product terms = 0 (expected) |
| 4 | `failing/emails/02_prequalification_as_approval_mortgage.eml` | Mortgage | Email | Prequalification conflated with final approval | "After completing our 2-minute prequalification questionnaire, you're approved for your ClearPath Financial mortgage" | Section 6; `rule_key: prequalification_not_approval` → **fail** (co-occurrence of "prequalification" + "you're approved") |
| 5 | `failing/web/03_discriminatory_steering_personal_loan.html` | Personal loan | Web | Steering by ZIP code as a proxy characteristic | "featured for applicants in select higher-income ZIP codes. If your ZIP code isn't one of our featured areas, we recommend our Starter Loan instead" | Section 9; **LLM-judged** (no deterministic rule covers proxy-based steering). Rubric dimension: Fairness = 0 (expected) |
| 6 | `failing/emails/03_cherry_picked_testimonial_credit_card.eml` | Credit card | Email | Cherry-picked testimonial presented as a typical/achievable result | "Denise ... paid off $40,000 in credit card debt in just 3 months ... Imagine what it could do for you" — no substantiation or "results may vary" | Section 3 ("Customer outcomes" row); **LLM-judged** (no deterministic rule). Rubric dimensions: Truthfulness = 0, Evidence grounding = 0 (expected) |
| 7 | `failing/web/04_false_urgency_mortgage.html` | Mortgage | Web | False urgency, no genuine deadline | "Act now or you will lose your chance to lock in today's rate" | Section 8 blocklist; `rule_key: prohibited_phrase_blocklist` → **fail** (matched "act now or you will lose your chance") |
| 8 | `failing/web/05_fake_objective_ranking_personal_loan.html` | Personal loan | Web | Ranking claimed as objective ("best for everyone") while compensation drives placement, no real methodology disclosed | "Sponsored placements below. ClearPath Financial's Premier Personal Loan is the best product for everyone, our top pick" | Section 7 + Section 8 blocklist; `rule_key: prohibited_phrase_blocklist` → **fail** (matched "the best product for everyone"). Note: `disclosure_presence` actually **passes** here because the bare word "Sponsored" satisfies the keyword-level check — a good illustration that passing the disclosure keyword check is not the same as real methodology transparency (Rubric dimension: Affiliate integrity = 0, expected) |
| 9 | `failing/emails/04_promo_missing_conditions_credit_card.eml` | Credit card | Email | Welcome bonus advertised with no spend requirement or time window | "get a $200 welcome bonus, on us" | Section 5; `rule_key: promo_conditions_present` → **fail** ("Promotional language found without qualifying condition language nearby") |
| 10 | `failing/emails/05_free_money_guaranteed_rewards_credit_card.eml` | Credit card | Email | "Free money" / rewards guaranteed regardless of conditions | "gives you free money on every purchase - your rewards are guaranteed no matter how you use the card" | Section 8 blocklist; `rule_key: prohibited_phrase_blocklist` → **fail** (matched "free money") |

## Coverage summary

- **Content types:** 10 emails (`.eml`), 10 web pages (`.html`) — 5/5 split within each of passing/failing.
- **Product types:** personal loan (7), credit card (8), mortgage (5) — spread across both groups, no single type dominates.
- **Deterministic rules exercised:** all 5 seeded rules (`prohibited_phrase_blocklist`, `disclosure_presence`, `promo_conditions_present`, `prequalification_not_approval`, `apr_matches_product_terms`) produce at least one `pass` and, where applicable, at least one `fail` across the set.
- **LLM-only violations (3):** examples 3, 5, and 6 in the failing set have a fully clean deterministic pass and rely entirely on the LLM-as-judge rubric to be caught — use these specifically to confirm the LLM layer is contributing value beyond the deterministic checks.

## `product_terms` and the `apr_matches_product_terms` rule

`app/db/seed_data.py` now seeds three `product_terms` rows matching these fixtures (applied via migration `0002_seed_product_terms.py`): **ClearPath Personal Loan** (APR 7.99%–21.99%), **ClearPath Rewards Card** (annual fee $0 — see caveat below), and **ClearPath Mortgage** (APR 6.25%–7.5%).

Because HTML/email ingestion never infers a `product_identifier` from content (only Excel/CSV does, via a column), `POST /submissions/batch` now accepts an optional `product_identifier` form field that overrides it for the file being uploaded — pass it explicitly when uploading these fixtures to exercise this rule. Verified directly against the deterministic engine (not hand-predicted):

| File | `product_identifier` to pass | Result |
|---|---|---|
| `failing/web/02_invented_rate_no_conditions_personal_loan.html` | `ClearPath Personal Loan` | **fail** — 4.99% is outside the seeded 7.99–21.99% range (this is the primary fixture this feature exists to catch) |
| `passing/emails/02_complete_promo_terms_credit_card.eml` | `ClearPath Rewards Card` | pass |
| `passing/web/05_substantiated_savings_credit_card.html` | `ClearPath Rewards Card` | pass |
| `passing/emails/04_no_guarantee_language_personal_loan.eml` | `ClearPath Personal Loan` | not_applicable (no APR/fee claim in the text at all — harmless) |
| `passing/web/04_eligibility_transparency_mortgage.html` | `ClearPath Mortgage` | not_applicable |

**Do not** pass a `product_identifier` on these files — the rule's regex is a documented v1 best-effort (it can't distinguish an APR from any other percentage, or an annual fee from any other dollar amount) and will produce a false `fail` on genuinely compliant content:
- `passing/emails/05_accurate_fee_terms_credit_card.eml` and `failing/web/01_missing_disclosure_credit_card.html` both accurately state a **tiered** fee ("$0 first year, $95/year after") — the `product_terms.annual_fee` column only holds one number, so whichever value is seeded, the other tier reads as a mismatch.
- `passing/web/03_rate_assumptions_mortgage.html` states a "20% down payment" — the regex reads any `NN%` as an APR claim, so it misreads the down payment percentage as a mortgage rate and compares it against the 6.25–7.5% range.
- `passing/web/01_transparent_comparison_personal_loan.html` is a comparison of *other* lenders (Summit Trust Bank, Harborview Lending), not ClearPath's own product, so it shouldn't be tagged with a ClearPath `product_identifier` at all — doing so misreads the competitors' listed rates as ClearPath's own.

These are genuine limitations of the naive regex-based v1 rule (by design — see the code comment in `app/evaluation/deterministic/rules/product_terms_match.py`), not bugs in the fixtures. They're exactly the kind of nuance the LLM-as-judge pass is meant to handle instead.
