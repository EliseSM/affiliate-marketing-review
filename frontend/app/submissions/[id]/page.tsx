"use client";

import { use } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useSubmission } from "@/hooks/useSubmissions";
import { retryEvaluationRun } from "@/lib/api-client";
import { RubricScoreCard } from "@/components/submissions/RubricScoreCard";
import { DeterministicResultsTable } from "@/components/submissions/DeterministicResultsTable";
import { ClaimsList } from "@/components/submissions/ClaimsList";
import { AssetGallery } from "@/components/submissions/AssetGallery";
import {
  OverallFlagBadge,
  RunStatusBadge,
} from "@/components/submissions/SubmissionStatusBadge";

interface SubmissionDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function SubmissionDetailPage({
  params,
}: SubmissionDetailPageProps) {
  const { id } = use(params);
  const queryClient = useQueryClient();
  const { data: submission, isLoading, isError, error } = useSubmission(id);

  const retryMutation = useMutation({
    mutationFn: () => retryEvaluationRun(submission!.latest_run!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["submission", id] });
    },
  });

  if (isLoading) {
    return <p className="text-sm text-zinc-500">Loading submission&hellip;</p>;
  }

  if (isError || !submission) {
    return (
      <p className="text-sm text-red-600">
        Failed to load submission: {error?.message}
      </p>
    );
  }

  const run = submission.latest_run;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">
          {submission.content_type.replace("_", " ")} submission
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          {submission.product_identifier ?? "No product identifier"} &middot;{" "}
          {submission.affiliate_partner ?? "No affiliate partner"} &middot;{" "}
          {submission.poc_email ? (
            <>
              POC:{" "}
              <a href={`mailto:${submission.poc_email}`} className="underline-offset-2 hover:underline">
                {submission.poc_email}
              </a>
            </>
          ) : (
            "No point-of-contact email"
          )}
        </p>
        <div className="mt-3 flex items-center gap-3">
          {run && <RunStatusBadge status={run.status} />}
          <OverallFlagBadge flag={run?.overall_flag ?? null} />
          {run?.status === "failed" && (
            <button
              type="button"
              onClick={() => retryMutation.mutate()}
              disabled={retryMutation.isPending}
              className="rounded-md bg-zinc-900 px-3 py-1 text-xs font-medium text-white disabled:opacity-50"
            >
              {retryMutation.isPending ? "Retrying..." : "Retry evaluation"}
            </button>
          )}
        </div>
      </div>

      <section>
        <h2 className="text-lg font-semibold">Content</h2>
        <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded-md border border-zinc-200 bg-white p-4 text-sm text-zinc-700">
          {submission.raw_text}
        </pre>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Assets</h2>
        <div className="mt-2">
          <AssetGallery assets={submission.assets} />
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold">LLM-as-judge rubric</h2>
        {!run || run.judge_results.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-500">
            No judge results yet — evaluation may still be running.
          </p>
        ) : (
          <div className="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-2">
            {run.judge_results.map((result) => (
              <RubricScoreCard key={result.dimension_key} result={result} />
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold">Deterministic checks</h2>
        <div className="mt-2 rounded-md border border-zinc-200 bg-white p-4">
          <DeterministicResultsTable results={run?.deterministic_results ?? []} />
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Claims</h2>
        <div className="mt-2">
          <ClaimsList claims={run?.claims ?? []} />
        </div>
      </section>
    </div>
  );
}
