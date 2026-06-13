"use client";

import { Users, TrendingUp, Clock } from "lucide-react";
import type { MarketAnalysis } from "@/lib/types";

interface DemandMapProps {
  analysis: MarketAnalysis;
}

export default function DemandMap({ analysis }: DemandMapProps) {
  const trendIcon = analysis.demand_trend === "rising" ? "↑" : analysis.demand_trend === "declining" ? "↓" : "→";
  const trendColor = analysis.demand_trend === "rising" ? "text-green-600" : analysis.demand_trend === "declining" ? "text-red-600" : "text-gray-600";

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-5 w-5 text-blue-500" />
        <h3 className="font-semibold text-gray-900">Market Demand</h3>
      </div>

      {/* Demand Score */}
      <div className="mb-4">
        <div className="flex items-end gap-2">
          <span className="text-3xl font-bold text-gray-900">{analysis.demand_score}</span>
          <span className="text-sm text-gray-500 mb-1">/ 100</span>
          <span className={`text-lg ml-2 ${trendColor}`}>{trendIcon}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{ width: `${analysis.demand_score}%` }}
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-gray-400" />
          <div>
            <p className="text-lg font-bold text-gray-900">{analysis.buyer_count}</p>
            <p className="text-xs text-gray-500">Nearby Buyers</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-gray-400" />
          <div>
            <p className="text-lg font-bold text-gray-900">{analysis.expected_sale_days}</p>
            <p className="text-xs text-gray-500">Days to Sell</p>
          </div>
        </div>
      </div>

      {/* Region */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Region</span>
          <span className="font-medium">{analysis.region}</span>
        </div>
        <div className="flex justify-between text-sm mt-1">
          <span className="text-gray-500">Trend</span>
          <span className={`font-medium capitalize ${trendColor}`}>{analysis.demand_trend}</span>
        </div>
      </div>
    </div>
  );
}
