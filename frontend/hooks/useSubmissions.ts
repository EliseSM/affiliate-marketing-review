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
