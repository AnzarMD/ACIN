/**
 * API route to get a presigned S3 upload URL
 */
import { NextResponse } from "next/server";

const API_BASE = process.env.API_URL || "http://localhost:8000/v1";

export async function POST(request: Request) {
  try {
    const { return_id, filename } = await request.json();
    const response = await fetch(
      `${API_BASE}/returns/${return_id}/upload-url?filename=${encodeURIComponent(filename)}`,
      { method: "POST" }
    );
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: "Failed to get upload URL" }, { status: 500 });
  }
}
