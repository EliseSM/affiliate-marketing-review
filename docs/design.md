# Design Doc: Affiliate Marketing Compliance Review Tool

## Context

The company currently reviews affiliate marketing content (loans, credit cards, mortgage prequalification) against a written compliance guidelines document (`reference-docs/affiliate_marketing_guidelines_consumer_financial_services.md`) using a manual Excel + email process. That guidelines document was written with automated evaluation in mind — it already contains a prohibited-phrase blocklist (Section 8), an 8-dimension 0/1/2 LLM-judge rubric (Section 12), a deterministic checklist (Section 13), and a suggested claim-level data model (Section 16).

The goal is a v1 internal tool that lets a reviewer upload affiliate content, runs it through an automated evaluation pipeline (LLM-as-judge + deterministic checks, kept as two distinct-but-combinable subsystems so each can evolve independently), and lets the reviewer view results and export them to Excel to slot into the existing process. The repo is currently empty except for `LICENSE`, `.gitignore`, and the guidelines doc — this is a from-scratch build.

**Confirmed v1 scope (via user clarification):**
- Intake: upload Excel/CSV (bulk), or a single HTML/plaintext/email-like file, possibly containing embedded or standalone images (jpg/png/gif).
- Content types: web/landing pages, email marketing copy, ad copy.
- Images are evaluated too, via a vision-capable LLM in the same judge pass.
- No auth in v1 (single trusted internal team).
- No product-terms source of truth yet, but a `product_terms` table will be added and populated later — deterministic checks must degrade gracefully (`not_applicable`) until then.
- Output: in-app list + detail view of results; export selected results to `.xlsx`. No in-app approve/reject workflow.
- Volume: low (a few–~50 items/week), but a single upload can contain dozens of rows — needs non-blocking background processing, without adding heavy queue infrastructure (Celery/Redis) given the volume.
- Stack (given, not negotiable): FastAPI backend, Next.js frontend, Supabase Postgres + Storage, OpenAI as the initial LLM behind a swappable provider abstraction, deployed on Railway.

**Why this document exists:** to fix the architecture, schema, and folder structure *before* writing code, since the LLM-judge/deterministic split, the provider abstraction, and the rule-registry pattern all need to be right from the first migration and first module — retrofitting them later would mean reworking the core pipeline.

---

## 1. High-Level Architecture

**Components**
- **Frontend (Next.js, App Router)** — Railway service. Talks only to the backend REST API. Upload UI, submissions list (filter/sort/status), submission detail view (scores, flags, evidence, images), export action, polling for async job status.
- **Backend API (FastAPI)** — Railway service. Owns ingestion, submission storage, triggering evaluation, serving results, building `.xlsx` exports. Connects to Supabase Postgres via SQLAlchemy (async, pooled/transaction-mode connection) and to Supabase Storage via its S3-compatible/storage client.
- **Background execution** — no separate worker service in v1. FastAPI `BackgroundTasks` kicks off each evaluation run immediately after ingestion; a Postgres-backed `evaluation_runs.status` field is the source of truth (not an in-memory queue), and a small in-process reconciliation sweep (async loop started at FastAPI startup, e.g. every 30–60s) re-enqueues any run stuck in `pending`/stale `running` past a timeout — covering the case where the backend process restarts mid-job. This is implemented behind a `JobRunner` interface so it can be swapped for a real queue later without touching pipeline logic.
  - **Known limitation (accepted for v1 given low volume):** a run killed mid-LLM-call is retried from scratch, not resumed. Acceptable at ~50 items/week; would need revisiting if volume or per-item latency grows substantially.
- **Postgres (Supabase)**: submissions/assets, evaluation pipeline (runs, judge results, deterministic results), two data-driven registries (rubric dimensions, rule definitions) so new dimensions/rules don't require code changes, a `claims` table implementing the Section 16 model, and a `product_terms` table (starts empty).
- **Supabase Storage**: `raw-uploads` bucket for original files, `submission-assets` bucket for extracted/normalized images. Postgres stores paths only, never blobs.
- **LLM provider abstraction**: `LLMProvider` interface + `OpenAIProvider` adapter + config-driven factory. All prompt/schema logic is vendor-agnostic; only the adapter knows OpenAI SDK specifics.
- **Deterministic rules engine**: rule-registry pattern — each rule is a small registered Python callable, matched to a `rule_definitions` row; adding a rule means writing a function and inserting a row, not touching the engine.

