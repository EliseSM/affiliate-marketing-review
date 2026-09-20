import { useQuery } from "@tanstack/react-query";
import {
  getEvaluationRun,
  getSubmission,
  listSubmissions,
} from "@/lib/api-client";
import { runStatusRefetchInterval } from "@/lib/polling";
import type { SubmissionListFilters } from "@/lib/types";

export function useSubmissionsList(filters: SubmissionListFilters) {
  return useQuery({
    queryKey: ["submissions", filters],
    queryFn: () => listSubmissions(filters),
    refetchInterval: (query) => {
      const items = query.state.data ?? [];
      const hasActiveRun = items.some((item) =>
        item.latest_run
          ? runStatusRefetchInterval(item.latest_run.status) !== false
          : false
      );
      return hasActiveRun ? 4_000 : false;
    },
  });
}

// Counts for the Active/Exported tab labels. Independent of whatever
// content_type/overall_flag filters are currently applied within a tab --
// these reflect the total membership of each tab, like an inbox count.
export function useSubmissionTabCounts() {
  const active = useQuery({
    queryKey: ["submissions", { exclude_status: "exported" }],
    queryFn: () => listSubmissions({ exclude_status: "exported" }),
  });
  const exported = useQuery({
    queryKey: ["submissions", { status: "exported" }],
    queryFn: () => listSubmissions({ status: "exported" }),
  });

  return {
    active: active.data?.length,
    exported: exported.data?.length,
  };
}

export function useSubmission(id: string) {
  return useQuery({
    queryKey: ["submission", id],
    queryFn: () => getSubmission(id),
    enabled: Boolean(id),
    refetchInterval: (query) =>
      runStatusRefetchInterval(query.state.data?.latest_run?.status),
  });
}

export function useEvaluationRunPolling(runId: string | undefined) {
  return useQuery({
    queryKey: ["evaluation-run", runId],
    queryFn: () => getEvaluationRun(runId as string),
    enabled: Boolean(runId),
    refetchInterval: (query) => runStatusRefetchInterval(query.state.data?.status),
  });
}
