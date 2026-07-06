import type { MetadataRoute } from "next";
import { FEATURE_PAGES } from "@/lib/featurePages";
import { BLOG_POSTS } from "@/lib/blogPosts";
import { COMPARISON_PAGES } from "@/lib/comparisonPages";
import { FREE_TOOLS } from "@/lib/freeTools";

// Public marketing/indexable apex routes only. Never include app/dashboard/
// admin/private routes here — those are noindex and excluded on purpose
// (see robots.ts and middleware.ts X-Robots-Tag handling). Owner-console
// routes (owner.bulkeditapp.com/*, including /content) are a separate,
// Cloudflare-Access-protected host and must never appear here.
const PUBLIC_ROUTES = ["/", "/features", "/pricing", "/faq", "/contact-us", "/privacy", "/terms", "/blog", "/tools", "/compare"];

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

  const toolEntries = FREE_TOOLS.map((t) => ({
    url: `${base}/tools/${t.slug}`,
    lastModified: now,
    changeFrequency: "monthly" as const,
    priority: 0.6,
  }));

  const compareEntries = COMPARISON_PAGES.map((c) => ({
    url: `${base}/compare/${c.slug}`,
    lastModified: now,
    changeFrequency: "monthly" as const,
    priority: 0.6,
  }));

  return [...staticEntries, ...featureEntries, ...blogEntries, ...toolEntries, ...compareEntries];
}
