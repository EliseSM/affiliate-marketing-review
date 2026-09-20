"use client";

import { useState } from "react";
import type { RunSummary } from "@/lib/types";

const SEVERITY_STYLES: Record<string, string> = {
  low: "bg-zinc-100 text-zinc-700",
  medium: "bg-amber-100 text-amber-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
};

interface EvaluationSummaryDropdownProps {
  summary: RunSummary | null;
}

// Renders only the already-persisted `summary` produced by the backend at
// evaluation time (see app/evaluation/summary_builder.py) -- this component
// never computes or fetches an explanation itself, it only formats stored data.
export function EvaluationSummaryDropdown({ summary }: EvaluationSummaryDropdownProps) {
  const [open, setOpen] = useState(false);

  if (!summary) {
    return (
      <p className="text-xs text-zinc-500">
        No evaluation summary was stored for this run.
      </p>
    );
  }

  const didPass = summary.outcome === "pass";

  return (
    <div className="rounded-md border border-zinc-200 bg-zinc-50">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-medium text-zinc-700"
        aria-expanded={open}
      >
        <span>
          {didPass
            ? "Claims made in this submission (verify before relying on this result)"
            : "Why this submission did not pass"}
        </span>
        <span aria-hidden="true">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="border-t border-zinc-200 px-3 py-3">
          {didPass ? (
            summary.claims_to_verify.length > 0 ? (
              <ul className="space-y-2">
                {summary.claims_to_verify.map((claim, index) => (
                  <li key={index} className="text-sm text-zinc-700">
                    <span
                      className={`mr-2 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                        SEVERITY_STYLES[claim.severity] ?? SEVERITY_STYLES.low
                      }`}
                    >
                      {claim.claim_type.replace("_", " ")}
                    </span>
                    {claim.claim_text}
                    {claim.product_identifier && (
                      <span className="ml-2 text-xs text-zinc-500">
                        ({claim.product_identifier})
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-zinc-500">
                No specific factual claims were identified in this content. Review the full
                rubric breakdown on the submission&rsquo;s detail page for the complete picture.
              </p>
            )
          ) : summary.reasons.length > 0 ? (
            <ul className="list-disc space-y-1 pl-4">
              {summary.reasons.map((reason, index) => (
                <li key={index} className="text-sm text-zinc-700">
                  {reason}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-zinc-500">
              This run was flagged for review, but no specific dimension or rule failure was
              recorded. See the full breakdown on the submission&rsquo;s detail page.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
