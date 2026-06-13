import Link from "next/link";

export default function Home() {
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
            className="border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 px-8 py-3 rounded-lg font-semibold hover:bg-gray-50 dark:bg-gray-800 transition"
          >
            View Impact Dashboard
          </Link>
        </div>
      </section>

      {/* Impact Metrics */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <MetricCard label="Processing Time" value="< 4 hours" improvement="20× faster" />
        <MetricCard label="Revenue Recovery" value="72-84%" improvement="+90%" />
        <MetricCard label="Landfill Diverted" value="78%" improvement="+4×" />
        <MetricCard label="Fraud Detection" value="94%" improvement="Automated" />
      </section>

      {/* Destinations */}
      <section>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Product Destinations</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <DestinationCard color="green" label="Instant Resale" desc="Score >85, High Demand" />
          <DestinationCard color="blue" label="Refurbish" desc="Score 50-85, Repair ROI" />
          <DestinationCard color="purple" label="Exchange" desc="Size/Variant Mismatch" />
          <DestinationCard color="orange" label="Donate" desc="Profit Negative, Good Condition" />
          <DestinationCard color="red" label="Recycle" desc="Low Score, Unsafe" />
        </div>
      </section>

      {/* Agent Pipeline */}
      <section>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">6-Agent AI Pipeline</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <AgentCard step={0} name="Validation Gate" desc="AI image forgery detection" />
          <AgentCard step={1} name="Product Intelligence" desc="Condition & defect analysis" />
          <AgentCard step={2} name="Market Intelligence" desc="Demand & buyer matching" />
          <AgentCard step={3} name="Dynamic Repricing" desc="3 optimised price points" />
          <AgentCard step={4} name="Logistics Routing" desc="Cost + carbon optimisation" />
          <AgentCard step={5} name="Circular Economy" desc="Best next-life decision" />
        </div>
      </section>
    </div>
  );
}

function MetricCard({ label, value, improvement }: { label: string; value: string; improvement: string }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
      <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
      <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
      <p className="text-sm text-green-600 mt-1">{improvement}</p>
    </div>
  );
}

function DestinationCard({ color, label, desc }: { color: string; label: string; desc: string }) {
  const colorMap: Record<string, string> = {
    green: "bg-green-500",
    blue: "bg-blue-500",
    purple: "bg-purple-500",
    orange: "bg-orange-500",
    red: "bg-red-500",
  };
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-800 shadow-sm">
      <div className={`w-3 h-3 rounded-full ${colorMap[color]} mb-2`} />
      <p className="font-semibold text-gray-900 dark:text-gray-100">{label}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{desc}</p>
    </div>
  );
}

function AgentCard({ step, name, desc }: { step: number; name: string; desc: string }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-800 shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <span className="bg-orange-100 text-orange-700 text-xs font-bold px-2 py-1 rounded">
          Step {step}
        </span>
      </div>
      <p className="font-semibold text-gray-900 dark:text-gray-100">{name}</p>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{desc}</p>
    </div>
  );
}
