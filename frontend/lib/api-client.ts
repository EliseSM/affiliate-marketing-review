import type {
  ContentType,
  EvaluationRun,
  RubricDimension,
  RuleDefinition,
  Submission,
  SubmissionDetail,
  SubmissionListFilters,
  UploadBatchResponse,
} from "./types";

export class ApiError extends Error {
  status: number;
  body: string;

  constructor(status: number, body: string) {
    super(`API request failed with status ${status}: ${body}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

function getBaseUrl(): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");
  }
  return baseUrl.replace(/\/$/, "");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getBaseUrl()}${path}`, init);
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new ApiError(response.status, body);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function uploadBatch(
  file: File,
  contentType: ContentType,
  pocEmail?: string,
  projectName?: string
): Promise<UploadBatchResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("content_type", contentType);
  if (pocEmail) {
    formData.append("poc_email", pocEmail);
  }
  if (projectName) {
    formData.append("project_name", projectName);
  }

  return request<UploadBatchResponse>("/submissions/batch", {
    method: "POST",
    body: formData,
  });
}

export async function listSubmissions(
  filters: SubmissionListFilters = {}
): Promise<Submission[]> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.exclude_status) params.set("exclude_status", filters.exclude_status);
  if (filters.content_type) params.set("content_type", filters.content_type);
  if (filters.overall_flag) params.set("overall_flag", filters.overall_flag);
  if (filters.project_name) params.set("project_name", filters.project_name);
  if (filters.sort) params.set("sort", filters.sort);

  const query = params.toString();
  return request<Submission[]>(`/submissions${query ? `?${query}` : ""}`);
}

export async function getSubmission(id: string): Promise<SubmissionDetail> {
  return request<SubmissionDetail>(`/submissions/${id}`);
}

export async function getEvaluationRun(id: string): Promise<EvaluationRun> {
  return request<EvaluationRun>(`/evaluation-runs/${id}`);
}

export async function retryEvaluationRun(id: string): Promise<EvaluationRun> {
  return request<EvaluationRun>(`/evaluation-runs/${id}/retry`, {
    method: "POST",
  });
}

export async function createExport(submissionIds: string[]): Promise<Blob> {
  const response = await fetch(`${getBaseUrl()}/exports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ submission_ids: submissionIds }),
  });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new ApiError(response.status, body);
  }
  return response.blob();
}

export async function listRubricDimensions(): Promise<RubricDimension[]> {
  return request<RubricDimension[]>("/rubric-dimensions");
}

export async function listRules(): Promise<RuleDefinition[]> {
  return request<RuleDefinition[]>("/rules");
}
