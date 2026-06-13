/**
 * Shared TypeScript types for ACIN frontend
 */

export type ValidationState = "idle" | "validating" | "pass" | "soft_flag" | "hard_block" | "manual_review";

export type Destination =
  | "INSTANT_RESALE"
  | "REFURBISH"
  | "EXCHANGE"
  | "DONATE"
  | "RECYCLE";

export type ReturnStatus =
  | "PENDING_REVIEW"
  | "ANALYZING"
  | "MANUAL_REVIEW"
  | "AI_DETECTED"
  | "DECIDED"
  | "COMPLETED";

export interface LocationData {
  lat: number;
  lng: number;
  city: string;
  pincode: string;
}

export interface ReturnCreateRequest {
  product_id: string;
  customer_id: string;
  return_reason: string;
  image_urls: string[];
  location?: LocationData;
}

export interface ReturnResponse {
  return_id: string;
  status: ReturnStatus;
  message?: string;
}

export interface Decision {
  return_id: string;
  destination: Destination;
  cvs_score: number;
  confidence: number;
  fraud_check: string;
  image_fcs: number;
  fraud_probability: number;
  listing_price: number;
  carbon_saved_kg: number;
  revenue_recovery_inr: number;
  trust_badges: string[];
  explanation: string;
}

export interface ProductAnalysis {
  condition_score: number;
  grade: "A" | "B" | "C" | "D";
  defects: Array<{ type: string; location: string; severity: string }>;
  packaging_status: string;
  usage_level: string;
  missing_parts: string[];
  safety_risk: boolean;
  fraud_probability: number;
  fraud_signals: string[];
  repair_recommendation: string;
  estimated_repair_cost_inr: number;
}

export interface MarketAnalysis {
  demand_score: number;
  buyer_count: number;
  expected_sale_days: number;
  region: string;
  demand_trend: string;
}

export interface PricingAnalysis {
  fast_sale_price: number;
  balanced_price: number;
  max_profit_price: number;
  recommended_strategy: string;
  original_price: number;
  discount_percentage?: number;
  market_insight?: string;
}

export interface ImpactMetrics {
  total_returns_processed: number;
  total_co2_saved_kg: number;
  total_revenue_recovered_inr: number;
  landfill_diverted_percentage: number;
  average_processing_time_hours: number;
  destinations: Record<Destination, { count: number; percentage: number }>;
  fraud_metrics: {
    total_flagged: number;
    ai_generated_blocked: number;
    condition_mismatch_flagged: number;
    fraud_prevented_value_inr: number;
  };
}
