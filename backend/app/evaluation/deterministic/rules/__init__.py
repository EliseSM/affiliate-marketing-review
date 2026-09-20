"""Importing this package registers all deterministic rule callables (each
module below calls @register_rule at import time)."""

from app.evaluation.deterministic.rules import (  # noqa: F401
    disclosure_presence,
    prequalification_language,
    product_terms_match,
    prohibited_phrases,
    promo_conditions,
)
