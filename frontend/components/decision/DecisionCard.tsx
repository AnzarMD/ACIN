"use client";

import { ShoppingCart, Wrench, ArrowLeftRight, Heart, Recycle } from "lucide-react";
import type { Decision } from "@/lib/types";

const DESTINATION_CONFIG = {
  INSTANT_RESALE: { color: "green", icon: ShoppingCart, label: "Instant Resale" },
  REFURBISH: { color: "blue", icon: Wrench, label: "Refurbishment" },
  EXCHANGE: { color: "purple", icon: ArrowLeftRight, label: "Exchange Pool" },
  DONATE: { color: "orange", icon: Heart, label: "Donation" },
  RECYCLE: { color: "red", icon: Recycle, label: "Recycling" },
};

interface DecisionCardProps {
  decision: Decision;
}

export function DecisionCard({ decision }: DecisionCardProps) {
  const cfg = DESTINATION_CONFIG[decision.destination] || DESTINATION_CONFIG.INSTANT_RESALE;
  const Icon = cfg.icon;

  const colorClasses: Record<string, { border: string; text: string; bg: string }> = {
    green: { border: "border-green-500", text: "text-green-600", bg: "bg-green-50" },
    blue: { border: "border-blue-500", text: "text-blue-600", bg: "bg-blue-50" },
    purple: { border: "border-purple-500", text: "text-purple-600", bg: "bg-purple-50" },
    orange: { border: "border-orange-500", text: "text-orange-600", bg: "bg-orange-50" },
    red: { border: "border-red-500", text: "text-red-600", bg: "bg-red-50" },
  };

  const colors = colorClasses[cfg.color] || colorClasses.green;

  return (
    <div className={`border-2 ${colors.border} rounded-xl p-6 ${colors.bg}`}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <Icon className={`h-8 w-8 ${colors.text}`} />
        <div>
          <span className={`${colors.text} font-bold text-xl`}>{cfg.label}</span>
          <span className="text-gray-500 text-sm ml-3">
            {decision.confidence}% confidence
          </span>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <Metric label="CVS Score" value={`${decision.cvs_score}/100`} />
        <Metric
          label="Recovery"
          value={`₹${decision.listing_price?.toLocaleString()}`}
        />
        <Metric label="CO₂ Saved" value={`${decision.carbon_saved_kg} kg`} />
      </div>

      {/* Explanation */}
      <p className="text-gray-700 text-sm">{decision.explanation}</p>

      {/* Trust Badges */}
      <div className="flex gap-2 mt-4">
        {decision.trust_badges?.map((b: string) => (
          <span
            key={b}
            className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium"
          >
            {b.replace(/_/g, " ")}
          </span>
        ))}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-bold text-gray-900">{value}</p>
    </div>
  );
}

export default DecisionCard;
