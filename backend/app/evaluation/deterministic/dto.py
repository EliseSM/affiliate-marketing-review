import uuid
from dataclasses import dataclass, field
from typing import Literal, Optional

RuleResult = Literal["pass", "fail", "warn", "not_applicable"]


@dataclass
class SubmissionInput:
    """Decouples rule callables from the ORM -- rules only need the text/html
    of the submission, not a live SQLAlchemy session."""

    raw_text: str
    raw_html: Optional[str]
    product_identifier: Optional[str]


@dataclass
class ProductTermsInput:
    product_identifier: str
    apr_min: Optional[float]
    apr_max: Optional[float]
    annual_fee: Optional[float]


@dataclass
class RuleOutcome:
    rule_definition_id: uuid.UUID
    rule_key: str
    result: RuleResult
    evidence: dict = field(default_factory=dict)
