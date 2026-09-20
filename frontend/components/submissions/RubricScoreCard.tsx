import type { JudgeResultView, RubricScore } from "@/lib/types";

const SCORE_STYLES: Record<RubricScore, string> = {
  0: "border-red-300 bg-red-50",
  1: "border-amber-300 bg-amber-50",
  2: "border-green-300 bg-green-50",
};

const SCORE_LABELS: Record<RubricScore, string> = {
  0: "0 · Fail",
  1: "1 · Partial",
  2: "2 · Pass",
};

export function RubricScoreCard({ result }: { result: JudgeResultView }) {
  return (
    <div className={`rounded-md border p-4 ${SCORE_STYLES[result.score]}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-900">
          {result.display_name}
        </h3>
        <span className="text-xs font-medium text-zinc-700">
          {SCORE_LABELS[result.score]}
        </span>
      </div>
      <p className="mt-2 text-sm text-zinc-700">{result.rationale}</p>
    </div>
  );
}
