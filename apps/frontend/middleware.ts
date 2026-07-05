import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Host-based routing for the bulkeditapp.com domain model.
//   bulkeditapp.com        -> public marketing/SEO (indexable)
//   www.bulkeditapp.com    -> 301 redirect to apex
//   app.bulkeditapp.com    -> private SaaS app (noindex)
//   staging.bulkeditapp.com-> staging app (noindex, whole host)
//   owner.bulkeditapp.com  -> internal owner console (noindex, superuser-only,
//                             rewritten to the /owner/* route tree so the URL
//                             bar stays on the owner host)
// Local dev (localhost) and preview hosts (*.ondigitalocean.app, *.vercel.app)
// pass through UNCHANGED so nothing breaks outside production DNS.

const APEX = "bulkeditapp.com";
const WWW = "www.bulkeditapp.com";
const APP = "app.bulkeditapp.com";
const STAGING = "staging.bulkeditapp.com";
const OWNER = "owner.bulkeditapp.com";

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
  return host === APEX || host === WWW || host === APP || host === STAGING || host === OWNER;
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

  // Apex marketing host: bounce app routes to the app subdomain.
  if (host === APEX && isAppPath(pathname)) {
    const url = new URL(req.url);
    url.hostname = APP;
    url.protocol = "https:";
    url.port = "";
    return NextResponse.redirect(url, 307);
  }

  // Owner console host: rewrite every request to the internal /owner/* route
  // tree, so owner.bulkeditapp.com/users serves app/owner/users/page.tsx
  // while the URL bar stays on the owner host. Superuser gating happens in
  // the owner pages themselves (client-side — this app has no server-visible
  // session, so middleware cannot enforce auth here).
  //
  // Auth pages are the one exception: there is no /owner/login route (the
  // owner console has no login form of its own — it reuses the same
  // localStorage-token login as the rest of the app), so those paths pass
  // through untouched instead of being rewritten into a 404.
  if (host === OWNER) {
    if (AUTH_PREFIXES.some((p) => pathname === p || pathname.startsWith(p + "/"))) {
      const res = NextResponse.next();
      res.headers.set("X-Robots-Tag", NOINDEX);
      return res;
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
