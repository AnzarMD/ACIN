"use client";

import { Activity } from "lucide-react";
import type { ProductAnalysis } from "@/lib/types";

interface ConditionCardProps {
  analysis: ProductAnalysis;
}

export default function ConditionCard({ analysis }: ConditionCardProps) {
  const gradeColors: Record<string, string> = {
    A: "text-green-600 bg-green-100",
    B: "text-blue-600 bg-blue-100",
    C: "text-yellow-600 bg-yellow-100",
    D: "text-red-600 bg-red-100",
  };

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="h-5 w-5 text-orange-500" />
        <h3 className="font-semibold text-gray-900">Product Condition</h3>
      </div>

      {/* Score + Grade */}
      <div className="flex items-center gap-4 mb-4">
        <div className="text-center">
          <div className="text-3xl font-bold text-gray-900">
            {analysis.condition_score}
          </div>
          <div className="text-xs text-gray-500">/ 100</div>
        </div>
        <span
          className={`text-lg font-bold px-3 py-1 rounded ${
            gradeColors[analysis.grade] || "text-gray-600 bg-gray-100"
          }`}
        >
          Grade {analysis.grade}
        </span>
      </div>

      {/* Details */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">Usage Level</span>
          <span className="font-medium capitalize">{analysis.usage_level}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Packaging</span>
          <span className="font-medium capitalize">{analysis.packaging_status}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Safety Risk</span>
          <span className={`font-medium ${analysis.safety_risk ? "text-red-600" : "text-green-600"}`}>
            {analysis.safety_risk ? "Yes" : "None"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Repair Cost</span>
          <span className="font-medium">₹{analysis.estimated_repair_cost_inr.toLocaleString()}</span>
        </div>
      </div>

      {/* Defects */}
      {analysis.defects.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Defects Found</p>
          <div className="space-y-1">
            {analysis.defects.map((d, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span
                  className={`w-2 h-2 rounded-full ${
                    d.severity === "high" || d.severity === "critical"
                      ? "bg-red-500"
                      : d.severity === "medium"
                      ? "bg-yellow-500"
                      : "bg-green-500"
                  }`}
                />
                <span className="text-gray-700">
                  {d.type} ({d.location}) — {d.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
