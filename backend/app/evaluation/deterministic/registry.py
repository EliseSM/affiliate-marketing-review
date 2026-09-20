from collections.abc import Callable
from typing import Optional

from app.evaluation.deterministic.dto import ProductTermsInput, RuleResult, SubmissionInput

# A rule callable takes the submission, the rule's config blob (from
# rule_definitions.config), and the resolved product terms (or None if not
# found / not required) and returns (result, evidence).
RuleCallable = Callable[[SubmissionInput, Optional[dict], Optional[ProductTermsInput]], tuple[RuleResult, dict]]

_RULE_REGISTRY: dict[str, RuleCallable] = {}


def register_rule(rule_key: str) -> Callable[[RuleCallable], RuleCallable]:
    """Decorator that registers a rule callable under `rule_key`, matching a
    row in the `rule_definitions` table. Adding a new deterministic check is
    just: write a function decorated with this, insert a rule_definitions row
    with the same rule_key -- no changes to the engine itself."""

    def decorator(func: RuleCallable) -> RuleCallable:
        if rule_key in _RULE_REGISTRY:
            raise ValueError(f"Rule key {rule_key!r} is already registered.")
        _RULE_REGISTRY[rule_key] = func
        return func

    return decorator


def get_rule(rule_key: str) -> Optional[RuleCallable]:
    return _RULE_REGISTRY.get(rule_key)


def all_registered_rule_keys() -> list[str]:
    return list(_RULE_REGISTRY.keys())