**End-to-end flow**
1. **Upload** → `POST /api/v1/submissions/batch`. Backend stores the raw file in Storage, creates one `submission_batches` row (every upload is wrapped in a batch, even single files, for schema uniformity), parses it per file type into one or more `submissions` rows (status `ingested`), and extracts any images into `submission_assets`.
2. **Enqueue** → one `evaluation_runs` row per submission (status `pending`), scheduled via `BackgroundTasks`. Upload endpoint returns immediately with submission/run IDs.
3. **Background execution** (`JobRunner.run_evaluation(run_id)`): marks `running` → runs the deterministic rule engine → runs the LLM-as-judge (single multimodal call, text + images together) → persists results and claims → computes an aggregate `overall_score`/`overall_flag` → marks `completed`/`failed`.
4. **Polling**: frontend polls submission/run status every few seconds while non-terminal.
5. **Detail view**: `GET /api/v1/submissions/{id}` returns metadata, assets, latest run, all 8 rubric scores + rationale, all deterministic results + evidence, and claims.
6. **Export**: user selects rows in the list view → `POST /api/v1/exports` → backend builds `.xlsx` (via `openpyxl`) matching the legacy tracker's columns and returns it for download.

---

## 2. Postgres Schema

Design principle: rubric dimensions and deterministic rules are **data**, not code constants — new ones are added via inserts, not deploys. The Section 16 claim model (`claim → product → source → source_date → rule_id → severity → evaluator_result → human_review_status`) is a first-class table fed by both evaluation paths.

- **`submission_batches`**: `id`, `original_filename`, `storage_path`, `upload_type` (`excel|csv|html|email|plaintext|image`), `uploaded_by_email` (nullable — captured now to ease a future auth retrofit), `row_count`, `created_at`.
- **`submissions`** (one per content item): `id`, `batch_id` (fk, required), `content_type` (`web_page|email|ad_copy`), `source_row_number` (nullable, traceability to legacy sheet), `raw_text`, `raw_html` (nullable), `product_identifier` (free text now), `affiliate_partner` (nullable), `landing_url` (nullable, reserved for future link checks), `metadata` (jsonb catch-all for unmapped Excel columns), `status` (`ingested|evaluating|evaluated|error`), `created_at`, `updated_at`.
- **`submission_assets`**: `id`, `submission_id` (fk), `asset_type` (`inline_image|referenced_image|standalone_image|attachment`), `storage_path`, `original_src` (nullable), `mime_type`, `width`/`height` (nullable), `created_at`.
- **`evaluation_runs`**: `id`, `submission_id` (fk), `status` (`pending|running|completed|failed`, polled by frontend), `started_at`/`completed_at` (nullable), `error_message` (nullable), `llm_provider` (snapshot, e.g. `openai:gpt-4o-...`), `deterministic_ruleset_version`, `overall_score` (nullable), `overall_flag` (`pass|needs_review|fail`, nullable), `created_at`.
- **`rubric_dimensions`** (registry, seeded from guidelines Section 12 — 8 rows): `id`, `key` (`truthfulness|disclosure|product_terms|no_guarantees|evidence_grounding|fairness|consumer_clarity|affiliate_integrity`), `display_name`, `description`, `scoring_scale` (jsonb: text for 0/1/2 straight from the Section 12 table), `active`, `sort_order`.
- **`llm_judge_results`**: `id`, `evaluation_run_id` (fk), `rubric_dimension_id` (fk), `score` (0/1/2), `rationale`, `evidence_refs` (jsonb, nullable), `raw_model_response` (jsonb, nullable, for audit), `created_at`. Unique on (`evaluation_run_id`, `rubric_dimension_id`).
- **`rule_definitions`** (registry, seeded from guidelines Section 8 & 13): `id`, `rule_key` (e.g. `prohibited_phrase_blocklist`, `disclosure_presence`, `disclosure_placement_proximity`, `promo_conditions_present`, `prequalification_not_approval`, `apr_matches_product_terms`), `display_name`, `description`, `category` (`deterministic_now|requires_product_terms|hybrid`), `severity` (`low|medium|high|critical`), `requires_product_terms` (bool, drives graceful degradation), `active`, `config` (jsonb — **the Section 8 phrase list itself lives here**, editable by compliance without a deploy, rather than hardcoded).
- **`deterministic_check_results`**: `id`, `evaluation_run_id` (fk), `rule_definition_id` (fk), `result` (`pass|fail|warn|not_applicable`), `evidence` (jsonb — matched phrase + offset, or APR mismatch detail, etc.), `created_at`.
- **`claims`** (Section 16 model): `id`, `submission_id` (fk), `evaluation_run_id` (fk), `claim_text`, `claim_type` (`apr|fee|reward|eligibility|approval_odds|savings|other`), `product_identifier` (nullable), `source_reference` (nullable), `source_date` (nullable), `rule_id` (fk, nullable — set when a deterministic rule produced it), `rubric_dimension_id` (fk, nullable — set when the LLM pass produced it), `severity`, `evaluator_result` (`supported|unsupported|contradicted|unverifiable`), `human_review_status` (`unreviewed|confirmed|dismissed`, default `unreviewed` — column exists for a future review workflow, no UI drives it in v1), `created_at`.
- **`product_terms`** (starts empty; user will populate/maintain): `id`, `product_identifier`, `product_type` (`personal_loan|credit_card|mortgage`), `apr_min`/`apr_max` (nullable), `annual_fee` (nullable), `promo_terms` (jsonb, nullable), `eligibility_notes` (nullable), `effective_date`/`expiration_date` (nullable), `source_document_ref` (nullable), `created_at`, `updated_at`.

