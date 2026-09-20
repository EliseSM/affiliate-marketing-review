import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SubmissionAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_type: str
    storage_path: str
    original_src: Optional[str]
    mime_type: str


class DeterministicCheckResultOut(BaseModel):
    # Not from_attributes: rule_key/display_name come from the joined
    # rule_definition relationship, not directly off this row, so callers
    # build this explicitly (see app/api/v1/routes/converters.py) rather than
    # via model_validate.
    rule_key: str
    display_name: str
    result: str
    evidence: dict


class LLMJudgeResultOut(BaseModel):
    # See DeterministicCheckResultOut note -- dimension_key/display_name come
    # from the joined rubric_dimension relationship.
    dimension_key: str
    display_name: str
    score: int
    rationale: str


class ClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    claim_text: str
    claim_type: str
    product_identifier: Optional[str]
    source_reference: Optional[str]
    source_date: Optional[date]
    severity: str
    evaluator_result: str
    human_review_status: str


class EvaluationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    llm_provider: Optional[str]
    overall_score: Optional[float]
    overall_flag: Optional[str]
    summary: Optional[dict]
    judge_results: list[LLMJudgeResultOut] = []
    deterministic_results: list[DeterministicCheckResultOut] = []
    claims: list[ClaimOut] = []


class SubmissionListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content_type: str
    product_identifier: Optional[str]
    affiliate_partner: Optional[str]
    poc_email: Optional[str]
    project_name: Optional[str]
    status: str
    created_at: datetime
    latest_run: Optional[EvaluationRunOut] = None


class SubmissionDetailOut(SubmissionListItemOut):
    raw_text: str
    raw_html: Optional[str]
    landing_url: Optional[str]
    metadata: dict
    assets: list[SubmissionAssetOut] = []


class SubmissionUploadResultOut(BaseModel):
    batch_id: uuid.UUID
    submissions: list[SubmissionListItemOut]
