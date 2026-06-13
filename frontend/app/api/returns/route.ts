/**
 * Next.js API route proxy for returns
 * Proxies to the FastAPI backend
 */

import { NextResponse } from "next/server";

const API_BASE = process.env.API_URL || "http://localhost:8000/v1";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const response = await fetch(`${API_BASE}/returns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    // For demo: return a mock response
    const returnId = `RET-${new Date().toISOString().slice(0, 10)}-${Math.random().toString(36).slice(2, 10)}`;
    return NextResponse.json({
      return_id: returnId,
      status: "ANALYZING",
    });
  }
}
