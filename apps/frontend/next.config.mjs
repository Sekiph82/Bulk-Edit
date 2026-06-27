/** @type {import('next').NextConfig} */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";

// CSP: pragmatic for self-hosted SaaS.
// 'unsafe-inline' required for the anti-flash theme script in app/layout.tsx.
// Nonce-based CSP hardening is deferred to Sprint 21 (see docs/operations/LAUNCH_CHECKLIST.md).
const ContentSecurityPolicy = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com`,
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
