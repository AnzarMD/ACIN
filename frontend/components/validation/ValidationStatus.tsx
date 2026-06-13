"use client";

import { CheckCircle, AlertTriangle, XCircle, Shield } from "lucide-react";

interface ValidationStatusProps {
  fcs: number;
  status: string;
  signals?: Record<string, number>;
}

export default function ValidationStatusCard({ fcs, status, signals }: ValidationStatusProps) {
  const getConfig = () => {
    if (status === "AUTHENTIC" || fcs < 0.30) {
      return {
        icon: <CheckCircle className="h-6 w-6 text-green-500" />,
        title: "Images Verified",
        subtitle: "All authenticity checks passed",
        bg: "bg-green-50 border-green-200",
        badge: "text-green-700 bg-green-100",
      };
    }
    if (status === "LOW" || fcs < 0.50) {
      return {
        icon: <Shield className="h-6 w-6 text-blue-500" />,
        title: "Images Accepted",
        subtitle: "Minor quality notes logged",
        bg: "bg-blue-50 border-blue-200",
        badge: "text-blue-700 bg-blue-100",
      };
    }
    if (status === "MODERATE" || fcs < 0.70) {
      return {
        icon: <AlertTriangle className="h-6 w-6 text-yellow-500" />,
        title: "Review Needed",
        subtitle: "Please retake unclear photos in better lighting",
        bg: "bg-yellow-50 border-yellow-200",
        badge: "text-yellow-700 bg-yellow-100",
      };
    }
    if (status === "HIGH" || fcs < 0.85) {
      return {
        icon: <AlertTriangle className="h-6 w-6 text-orange-500" />,
        title: "Verification Pending",
        subtitle: "We need clearer photos for this return",
        bg: "bg-orange-50 border-orange-200",
        badge: "text-orange-700 bg-orange-100",
      };
    }
    return {
      icon: <XCircle className="h-6 w-6 text-red-500" />,
      title: "Verification Failed",
      subtitle: "Upload original unedited photos",
      bg: "bg-red-50 border-red-200",
      badge: "text-red-700 bg-red-100",
    };
  };

  const config = getConfig();

  return (
    <div className={`rounded-xl p-4 border ${config.bg}`}>
      <div className="flex items-center gap-3">
        {config.icon}
        <div>
          <p className="font-semibold text-gray-900 dark:text-gray-100">{config.title}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400">{config.subtitle}</p>
        </div>
        <span className={`ml-auto text-xs font-bold px-2 py-1 rounded ${config.badge}`}>
          {status}
        </span>
      </div>
    </div>
  );
}
