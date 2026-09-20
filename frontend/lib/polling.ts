import type { RunStatus } from "./types";

export const POLL_INTERVAL_MS = 4_000;

const NON_TERMINAL_STATUSES: RunStatus[] = ["pending", "running"];

export function isNonTerminalRunStatus(status: RunStatus | undefined | null): boolean {
  if (!status) return false;
  return NON_TERMINAL_STATUSES.includes(status);
}

/**
 * React Query `refetchInterval` callback: keep polling at a fixed interval
 * while the run is pending/running, stop once it reaches a terminal status.
 */
export function runStatusRefetchInterval(status: RunStatus | undefined | null): number | false {
  return isNonTerminalRunStatus(status) ? POLL_INTERVAL_MS : false;
}
