import type { SubmissionAsset } from "@/lib/types";

export function AssetGallery({ assets }: { assets: SubmissionAsset[] }) {
  if (assets.length === 0) {
    return <p className="text-sm text-zinc-500">No images or attachments.</p>;
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
      {assets.map((asset) => (
        <figure
          key={asset.id}
          className="overflow-hidden rounded-md border border-zinc-200 bg-white"
        >
          {asset.mime_type.startsWith("image/") ? (
            // Storage URLs come from an arbitrary Supabase project domain,
            // so next/image remote-pattern allowlisting isn't practical here.
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={asset.storage_url}
              alt={asset.asset_type.replace("_", " ")}
              className="h-32 w-full object-cover"
            />
          ) : (
            <a
              href={asset.storage_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex h-32 items-center justify-center text-sm text-zinc-500 underline"
            >
              View attachment
            </a>
          )}
          <figcaption className="px-2 py-1 text-xs text-zinc-500">
            {asset.asset_type.replace("_", " ")}
          </figcaption>
        </figure>
      ))}
    </div>
  );
}
