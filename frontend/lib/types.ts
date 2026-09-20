export type ContentType = "web_page" | "email" | "ad_copy";

export type SubmissionStatus = "ingested" | "evaluating" | "evaluated" | "error" | "exported";

export type RunStatus = "pending" | "running" | "completed" | "failed";

export type OverallFlag = "pass" | "needs_review" | "fail";

export type RubricScore = 0 | 1 | 2;

export type DeterministicResult = "pass" | "fail" | "warn" | "not_applicable";

export type ClaimSeverity = "low" | "medium" | "high" | "critical";

export type EvaluatorResult = "supported" | "unsupported" | "contradicted" | "unverifiable";

export type AssetType =
  | "inline_image"
  | "referenced_image"
  | "standalone_image"
  | "attachment";

export interface RunSummaryClaim {
  claim_text: string;
  claim_type: string;
  product_identifier: string | null;
  severity: ClaimSeverity;
}

export interface RunSummary {
  outcome: OverallFlag;
  reasons: string[];
  claims_to_verify: RunSummaryClaim[];
}

export interface LatestRunSummary {
  id: string;
  status: RunStatus;
  overall_score: number | null;
  overall_flag: OverallFlag | null;
  // Computed once by the backend at evaluation time (app/evaluation/summary_builder.py)
  // and persisted -- never generated on the frontend.
  summary: RunSummary | null;
}

export interface Submission {
  id: string;
  batch_id: string;
  content_type: ContentType;
  product_identifier: string | null;
  affiliate_partner: string | null;
  poc_email: string | null;
  project_name: string | null;
  status: SubmissionStatus;
  created_at: string;
  latest_run: LatestRunSummary | null;
}

export interface SubmissionAsset {
  id: string;
  asset_type: AssetType;
  storage_url: string;
  mime_type: string;
}

export interface JudgeResultView {
  dimension_key: string;
  display_name: string;
  score: RubricScore;
  rationale: string;
}

export interface DeterministicResultView {
  rule_key: string;
  display_name: string;
  result: DeterministicResult;
  evidence: Record<string, unknown> | null;
}

export interface ClaimView {
  claim_text: string;
  claim_type: string;
  severity: ClaimSeverity;
  evaluator_result: EvaluatorResult;
  source_reference: string | null;
}

export interface EvaluationRun extends LatestRunSummary {
  judge_results: JudgeResultView[];
  deterministic_results: DeterministicResultView[];
  claims: ClaimView[];
}

export interface SubmissionDetail extends Omit<Submission, "latest_run"> {
  raw_text: string;
  raw_html: string | null;
  assets: SubmissionAsset[];
  latest_run: EvaluationRun | null;
}

export interface RubricDimension {
  key: string;
  display_name: string;
  description: string;
  scoring_scale: Record<string, string>;
  active: boolean;
  sort_order: number;
}

export interface RuleDefinition {
  rule_key: string;
  display_name: string;
  description: string;
  category: "deterministic_now" | "requires_product_terms" | "hybrid";
  severity: ClaimSeverity;
  requires_product_terms: boolean;
  active: boolean;
}

export interface UploadBatchResponse {
  batch_id: string;
  submissions: { id: string; status: SubmissionStatus }[];
}

export interface SubmissionListFilters {
  status?: SubmissionStatus;
  exclude_status?: SubmissionStatus;
  content_type?: ContentType;
  overall_flag?: OverallFlag;
  project_name?: string;
  sort?: string;
}

