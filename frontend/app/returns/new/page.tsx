import UploadZone from "@/components/upload/UploadZone";

export default function NewReturnPage() {
  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Start a Return</h1>
        <p className="text-gray-600 dark:text-gray-300 mt-2">
          Upload product photos and we&apos;ll find the best second life for your item.
        </p>
      </div>
      <UploadZone />
    </div>
  );
}
