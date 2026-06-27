"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getAccessToken } from "@/lib/api";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

type PlatformState = "app_not_configured" | "not_connected" | "connected" | "expired";

interface PlatformStatus {
  platform: string;
  state: PlatformState;
  connected_at: string | null;
  expires_at: string | null;
}

function authFetch(path: string, options?: RequestInit) {
  const token = getAccessToken();
  return fetch(`${BACKEND_URL}${path}`, {
    ...options,
    headers: {
      ...(options?.headers ?? {}),
      Authorization: `Bearer ${token}`,
    },
  });
}

function PlatformCard({
  platform,
  icon,
  displayName,
  description,
  status,
  onConnect,
  onDisconnect,
  connecting,
  disconnecting,
}: {
  platform: string;
  icon: string;
  displayName: string;
  description: string;
  status: PlatformStatus | null;
  onConnect: () => void;
  onDisconnect: () => void;
  connecting: boolean;
  disconnecting: boolean;
}) {
  const state = status?.state ?? "not_connected";

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <h2 className="text-base font-semibold text-gray-900">{displayName}</h2>
        <span className={`ml-auto text-xs px-2 py-0.5 rounded-full font-medium ${
          state === "connected"
            ? "bg-green-100 text-green-700"
            : state === "expired"
            ? "bg-amber-100 text-amber-700"
            : state === "app_not_configured"
            ? "bg-gray-100 text-gray-500"
            : "bg-gray-100 text-gray-500"
        }`}>
          {state === "connected" && "Connected"}
          {state === "expired" && "Token expired"}
          {state === "not_connected" && "Not connected"}
          {state === "app_not_configured" && "Not configured"}
        </span>
      </div>

      <p className="text-sm text-gray-500">{description}</p>

      {state === "app_not_configured" && (
        <div className="px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-500">
          {displayName} app credentials are not configured. An admin must set{" "}
          {platform === "pinterest"
            ? "PINTEREST_CLIENT_ID, PINTEREST_CLIENT_SECRET, PINTEREST_REDIRECT_URI"
            : "META_APP_ID, META_APP_SECRET, INSTAGRAM_REDIRECT_URI"}{" "}
          in the server environment.
        </div>
      )}

      {state === "not_connected" && (
        <button
          onClick={onConnect}
          disabled={connecting}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          {connecting ? "Redirecting…" : `Connect ${displayName}`}
        </button>
      )}

      {state === "connected" && (
        <div className="space-y-3">
          {status?.connected_at && (
            <p className="text-xs text-gray-400">
              Connected {new Date(status.connected_at).toLocaleDateString()}
              {status.expires_at && ` · expires ${new Date(status.expires_at).toLocaleDateString()}`}
            </p>
          )}
          <button
            onClick={onDisconnect}
            disabled={disconnecting}
            className="text-sm text-red-600 hover:text-red-700 disabled:opacity-50 font-medium"
          >
            {disconnecting ? "Disconnecting…" : `Disconnect ${displayName}`}
          </button>
        </div>
      )}

      {state === "expired" && (
        <div className="space-y-3">
          <p className="text-xs text-amber-700">
            Access token has expired. Reconnect to continue using {displayName}.
          </p>
          <div className="flex gap-3">
            <button
              onClick={onConnect}
              disabled={connecting}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {connecting ? "Redirecting…" : `Reconnect ${displayName}`}
            </button>
            <button
              onClick={onDisconnect}
              disabled={disconnecting}
              className="text-sm text-red-600 hover:text-red-700 disabled:opacity-50 font-medium self-center"
            >
              {disconnecting ? "Removing…" : "Remove"}
            </button>
          </div>
        </div>
      )}

      {platform === "instagram" && state !== "app_not_configured" && (
        <p className="text-xs text-gray-400 border-t border-gray-100 pt-3">
          Instagram publishing requires a <strong>Business</strong> or <strong>Creator</strong> account linked to a Facebook Page.
        </p>
      )}
    </div>
  );
}

function PromoteContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [pinterestStatus, setPinterestStatus] = useState<PlatformStatus | null>(null);
  const [instagramStatus, setInstagramStatus] = useState<PlatformStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  const [connectingPinterest, setConnectingPinterest] = useState(false);
  const [connectingInstagram, setConnectingInstagram] = useState(false);
  const [disconnectingPinterest, setDisconnectingPinterest] = useState(false);
  const [disconnectingInstagram, setDisconnectingInstagram] = useState(false);

  async function loadStatuses() {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    const [pr, ir] = await Promise.allSettled([
      authFetch("/api/v1/promote/pinterest/status").then((r) => r.ok ? r.json() : null),
      authFetch("/api/v1/promote/instagram/status").then((r) => r.ok ? r.json() : null),
    ]);
    if (pr.status === "fulfilled") setPinterestStatus(pr.value);
    if (ir.status === "fulfilled") setInstagramStatus(ir.value);
    setLoading(false);
  }

  useEffect(() => {
    loadStatuses();
  }, []);

  // Handle OAuth redirect-back query params
  useEffect(() => {
    const connected = searchParams.get("connected");
    const error = searchParams.get("error");
    if (connected) {
      setToast(`${connected.charAt(0).toUpperCase() + connected.slice(1)} connected successfully.`);
      loadStatuses();
      // Clear query params without full reload
      window.history.replaceState({}, "", "/promote");
    } else if (error) {
      const messages: Record<string, string> = {
        pinterest_not_configured: "Pinterest is not configured on this server.",
        pinterest_invalid_state: "Pinterest connection failed — invalid or expired state.",
        pinterest_token_exchange_failed: "Pinterest token exchange failed. Check your app credentials.",
        pinterest_no_token: "Pinterest did not return an access token.",
        instagram_not_configured: "Instagram is not configured on this server.",
        instagram_invalid_state: "Instagram connection failed — invalid or expired state.",
        instagram_token_exchange_failed: "Instagram token exchange failed. Check your app credentials.",
        instagram_no_token: "Instagram did not return an access token.",
      };
      setToast(messages[error] ?? `Connection error: ${error}`);
      window.history.replaceState({}, "", "/promote");
    }
  }, [searchParams]);

  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(null), 5000);
      return () => clearTimeout(t);
    }
  }, [toast]);

  async function handleConnect(platform: "pinterest" | "instagram") {
    const setConnecting = platform === "pinterest" ? setConnectingPinterest : setConnectingInstagram;
    setConnecting(true);
    try {
      const r = await authFetch(`/api/v1/promote/${platform}/connect-url`);
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        setToast(err.detail ?? `Failed to get ${platform} connect URL.`);
        return;
      }
      const { url } = await r.json();
      window.location.href = url;
    } catch {
      setToast(`Network error connecting ${platform}.`);
      setConnecting(false);
    }
  }

  async function handleDisconnect(platform: "pinterest" | "instagram") {
    const setDisconnecting = platform === "pinterest" ? setDisconnectingPinterest : setDisconnectingInstagram;
    setDisconnecting(true);
    try {
      await authFetch(`/api/v1/promote/${platform}/disconnect`, { method: "DELETE" });
      setToast(`${platform.charAt(0).toUpperCase() + platform.slice(1)} disconnected.`);
      await loadStatuses();
    } catch {
      setToast(`Failed to disconnect ${platform}.`);
    } finally {
      setDisconnecting(false);
    }
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Promote</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Connect your social accounts to share listings. Always review before posting.
        </p>
      </div>

      <div className="px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        Social posts are <strong>never auto-published</strong>. You will explicitly review and confirm before anything is shared.
      </div>

      {toast && (
        <div className="px-4 py-3 bg-gray-900 text-white text-sm rounded-lg shadow">
          {toast}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="space-y-4">
          <PlatformCard
            platform="pinterest"
            icon="📌"
            displayName="Pinterest"
            description="Pin your listing photos to Pinterest boards with an auto-generated caption. Connect your own Pinterest account."
            status={pinterestStatus}
            onConnect={() => handleConnect("pinterest")}
            onDisconnect={() => handleDisconnect("pinterest")}
            connecting={connectingPinterest}
            disconnecting={disconnectingPinterest}
          />
          <PlatformCard
            platform="instagram"
            icon="📸"
            displayName="Instagram"
            description="Generate an Instagram caption from your listing details. Connect your Business or Creator account."
            status={instagramStatus}
            onConnect={() => handleConnect("instagram")}
            onDisconnect={() => handleDisconnect("instagram")}
            connecting={connectingInstagram}
            disconnecting={disconnectingInstagram}
          />
        </div>
      )}
    </main>
  );
}

export default function PromotePage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-400">Loading…</div>}>
      <PromoteContent />
    </Suspense>
  );
}
