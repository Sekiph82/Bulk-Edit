import type { MetadataRoute } from "next";

// Public marketing/indexable apex routes only. Never include app/dashboard/
// admin/private routes here — those are noindex and excluded on purpose
// (see robots.ts and middleware.ts X-Robots-Tag handling).
const PUBLIC_ROUTES = ["/", "/features", "/pricing", "/faq", "/contact-us", "/privacy", "/terms"];

export default function sitemap(): MetadataRoute.Sitemap {
  const base = "https://bulkeditapp.com";
  const now = new Date();
  return PUBLIC_ROUTES.map((path) => ({
    url: `${base}${path}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: path === "/" ? 1 : 0.7,
  }));
}
