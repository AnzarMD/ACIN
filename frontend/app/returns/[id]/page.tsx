"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Loader2, CheckCircle } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
import ConditionCard from "@/components/analysis/ConditionCard";
import DemandMap from "@/components/analysis/DemandMap";
import LogisticsCard from "@/components/analysis/LogisticsCard";
import PricingCard from "@/components/pricing/PricingCard";
import dynamic from "next/dynamic";

// Leaflet requires browser APIs — must be loaded client-side only
const HyperlocalMap = dynamic(
  () => import("@/components/analysis/HyperlocalMap"),
  { ssr: false, loading: () => <div className="h-96 bg-gray-100 dark:bg-gray-800 rounded-xl animate-pulse" /> }
);
import DecisionCard from "@/components/decision/DecisionCard";
import ValidationStatusCard from "@/components/validation/ValidationStatus";

export default function ReturnAnalysisPage() {
  const params = useParams();
  const returnId = (params?.id as string) || "";
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("ANALYZING");
  const [validation, setValidation] = useState<any>(null);
  const [product, setProduct] = useState<any>(null);
  const [market, setMarket] = useState<any>(null);
  const [pricing, setPricing] = useState<any>(null);
  const [logistics, setLogistics] = useState<any>(null);
  const [decision, setDecision] = useState<any>(null);
  const [sellerLat, setSellerLat] = useState<number | null>(null);
  const [sellerLng, setSellerLng] = useState<number | null>(null);
  const [sellerCity, setSellerCity] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    const fetchData = async () => {
      try {
        // Fetch all return items
        const res = await fetch(`${API_BASE}/returns/${returnId}`);
        if (!res.ok) {
          setError("Return not found");
          setLoading(false);
          return;
        }
        const data = await res.json();
        const items = data.items || [];

        // Parse items by entity type
        for (const item of items) {
          const sk = item.SK || "";
          const entityType = item.entity_type || "";

          if (sk === "META") {
            setStatus(item.status || "ANALYZING");
            // Extract seller location from META
            if (item.lat) setSellerLat(parseFloat(String(item.lat)));
            if (item.lng) setSellerLng(parseFloat(String(item.lng)));
            if (item.city) setSellerCity(item.city);
          }

          if (entityType === "IMAGE_VALIDATION" || sk.startsWith("VALIDATION#")) {
            setValidation({
              fcs: parseFloat(item.fcs || "0"),
              status: item.status || "AUTHENTIC",
            });
          }

          if (entityType === "AGENT_OUTPUT" && item.agent === "PRODUCT") {
            const payload = item.payload || {};
            setProduct({
              condition_score: payload.condition_score || 0,
              grade: payload.grade || "B",
              defects: payload.defects || [],
              packaging_status: payload.packaging_status || "intact",
              usage_level: payload.usage_level || "light",
              missing_parts: payload.missing_parts || [],
              safety_risk: payload.safety_risk || false,
              fraud_probability: payload.fraud_probability || 0,
              fraud_signals: payload.fraud_signals || [],
              repair_recommendation: payload.repair_recommendation || "",
              estimated_repair_cost_inr: payload.estimated_repair_cost_inr || 0,
            });
          }

          if (entityType === "AGENT_OUTPUT" && item.agent === "MARKET") {
            const payload = item.payload || {};
            setMarket({
              demand_score: payload.demand_score || 0,
              buyer_count: payload.buyer_count || 0,
              expected_sale_days: payload.expected_sale_days || 0,
              region: payload.region || "Local",
              demand_trend: payload.demand_trend || "stable",
            });
          }

          if (entityType === "AGENT_OUTPUT" && item.agent === "LOGISTICS") {
            const payload = item.payload || {};
            setLogistics({
              selected_route: payload.selected_route || "WAREHOUSE",
              route_score: parseFloat(payload.route_score || "0"),
              distance_km: parseFloat(payload.distance_km || "0"),
              total_cost_inr: parseInt(payload.total_cost_inr || payload.cost_inr || "0"),
              eta_hours: parseFloat(payload.eta_hours || "0"),
              carbon_kg: parseFloat(payload.carbon_kg || payload.co2_kg || "0"),
              carbon_saved_vs_default_kg: parseFloat(payload.carbon_saved_vs_default_kg || "0"),
              demand_match: parseFloat(payload.demand_match || "0"),
              capacity_reliability: parseFloat(payload.capacity_reliability || "0"),
              risk_score: parseFloat(payload.risk_score || "0"),
              alternatives: payload.alternatives || [],
              reason: payload.reason || "",
              rule_version: payload.rule_version || "",
            });
          }

          if (entityType === "AGENT_OUTPUT" && item.agent === "PRICING") {
            const payload = item.payload || {};
            setPricing({
              fast_sale_price: payload.fast_sale_price || 0,
              balanced_price: payload.balanced_price || 0,
              max_profit_price: payload.max_profit_price || 0,
              recommended_strategy: payload.recommended_strategy || "balanced",
              original_price: payload.original_price || 0,
            });
          }

          if (entityType === "DECISION_LATEST" || sk === "DECISION#LATEST") {
            setDecision({
              return_id: returnId,
              destination: item.destination || "",
              cvs_score: parseFloat(item.cvs_score || "0"),
              confidence: parseInt(item.confidence || "0"),
              fraud_check: item.fraud_check || "CLEAR",
              image_fcs: parseFloat(item.image_fcs || "0"),
              fraud_probability: parseFloat(item.fraud_probability || "0"),
              listing_price: parseInt(item.listing_price || "0"),
              carbon_saved_kg: parseFloat(item.carbon_saved_kg || "0"),
              revenue_recovery_inr: parseInt(item.revenue_recovery_inr || "0"),
              trust_badges: item.trust_badges || [],
              explanation: item.explanation || "",
            });
            setStatus("DECIDED");
          }
        }

        setLoading(false);

        // Stop polling if decided
        if (items.some((i: any) => i.entity_type === "DECISION_LATEST" || i.SK === "DECISION#LATEST")) {
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Fetch error:", err);
        setLoading(false);
      }
    };

    // Poll every 3 seconds until decision is ready
    fetchData();
    interval = setInterval(fetchData, 3000);

    return () => clearInterval(interval);
  }, [returnId]);

  if (error) {
    return <div className="text-center py-20 text-red-500">{error}</div>;
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="h-12 w-12 animate-spin text-orange-500 mb-4" />
        <p className="text-gray-600 dark:text-gray-400">Running AI agents on your return...</p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">This takes 10-20 seconds</p>
      </div>
    );
  }

  // Determine progress stage
  const stage = decision ? 6 : logistics ? 5 : pricing ? 4 : market ? 3 : product ? 2 : validation ? 1 : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Return Analysis</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">ID: {returnId}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          status === "DECIDED" || status === "COMPLETED"
            ? "bg-green-100 text-green-700"
            : status === "AI_DETECTED"
            ? "bg-red-100 text-red-700"
            : "bg-yellow-100 text-yellow-700"
        }`}>
          {status}
        </span>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-1">
        {["Validation", "Condition", "Demand", "Pricing", "Logistics", "Decision"].map(
          (step, i) => (
            <div key={step} className="flex-1">
              <div
                className={`h-2 rounded-full ${
                  i < stage ? "bg-green-500" : i === stage ? "bg-orange-500 animate-pulse" : "bg-gray-200"
                }`}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-center">{step}</p>
            </div>
          )
        )}
      </div>

      {/* Validation */}
      {validation && (
        <ValidationStatusCard fcs={validation.fcs} status={validation.status} />
      )}

      {/* Product + Market */}
      {(product || market) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {product && <ConditionCard analysis={product} />}
          {market && <DemandMap analysis={market} />}
        </div>
      )}

      {/* Pricing */}
      {pricing && <PricingCard analysis={pricing} />}

      {/* Logistics */}
      {logistics && <LogisticsCard analysis={logistics} />}

      {/* Decision */}
      {decision && <DecisionCard decision={decision} />}

      {/* Approve & List action for resale destinations */}
      {decision && (decision.destination === "INSTANT_RESALE" || decision.destination === "REFURBISH") && (
        <ResaleAction
          returnId={returnId}
          sellerLat={typeof sellerLat === "number" ? sellerLat : undefined}
          sellerLng={typeof sellerLng === "number" ? sellerLng : undefined}
          sellerCity={sellerCity}
        />
      )}

      {/* Still analyzing */}
      {!decision && status === "ANALYZING" && (
        <div className="flex items-center justify-center py-8 bg-orange-50 rounded-xl border border-orange-200">
          <Loader2 className="h-5 w-5 animate-spin text-orange-500 mr-3" />
          <span className="text-orange-700 font-medium">AI agents are still processing...</span>
        </div>
      )}
    </div>
  );
}

function ResaleAction({ returnId, sellerLat, sellerLng, sellerCity }: {
  returnId: string;
  sellerLat?: number;
  sellerLng?: number;
  sellerCity?: string;
}) {
  const [listing, setListing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [contactOpen, setContactOpen] = useState<string | null>(null);

  const handleList = async () => {
    setListing(true);
    try {
      const res = await fetch(`${API_BASE}/returns/${returnId}/list-resale`, {
        method: "POST",
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error("List error:", err);
      setResult({ error: "Failed to list. Is the backend running?" });
    } finally {
      setListing(false);
    }
  };

  if (result && !result.error) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle className="h-6 w-6 text-green-600" />
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">Listed for Resale</h3>
        </div>
        <p className="text-sm text-gray-700 dark:text-gray-200 mb-4">{result.message}</p>

        {/* Hyperlocal Buyer Radar Map — use real buyer lat/lng */}
        {result.buyers && result.buyers.length > 0 && (
          <div className="mb-6">
            <HyperlocalMap
              sellerLocation={{
                lat: sellerLat || 12.9716,
                lng: sellerLng || 77.5946,
                city: sellerCity || result.buyers[0]?.city || "Location",
              }}
              buyers={result.buyers.map((b: any) => ({
                name: b.name || "Buyer",
                city: b.city || "",
                distance_km: b.distance_km ?? 10,
                match_score: b.match_score ?? 0.5,
                email: b.email,
                lat: b.lat ? parseFloat(String(b.lat)) : undefined,
                lng: b.lng ? parseFloat(String(b.lng)) : undefined,
              }))}
            />
          </div>
        )}

        {result.buyers && result.buyers.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">
              Notified Buyers ({result.matched_buyers}) — Same City
            </p>
            <div className="space-y-2">
              {result.buyers.map((b: any, i: number) => (
                <div key={i} className="bg-white dark:bg-gray-900 rounded-lg border border-gray-100 dark:border-gray-800 overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-3">
                    <div>
                      <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">{b.name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{b.city}</p>
                    </div>
                    <button
                      onClick={() => setContactOpen(contactOpen === b.email ? null : b.email)}
                      className="bg-blue-600 text-white text-xs px-3 py-1.5 rounded-lg hover:bg-blue-700 transition"
                    >
                      Contact
                    </button>
                  </div>
                  {contactOpen === b.email && (
                    <div className="border-t border-gray-100 dark:border-gray-800 bg-blue-50 px-4 py-3">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">Contact Options</p>
                      <div className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
                        <p>📧 <span className="text-gray-400 dark:text-gray-500 italic">
                          {b.email || "Email not available"}
                        </span></p>
                        <p>📱 <span className="text-gray-400 dark:text-gray-500 italic">
                          Phone hidden (coming soon)
                        </span></p>
                        <p className="text-xs text-blue-600 mt-2">
                          ℹ️ Buyer has been notified and will reach out if interested.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        {result.buyers && result.buyers.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">No registered buyers found in this city for this category yet.</p>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-6 text-center">
      <p className="text-gray-600 dark:text-gray-300 mb-4">
        Approve this decision to list the item and notify matching nearby buyers in your city.
      </p>
      <button
        onClick={handleList}
        disabled={listing}
        className="bg-green-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-700 transition disabled:opacity-50 inline-flex items-center gap-2"
      >
        {listing && <Loader2 className="h-4 w-4 animate-spin" />}
        {listing ? "Listing & Notifying Buyers..." : "Approve & List for Resale"}
      </button>
      {result?.error && <p className="text-red-500 text-sm mt-3">{result.error}</p>}
    </div>
  );
}
