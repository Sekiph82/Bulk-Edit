import type { MetadataRoute } from "next";
import { FEATURE_PAGES } from "@/lib/featurePages";
import { BLOG_POSTS } from "@/lib/blogPosts";

// Public marketing/indexable apex routes only. Never include app/dashboard/
// admin/private routes here — those are noindex and excluded on purpose
// (see robots.ts and middleware.ts X-Robots-Tag handling).
const PUBLIC_ROUTES = ["/", "/features", "/pricing", "/faq", "/contact-us", "/privacy", "/terms", "/blog"];

export default function sitemap(): MetadataRoute.Sitemap {
  const base = "https://bulkeditapp.com";
  const now = new Date();

  const staticEntries = PUBLIC_ROUTES.map((path) => ({
    url: `${base}${path}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: path === "/" ? 1 : 0.7,
  }));

  const featureEntries = FEATURE_PAGES.map((f) => ({
    url: `${base}/features/${f.slug}`,
    lastModified: now,
    changeFrequency: "monthly" as const,
    priority: 0.6,
  }));

  const blogEntries = BLOG_POSTS.map((p) => ({
    url: `${base}/blog/${p.slug}`,
    lastModified: new Date(p.updatedAt ?? p.publishedAt),
    changeFrequency: "monthly" as const,
    priority: 0.6,
  }));

  return [...staticEntries, ...featureEntries, ...blogEntries];
}
