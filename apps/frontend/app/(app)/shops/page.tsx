"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";

type Shop = {
  id: string;
  etsy_shop_id: string;
  shop_name: string | null;
  is_connected: boolean;
  last_synced_at: string | null;
  created_at: string;
};

function ShopsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [shops, setShops] = useState<Shop[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const connected = searchParams.get("connected");
  const connectError = searchParams.get("error");

  useEffect(() => {
    if (connected === "true") {
      setSuccessMsg("Etsy shop connected successfully!");
      router.replace("/shops");
    }
    if (connectError) {
      setError("Failed to connect Etsy shop. Please try again.");
      router.replace("/shops");
    }
  }, [connected, connectError, router]);

  useEffect(() => {
    fetchShops();
  }, []);

  async function fetchShops() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }
    try {
      const r = await fetch(`${BACKEND_URL}/api/v1/etsy/shops`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (r.status === 401) {
        router.push("/login");
        return;
      }
      const data = await r.json();
      setShops(data.shops ?? []);
    } catch {
      setError("Failed to load shops.");
    } finally {
      setLoading(false);
    }
  }

  async function connectShop() {
    setConnecting(true);
    setError(null);
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }
    try {
      const r = await fetch(`${BACKEND_URL}/api/v1/etsy/authorize`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await r.json();
      if (r.status === 503) {
        setError(data.detail ?? "Etsy is not configured on this server.");
        setConnecting(false);
        return;
      }
      if (!r.ok) {
        setError(data.detail ?? "Failed to start Etsy connection.");
        setConnecting(false);
        return;
      }
      window.location.href = data.authorization_url;
    } catch {
      setError("Network error. Please try again.");
      setConnecting(false);
    }
  }

  async function disconnectShop(shopId: string) {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    try {
      const r = await fetch(`${BACKEND_URL}/api/v1/etsy/shops/${shopId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (r.ok) {
        setShops((prev) => prev.filter((s) => s.id !== shopId));
        setSuccessMsg("Shop disconnected.");
      } else {
        setError("Failed to disconnect shop.");
      }
    } catch {
      setError("Network error.");
    }
  }

  return (
    <main className="max-w-4xl mx-auto px-8 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Etsy Shops</h1>
            <p className="text-gray-500 mt-1">Connect and manage your Etsy shops</p>
          </div>
          <button
            onClick={connectShop}
            disabled={connecting}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-medium px-5 py-2.5 rounded-lg transition-colors text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            {connecting ? "Redirecting to Etsy..." : "Connect Etsy Shop"}
          </button>
        </div>

        {successMsg && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-800 rounded-lg px-5 py-3 text-sm">
            {successMsg}
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-800 rounded-lg px-5 py-3 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : shops.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-xl p-10 text-center">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">No shops connected</h3>
            <p className="text-gray-500 text-sm mb-2">
              Connect your Etsy shop to start managing listings in bulk.
            </p>
            <p className="text-gray-400 text-xs mb-6 max-w-sm mx-auto">
              Clicking &quot;Connect Etsy Shop&quot; will redirect you to Etsy to authorise access.
              Your Etsy credentials are never stored by this application — only the OAuth token
              Etsy issues is saved. Etsy® is a trademark of Etsy, Inc.
            </p>
            <button
              onClick={connectShop}
              disabled={connecting}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-medium px-6 py-2.5 rounded-lg transition-colors text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              {connecting ? "Redirecting to Etsy..." : "Connect Etsy Shop"}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {shops.map((shop) => (
              <div
                key={shop.id}
                className="bg-white border border-gray-200 rounded-xl p-6 flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-semibold text-gray-900">{shop.shop_name ?? "Unnamed Shop"}</p>
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        shop.is_connected
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {shop.is_connected ? "Connected" : "Disconnected"}
                    </span>
                  </div>
                  <p className="text-sm text-gray-400">Shop ID: {shop.etsy_shop_id}</p>
                  {shop.last_synced_at && (
                    <p className="text-xs text-gray-400 mt-0.5">
                      Last synced: {new Date(shop.last_synced_at).toLocaleString()}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => disconnectShop(shop.id)}
                  className="text-sm text-red-500 hover:text-red-700 font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-red-200 rounded"
                >
                  Disconnect
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
  );
}

export default function ShopsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-50 flex items-center justify-center">Loading...</div>}>
      <ShopsContent />
    </Suspense>
  );
}
