import { UploadForm } from "@/components/upload/UploadForm";

export default function UploadPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold">Submit content for review</h1>
      <p className="mt-1 text-sm text-zinc-600">
        Upload a bulk Excel/CSV tracker, or a single web page, email, or ad copy
        file for automated compliance evaluation.
      </p>
      <div className="mt-6">
        <UploadForm />
      </div>
    </div>
  );
}
