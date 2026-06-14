"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

interface LiveMetrics {
  total_returns_processed: number;
  total_co2_saved_kg: number;
  total_revenue_recovered_inr: number;
  landfill_diverted_percentage: number;
  revenue_recovery_rate: number;
  average_cvs_score: number;
  fraud_metrics: {
    total_flagged: number;
    ai_generated_blocked: number;
  };
  destinations: Record<string, { count: number; percentage: number }>;
  buyer_stats?: { total_registered_buyers: number };
}

export default function Home() {
  const [metrics, setMetrics] = useState<LiveMetrics | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/analytics/impact`)
      .then((r) => r.json())
      .then(setMetrics)
      .catch(() => {});
  }, []);

  // Derived live values from real data
  const returnsProcessed = metrics?.total_returns_processed ?? 0;
  const co2Saved = metrics ? metrics.total_co2_saved_kg.toFixed(1) : "—";
  const landfillDiverted = metrics ? `${metrics.landfill_diverted_percentage}%` : "—";
  const revenueRate = metrics ? `${metrics.revenue_recovery_rate}%` : "—";
  const fraudBlocked = metrics ? metrics.fraud_metrics.ai_generated_blocked : 0;
  const totalFlagged = metrics ? metrics.fraud_metrics.total_flagged : 0;
  const revenueRecovered = metrics
    ? `₹${(metrics.total_revenue_recovered_inr / 100000).toFixed(1)}L`
    : "—";
  const registeredBuyers = metrics?.buyer_stats?.total_registered_buyers ?? 0;

  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="text-center py-16">
        <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">
          Amazon Circular Intelligence Network
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto mb-8">
          AI-Powered Multi-Agent Returns & Sustainable Resale Platform.
          Every return gets a second life — powered by 6 specialised AI agents.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/returns/new"
            className="bg-orange-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-orange-600 transition"
          >
            Start a Return
          </Link>
          <Link
            href="/dashboard"
            className="border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 px-8 py-3 rounded-lg font-semibold hover:bg-gray-50 dark:hover:bg-gray-800 transition"
          >
            View Impact Dashboard
          </Link>
        </div>
      </section>

      {/* Live Impact Metrics — pulled from DynamoDB */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <MetricCard
          label="Returns Processed"
          value={returnsProcessed > 0 ? returnsProcessed.toLocaleString() : "—"}
          sub="All time"
          color="blue"
          loading={!metrics}
        />
        <MetricCard
          label="Revenue Recovered"
          value={revenueRecovered}
          sub={`${revenueRate} recovery rate`}
          color="green"
          loading={!metrics}
        />
        <MetricCard
          label="CO₂ Saved"
          value={co2Saved !== "—" ? `${co2Saved} kg` : "—"}
          sub={`${landfillDiverted} landfill diverted`}
          color="green"
          loading={!metrics}
        />
        <MetricCard
          label="Fraud Blocked"
          value={metrics ? `${fraudBlocked} images` : "—"}
          sub={`${totalFlagged} total flagged`}
          color="red"
          loading={!metrics}
        />
      </section>

      {/* Second row: buyers + CVS */}
      <section className="grid grid-cols-2 gap-6">
        <MetricCard
          label="Registered Buyers"
          value={registeredBuyers > 0 ? registeredBuyers.toLocaleString() : "—"}
          sub="Across 8 Indian cities"
          color="purple"
          loading={!metrics}
        />
        <MetricCard
          label="Avg CVS Score"
          value={metrics ? `${metrics.average_cvs_score.toFixed(1)}/100` : "—"}
          sub="Circular Value Score"
          color="blue"
          loading={!metrics}
        />
      </section>

      {/* Destination breakdown */}
      {metrics?.destinations && (
        <section>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Live Destination Breakdown
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(metrics.destinations).map(([dest, data]) => {
              const config: Record<string, { color: string; label: string; desc: string }> = {
                INSTANT_RESALE: { color: "green", label: "Instant Resale", desc: "Score >85, High Demand" },
                REFURBISH: { color: "blue", label: "Refurbish", desc: "Repair ROI positive" },
                EXCHANGE: { color: "purple", label: "Exchange", desc: "Size/Variant Mismatch" },
                DONATE: { color: "orange", label: "Donate", desc: "Profit Negative" },
                RECYCLE: { color: "red", label: "Recycle", desc: "Low Score, Unsafe" },
              };
              const c = config[dest] || { color: "gray", label: dest, desc: "" };
              return (
                <DestinationCard
                  key={dest}
                  color={c.color}
                  label={c.label}
                  desc={c.desc}
                  count={data.count}
                  percentage={data.percentage}
                />
              );
            })}
          </div>
        </section>
      )}

      {/* Agent Pipeline */}
      <section>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">6-Agent AI Pipeline</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <AgentCard step={0} name="Validation Gate" desc="AI image forgery detection" />
          <AgentCard step={1} name="Product Intelligence" desc="Condition & defect analysis" />
          <AgentCard step={2} name="Market Intelligence" desc="Demand & buyer matching" />
          <AgentCard step={3} name="Dynamic Repricing" desc="3 optimised price points" />
          <AgentCard step={4} name="Logistics Routing" desc="LRS formula — cost + carbon" />
          <AgentCard step={5} name="Circular Economy" desc="Best next-life decision" />
        </div>
      </section>
    </div>
  );
}

function MetricCard({
  label, value, sub, color, loading,
}: {
  label: string; value: string; sub: string; color: string; loading?: boolean;
}) {
  const colorMap: Record<string, string> = {
    green: "text-green-600", blue: "text-blue-600",
    orange: "text-orange-500", red: "text-red-500", purple: "text-purple-600",
  };
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
      <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
      {loading ? (
        <div className="h-8 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mt-1" />
      ) : (
        <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
      )}
      <p className={`text-sm mt-1 ${colorMap[color] || "text-gray-500"}`}>{sub}</p>
    </div>
  );
}

function DestinationCard({
  color, label, desc, count, percentage,
}: {
  color: string; label: string; desc: string; count: number; percentage: number;
}) {
  const colorMap: Record<string, string> = {
    green: "bg-green-500", blue: "bg-blue-500",
    purple: "bg-purple-500", orange: "bg-orange-500", red: "bg-red-500",
  };
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-800 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className={`w-3 h-3 rounded-full ${colorMap[color] || "bg-gray-400"}`} />
        <span className="text-xs font-bold text-gray-700 dark:text-gray-300">{percentage}%</span>
      </div>
      <p className="font-semibold text-gray-900 dark:text-gray-100">{label}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{desc}</p>
      <p className="text-xs font-medium text-gray-600 dark:text-gray-300 mt-2">{count} returns</p>
    </div>
  );
}

function AgentCard({ step, name, desc }: { step: number; name: string; desc: string }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-800 shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <span className="bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 text-xs font-bold px-2 py-1 rounded">
          Step {step}
        </span>
      </div>
      <p className="font-semibold text-gray-900 dark:text-gray-100">{name}</p>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{desc}</p>
    </div>
  );
}
