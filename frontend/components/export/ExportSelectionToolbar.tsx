"use client";

import { useMutation } from "@tanstack/react-query";
import { createExport } from "@/lib/api-client";

interface ExportSelectionToolbarProps {
  selectedIds: string[];
  onExported?: () => void;
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function ExportSelectionToolbar({
  selectedIds,
  onExported,
}: ExportSelectionToolbarProps) {
  const mutation = useMutation({
    mutationFn: () => createExport(selectedIds),
    onSuccess: (blob) => {
      const timestamp = new Date().toISOString().slice(0, 10);
      triggerDownload(blob, `affiliate-review-export-${timestamp}.xlsx`);
      onExported?.();
    },
  });

  return (
    <div className="flex items-center gap-3 rounded-md border border-zinc-200 bg-white px-4 py-3">
      <span className="text-sm text-zinc-600">
        {selectedIds.length} selected
      </span>
      <button
        type="button"
        disabled={selectedIds.length === 0 || mutation.isPending}
        onClick={() => mutation.mutate()}
        className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
      >
        {mutation.isPending ? "Exporting..." : "Export to Excel"}
      </button>
      {mutation.isError && (
        <span className="text-sm text-red-600">
          Export failed: {mutation.error.message}
        </span>
      )}
    </div>
  );
}
