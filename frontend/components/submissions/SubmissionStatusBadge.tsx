import type { OverallFlag, RunStatus, SubmissionStatus } from "@/lib/types";

const STATUS_STYLES: Record<SubmissionStatus | RunStatus, string> = {
  ingested: "bg-zinc-100 text-zinc-700",
  evaluating: "bg-blue-100 text-blue-700",
  evaluated: "bg-zinc-100 text-zinc-700",
  error: "bg-red-100 text-red-700",
  pending: "bg-zinc-100 text-zinc-700",
  running: "bg-blue-100 text-blue-700",
  completed: "bg-zinc-100 text-zinc-700",
  failed: "bg-red-100 text-red-700",
};

const FLAG_STYLES: Record<OverallFlag, string> = {
  pass: "bg-green-100 text-green-800",
  needs_review: "bg-amber-100 text-amber-800",
  fail: "bg-red-100 text-red-800",
};

function Badge({ label, className }: { label: string; className: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${className}`}
    >
      {label}
    </span>
  );
}

export function SubmissionStatusBadge({ status }: { status: SubmissionStatus }) {
  return <Badge label={status} className={STATUS_STYLES[status]} />;
}

export function RunStatusBadge({ status }: { status: RunStatus }) {
  return <Badge label={status} className={STATUS_STYLES[status]} />;
}

export function OverallFlagBadge({ flag }: { flag: OverallFlag | null }) {
  if (!flag) {
    return <Badge label="pending" className="bg-zinc-100 text-zinc-500" />;
  }
  return <Badge label={flag.replace("_", " ")} className={FLAG_STYLES[flag]} />;
}
