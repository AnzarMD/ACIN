"use client";

import { Truck, Navigation, Leaf, Clock, DollarSign, BarChart3 } from "lucide-react";

interface LogisticsAnalysis {
  selected_route: string;
  route_score: number;
  distance_km: number;
  total_cost_inr: number;
  eta_hours: number;
  carbon_kg: number;
  carbon_saved_vs_default_kg: number;
  demand_match: number;
  capacity_reliability: number;
  risk_score: number;
  alternatives: string[];
  reason: string;
  rule_version: string;
}

const ROUTE_LABELS: Record<string, { label: string; color: string }> = {
  NEARBY_BUYER:      { label: "Direct to Nearby Buyer", color: "text-green-600" },
  EXCHANGE_POOL:     { label: "Direct Exchange", color: "text-purple-600" },
  LOCAL_HUB:         { label: "Local Fulfilment Hub", color: "text-blue-600" },
  WAREHOUSE:         { label: "Central Warehouse", color: "text-gray-600 dark:text-gray-400" },
  REFURB_CENTER:     { label: "Refurbishment Centre", color: "text-orange-600" },
  DONATION_PARTNER:  { label: "NGO Partner", color: "text-pink-600" },
  RECYCLE_CENTER:    { label: "Certified Recycler", color: "text-red-600" },
};

export default function LogisticsCard({ analysis }: { analysis: LogisticsAnalysis }) {
  const route = ROUTE_LABELS[analysis.selected_route] || { label: analysis.selected_route, color: "text-gray-600 dark:text-gray-400" };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm space-y-5">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Truck className="h-5 w-5 text-blue-500" />
        <h3 className="font-semibold text-gray-900 dark:text-gray-100">Logistics Routing</h3>
        <span className="ml-auto bg-blue-50 text-blue-700 text-xs font-bold px-2 py-1 rounded">
          LRS {analysis.route_score?.toFixed(1)}/100
        </span>
      </div>

      {/* Selected Route */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
        <p className="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold mb-1">Selected Route</p>
        <p className={`text-lg font-bold ${route.color}`}>{route.label}</p>
        {analysis.reason && (
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{analysis.reason}</p>
        )}
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-3">
        <MetricTile
          icon={<Navigation className="h-4 w-4 text-blue-400" />}
          label="Distance"
          value={`${analysis.distance_km} km`}
        />
        <MetricTile
          icon={<DollarSign className="h-4 w-4 text-green-400" />}
          label="Logistics Cost"
          value={`₹${analysis.total_cost_inr}`}
        />
        <MetricTile
          icon={<Clock className="h-4 w-4 text-orange-400" />}
          label="ETA"
          value={analysis.eta_hours < 24
            ? `~${analysis.eta_hours}h`
            : `${Math.round(analysis.eta_hours / 24)}d`}
        />
        <MetricTile
          icon={<Leaf className="h-4 w-4 text-green-500" />}
          label="Route CO₂"
          value={`${analysis.carbon_kg} kg`}
        />
      </div>

      {/* Carbon Saved */}
      {analysis.carbon_saved_vs_default_kg > 0 && (
        <div className="flex items-center gap-2 bg-green-50 rounded-lg px-4 py-3">
          <Leaf className="h-5 w-5 text-green-600" />
          <div>
            <p className="text-sm font-semibold text-green-800">
              {analysis.carbon_saved_vs_default_kg} kg CO₂ saved vs warehouse route
            </p>
            <p className="text-xs text-green-600">Local routing reduces carbon footprint</p>
          </div>
        </div>
      )}

      {/* Scoring Breakdown */}
      <div>
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2 flex items-center gap-1">
          <BarChart3 className="h-3 w-3" /> LRS Component Scores
        </p>
        <div className="space-y-1">
          <ScoreBar label="Demand Match" value={analysis.demand_match} color="bg-blue-500" />
          <ScoreBar label="Capacity" value={analysis.capacity_reliability} color="bg-green-500" />
          <ScoreBar label="Risk (lower=better)" value={1 - (analysis.risk_score || 0)} color="bg-yellow-500" />
        </div>
      </div>

      {/* Alternatives */}
      {analysis.alternatives && analysis.alternatives.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400 font-semibold uppercase mb-1">Alternatives Considered</p>
          <div className="flex flex-wrap gap-2">
            {analysis.alternatives.map((alt) => (
              <span key={alt} className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded">
                {ROUTE_LABELS[alt]?.label || alt}
              </span>
            ))}
          </div>
        </div>
      )}

      {analysis.rule_version && (
        <p className="text-xs text-gray-400 dark:text-gray-500">{analysis.rule_version}</p>
      )}
    </div>
  );
}

function MetricTile({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2">
      {icon}
      <div>
        <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
        <p className="text-sm font-bold text-gray-800 dark:text-gray-100">{value}</p>
      </div>
    </div>
  );
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round((value || 0) * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-600 dark:text-gray-300 w-32">{label}</span>
      <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-600 dark:text-gray-300 w-8 text-right">{pct}%</span>
    </div>
  );
}
