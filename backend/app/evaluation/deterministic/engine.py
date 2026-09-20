import logging

import app.evaluation.deterministic.rules  # noqa: F401 -- registers all rule callables
from app.evaluation.deterministic.dto import ProductTermsInput, RuleOutcome, SubmissionInput
from app.evaluation.deterministic.registry import get_rule

logger = logging.getLogger(__name__)


class RuleDefinitionLike:
    """Structural type for whatever the caller passes in (an ORM row or a
    plain object) -- engine.py only reads these attributes."""

    id: object
    rule_key: str
    active: bool
    config: dict | None


class RuleEngine:
    def run(
        self,
        submission: SubmissionInput,
        rule_definitions: list[RuleDefinitionLike],
        product_terms: ProductTermsInput | None,
    ) -> list[RuleOutcome]:
        outcomes: list[RuleOutcome] = []
        for rule_def in rule_definitions:
            if not rule_def.active:
                continue
            rule_fn = get_rule(rule_def.rule_key)
            if rule_fn is None:
                logger.warning("No registered callable for rule_key=%s; skipping.", rule_def.rule_key)
                continue
            try:
                result, evidence = rule_fn(submission, rule_def.config, product_terms)
            except Exception:  # noqa: BLE001 -- one rule failing must not abort the whole run
                logger.exception("Rule %s raised an exception; recording as fail.", rule_def.rule_key)
                result, evidence = "fail", {"error": "Rule raised an exception during evaluation."}

            outcomes.append(
                RuleOutcome(
                    rule_definition_id=rule_def.id,
                    rule_key=rule_def.rule_key,
                    result=result,
                    evidence=evidence,
                )
            )
        return outcomes
