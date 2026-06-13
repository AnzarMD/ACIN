/**
 * Catch-all API proxy using Pages Router (works reliably on Vercel).
 * Proxies /api/proxy/X → http://ALB/v1/X
 */

import type { NextApiRequest, NextApiResponse } from "next";

const BACKEND = process.env.API_URL || "http://acin-alb-1572894229.ap-south-1.elb.amazonaws.com/v1";

export const config = {
  api: {
    bodyParser: {
      sizeLimit: "10mb",
    },
  },
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // slug = ["proxy", "returns", "validate"] → path = "returns/validate"
  const slugArray = Array.isArray(req.query.slug) ? req.query.slug : [req.query.slug || ""];

  // Remove "proxy" prefix if present
  const pathParts = slugArray[0] === "proxy" ? slugArray.slice(1) : slugArray;
  const path = pathParts.join("/");
  const queryString = req.url?.includes("?") ? "?" + req.url.split("?")[1] : "";
  const url = `${BACKEND}/${path}${queryString}`;

  const headers: Record<string, string> = {};
  if (req.headers["content-type"]) {
    headers["Content-Type"] = req.headers["content-type"] as string;
  }

  const fetchOptions: RequestInit = {
    method: req.method || "GET",
    headers,
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    fetchOptions.body = typeof req.body === "string" ? req.body : JSON.stringify(req.body);
  }

  try {
    const response = await fetch(url, { ...fetchOptions, redirect: "follow" });
    const contentType = response.headers.get("content-type") || "application/json";
    const data = await response.text();

    res.setHeader("Content-Type", contentType);
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    res.status(response.status).send(data);
  } catch (error) {
    res.status(502).json({ error: "Backend unavailable", detail: String(error) });
  }
}
