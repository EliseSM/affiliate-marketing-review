"use client";

import { Fragment } from "react";
import Link from "next/link";
import type { Submission } from "@/lib/types";
import { EvaluationSummaryDropdown } from "./EvaluationSummaryDropdown";
import { OverallFlagBadge, SubmissionStatusBadge } from "./SubmissionStatusBadge";

const TABLE_COLUMN_COUNT = 9;

type SortDirection = "asc" | "desc";

interface SubmissionsTableProps {
  submissions: Submission[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onToggleSelectAll: () => void;
  projectNameSort: SortDirection | null;
  onToggleProjectNameSort: () => void;
}

function formatDate(value: string): string {
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function SubmissionsTable({
  submissions,
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
  projectNameSort,
  onToggleProjectNameSort,
}: SubmissionsTableProps) {
  const allSelected =
    submissions.length > 0 && submissions.every((s) => selectedIds.has(s.id));

  if (submissions.length === 0) {
    return (
      <p className="rounded-md border border-dashed border-zinc-300 px-4 py-8 text-center text-sm text-zinc-500">
        No submissions match the current filters.
      </p>
    );
  }

  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="border-b border-zinc-200 text-left text-xs uppercase tracking-wide text-zinc-500">
          <th className="w-8 py-2">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={onToggleSelectAll}
              aria-label="Select all"
            />
          </th>
          <th className="py-2 pr-4">Content type</th>
          <th className="py-2 pr-4">
            <button
              type="button"
              onClick={onToggleProjectNameSort}
              className="flex items-center gap-1 uppercase tracking-wide text-zinc-500 hover:text-zinc-700"
            >
              Project
              <span aria-hidden="true" className={projectNameSort ? "text-zinc-900" : "text-zinc-400"}>
                {projectNameSort === "desc" ? "▼" : projectNameSort === "asc" ? "▲" : "⇅"}
              </span>
              <span className="sr-only">
                {projectNameSort === "asc"
                  ? "sorted ascending"
                  : projectNameSort === "desc"
                    ? "sorted descending"
                    : "not sorted"}
              </span>
            </button>
          </th>
          <th className="py-2 pr-4">Product</th>
          <th className="py-2 pr-4">Affiliate</th>
          <th className="py-2 pr-4">POC email</th>
          <th className="py-2 pr-4">Status</th>
          <th className="py-2 pr-4">Overall</th>
          <th className="py-2 pr-4">Created</th>
        </tr>
      </thead>
      <tbody>
        {submissions.map((submission) => (
          <Fragment key={submission.id}>
            <tr className="border-b border-zinc-100 hover:bg-zinc-50">
              <td className="py-2">
                <input
                  type="checkbox"
                  checked={selectedIds.has(submission.id)}
                  onChange={() => onToggleSelect(submission.id)}
                  aria-label={`Select submission ${submission.id}`}
                />
              </td>
              <td className="py-2 pr-4">
                <Link
                  href={`/submissions/${submission.id}`}
                  className="font-medium text-zinc-900 underline-offset-2 hover:underline"
                >
                  {submission.content_type.replace("_", " ")}
                </Link>
              </td>
              <td className="py-2 pr-4 text-zinc-600">
                {submission.project_name ?? "—"}
              </td>
              <td className="py-2 pr-4 text-zinc-600">
                {submission.product_identifier ?? "—"}
              </td>
              <td className="py-2 pr-4 text-zinc-600">
                {submission.affiliate_partner ?? "—"}
              </td>
              <td className="py-2 pr-4 text-zinc-600">
                {submission.poc_email ? (
                  <a
                    href={`mailto:${submission.poc_email}`}
                    className="underline-offset-2 hover:underline"
                  >
                    {submission.poc_email}
                  </a>
                ) : (
                  "—"
                )}
              </td>
              <td className="py-2 pr-4">
                <SubmissionStatusBadge status={submission.status} />
              </td>
              <td className="py-2 pr-4">
                <OverallFlagBadge flag={submission.latest_run?.overall_flag ?? null} />
              </td>
              <td className="py-2 pr-4 text-zinc-500">
                {formatDate(submission.created_at)}
              </td>
            </tr>
            {submission.latest_run?.summary && (
              <tr className="border-b border-zinc-100">
                <td colSpan={TABLE_COLUMN_COUNT} className="bg-white px-2 py-2">
                  <EvaluationSummaryDropdown summary={submission.latest_run?.summary ?? null} />
                </td>
              </tr>
            )}
          </Fragment>
        ))}
      </tbody>
    </table>
  );
}
