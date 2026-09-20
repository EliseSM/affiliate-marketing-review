import type { DeterministicResult, DeterministicResultView } from "@/lib/types";

const RESULT_STYLES: Record<DeterministicResult, string> = {
  pass: "bg-green-100 text-green-800",
  fail: "bg-red-100 text-red-800",
  warn: "bg-amber-100 text-amber-800",
  not_applicable: "bg-zinc-100 text-zinc-500",
};

export function DeterministicResultsTable({
  results,
}: {
  results: DeterministicResultView[];
}) {
  if (results.length === 0) {
    return <p className="text-sm text-zinc-500">No deterministic checks ran.</p>;
  }

  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="border-b border-zinc-200 text-left text-xs uppercase tracking-wide text-zinc-500">
          <th className="py-2 pr-4">Rule</th>
          <th className="py-2 pr-4">Result</th>
          <th className="py-2 pr-4">Evidence</th>
        </tr>
      </thead>
      <tbody>
        {results.map((result) => (
          <tr key={result.rule_key} className="border-b border-zinc-100">
            <td className="py-2 pr-4 font-medium text-zinc-900">
              {result.display_name}
            </td>
            <td className="py-2 pr-4">
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${RESULT_STYLES[result.result]}`}
              >
                {result.result.replace("_", " ")}
              </span>
            </td>
            <td className="py-2 pr-4 text-zinc-600">
              {result.evidence ? (
                <pre className="whitespace-pre-wrap text-xs text-zinc-600">
                  {JSON.stringify(result.evidence, null, 2)}
                </pre>
              ) : (
                "—"
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
