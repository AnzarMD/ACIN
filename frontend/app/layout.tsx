import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ui/ThemeProvider";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

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
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors">
        <ThemeProvider>
          <nav className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4">
            <div className="max-w-7xl mx-auto flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">A</span>
                </div>
                <span className="font-bold text-xl">ACIN</span>
                <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">Circular Intelligence</span>
              </div>
              <div className="flex items-center gap-6">
                <a href="/" className="text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">Home</a>
                <a href="/returns/new" className="text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">New Return</a>
                <a href="/dashboard" className="text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">Dashboard</a>
                <ThemeToggle />
              </div>
            </div>
          </nav>
          <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}
