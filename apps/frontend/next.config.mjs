/** @type {import('next').NextConfig} */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";
const IS_PROD = process.env.NODE_ENV === "production";

// CSP notes:
// - 'unsafe-inline' in script-src is required because Next.js App Router injects several
//   inline bootstrap scripts in production beyond just our anti-flash script. The sha256
//   approach only covers one known inline script; Next.js may add others per build.
// - Anti-flash script sha256 (for future nonce CSP reference):
//   sha256-tRVAlVKnDSmcZQ61d+9zNAPSQWWgJxOlnrg/ZOZsLFM=
// - Full CSP hardening (removing 'unsafe-inline') requires Next.js middleware nonce injection.
//   See docs/operations/LAUNCH_CHECKLIST.md and docs/operations/PRODUCTION_LAUNCH_FOLLOWUPS.md #7
//   — tracked as its own pre/post-launch hardening PR, not attempted as a drive-by change.
// - 'unsafe-eval' removed for production; only included in dev where Next.js HMR needs it.
const scriptSrc = IS_PROD
  ? `'self' 'unsafe-inline' https://js.stripe.com`
  : `'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com`;

const ContentSecurityPolicy = [
  "default-src 'self'",
  `script-src ${scriptSrc}`,
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com data:",
  "img-src 'self' data: blob: https:",
  `connect-src 'self' ${BACKEND_URL} https://api.stripe.com`,
  "frame-src https://js.stripe.com https://hooks.stripe.com",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const securityHeaders = [
  { key: "X-DNS-Prefetch-Control", value: "on" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), payment=(self)",
  },
  {
    key: "Content-Security-Policy",
    value: ContentSecurityPolicy,
  },
];

// HSTS: only in production — never in dev/staging without SSL
if (IS_PROD) {
  securityHeaders.push({
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  });
}

const nextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
