"use client";

import { useEffect, useRef, useState } from "react";
import "leaflet/dist/leaflet.css";

interface Buyer {
  name: string;
  city: string;
  distance_km: number;
  match_score: number;
  email?: string;
  lat?: number;
  lng?: number;
}

interface HyperlocalMapProps {
  sellerLocation: { lat: number; lng: number; city: string };
  buyers: Buyer[];
}

function getMatchColor(score: number): string {
  if (score >= 0.8) return "#22c55e";
  if (score >= 0.6) return "#eab308";
  if (score >= 0.4) return "#f97316";
  return "#ef4444";
}

// City-level fallback coordinates for buyers without exact lat/lng
const CITY_COORDS: Record<string, [number, number]> = {
  Mumbai:    [19.076,  72.8777],
  Delhi:     [28.6139, 77.209],
  Bangalore: [12.9716, 77.5946],
  Chennai:   [13.0827, 80.2707],
  Hyderabad: [17.385,  78.4867],
  Pune:      [18.5204, 73.8567],
  Kolkata:   [22.5726, 88.3639],
  Jaipur:    [26.9124, 75.7873],
};

function getBuyerCoords(buyer: Buyer): [number, number] | null {
  if (buyer.lat && buyer.lng) return [buyer.lat, buyer.lng];
  const key = Object.keys(CITY_COORDS).find(
    (c) => c.toLowerCase() === (buyer.city || "").toLowerCase()
  );
  return key ? CITY_COORDS[key] : null;
}

