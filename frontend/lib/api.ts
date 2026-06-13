/**
 * ACIN API Client
 */

import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// ─── Returns ────────────────────────────────────────────────────────────────

export async function createReturn(data: {
  product_id: string;
  customer_id: string;
  return_reason: string;
  image_urls: string[];
  location?: { lat: number; lng: number; city: string; pincode: string };
}) {
  const response = await api.post("/returns", data);
  return response.data;
}

export async function getReturn(returnId: string) {
  const response = await api.get(`/returns/${returnId}`);
  return response.data;
}

export async function getDecision(returnId: string) {
  const response = await api.get(`/returns/${returnId}/decision`);
  return response.data;
}

export async function getUploadUrl(returnId: string, filename: string) {
  const response = await api.post(`/returns/${returnId}/upload-url?filename=${filename}`);
  return response.data;
}

export async function submitFeedback(returnId: string, feedback: object) {
  const response = await api.post(`/returns/${returnId}/feedback`, feedback);
  return response.data;
}

// ─── Products ───────────────────────────────────────────────────────────────

export async function getDemand(asin: string, city?: string) {
  const params = city ? `?city=${city}` : "";
  const response = await api.get(`/products/${asin}/demand${params}`);
  return response.data;
}

export async function getPriceSuggestion(asin: string, conditionScore: number, originalPrice: number) {
  const response = await api.get(
    `/products/${asin}/price-suggestion?condition_score=${conditionScore}&original_price=${originalPrice}`
  );
  return response.data;
}

// ─── Analytics ──────────────────────────────────────────────────────────────

export async function getImpactMetrics() {
  const response = await api.get("/analytics/impact");
  return response.data;
}

export async function getDailyImpact(days: number = 7) {
  const response = await api.get(`/analytics/impact/daily?days=${days}`);
  return response.data;
}

// ─── Validation (frontend proxy) ────────────────────────────────────────────

export async function validateImages(formData: FormData) {
  const response = await api.post("/returns/validate-images", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export default api;
