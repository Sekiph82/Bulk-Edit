"use client";

import { useEffect, useState, Suspense, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

type PlatformState = "app_not_configured" | "not_connected" | "connected" | "expired";

interface PlatformStatus {
  platform: string;
  state: PlatformState;
  connected: boolean;
  connected_at?: string | null;
  expires_at?: string | null;
  account_name?: string | null;
  username?: string | null;
  external_account_id?: string | null;
}

interface PromoteListing {
  listing_id: string;
  title: string;
  price?: string | null;
  currency_code?: string | null;
  primary_image_url?: string | null;
  etsy_listing_url?: string | null;
}

interface ShareResult {
  success: boolean;
  deferred?: boolean;
  message: string;
  caption?: string;
}

function authFetch(path: string, options?: RequestInit) {
  const token = getAccessToken();
  return fetch(`${BACKEND_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
      Authorization: `Bearer ${token}`,
    },
  });
}

// ---------------------------------------------------------------------------
// Popup OAuth hook
// ---------------------------------------------------------------------------

function usePopupOAuth(platform: "pinterest" | "instagram") {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [popupUrl, setPopupUrl] = useState<string | null>(null);

  const startConnect = useCallback(async (onSuccess: () => void) => {
    setPending(true);
    setError(null);
    setPopupUrl(null);
    try {
      const r = await authFetch(`/api/v1/promote/${platform}/connect-url`);
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        setError(err.detail ?? `Failed to get ${platform} connection URL.`);
        setPending(false);
        return;
      }
      const { url } = await r.json();

      const width = 600;
      const height = 700;
      const left = Math.round(window.screen.width / 2 - width / 2);
      const top = Math.round(window.screen.height / 2 - height / 2);
      const popup = window.open(
        url,
        `${platform}_oauth`,
        `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
      );

      if (!popup || popup.closed) {
        setPopupUrl(url);
        setError("Popup was blocked. Use the link below to connect.");
        setPending(false);
        return;
      }

      const messageHandler = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return;
        const msg = event.data;
        if (!msg || msg.type !== "bulk-edit-social-oauth" || msg.platform !== platform) return;
        window.removeEventListener("message", messageHandler);
        clearInterval(pollTimer);
        setPending(false);
        if (msg.status === "success") {
          onSuccess();
        } else {
          setError(msg.message ?? "Connection failed. Please try again.");
        }
      };
      window.addEventListener("message", messageHandler);

      const pollTimer = setInterval(() => {
        if (popup.closed) {
          clearInterval(pollTimer);
          window.removeEventListener("message", messageHandler);
          setPending(false);
        }
      }, 500);
    } catch {
      setError(`Network error. Please try again.`);
      setPending(false);
    }
  }, [platform]);

  return { startConnect, pending, error, popupUrl, clearError: () => { setError(null); setPopupUrl(null); } };
}

// ---------------------------------------------------------------------------
// SocialConnectModal
// ---------------------------------------------------------------------------

