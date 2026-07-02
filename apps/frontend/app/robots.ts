import type { MetadataRoute } from "next";
import { headers } from "next/headers";

// Per-host robots. Marketing apex is indexable; app + staging + anything else
// (previews, dev) are fully disallowed. X-Robots-Tag headers in middleware.ts
// enforce noindex as a second layer for app/staging hosts.
export default function robots(): MetadataRoute.Robots {
  const host = (headers().get("host") || "").split(":")[0].toLowerCase();
  const isMarketing = host === "bulkeditapp.com" || host === "www.bulkeditapp.com";

  if (isMarketing) {
    return {
      rules: { userAgent: "*", allow: "/", disallow: ["/api/"] },
      sitemap: "https://bulkeditapp.com/sitemap.xml",
      host: "https://bulkeditapp.com",
    };
  }

  return {
    rules: { userAgent: "*", disallow: "/" },
  };
}
