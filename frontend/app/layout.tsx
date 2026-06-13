import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ACIN - Amazon Circular Intelligence Network",
  description: "AI-Powered Multi-Agent Returns & Sustainable Resale Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        <nav className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">A</span>
              </div>
              <span className="font-bold text-xl text-gray-900">ACIN</span>
              <span className="text-xs text-gray-500 ml-2">Circular Intelligence</span>
            </div>
            <div className="flex items-center gap-6">
              <a href="/" className="text-sm text-gray-600 hover:text-gray-900">Home</a>
              <a href="/returns/new" className="text-sm text-gray-600 hover:text-gray-900">New Return</a>
              <a href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">Dashboard</a>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
