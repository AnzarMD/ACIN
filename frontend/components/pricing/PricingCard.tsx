"use client";

import { DollarSign, Zap, Scale, TrendingUp } from "lucide-react";
import type { PricingAnalysis } from "@/lib/types";

interface PricingCardProps {
  analysis: PricingAnalysis;
}

export default function PricingCard({ analysis }: PricingCardProps) {
  const strategies = [
    {
      key: "fast_sale",
      label: "Fast Sale",
      price: analysis.fast_sale_price,
      time: "< 24 hours",
      icon: <Zap className="h-4 w-4" />,
      color: "border-green-500 bg-green-50",
    },
    {
      key: "balanced",
      label: "Balanced",
      price: analysis.balanced_price,
      time: "2-5 days",
      icon: <Scale className="h-4 w-4" />,
      color: "border-blue-500 bg-blue-50",
    },
    {
      key: "max_profit",
      label: "Max Profit",
      price: analysis.max_profit_price,
      time: "7-14 days",
      icon: <TrendingUp className="h-4 w-4" />,
      color: "border-purple-500 bg-purple-50",
    },
  ];

  const discountPct = analysis.discount_percentage
    ? Math.round(analysis.discount_percentage)
    : analysis.original_price
    ? Math.round((1 - analysis.balanced_price / analysis.original_price) * 100)
    : 0;

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <DollarSign className="h-5 w-5 text-green-500" />
        <h3 className="font-semibold text-gray-900">Dynamic Pricing</h3>
        {discountPct > 0 && (
          <span className="ml-auto text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded font-medium">
            {discountPct}% off original
          </span>
        )}
      </div>

      {/* Original Price */}
      {analysis.original_price > 0 && (
        <div className="text-sm text-gray-500 mb-4">
          Original: <span className="line-through">₹{analysis.original_price.toLocaleString()}</span>
        </div>
      )}

      {/* Price Strategies */}
      <div className="space-y-3">
        {strategies.map((s) => (
          <div
            key={s.key}
            className={`flex items-center justify-between p-3 rounded-lg border-2 ${
              analysis.recommended_strategy === s.key
                ? s.color
                : "border-gray-100 bg-gray-50"
            }`}
          >
            <div className="flex items-center gap-2">
              {s.icon}
              <div>
                <p className="text-sm font-semibold">{s.label}</p>
                <p className="text-xs text-gray-500">{s.time}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold">₹{s.price.toLocaleString()}</p>
              {analysis.recommended_strategy === s.key && (
                <span className="text-xs text-blue-600 font-medium">Recommended</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Market Insight */}
      {(analysis as any).market_insight && (
        <p className="text-xs text-gray-500 mt-3 italic">{(analysis as any).market_insight}</p>
      )}
    </div>
  );
}
