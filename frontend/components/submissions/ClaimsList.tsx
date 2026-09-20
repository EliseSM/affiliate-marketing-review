import type { ClaimSeverity, ClaimView, EvaluatorResult } from "@/lib/types";

const SEVERITY_STYLES: Record<ClaimSeverity, string> = {
  low: "bg-zinc-100 text-zinc-700",
  medium: "bg-amber-100 text-amber-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
};

const EVALUATOR_RESULT_STYLES: Record<EvaluatorResult, string> = {
  supported: "text-green-700",
  unsupported: "text-red-700",
  contradicted: "text-red-700",
  unverifiable: "text-zinc-500",
};

export function ClaimsList({ claims }: { claims: ClaimView[] }) {
  if (claims.length === 0) {
    return <p className="text-sm text-zinc-500">No claims extracted.</p>;
  }

  return (
    <ul className="space-y-3">
      {claims.map((claim, index) => (
        <li
          key={index}
          className="rounded-md border border-zinc-200 bg-white p-3 text-sm"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${SEVERITY_STYLES[claim.severity]}`}
            >
              {claim.severity}
            </span>
            <span className="text-xs uppercase tracking-wide text-zinc-500">
              {claim.claim_type.replace("_", " ")}
            </span>
            <span
              className={`text-xs font-medium ${EVALUATOR_RESULT_STYLES[claim.evaluator_result]}`}
            >
              {claim.evaluator_result}
            </span>
          </div>
          <p className="mt-1 text-zinc-800">{claim.claim_text}</p>
          {claim.source_reference && (
            <p className="mt-1 text-xs text-zinc-500">
              Source: {claim.source_reference}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}