**Section 13 checklist → check-type mapping** (drives `rule_definitions.category` and which rubric dimension covers what, so the split is data-auditable, not buried in code):

| Section 13 item | Type |
|---|---|
| Disclosure present near link | deterministic (keyword + proximity heuristic) |
| No unsupported guarantee terms | deterministic (Section 8 blocklist) |
| APR/fee/reward matches product source | requires `product_terms` (returns `not_applicable` until populated) |
| Promo conditions present | hybrid (presence = deterministic; correctness = LLM) |
| Prequalification not described as approval | hybrid (keyword co-occurrence + LLM semantic check) |
| No invented lender/rate/reward | LLM (+ `product_terms` cross-check once available) |
| Claims have evidence + timestamps | LLM (`evidence_grounding` dimension) |
| Criteria based on product-fit, not compensation | LLM (`affiliate_integrity` dimension) |
| No protected-class targeting | LLM (`fairness` dimension) + deterministic keyword flags |
| Links resolve | **deferred** (see Out of Scope) |
| Disclosures visible mobile/desktop | **partial/deferred** — only a best-effort `display:none`/`visibility:hidden` source check; true visual/rendered verification is out of scope |
| No implied personalized advice | LLM |

---

## 3. Backend Structure (FastAPI)

```
backend/
  app/
    main.py                    # app factory, startup hook registers reconciliation sweep
    config.py                  # pydantic Settings — LLM provider/model, Supabase creds, all env-driven
    db/
      session.py                # async SQLAlchemy engine/session (pooled Supabase connection)
      models/                   # ORM models mirroring the schema above
      migrations/                # Alembic; first migration seeds rubric_dimensions (8 rows) + rule_definitions
    api/v1/
      routes/
        submissions.py          # POST /submissions/batch, GET /submissions, GET /submissions/{id}
        evaluation_runs.py      # GET /evaluation-runs/{id} (poll target), POST /{id}/retry
        exports.py              # POST /exports -> .xlsx
        rules.py, rubric.py     # read-only listing, for debugging/future admin UI
      deps.py
    ingestion/
      base.py, dto.py           # IngestionStrategy interface, ParsedSubmission/ParsedAsset DTOs
      excel_csv.py               # row-per-item, column-alias mapping, unmapped columns -> metadata jsonb
      html_email.py              # BeautifulSoup + `email` stdlib; inline base64 image extraction
      plaintext.py, image_standalone.py
      factory.py                 # picks strategy by extension/mime
    evaluation/
      job_runner.py              # JobRunner interface + BackgroundTasks impl
      reconciliation.py          # startup sweep for stale pending/running runs
      pipeline.py                 # orchestrates deterministic + LLM passes, computes overall rollup
      llm_judge/
        provider_interface.py     # LLMProvider ABC — the key seam for model swapping
        openai_provider.py        # only file that knows OpenAI SDK specifics
        provider_factory.py       # env-driven: LLM_PROVIDER, LLM_MODEL
        schema.py                  # vendor-agnostic JudgeResult/DimensionScore/ExtractedClaim (dimension_scores as a list keyed by dimension `key`, not fixed fields — so adding a 9th rubric dimension needs zero schema changes)
        prompt_builder.py           # builds prompt live from rubric_dimensions + rule_definitions.config (blocklist)
      deterministic/
        engine.py, registry.py     # RuleEngine + @register_rule("rule_key") pattern
        rules/                      # one file per rule, matched to rule_definitions.rule_key
    export/xlsx_builder.py
    storage/supabase_storage.py
    schemas/                        # API-layer Pydantic request/response models
  tests/{fixtures,unit,integration}/
  alembic.ini, pyproject.toml
```

