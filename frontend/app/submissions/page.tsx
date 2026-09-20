"use client";

import { Suspense, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useSubmissionsList } from "@/hooks/useSubmissions";
import { SubmissionsTable } from "@/components/submissions/SubmissionsTable";
import { ExportSelectionToolbar } from "@/components/export/ExportSelectionToolbar";
import type {
  ContentType,
  OverallFlag,
  SubmissionListFilters,
  SubmissionStatus,
} from "@/lib/types";

const STATUS_OPTIONS: SubmissionStatus[] = [
  "ingested",
  "evaluating",
  "evaluated",
  "error",
];
const CONTENT_TYPE_OPTIONS: ContentType[] = ["web_page", "email", "ad_copy"];
const FLAG_OPTIONS: OverallFlag[] = ["pass", "needs_review", "fail"];

function FilterSelect<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T | "";
  options: T[];
  onChange: (value: T | "") => void;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium text-zinc-600">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as T | "")}
        className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-sm text-zinc-900"
      >
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option.replace("_", " ")}
          </option>
        ))}
      </select>
    </label>
  );
}

function SubmissionsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const filters: SubmissionListFilters = useMemo(
    () => ({
      status: (searchParams.get("status") as SubmissionStatus) || undefined,
      content_type:
        (searchParams.get("content_type") as ContentType) || undefined,
      overall_flag:
        (searchParams.get("overall_flag") as OverallFlag) || undefined,
    }),
    [searchParams]
  );

  const { data, isLoading, isError, error } = useSubmissionsList(filters);
  const submissions = data ?? [];

  function updateFilter(key: keyof SubmissionListFilters, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    router.push(`/submissions?${params.toString()}`);
  }

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function toggleSelectAll() {
    setSelectedIds((prev) => {
      const allSelected = submissions.every((s) => prev.has(s.id));
      return allSelected ? new Set() : new Set(submissions.map((s) => s.id));
    });
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Submissions</h1>
      </div>

      <div className="mt-4 flex flex-wrap items-end gap-4">
        <FilterSelect
          label="Status"
          value={filters.status ?? ""}
          options={STATUS_OPTIONS}
          onChange={(value) => updateFilter("status", value)}
        />
        <FilterSelect
          label="Content type"
          value={filters.content_type ?? ""}
          options={CONTENT_TYPE_OPTIONS}
          onChange={(value) => updateFilter("content_type", value)}
        />
        <FilterSelect
          label="Overall flag"
          value={filters.overall_flag ?? ""}
          options={FLAG_OPTIONS}
          onChange={(value) => updateFilter("overall_flag", value)}
        />
      </div>

      <div className="mt-4">
        <ExportSelectionToolbar
          selectedIds={Array.from(selectedIds)}
          onExported={() => setSelectedIds(new Set())}
        />
      </div>

      <div className="mt-6 overflow-x-auto rounded-md border border-zinc-200 bg-white p-4">
        {isLoading && <p className="text-sm text-zinc-500">Loading submissions&hellip;</p>}
        {isError && (
          <p className="text-sm text-red-600">
            Failed to load submissions: {error.message}
          </p>
        )}
        {!isLoading && !isError && (
          <SubmissionsTable
            submissions={submissions}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onToggleSelectAll={toggleSelectAll}
          />
        )}
      </div>
    </div>
  );
}

export default function SubmissionsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-zinc-500">Loading&hellip;</p>}>
      <SubmissionsPageContent />
    </Suspense>
  );
}
