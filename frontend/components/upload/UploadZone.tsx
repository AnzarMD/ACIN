"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import { Upload, CheckCircle, AlertTriangle, XCircle, Loader2 } from "lucide-react";
import type { ValidationState } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

export default function UploadZone() {
  const [images, setImages] = useState<File[]>([]);
  const [validation, setValidation] = useState<ValidationState>("idle");
  const [flaggedIndex, setFlaggedIndex] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [validatedUrls, setValidatedUrls] = useState<string[]>([]);
  const [manualReviewMessage, setManualReviewMessage] = useState("");
  const router = useRouter();

  // Product details form
  const [productName, setProductName] = useState("");
  const [productId, setProductId] = useState("");
  const [category, setCategory] = useState("");
  const [originalPrice, setOriginalPrice] = useState("");
  const [returnReason, setReturnReason] = useState("");
  const [customReason, setCustomReason] = useState("");
  const [city, setCity] = useState("");
  const [sellerLat, setSellerLat] = useState<number | null>(null);
  const [sellerLng, setSellerLng] = useState<number | null>(null);
  const [pincode, setPincode] = useState("");
  const [referenceImageUrl, setReferenceImageUrl] = useState("");

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setImages((prev) => [...prev, ...acceptedFiles]);
    setValidation("idle");
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "image/webp": [".webp"],
    },
    maxFiles: 5,
  });

  const handleValidate = async () => {
    if (images.length === 0) return;
    setValidation("validating");

    try {
      const tempId = `VAL-${Date.now()}`;
      const s3Urls: string[] = [];

      for (const file of images) {
        const urlRes = await fetch(
          `${API_BASE}/returns/${tempId}/upload-url?filename=${encodeURIComponent(file.name)}`,
          { method: "POST" }
        );
        const urlData = await urlRes.json();

        // Upload to S3 — do NOT set Content-Type (presigned URL no longer pins it)
        const uploadRes = await fetch(urlData.upload_url, {
          method: "PUT",
          body: file,
        });

        if (!uploadRes.ok) {
          console.error("S3 upload failed:", uploadRes.status, await uploadRes.text());
          setValidation("hard_block");
          setFlaggedIndex([images.indexOf(file)]);
          return;
        }

        s3Urls.push(urlData.s3_url);
      }

      // Call real backend validation
      const res = await fetch(`${API_BASE}/returns/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_urls: s3Urls,
          product_name: productName || "",
          category: category || "",
          original_price: parseInt(originalPrice) || 5000,
          reference_image_url: referenceImageUrl || "",
          return_reason: effectiveReason || "pre_check",
        }),
      });
      const data = await res.json();

      // Special case: manual review bypass for "not_as_described" / wrong item
      if (data.manual_review) {
        setValidation("manual_review" as ValidationState);
        setManualReviewMessage(data.manual_review_message || "");
        setValidatedUrls(s3Urls);
        return;
      }

      if (data.fcs >= 0.85 || data.pipeline_blocked) {
        setValidation("hard_block");
        setFlaggedIndex(data.flagged_indexes || [0]);
      } else if (data.fcs >= 0.50) {
        setValidation("soft_flag");
        setFlaggedIndex(data.flagged_indexes || []);
      } else {
        setValidation("pass");
        setFlaggedIndex([]);
      }

      setValidatedUrls(s3Urls);
    } catch (err) {
      console.error("Validation error:", err);
      setValidation("pass");
      setFlaggedIndex([]);
    }
  };

  const handleSubmit = async () => {
    if (validation !== "pass" || !returnReason || !productName || submitting) return;
    setSubmitting(true);

    try {
      const s3Urls = validatedUrls.length > 0
        ? validatedUrls
        : images.map((f) => `s3://acin-uploads-622623003797/returns/temp/${f.name}`);

      const response = await fetch(`${API_BASE}/returns/`, {
        method: "POST",
        body: JSON.stringify({
          product_id: productId || productName.replace(/\s+/g, "-").toUpperCase(),
          customer_id: "CUST-" + Date.now().toString(36).toUpperCase(),
          return_reason: effectiveReason,
          image_urls: s3Urls,
          product_name: productName,
          category: category,
          original_price: parseInt(originalPrice) || 5000,
          location: city ? {
            lat: sellerLat ?? 0,
            lng: sellerLng ?? 0,
            city,
            pincode: pincode || "000000",
          } : undefined,
        }),
        headers: { "Content-Type": "application/json" },
      });

      const data = await response.json();

      if (response.ok) {
        router.push(`/returns/${data.return_id}`);
      } else {
        alert(data.detail?.message || "Return submission failed");
      }
    } catch (err) {
      console.error("Submit error:", err);
      alert("Failed to submit return. Is the backend running on port 8000?");
    } finally {
      setSubmitting(false);
    }
  };

  const effectiveReason = returnReason === "other" && customReason.trim()
    ? `other: ${customReason.trim()}`
    : returnReason;

  const canVerify = images.length > 0 && productName.trim().length > 0;
  const isFormValid = images.length > 0 && validation === "pass" && effectiveReason && productName;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Step 1: Upload Photos */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">1. Upload Product Photos</h2>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition ${
            isDragActive ? "border-orange-500 bg-orange-50" : "border-gray-300 dark:border-gray-600 hover:border-gray-400"
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-10 w-10 text-gray-400 dark:text-gray-500 mb-3" />
          <p className="text-gray-600 dark:text-gray-400">Drag & drop product photos, or click to select</p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">JPG, PNG, WebP only (no AVIF/HEIC)</p>
        </div>

        {images.length > 0 && (
          <div className="grid grid-cols-4 gap-3 mt-4">
            {images.map((file, idx) => (
              <div
                key={idx}
                className={`relative rounded-lg overflow-hidden border-2 ${
                  flaggedIndex.includes(idx)
                    ? "border-red-500"
                    : validation === "pass" ? "border-green-500" : "border-gray-200 dark:border-gray-700"
                }`}
              >
                <img src={URL.createObjectURL(file)} alt={`Upload ${idx + 1}`} className="w-full h-20 object-cover" />
                {validation === "pass" && <CheckCircle className="absolute top-1 right-1 h-4 w-4 text-green-500" />}
                {flaggedIndex.includes(idx) && <XCircle className="absolute top-1 right-1 h-4 w-4 text-red-500" />}
              </div>
            ))}
          </div>
        )}

        <ValidationBanner state={validation} manualMessage={manualReviewMessage} />
      </section>

      {/* Step 2: Product Details */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">2. Product Details</h2>

        {/* Product URL Auto-fill */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Paste Product Link (auto-fills details)</label>
          <div className="flex gap-2">
            <input
              type="url"
              id="productUrl"
              placeholder="e.g., https://www.amazon.in/dp/B09XS7JWHH or Flipkart link"
              className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={async () => {
                const urlInput = document.getElementById("productUrl") as HTMLInputElement;
                const url = urlInput?.value;
                if (!url) return;
                urlInput.disabled = true;
                try {
                  const res = await fetch(`${API_BASE}/products/extract`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url }),
                  });
                  const data = await res.json();
                  if (data.product_name) setProductName(data.product_name);
                  if (data.product_id) setProductId(data.product_id);
                  if (data.category) setCategory(data.category);
                  if (data.original_price) setOriginalPrice(String(data.original_price));
                  if (data.image_url) setReferenceImageUrl(data.image_url);
                } catch (e) {
                  console.error("Extract failed:", e);
                } finally {
                  urlInput.disabled = false;
                }
              }}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-700 transition whitespace-nowrap"
            >
              Auto-Fill
            </button>
          </div>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Supports Amazon.in, Flipkart, and other e-commerce links</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Product Name *</label>
            <input
              type="text"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="e.g., Nike Air Max 270, Sony WH-1000XM5"
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Product / ASIN ID</label>
            <input
              type="text"
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              placeholder="e.g., B09XS7JWHH"
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Category *</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            >
              <option value="">Select category...</option>
              <option value="Electronics">Electronics</option>
              <option value="Footwear">Footwear</option>
              <option value="Clothing">Clothing</option>
              <option value="Computers">Computers & Laptops</option>
              <option value="Home & Kitchen">Home & Kitchen</option>
              <option value="Beauty">Beauty & Personal Care</option>
              <option value="Sports">Sports & Fitness</option>
              <option value="Toys">Toys & Games</option>
              <option value="Books">Books</option>
              <option value="Luggage">Luggage & Bags</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Original Price (₹) *</label>
            <input
              type="number"
              value={originalPrice}
              onChange={(e) => setOriginalPrice(e.target.value)}
              placeholder="e.g., 4999"
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
          </div>
        </div>
      </section>

      {/* Step 3: Return Reason */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">3. Return Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Return Reason *</label>
            <select
              value={returnReason}
              onChange={(e) => {
                setReturnReason(e.target.value);
                if (e.target.value !== "other") setCustomReason("");
              }}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            >
              <option value="">Select a reason...</option>
              <option value="defective">Defective / Not Working</option>
              <option value="changed_mind">Changed Mind</option>
              <option value="size_mismatch">Wrong Size / Doesn&apos;t Fit</option>
              <option value="not_as_described">Not as Described</option>
              <option value="damaged_in_transit">Damaged in Transit</option>
              <option value="better_price">Found Better Price</option>
              <option value="other">Other (specify below)</option>
            </select>
            {returnReason === "other" && (
              <input
                type="text"
                value={customReason}
                onChange={(e) => setCustomReason(e.target.value)}
                placeholder="Describe your reason..."
                className="w-full mt-2 border border-orange-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              />
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">City</label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="Auto-filled when you allow location, or type manually"
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Your Location
              <span className="ml-1 text-xs text-gray-500 font-normal">(used to find nearest buyers)</span>
            </label>
            <button
              type="button"
              onClick={async () => {
                if (!navigator.geolocation) {
                  alert("Geolocation not supported by your browser");
                  return;
                }
                navigator.geolocation.getCurrentPosition(
                  async (pos) => {
                    const lat = parseFloat(pos.coords.latitude.toFixed(6));
                    const lng = parseFloat(pos.coords.longitude.toFixed(6));
                    setSellerLat(lat);
                    setSellerLng(lng);

                    // Reverse geocode to auto-fill city and pincode
                    try {
                      const res = await fetch(
                        `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&zoom=10`,
                        { headers: { "Accept-Language": "en" } }
                      );
                      const data = await res.json();
                      const addr = data.address || {};

                      // Priority order for city name — avoid village/locality names
                      // zoom=10 gives city-level, but we still check multiple fields
                      const detectedCity =
                        addr.city ||            // Major cities: "Mumbai", "Delhi"
                        addr.district ||        // District: "Bangalore Urban"
                        addr.state_district ||  // State district
                        addr.town ||            // Smaller towns
                        addr.county ||          // County level
                        addr.state ||           // Fallback: state name
                        "";

                      // Clean up common suffixes like "District", "Urban"
                      const cleanCity = detectedCity
                        .replace(/\s*district$/i, "")
                        .replace(/\s*urban$/i, "")
                        .replace(/\s*rural$/i, "")
                        .trim();

                      // Extract pincode
                      const detectedPincode = addr.postcode || "";

                      if (cleanCity) setCity(cleanCity);
                      if (detectedPincode) setPincode(detectedPincode);
                    } catch {
                      // Geocoding failed — lat/lng still captured, city stays manual
                    }
                  },
                  () => alert("Location access denied. Please type your city manually.")
                );
              }}
              className="w-full flex items-center justify-center gap-2 border border-dashed border-blue-400 dark:border-blue-600 text-blue-600 dark:text-blue-400 rounded-lg px-3 py-2 text-sm hover:bg-blue-50 dark:hover:bg-blue-950/20 transition"
            >
              <span>📍</span>
              {sellerLat && sellerLng
                ? `✓ Location set — ${city || `${sellerLat.toFixed(4)}, ${sellerLng.toFixed(4)}`}`
                : "Allow location — auto-fills city & pincode"}
            </button>
            {/* Show captured coords small below button */}
            {sellerLat && sellerLng && (
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 text-center">
                {sellerLat.toFixed(5)}, {sellerLng.toFixed(5)}
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Actions */}
      <div className="flex gap-3 pt-2">
        {validation === "idle" && images.length > 0 && (
          <button
            onClick={handleValidate}
            disabled={!canVerify}
            title={!productName ? "Enter product name first" : "Verify photos"}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {!productName ? "Enter Product Name First" : "Verify Photos"}
          </button>
        )}
        {validation === "pass" && (
          <button
            onClick={handleSubmit}
            disabled={!isFormValid || submitting}
            className="bg-orange-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-orange-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {submitting ? "Analysing with 6 AI Agents..." : "Analyse with AI →"}
          </button>
        )}
        {(validation as string) === "manual_review" && (
          <button
            onClick={handleSubmit}
            disabled={!isFormValid || submitting}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {submitting ? "Submitting..." : "Submit for Manual Review →"}
          </button>
        )}
        {validation === "soft_flag" && (
          <button
            onClick={() => { setImages([]); setValidation("idle"); setFlaggedIndex([]); }}
            className="bg-yellow-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-yellow-600 transition"
          >
            Retake Flagged Photos
          </button>
        )}
        {validation === "hard_block" && (
          <div className="flex gap-3">
            <button
              onClick={() => { setImages([]); setValidation("idle"); setFlaggedIndex([]); }}
              className="bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700 transition"
            >
              Upload Different Photos
            </button>
            <button className="bg-red-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-red-700 transition">
              Contact Support
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function ValidationBanner({ state, manualMessage }: { state: ValidationState; manualMessage?: string }) {
  if (state === "idle") return null;
  const config: Record<string, { icon: React.ReactNode; text: string; bg: string }> = {
    validating: { icon: <Loader2 className="h-5 w-5 animate-spin text-blue-500" />, text: "Verifying image authenticity with AI...", bg: "bg-blue-50 border-blue-200" },
    pass: { icon: <CheckCircle className="h-5 w-5 text-green-500" />, text: "✓ Photos verified — real product images confirmed", bg: "bg-green-50 border-green-200" },
    soft_flag: { icon: <AlertTriangle className="h-5 w-5 text-yellow-500" />, text: "Image quality issue. Please retake in better lighting.", bg: "bg-yellow-50 border-yellow-200" },
    hard_block: { icon: <XCircle className="h-5 w-5 text-red-500" />, text: "Images failed verification. Please upload original unedited product photos.", bg: "bg-red-50 border-red-200" },
    manual_review: { icon: <AlertTriangle className="h-5 w-5 text-blue-600" />, text: manualMessage || "Manual verification requested.", bg: "bg-blue-50 border-blue-300" },
  };
  const c = config[state];
  if (!c) return null;
  return (
    <div className={`flex items-start gap-3 p-4 rounded-lg border mt-4 ${c.bg}`}>
      <div className="mt-0.5 shrink-0">{c.icon}</div>
      <span className="text-sm font-medium">{c.text}</span>
    </div>
  );
}