**Key seams:**
- `LLMProvider` interface (`provider_interface.py`) + vendor-agnostic `JudgeResult` schema (`schema.py`) are what make the OpenAI→other-model swap a one-adapter change.
- `RuleEngine`/`registry.py` is what makes deterministic checks addable via a function + a data row.
- `pipeline.py` is the seam where the two independent evaluation paths (deterministic, LLM) combine into one run's results — keep it a thin orchestrator, not where rule/judge logic lives.

---

## 4. Frontend Structure (Next.js, App Router)

```
frontend/
  app/
    upload/page.tsx                     # upload form, content_type selector
    submissions/
      page.tsx                          # list: filter (status/content_type/date/overall_flag) + sort
      [id]/page.tsx                     # detail: rubric scores, deterministic results, claims, asset gallery
  components/
    upload/UploadForm.tsx, BatchUploadProgress.tsx
    submissions/SubmissionsTable.tsx, SubmissionStatusBadge.tsx, RubricScoreCard.tsx,
                DeterministicResultsTable.tsx, ClaimsList.tsx, AssetGallery.tsx
    export/ExportSelectionToolbar.tsx
  lib/api-client.ts, types.ts, polling.ts
  hooks/useSubmissions.ts
```

Polling: fixed 3–5s interval (React Query `refetchInterval`, stopped once status is terminal) on both list and detail views — no websockets/SSE in v1; low volume doesn't justify it.

---

## 5. LLM-as-Judge Design

- **Structured output**: OpenAI structured outputs / JSON schema mode guarantees a parseable response. Schema: `dimension_scores: [{dimension_key, score, rationale}]` as a **list**, not 8 fixed fields — so a future added rubric dimension needs only a new `rubric_dimensions` row, zero contract changes. Also returns `claims: [ExtractedClaim]` per the Section 16 model.
- **Prompt construction** is built live from data: the full Section 12 rubric text from `rubric_dimensions`, the Section 8 phrase list from `rule_definitions.config` (given to the LLM as context so it can also catch paraphrased near-misses the exact-match blocklist would miss), and instructions to extract claims.
- **Vision**: one combined multimodal call (text + images together), not a separate pass — a claim can span text and image (e.g., APR in a banner image, disclosure in body text), and merging two independently-scored passes would be more complex than it's worth at this volume. Cap images per call as a tuning parameter if a submission has unusually many.
- **Reliability**: on schema-validation failure, retry once with the validation error appended to the prompt before marking the run `failed`. Store `raw_model_response` for audit.
- Deterministic rules can also emit `claims` rows (e.g., a regex-extracted APR literal), with `rule_id` set instead of `rubric_dimension_id` — both paths converge on the same `claims` table.