export default function HyperlocalMap({ sellerLocation, buyers }: HyperlocalMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef  = useRef<any>(null);
  const [selectedBuyer, setSelectedBuyer] = useState<number | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // ── Cancellation flag for the async import ──────────────────────────
    // Without this, React StrictMode's unmount→remount cycle causes the
    // first import() callback to fire AFTER cleanup, re-initialising the
    // already-removed container and triggering "Map already initialized".
    let isMounted = true;

    // Clean up any leftover instance from a previous render
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    // Also wipe Leaflet's internal container marker (belt-and-suspenders)
    const container = mapContainerRef.current as any;
    if (container._leaflet_id) {
      delete container._leaflet_id;
    }

    import("leaflet").then((L) => {
      // If the component unmounted while the import was in flight, bail out.
      // This is the key guard that prevents the double-init error.
      if (!isMounted || !mapContainerRef.current) return;

      // Fix Leaflet default icon paths (broken in webpack / Next.js builds)
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const sellerLat = sellerLocation.lat || 12.9716;
      const sellerLng = sellerLocation.lng || 77.5946;

      const map = L.map(mapContainerRef.current, {
        center: [sellerLat, sellerLng],
        zoom: 12,
        zoomControl: true,
        attributionControl: true,
      });
      mapInstanceRef.current = map;

      // OpenStreetMap tiles
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '© <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
      }).addTo(map);

      // ── Seller pin ────────────────────────────────────────────────────
      const sellerIcon = L.divIcon({
        className: "",
        html: `<div style="
          width:20px;height:20px;border-radius:50%;
          background:#3b82f6;border:3px solid white;
          box-shadow:0 0 0 3px rgba(59,130,246,0.4),0 3px 10px rgba(59,130,246,0.5);
        "></div>`,
        iconSize:   [20, 20],
        iconAnchor: [10, 10],
      });

      L.marker([sellerLat, sellerLng], { icon: sellerIcon })
        .addTo(map)
        .bindPopup(`
          <div style="font-family:system-ui;min-width:130px;padding:4px 0">
            <strong style="color:#3b82f6">📦 Seller Location</strong><br/>
            <span style="color:#555;font-size:12px">${sellerLocation.city || "Your location"}</span><br/>
            <span style="color:#888;font-size:11px">${sellerLat.toFixed(5)}, ${sellerLng.toFixed(5)}</span>
          </div>
        `);

      // Collect all valid points for auto-fit bounds
      const allPoints: [number, number][] = [[sellerLat, sellerLng]];

      // ── Buyer pins ────────────────────────────────────────────────────
      buyers.forEach((buyer) => {
        const coords = getBuyerCoords(buyer);
        if (!coords) return;

        const [bLat, bLng] = coords;
        allPoints.push([bLat, bLng]);

        const color = getMatchColor(buyer.match_score);

        const buyerIcon = L.divIcon({
          className: "",
          html: `<div style="
            width:16px;height:16px;border-radius:50%;
            background:${color};border:2.5px solid white;
            box-shadow:0 2px 8px rgba(0,0,0,0.25);
            cursor:pointer;
          "></div>`,
          iconSize:   [16, 16],
          iconAnchor: [8, 8],
        });

        L.marker([bLat, bLng], { icon: buyerIcon })
          .addTo(map)
          .bindPopup(`
            <div style="font-family:system-ui;min-width:170px;padding:4px 0">
              <strong style="color:#111;font-size:14px">${buyer.name}</strong><br/>
              <span style="color:#666;font-size:12px">${buyer.city}</span><br/>
              <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap">
                <span style="background:#f0fdf4;color:#16a34a;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600">
                  ${(buyer.match_score * 100).toFixed(0)}% match
                </span>
                <span style="background:#eff6ff;color:#2563eb;padding:2px 8px;border-radius:12px;font-size:11px">
                  ${buyer.distance_km.toFixed(1)} km away
                </span>
              </div>
              ${buyer.email ? `<div style="margin-top:5px;color:#888;font-size:11px">📧 ${buyer.email}</div>` : ""}
            </div>
          `);

        // Dashed line: seller → buyer
        L.polyline([[sellerLat, sellerLng], [bLat, bLng]], {
          color,
          weight: 1.5,
          opacity: 0.5,
          dashArray: "5 5",
        }).addTo(map);
      });

      // Auto-fit to show seller + all buyers
      if (allPoints.length > 1) {
        map.fitBounds(L.latLngBounds(allPoints), { padding: [50, 50], maxZoom: 13 });
      }
    });

    // ── Cleanup ───────────────────────────────────────────────────────────
    return () => {
      isMounted = false; // signals any in-flight import() to abort
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []); // Run once — sellerLocation/buyers are stable from parent

  return (
    <div className="w-full rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-sm bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
          <span className="text-sm font-semibold text-gray-900 dark:text-white">Hyperlocal Buyer Map</span>
          <span className="text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full">
            {buyers.length} buyer{buyers.length !== 1 ? "s" : ""} nearby
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500 inline-block" /> 80%+
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-yellow-500 inline-block" /> 60–80%
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-orange-500 inline-block" /> 40–60%
          </span>
        </div>
      </div>

      {/* Map */}
      <div ref={mapContainerRef} style={{ height: "400px", width: "100%" }} />

      {/* Buyer list */}
      <div className="border-t border-gray-100 dark:border-gray-800">
        {buyers.slice(0, 6).map((buyer, i) => (
          <div
            key={i}
            onClick={() => setSelectedBuyer(selectedBuyer === i ? null : i)}
            className={`flex items-center justify-between px-4 py-2.5 cursor-pointer border-b border-gray-50 dark:border-gray-800 last:border-0 transition-colors ${
              selectedBuyer === i
                ? "bg-blue-50 dark:bg-blue-950/20"
                : "hover:bg-gray-50 dark:hover:bg-gray-800/40"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <div
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: getMatchColor(buyer.match_score) }}
              />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{buyer.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{buyer.city}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="text-gray-500 dark:text-gray-400">{buyer.distance_km.toFixed(1)} km</span>
              <span
                className="font-semibold px-2 py-0.5 rounded-full"
                style={{
                  backgroundColor: getMatchColor(buyer.match_score) + "22",
                  color: getMatchColor(buyer.match_score),
                }}
              >
                {(buyer.match_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}