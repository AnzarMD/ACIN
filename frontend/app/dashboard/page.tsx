"use client";

import { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
import {
  Leaf,
  DollarSign,
  Package,
  Shield,
  Recycle,
  ShoppingCart,
  Wrench,
  ArrowLeftRight,
  Heart,
  Loader2,
} from "lucide-react";

interface ImpactData {
  total_returns_processed: number;
  total_co2_saved_kg: number;
  total_revenue_recovered_inr: number;
  landfill_diverted_percentage: number;
  average_processing_time_hours: number;
  revenue_recovery_rate: number;
  average_cvs_score: number;
  destinations: Record<string, { count: number; percentage: number }>;
  fraud_metrics: {
    total_flagged: number;
    ai_generated_blocked: number;
    condition_mismatch_flagged: number;
    fraud_prevented_value_inr: number;
  };
  buyer_stats?: {
    total_registered_buyers: number;
    by_city: Record<string, number>;
    by_category: Record<string, number>;
  };
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<ImpactData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/analytics/impact`)
      .then((r) => r.json())
      .then((data) => { setMetrics(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-orange-500" />
        <span className="ml-3 text-gray-600 dark:text-gray-400">Loading live metrics from DynamoDB...</span>
      </div>
    );
  }

  if (!metrics) {
    return <div className="text-center py-20 text-gray-500 dark:text-gray-400">Failed to load metrics. Is the backend running?</div>;
  }

  const DEST_CONFIG: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
    INSTANT_RESALE: { icon: <ShoppingCart className="h-4 w-4 text-green-500" />, label: "Instant Resale", color: "bg-green-500" },
    REFURBISH: { icon: <Wrench className="h-4 w-4 text-blue-500" />, label: "Refurbishment", color: "bg-blue-500" },
    EXCHANGE: { icon: <ArrowLeftRight className="h-4 w-4 text-purple-500" />, label: "Exchange", color: "bg-purple-500" },
    DONATE: { icon: <Heart className="h-4 w-4 text-orange-500" />, label: "Donation", color: "bg-orange-500" },
    RECYCLE: { icon: <Recycle className="h-4 w-4 text-red-500" />, label: "Recycling", color: "bg-red-500" },
    AI_DETECTED: { icon: <Shield className="h-4 w-4 text-red-600" />, label: "Fraud Blocked", color: "bg-red-600" },
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Impact Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-300 mt-1">Live metrics from DynamoDB — {metrics.total_returns_processed} returns processed</p>
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <BigMetric
          icon={<Package className="h-6 w-6 text-blue-500" />}
          label="Returns Processed"
          value={metrics.total_returns_processed.toLocaleString()}
          subtitle="From ACIN_Main"
        />
        <BigMetric
          icon={<Leaf className="h-6 w-6 text-green-500" />}
          label="CO₂ Saved"
          value={`${metrics.total_co2_saved_kg.toLocaleString()} kg`}
          subtitle="vs landfill baseline"
        />
        <BigMetric
          icon={<DollarSign className="h-6 w-6 text-orange-500" />}
          label="Revenue Recovered"
          value={`₹${metrics.total_revenue_recovered_inr.toLocaleString()}`}
          subtitle={`${metrics.revenue_recovery_rate}% rate`}
        />
        <BigMetric
          icon={<Shield className="h-6 w-6 text-red-500" />}
          label="Fraud Prevented"
          value={`₹${metrics.fraud_metrics.fraud_prevented_value_inr.toLocaleString()}`}
          subtitle={`${metrics.fraud_metrics.total_flagged} flagged`}
        />
      </div>

      {/* Destination Breakdown */}
      <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Destination Breakdown (Live)</h2>
        <div className="space-y-3">
          {Object.entries(metrics.destinations).map(([dest, data]) => {
            const cfg = DEST_CONFIG[dest] || { icon: <Package className="h-4 w-4" />, label: dest, color: "bg-gray-50 dark:bg-gray-8000" };
            return (
              <div key={dest} className="flex items-center gap-3">
                {cfg.icon}
                <span className="text-sm font-medium text-gray-700 dark:text-gray-200 w-32">{cfg.label}</span>
                <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className={`${cfg.color} h-3 rounded-full transition-all`}
                    style={{ width: `${data.percentage}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600 dark:text-gray-300 w-24 text-right">
                  {data.count} ({data.percentage}%)
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Performance */}
      <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Fraud Detection (Live)</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{metrics.fraud_metrics.total_flagged}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Total Flagged</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-red-600">{metrics.fraud_metrics.ai_generated_blocked}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">AI Images Blocked</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-orange-600">{metrics.fraud_metrics.condition_mismatch_flagged}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Soft FLags</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">₹{metrics.fraud_metrics.fraud_prevented_value_inr.toLocaleString()}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Value Protected</p>
          </div>
        </div>
      </div>

      {/* Buyer Registry */}
      <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-1">Registered Buyer Network</h2>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">{metrics.buyer_stats?.total_registered_buyers || 0} active buyers across India</p>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">By City</p>
            <div className="space-y-1">
              {Object.entries(metrics.buyer_stats?.by_city || {}).map(([city, count]) => (
                <div key={city} className="flex items-center gap-2">
                  <div className="flex-1 flex items-center justify-between text-sm">
                    <span className="text-gray-700 dark:text-gray-300">{city}</span>
                    <span className="font-bold text-gray-900 dark:text-gray-100">{count as number}</span>
                  </div>
                  <div className="w-24 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${Math.min(100, ((count as number) / (metrics.buyer_stats?.total_registered_buyers || 1)) * 100 * 3)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">By Category</p>
            <div className="space-y-1">
              {Object.entries(metrics.buyer_stats?.by_category || {}).map(([cat, count]) => (
                <div key={cat} className="flex justify-between text-sm">
                  <span className="text-gray-700 dark:text-gray-300">{cat}</span>
                  <span className="font-bold text-gray-900 dark:text-gray-100">{count as number}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Processing Performance */}
      <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Processing Performance</h2>
        <div className="grid grid-cols-3 gap-6">
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{metrics.average_processing_time_hours}h</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Avg Processing Time</p>
            <p className="text-xs text-green-600">vs 3-5 days baseline</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{metrics.landfill_diverted_percentage}%</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Landfill Diversion</p>
            <p className="text-xs text-green-600">vs 20% baseline</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{metrics.average_cvs_score}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Avg CVS Score</p>
            <p className="text-xs text-green-600">out of 100</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function BigMetric({ icon, label, value, subtitle }: { icon: React.ReactNode; label: string; value: string; subtitle: string }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl p-5 border border-gray-200 dark:border-gray-800 shadow-sm">
      <div className="flex items-center gap-2 mb-2">{icon}</div>
      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
      <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{subtitle}</p>
    </div>
  );
}