---

## 6. Deployment (Railway)

- **Two Railway services**, one project: `backend` (FastAPI) and `frontend` (Next.js), independent build/restart cycles. No separate worker service in v1 (see Section 1 limitation).
- **Supabase** is external managed Postgres + Storage (not hosted on Railway). Backend uses the **pooled/transaction-mode** connection string (appropriate for a single-instance Railway backend) and the **service-role key** for Storage/DB access (acceptable since there's no auth/RLS yet in v1 — this means the backend is fully trusted; revisit toward RLS + scoped keys when auth is added).
- Since the frontend polls from the browser (client components), the backend needs a public HTTPS URL regardless of Railway's private networking — no proxy layer needed for v1.
- **Backend env vars**: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, `OPENAI_API_KEY`, `LLM_MAX_IMAGES_PER_SUBMISSION`, `LLM_TIMEOUT_SECONDS`, `RECONCILIATION_SWEEP_INTERVAL_SECONDS`, `RUN_STALE_THRESHOLD_SECONDS`, `CORS_ALLOWED_ORIGINS`.
- **Frontend env vars**: `NEXT_PUBLIC_API_BASE_URL`.
- **Migrations**: Alembic, run via a Railway release/pre-deploy command (or documented manual `railway run alembic upgrade head` step given low deploy frequency).

---

## 7. Explicitly Out of Scope for v1

- Authentication/authorization (schema leaves room for it: `uploaded_by_email`, `human_review_status`).
- URL-fetch or API-based content intake (only file upload).
- In-app approve/reject review workflow (`human_review_status` column exists, unused).
- Product-terms validation beyond graceful `not_applicable` (table exists, starts empty, no admin UI to maintain it).
- Post-publication monitoring/periodic re-check (guidelines Section 14 step 6).
- Per-run/user-selectable model routing (provider/model is global config).
- Affiliate link resolution checks (would need outbound HTTP calls with their own latency/failure handling — punted; `rule_definitions.active` makes it easy to add later without a new migration).
- True rendered/visual mobile-desktop disclosure-visibility verification (only a best-effort HTML-source heuristic).
- Websocket/SSE live updates and a dedicated worker/queue service (both have a documented upgrade path via the `JobRunner` interface).

---

## Verification

Since this phase delivers a design document rather than running code, verification is:
1. Confirm this doc is written to the repo and committed once approved.
2. Cross-check each schema table and rule/dimension mapping against the guidelines doc sections (8, 12, 13, 16) for fidelity — done inline above.
3. Before implementation begins, validate the two riskiest seams early with throwaway scripts: (a) an OpenAI structured-output call against the `JudgeResult` schema shape, and (b) a Supabase pooled-connection SQLAlchemy session — both are foundational enough that a false assumption here would ripple through the whole build.
4. Once implementation starts, standard verification applies per component: Alembic migration applies cleanly and seeds the two registry tables; ingestion unit tests against fixture files (sample `.xlsx`, `.html`, `.eml`, images); an end-to-end manual test (upload → poll → view results → export `.xlsx`) before considering v1 done.

### Critical files (build order)
1. `backend/app/db/models/*` + first Alembic migration (schema backbone, seeds `rubric_dimensions` + `rule_definitions`).
2. `backend/app/evaluation/llm_judge/schema.py` + `provider_interface.py` (vendor-agnostic contract everything else depends on).
3. `backend/app/evaluation/deterministic/registry.py` (rule extensibility pattern).
4. `backend/app/evaluation/pipeline.py` (where both evaluation paths combine).
5. `backend/app/ingestion/factory.py` + `html_email.py` (most complex intake logic — multi-format + image extraction).
