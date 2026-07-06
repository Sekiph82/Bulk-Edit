import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Host-based routing for the bulkeditapp.com domain model.
//   bulkeditapp.com          -> public marketing/SEO (indexable)
//   www.bulkeditapp.com      -> 301 redirect to apex
//   app.bulkeditapp.com      -> private SaaS app (noindex)
//   staging.bulkeditapp.com  -> staging app (noindex, whole host)
//   owner.bulkeditapp.com,
//   owner-staging.bulkeditapp.com
//                            -> internal owner console (noindex, superuser-only,
//                               rewritten to the /owner/* route tree so the URL
//                               bar stays on the owner host). Same rewrite logic
//                               for both hosts — one is production, one staging,
//                               each behind its own Cloudflare Access app.
// Local dev (localhost) and preview hosts (*.ondigitalocean.app, *.vercel.app)
// pass through UNCHANGED so nothing breaks outside production DNS.

const APEX = "bulkeditapp.com";
const WWW = "www.bulkeditapp.com";
const APP = "app.bulkeditapp.com";
const STAGING = "staging.bulkeditapp.com";
const OWNER = "owner.bulkeditapp.com";
const OWNER_STAGING = "owner-staging.bulkeditapp.com";
const OWNER_HOSTS = new Set([OWNER, OWNER_STAGING]);

// Private beta gate: when true, every app-path request (login, register,
// dashboard, billing, media, etc. — anything in APP_PREFIXES) is redirected
// to /private-beta instead of reaching the real (unconfigured-integrations)
// SaaS app. Off by default; only set NEXT_PUBLIC_PRIVATE_BETA_MODE=true on
// the production frontend app while Etsy/Stripe/email secrets are pending.
const PRIVATE_BETA_MODE = process.env.NEXT_PUBLIC_PRIVATE_BETA_MODE === "true";
const PRIVATE_BETA_PATH = "/private-beta";

// Authenticated product routes (the app/(app) group + auth pages).
// Requests for these on the apex marketing host are sent to the app subdomain.
const APP_PREFIXES = [
  "/dashboard", "/listings", "/bulk-edit", "/bulk-create", "/media", "/ai",
  "/csv", "/variations", "/pricing-rules", "/profit", "/insights",
  "/listing-health", "/scheduled", "/promote", "/video-generator", "/shops",
  "/billing", "/admin", "/owner", "/login", "/register",
];

const NOINDEX = "noindex, nofollow";

// Auth pages the owner host must pass through instead of rewriting into /owner/*.
const AUTH_PREFIXES = ["/login", "/register", "/forgot-password", "/reset-password"];

function hostname(req: NextRequest): string {
  const h = req.headers.get("host") || "";
  return h.split(":")[0].toLowerCase();
}

function isProductionDomain(host: string): boolean {
  return host === APEX || host === WWW || host === APP || host === STAGING || OWNER_HOSTS.has(host);
}

function isAppPath(pathname: string): boolean {
  return APP_PREFIXES.some((p) => pathname === p || pathname.startsWith(p + "/"));
}

export function middleware(req: NextRequest) {
  const host = hostname(req);
  const { pathname } = req.nextUrl;

  // Dev / preview hosts: do nothing (keeps localhost:3100 + DO/Vercel previews working).
  if (!isProductionDomain(host)) {
    return NextResponse.next();
  }

  // www -> apex (301), preserve path + query
  if (host === WWW) {
    const url = new URL(req.url);
    url.hostname = APEX;
    url.protocol = "https:";
    url.port = "";
    return NextResponse.redirect(url, 301);
  }

  // Apex marketing host: bounce app routes to the app subdomain — or, during
  // private beta, straight to the beta gate page on the same host, so a
  // visitor never even reaches app.bulkeditapp.com.
  if (host === APEX && isAppPath(pathname)) {
    const url = new URL(req.url);
    if (PRIVATE_BETA_MODE) {
      url.pathname = PRIVATE_BETA_PATH;
      return NextResponse.redirect(url, 307);
    }
    url.hostname = APP;
    url.protocol = "https:";
    url.port = "";
    return NextResponse.redirect(url, 307);
  }

  // App host directly requested during private beta (e.g. a stale bookmark
  // or someone typing the URL): redirect everything except the gate page
  // itself to /private-beta, before any real app page ever renders.
  if (PRIVATE_BETA_MODE && host === APP && pathname !== PRIVATE_BETA_PATH) {
    const url = req.nextUrl.clone();
    url.pathname = PRIVATE_BETA_PATH;
    return NextResponse.redirect(url, 307);
  }

  // Owner console host: clean public paths (owner.bulkeditapp.com/users) map
  // to the internal /owner/* route tree (app/owner/users/page.tsx) so the
  // URL bar stays clean. Superuser gating happens in the owner pages
  // themselves (client-side — this app has no server-visible session, so
  // middleware cannot enforce auth here).
  //
  // Auth pages are the one exception: there is no /owner/login route (the
  // owner console has no login form of its own — it reuses the same
  // localStorage-token login as the rest of the app), so those paths pass
  // through untouched instead of being rewritten into a 404.
  //
  // /owner and /owner/* are redirected (not rewritten) to their clean
  // equivalent — without this, a stray link to /owner/users on this host
  // would get the rewrite applied a second time and 404 as /owner/owner/users.
  if (OWNER_HOSTS.has(host)) {
    if (AUTH_PREFIXES.some((p) => pathname === p || pathname.startsWith(p + "/"))) {
      const res = NextResponse.next();
      res.headers.set("X-Robots-Tag", NOINDEX);
      return res;
    }
    if (pathname === "/owner" || pathname.startsWith("/owner/")) {
      const url = req.nextUrl.clone();
      url.pathname = pathname === "/owner" ? "/" : pathname.slice("/owner".length);
      return NextResponse.redirect(url, 307);
    }
    const url = req.nextUrl.clone();
    url.pathname = pathname === "/" ? "/owner" : `/owner${pathname}`;
    const res = NextResponse.rewrite(url);
    res.headers.set("X-Robots-Tag", NOINDEX);
    return res;
  }

  const res = NextResponse.next();

  // Private + staging hosts must never be indexed.
  if (host === APP || host === STAGING) {
    res.headers.set("X-Robots-Tag", NOINDEX);
  }
  // Staging: also mark app-env for downstream (banner is driven by build env too).
  if (host === STAGING) {
    res.headers.set("X-App-Env", "staging");
  }

  return res;
}

export const config = {
  // Run on everything except static assets and Next internals.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml|.*\\..*).*)"],
};
