"use client";

import Link from "next/link";
import type { UploadBatchResponse } from "@/lib/types";

interface BatchUploadProgressProps {
  status: "idle" | "uploading" | "success" | "error";
  result?: UploadBatchResponse;
  error?: string;
}

export function BatchUploadProgress({
  status,
  result,
  error,
}: BatchUploadProgressProps) {
  if (status === "idle") return null;

  if (status === "uploading") {
    return (
      <p className="mt-4 text-sm text-zinc-600">Uploading and ingesting content&hellip;</p>
    );
  }

  if (status === "error") {
    return (
      <p className="mt-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
        Upload failed: {error}
      </p>
    );
  }

  if (status === "success" && result) {
    return (
      <div className="mt-4 rounded-md bg-green-50 px-4 py-3 text-sm text-green-800">
        <p>
          Created {result.submissions.length} submission
          {result.submissions.length === 1 ? "" : "s"} in batch{" "}
          <code>{result.batch_id}</code>.
        </p>
        <Link
          href="/submissions"
          className="mt-2 inline-block font-medium underline underline-offset-2"
        >
          View submissions &rarr;
        </Link>
      </div>
    );
  }

  return null;
}
