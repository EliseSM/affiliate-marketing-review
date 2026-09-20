"use client";

import { Suspense, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useSubmissionsList, useSubmissionTabCounts } from "@/hooks/useSubmissions";
import { SubmissionsTable } from "@/components/submissions/SubmissionsTable";
import { ExportSelectionToolbar } from "@/components/export/ExportSelectionToolbar";
import type {
  ContentType,
  OverallFlag,
  SubmissionListFilters,
  SubmissionStatus,
} from "@/lib/types";

type Tab = "active" | "exported";

// "exported" isn't offered as a status filter choice within the Active tab --
// it's a separate tab dimension (see Tab above), not a per-item status filter.
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
  const queryClient = useQueryClient();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const tab: Tab = searchParams.get("tab") === "exported" ? "exported" : "active";

  const filters: SubmissionListFilters = useMemo(
    () => ({
      status: tab === "exported" ? "exported" : (searchParams.get("status") as SubmissionStatus) || undefined,
      exclude_status: tab === "active" ? "exported" : undefined,
      content_type:
        (searchParams.get("content_type") as ContentType) || undefined,
      overall_flag:
        (searchParams.get("overall_flag") as OverallFlag) || undefined,
      sort: searchParams.get("sort") || undefined,
    }),
    [tab, searchParams]
  );

  const { data, isLoading, isError, error } = useSubmissionsList(filters);
  const submissions = data ?? [];
  const tabCounts = useSubmissionTabCounts();

  const projectNameSort =
    filters.sort === "project_name" ? "asc" : filters.sort === "-project_name" ? "desc" : null;

  function toggleProjectNameSort() {
    const params = new URLSearchParams(searchParams.toString());
    if (projectNameSort === null) {
      params.set("sort", "project_name");
    } else if (projectNameSort === "asc") {
      params.set("sort", "-project_name");
    } else {
      params.delete("sort");
    }
    router.replace(`/submissions?${params.toString()}`);
  }

  function updateFilter(key: keyof SubmissionListFilters, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    router.replace(`/submissions?${params.toString()}`);
  }

  function switchTab(nextTab: Tab) {
    const params = new URLSearchParams(searchParams.toString());
    if (nextTab === "active") {
      params.delete("tab");
      params.delete("status");
    } else {
      params.set("tab", "exported");
      params.delete("status");
    }
    setSelectedIds(new Set());
    router.replace(`/submissions?${params.toString()}`);
  }

  function handleExported() {
    setSelectedIds(new Set());
    queryClient.invalidateQueries({ queryKey: ["submissions"] });
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

      <div className="mt-4 flex gap-1 border-b border-zinc-200">
        {(["active", "exported"] as Tab[]).map((tabOption) => {
          const count = tabCounts[tabOption];
          const isSelected = tab === tabOption;
          return (
            <button
              key={tabOption}
              type="button"
              onClick={() => switchTab(tabOption)}
              className={`-mb-px flex items-center gap-2 border-b-2 px-3 py-2 text-sm font-medium ${
                isSelected
                  ? "border-zinc-900 text-zinc-900"
                  : "border-transparent text-zinc-500 hover:text-zinc-700"
              }`}
            >
              {tabOption === "active" ? "Active" : "Exported (reviewed)"}
              {typeof count === "number" && (
                <span
                  className={`inline-flex min-w-[1.5rem] items-center justify-center rounded-full px-1.5 py-0.5 text-xs font-semibold tabular-nums ${
                    isSelected
                      ? "bg-zinc-900 text-white"
                      : "bg-zinc-100 text-zinc-600"
                  }`}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="mt-4 flex flex-wrap items-end gap-4">
        {tab === "active" && (
          <FilterSelect
            label="Status"
            value={filters.status ?? ""}
            options={STATUS_OPTIONS}
            onChange={(value) => updateFilter("status", value)}
          />
        )}
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
          onExported={handleExported}
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
            projectNameSort={projectNameSort}
            onToggleProjectNameSort={toggleProjectNameSort}
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
