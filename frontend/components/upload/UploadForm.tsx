"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { uploadBatch } from "@/lib/api-client";
import type { ContentType, UploadBatchResponse } from "@/lib/types";
import { BatchUploadProgress } from "./BatchUploadProgress";

const CONTENT_TYPE_OPTIONS: { value: ContentType; label: string }[] = [
  { value: "web_page", label: "Web / landing page" },
  { value: "email", label: "Email marketing copy" },
  { value: "ad_copy", label: "Ad copy" },
];

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [contentType, setContentType] = useState<ContentType>("web_page");
  const [pocEmail, setPocEmail] = useState("");
  const [projectName, setProjectName] = useState("");

  const mutation = useMutation<UploadBatchResponse, Error, void>({
    mutationFn: () => {
      if (!file) {
        throw new Error("Choose a file first");
      }
      return uploadBatch(
        file,
        contentType,
        pocEmail.trim() || undefined,
        projectName.trim() || undefined
      );
    },
  });

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    mutation.mutate();
  };

  const status = mutation.isPending
    ? "uploading"
    : mutation.isSuccess
      ? "success"
      : mutation.isError
        ? "error"
        : "idle";

  return (
    <form onSubmit={handleSubmit} className="max-w-xl space-y-5">
      <div>
        <label htmlFor="content-type" className="block text-sm font-medium text-zinc-700">
          Content type
        </label>
        <select
          id="content-type"
          value={contentType}
          onChange={(event) => setContentType(event.target.value as ContentType)}
          className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-zinc-500 focus:outline-none"
        >
          {CONTENT_TYPE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="poc-email" className="block text-sm font-medium text-zinc-700">
          Point-of-contact email
        </label>
        <input
          id="poc-email"
          type="email"
          value={pocEmail}
          onChange={(event) => setPocEmail(event.target.value)}
          placeholder="marketer@example.com"
          className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-zinc-500 focus:outline-none"
        />
        <p className="mt-1 text-xs text-zinc-500">
          Who owns this marketing material, so a reviewer knows who to follow up with. Applied to
          every submission in this upload &mdash; leave blank if your Excel/CSV file already has a
          per-row &quot;poc_email&quot; column, since filling this in will override it.
        </p>
      </div>

      <div>
        <label htmlFor="project-name" className="block text-sm font-medium text-zinc-700">
          Project name
        </label>
        <input
          id="project-name"
          type="text"
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
          placeholder="e.g. Spring Loan Refresh"
          className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-zinc-500 focus:outline-none"
        />
        <p className="mt-1 text-xs text-zinc-500">
          Optional. Use the same name across resubmissions of the same marketing material (e.g.
          an improved version after a failed review) so they can be filtered together later.
        </p>
      </div>

      <div>
        <label htmlFor="file" className="block text-sm font-medium text-zinc-700">
          File (Excel/CSV for bulk, or a single HTML/plaintext/email file)
        </label>
        <input
          id="file"
          type="file"
          accept=".xlsx,.xls,.csv,.html,.htm,.eml,.txt,.jpg,.jpeg,.png,.gif"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          className="mt-1 block w-full text-sm text-zinc-700 file:mr-4 file:rounded-md file:border-0 file:bg-zinc-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-zinc-700"
        />
      </div>

      <button
        type="submit"
        disabled={!file || mutation.isPending}
        className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
      >
        {mutation.isPending ? "Uploading..." : "Submit for review"}
      </button>

      <BatchUploadProgress
        status={status}
        result={mutation.data}
        error={mutation.error?.message}
      />
    </form>
  );
}
