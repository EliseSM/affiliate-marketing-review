import uuid

from pydantic import BaseModel, ConfigDict


class RubricDimensionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    display_name: str
    description: str
    scoring_scale: dict
    active: bool
    sort_order: int


class RuleDefinitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rule_key: str
    display_name: str
    description: str
    category: str
    severity: str
    requires_product_terms: bool
    active: bool