function SocialConnectModal({
  open,
  onClose,
  platform,
  state,
  isSuperuser,
  onStartOAuth,
  oauthPending,
  oauthError,
  oauthPopupUrl,
}: {
  open: boolean;
  onClose: () => void;
  platform: "pinterest" | "instagram";
  state: "app_not_configured" | "not_connected" | "expired";
  isSuperuser: boolean;
  onStartOAuth?: () => void;
  oauthPending?: boolean;
  oauthError?: string | null;
  oauthPopupUrl?: string | null;
}) {
  if (!open) return null;
  const displayName = platform === "pinterest" ? "Pinterest" : "Instagram";
  const isConfigured = state !== "app_not_configured";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 border-b border-gray-100">
          <h3 className="text-base font-semibold text-gray-900">
            {state === "expired" ? `Reconnect ${displayName}` : `Connect ${displayName}`}
          </h3>
        </div>
        <div className="p-5 space-y-3">
          {!isConfigured ? (
            <>
              <p className="text-sm text-gray-700">
                {displayName} connection is not available yet. Once Bulk-Edit enables {displayName} integration, you will be able to connect your {displayName} account here.
              </p>
              {platform === "instagram" && (
                <p className="text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
                  Instagram publishing requires a <strong>Business</strong> or <strong>Creator</strong> account connected to a Facebook Page.
                </p>
              )}
              {isSuperuser && (
                <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                  Admin setup required: configure {platform === "pinterest" ? "Pinterest" : "Meta"} app credentials in environment settings.
                </p>
              )}
            </>
          ) : (
            <>
              <p className="text-sm text-gray-700">
                {platform === "pinterest"
                  ? state === "expired"
                    ? "Your Pinterest connection has expired. Reconnect to continue creating Pins from your Etsy listings."
                    : "Connect your Pinterest account to create Pins from your Etsy listings."
                  : state === "expired"
                    ? "Your Instagram connection has expired. Reconnect to continue."
                    : "Connect Instagram through Meta to prepare posts from your Etsy listings."}
              </p>
              {platform === "instagram" && (
                <p className="text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
                  Instagram publishing requires a <strong>Business</strong> or <strong>Creator</strong> account connected to a Facebook Page.
                </p>
              )}
              {oauthError && (
                <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                  {oauthError}
                  {oauthPopupUrl && (
                    <a
                      href={oauthPopupUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block mt-1 text-indigo-600 underline"
                    >
                      Open {displayName} connection in new tab
                    </a>
                  )}
                </div>
              )}
            </>
          )}
        </div>
        <div className="p-5 pt-0 flex gap-2">
          {isConfigured && onStartOAuth && (
            <button
              onClick={onStartOAuth}
              disabled={oauthPending}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {oauthPending ? `Opening ${displayName}…` : `Connect with ${displayName}`}
            </button>
          )}
          <button
            onClick={onClose}
            className="text-sm text-gray-500 hover:text-gray-700 font-medium px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            {isConfigured ? "Cancel" : "Close"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// PlatformCard
// ---------------------------------------------------------------------------

function PlatformCard({
  platform,
  icon,
  displayName,
  status,
  onOpenConnectModal,
  onDisconnect,
  disconnecting,
}: {
  platform: "pinterest" | "instagram";
  icon: string;
  displayName: string;
  status: PlatformStatus | null;
  onOpenConnectModal: () => void;
  onDisconnect: () => void;
  disconnecting: boolean;
}) {
  const state = status?.state ?? "not_connected";

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <h2 className="text-base font-semibold text-gray-900">{displayName}</h2>
        {state === "connected" && (
          <span className="ml-auto text-xs px-2 py-0.5 rounded-full font-medium bg-green-100 text-green-700">
            Connected
          </span>
        )}
        {state === "expired" && (
          <span className="ml-auto text-xs px-2 py-0.5 rounded-full font-medium bg-amber-100 text-amber-700">
            Expired
          </span>
        )}
      </div>

      {(state === "app_not_configured" || state === "not_connected") && (
        <button
          onClick={onOpenConnectModal}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          Connect {displayName}
        </button>
      )}

      {state === "connected" && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-green-600 text-sm">✓</span>
            <p className="text-sm text-gray-700 font-medium">{displayName} connected.</p>
          </div>
          {(status?.account_name || status?.username) && (
            <p className="text-xs text-gray-500">
              Account: <strong>{status.account_name ?? status.username}</strong>
              {status.username && status.account_name && status.username !== status.account_name && (
                <span className="text-gray-400"> (@{status.username})</span>
              )}
            </p>
          )}
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
        <div className="space-y-2">
          <p className="text-sm text-gray-500">Connection expired.</p>
          <div className="flex gap-2">
            <button
              onClick={onOpenConnectModal}
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              Reconnect {displayName}
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
    </div>
  );
}

// ---------------------------------------------------------------------------
// PromoteListingCard
// ---------------------------------------------------------------------------

function PromoteListingCard({
  listing,
  pinterestConnected,
  instagramConnected,
  onSharePinterest,
  onShareInstagram,
}: {
  listing: PromoteListing;
  pinterestConnected: boolean;
  instagramConnected: boolean;
  onSharePinterest: (l: PromoteListing) => void;
  onShareInstagram: (l: PromoteListing) => void;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition-shadow">
      <div className="aspect-square bg-gray-100 relative">
        {listing.primary_image_url ? (
          <img
            src={listing.primary_image_url}
            alt={listing.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300">
            <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 24 24">
              <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z" />
            </svg>
          </div>
        )}
      </div>
      <div className="p-3 space-y-2">
        <p className="text-sm font-medium text-gray-900 truncate" title={listing.title}>
          {listing.title}
        </p>
        {listing.price && (
          <p className="text-xs text-gray-500">
            {listing.currency_code ?? ""} {listing.price}
          </p>
        )}
        <div className="flex gap-2 pt-1">
          <button
            onClick={() => onSharePinterest(listing)}
            title={pinterestConnected ? "Share to Pinterest" : "Connect Pinterest first"}
            className={`flex-1 text-xs py-1.5 rounded-lg border font-medium transition-colors ${
              pinterestConnected
                ? "bg-red-50 border-red-200 text-red-700 hover:bg-red-100"
                : "bg-gray-50 border-gray-200 text-gray-400 cursor-pointer"
            }`}
          >
            📌 Pin
          </button>
          <button
            onClick={() => onShareInstagram(listing)}
            title={instagramConnected ? "Share to Instagram" : "Connect Instagram first"}
            className={`flex-1 text-xs py-1.5 rounded-lg border font-medium transition-colors ${
              instagramConnected
                ? "bg-purple-50 border-purple-200 text-purple-700 hover:bg-purple-100"
                : "bg-gray-50 border-gray-200 text-gray-400 cursor-pointer"
            }`}
          >
            📸 Post
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Share Modal (reused for Pinterest + Instagram)
// ---------------------------------------------------------------------------

function ShareModal({
  open,
  onClose,
  listing,
  platform,
  platformConnected,
  onConnect,
}: {
  open: boolean;
  onClose: () => void;
  listing: PromoteListing | null;
  platform: "pinterest" | "instagram";
  platformConnected: boolean;
  onConnect: () => void;
}) {
  const [caption, setCaption] = useState("");
  const [sharing, setSharing] = useState(false);
  const [result, setResult] = useState<ShareResult | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (listing) {
      const base = listing.title || "";
      const suffix = listing.etsy_listing_url ? ` ${listing.etsy_listing_url}` : "";
      setCaption(`${base} #etsy #handmade${suffix}`);
    }
    setResult(null);
    setCopied(false);
  }, [listing, open]);

  if (!open || !listing) return null;

  const displayName = platform === "pinterest" ? "Pinterest" : "Instagram";
  const endpoint = `/api/v1/promote/${platform}/share`;

  async function handleShare() {
    if (!listing) return;
    setSharing(true);
    setResult(null);
    try {
      const r = await authFetch(endpoint, {
        method: "POST",
        body: JSON.stringify({
          listing_id: listing.listing_id,
          caption,
          image_url: listing.primary_image_url,
          destination_url: listing.etsy_listing_url,
        }),
      });
      const data = await r.json();
      if (!r.ok) {
        setResult({ success: false, message: data.detail ?? "Share failed." });
      } else {
        setResult(data);
      }
    } catch {
      setResult({ success: false, message: "Network error. Please try again." });
    } finally {
      setSharing(false);
    }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(caption);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    if (!listing?.primary_image_url) return;
    const a = document.createElement("a");
    a.href = listing.primary_image_url;
    a.download = `${listing.title || "product"}.jpg`;
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 border-b border-gray-100">
          <h3 className="text-base font-semibold text-gray-900">
            Share to {displayName}
          </h3>
        </div>
        <div className="p-5 space-y-4">
          {listing.primary_image_url && (
            <img
              src={listing.primary_image_url}
              alt={listing.title}
              className="w-full h-40 object-cover rounded-xl"
            />
          )}
          <p className="text-sm font-medium text-gray-900">{listing.title}</p>

          {platform === "instagram" && (
            <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              Instagram publishing requires a <strong>Business</strong> or <strong>Creator</strong> account connected to a Facebook Page.
            </div>
          )}

          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Caption</label>
            <textarea
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              rows={3}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>

          {listing.etsy_listing_url && (
            <p className="text-xs text-gray-400 truncate">
              Etsy link: <a href={listing.etsy_listing_url} target="_blank" rel="noopener noreferrer" className="text-indigo-500 hover:underline">{listing.etsy_listing_url}</a>
            </p>
          )}

          {result && (
            <div className={`text-sm px-3 py-2 rounded-lg ${result.success ? "bg-green-50 text-green-700 border border-green-200" : "bg-amber-50 text-amber-700 border border-amber-200"}`}>
              {result.message}
            </div>
          )}

          {!platformConnected && (
            <div className="text-sm text-gray-600 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
              Connect your {displayName} account to share.{" "}
              <button onClick={onConnect} className="text-indigo-600 font-medium underline">
                Connect {displayName}
              </button>
            </div>
          )}
        </div>

        <div className="p-5 pt-0 flex gap-2 flex-wrap">
          {platformConnected && (
            <button
              onClick={handleShare}
              disabled={sharing}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {sharing ? "Sharing…" : platform === "pinterest" ? "Create Pin" : "Share to Instagram"}
            </button>
          )}
          <button
            onClick={handleCopy}
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            {copied ? "Copied!" : "Copy caption"}
          </button>
          {listing.primary_image_url && (
            <button
              onClick={handleDownload}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              Download image
            </button>
          )}
          <button
            onClick={onClose}
            className="ml-auto text-sm text-gray-500 hover:text-gray-700 font-medium px-4 py-2"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------

function Toast({ text, type, onClose }: { text: string; type: "success" | "error"; onClose: () => void }) {
  useEffect(() => {
    const t = setTimeout(onClose, 5000);
    return () => clearTimeout(t);
  }, [onClose]);

  return (
    <div
      className={`fixed bottom-5 right-5 z-50 px-4 py-3 text-sm rounded-xl shadow-lg cursor-pointer ${
        type === "error" ? "bg-red-700 text-white" : "bg-gray-900 text-white"
      }`}
      onClick={onClose}
    >
      {text}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main content
// ---------------------------------------------------------------------------

function PromoteContent() {
  const router = useRouter();

  const [isSuperuser, setIsSuperuser] = useState(false);
  const [pinterestStatus, setPinterestStatus] = useState<PlatformStatus | null>(null);
  const [instagramStatus, setInstagramStatus] = useState<PlatformStatus | null>(null);
  const [listings, setListings] = useState<PromoteListing[]>([]);
  const [listingsEmpty, setListingsEmpty] = useState(false);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const [disconnectingPinterest, setDisconnectingPinterest] = useState(false);
  const [disconnectingInstagram, setDisconnectingInstagram] = useState(false);

  // Connect modals (explanation / OAuth trigger)
  const [pinterestConnectOpen, setPinterestConnectOpen] = useState(false);
  const [instagramConnectOpen, setInstagramConnectOpen] = useState(false);

  // Share modals
  const [shareTarget, setShareTarget] = useState<PromoteListing | null>(null);
  const [pinterestModalOpen, setPinterestModalOpen] = useState(false);
  const [instagramModalOpen, setInstagramModalOpen] = useState(false);

  const pinterestOAuth = usePopupOAuth("pinterest");
  const instagramOAuth = usePopupOAuth("instagram");

  const loadStatuses = useCallback(async () => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    const [me, pr, ir, lr] = await Promise.allSettled([
      authFetch("/api/v1/auth/me").then((r) => r.ok ? r.json() : null),
      authFetch("/api/v1/promote/pinterest/status").then((r) => r.ok ? r.json() : null),
      authFetch("/api/v1/promote/instagram/status").then((r) => r.ok ? r.json() : null),
      authFetch("/api/v1/promote/listings").then((r) => r.ok ? r.json() : null),
    ]);
    if (me.status === "fulfilled" && me.value) setIsSuperuser(me.value.user?.is_superuser === true);
    if (pr.status === "fulfilled" && pr.value) setPinterestStatus(pr.value);
    if (ir.status === "fulfilled" && ir.value) setInstagramStatus(ir.value);
    if (lr.status === "fulfilled" && lr.value) {
      setListings(lr.value.listings ?? []);
      setListingsEmpty(lr.value.empty ?? true);
    }
    setLoading(false);
  }, [router]);

  useEffect(() => {
    loadStatuses();
  }, [loadStatuses]);

  function handleOAuthPinterest() {
    pinterestOAuth.startConnect(async () => {
      setPinterestConnectOpen(false);
      await loadStatuses();
      setToast({ text: "Pinterest connected successfully.", type: "success" });
    });
  }

  function handleOAuthInstagram() {
    instagramOAuth.startConnect(async () => {
      setInstagramConnectOpen(false);
      await loadStatuses();
      setToast({ text: "Instagram connected successfully.", type: "success" });
    });
  }

  async function handleDisconnectPinterest() {
    setDisconnectingPinterest(true);
    try {
      await authFetch("/api/v1/promote/pinterest/disconnect", { method: "DELETE" });
      setToast({ text: "Pinterest disconnected.", type: "success" });
      await loadStatuses();
    } catch {
      setToast({ text: "Failed to disconnect Pinterest.", type: "error" });
    } finally {
      setDisconnectingPinterest(false);
    }
  }

  async function handleDisconnectInstagram() {
    setDisconnectingInstagram(true);
    try {
      await authFetch("/api/v1/promote/instagram/disconnect", { method: "DELETE" });
      setToast({ text: "Instagram disconnected.", type: "success" });
      await loadStatuses();
    } catch {
      setToast({ text: "Failed to disconnect Instagram.", type: "error" });
    } finally {
      setDisconnectingInstagram(false);
    }
  }

  function handleSharePinterest(listing: PromoteListing) {
    if (!pinterestConnected) {
      setPinterestConnectOpen(true);
      return;
    }
    setShareTarget(listing);
    setPinterestModalOpen(true);
  }

  function handleShareInstagram(listing: PromoteListing) {
    if (!instagramConnected) {
      setInstagramConnectOpen(true);
      return;
    }
    setShareTarget(listing);
    setInstagramModalOpen(true);
  }

  const pinterestConnected = pinterestStatus?.connected === true;
  const instagramConnected = instagramStatus?.connected === true;

  return (
    <main className="max-w-4xl mx-auto px-6 py-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Promote</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Share your listings on social platforms. Connect your own accounts — we never post without your confirmation.
        </p>
      </div>

      <div className="px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        Posts are <strong>never auto-published</strong>. You review and confirm every post before it goes live.
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          {/* Connected Accounts */}
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Connected Accounts</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <PlatformCard
                platform="pinterest"
                icon="📌"
                displayName="Pinterest"
                status={pinterestStatus}
                onOpenConnectModal={() => { pinterestOAuth.clearError(); setPinterestConnectOpen(true); }}
                onDisconnect={handleDisconnectPinterest}
                disconnecting={disconnectingPinterest}
              />
              <PlatformCard
                platform="instagram"
                icon="📸"
                displayName="Instagram"
                status={instagramStatus}
                onOpenConnectModal={() => { instagramOAuth.clearError(); setInstagramConnectOpen(true); }}
                onDisconnect={handleDisconnectInstagram}
                disconnecting={disconnectingInstagram}
              />
            </div>
          </section>

          {/* Products */}
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Your Products</h2>
            {listingsEmpty ? (
              <div className="bg-gray-50 border border-gray-200 rounded-xl py-12 text-center text-gray-500 text-sm">
                Sync your Etsy listings first to promote products.
              </div>
            ) : (
              <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4">
                {listings.map((listing) => (
                  <PromoteListingCard
                    key={listing.listing_id}
                    listing={listing}
                    pinterestConnected={pinterestConnected}
                    instagramConnected={instagramConnected}
                    onSharePinterest={handleSharePinterest}
                    onShareInstagram={handleShareInstagram}
                  />
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {/* Connect modals */}
      <SocialConnectModal
        open={pinterestConnectOpen}
        onClose={() => setPinterestConnectOpen(false)}
        platform="pinterest"
        state={(pinterestStatus?.state as "app_not_configured" | "not_connected" | "expired") ?? "not_connected"}
        isSuperuser={isSuperuser}
        onStartOAuth={handleOAuthPinterest}
        oauthPending={pinterestOAuth.pending}
        oauthError={pinterestOAuth.error}
        oauthPopupUrl={pinterestOAuth.popupUrl}
      />
      <SocialConnectModal
        open={instagramConnectOpen}
        onClose={() => setInstagramConnectOpen(false)}
        platform="instagram"
        state={(instagramStatus?.state as "app_not_configured" | "not_connected" | "expired") ?? "not_connected"}
        isSuperuser={isSuperuser}
        onStartOAuth={handleOAuthInstagram}
        oauthPending={instagramOAuth.pending}
        oauthError={instagramOAuth.error}
        oauthPopupUrl={instagramOAuth.popupUrl}
      />

      {/* Share modals */}
      <ShareModal
        open={pinterestModalOpen}
        onClose={() => { setPinterestModalOpen(false); setShareTarget(null); }}
        listing={shareTarget}
        platform="pinterest"
        platformConnected={pinterestConnected}
        onConnect={() => { setPinterestModalOpen(false); setPinterestConnectOpen(true); }}
      />
      <ShareModal
        open={instagramModalOpen}
        onClose={() => { setInstagramModalOpen(false); setShareTarget(null); }}
        listing={shareTarget}
        platform="instagram"
        platformConnected={instagramConnected}
        onConnect={() => { setInstagramModalOpen(false); setInstagramConnectOpen(true); }}
      />

      {toast && (
        <Toast text={toast.text} type={toast.type} onClose={() => setToast(null)} />
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
