"use client";

import { Fragment, useState } from "react";
import { PageHeader, Card, StatCard, Badge, fmt, downloadCsv, todayStamp } from "@/components/owner/OwnerUI";
import { BLOG_POSTS, BLOG_CATEGORIES, type BlogPost } from "@/lib/blogPosts";
import { FREE_TOOLS } from "@/lib/freeTools";
import { COMPARISON_PAGES } from "@/lib/comparisonPages";

const PUBLIC_BASE = "https://bulkeditapp.com";

// Audits the typed static content system (lib/blogPosts.ts, lib/freeTools.ts,
// lib/comparisonPages.ts) — there is no CMS/blog backend, so this page reads
// the same content registries the public site renders from, rather than a
// database. See the "safe editing" note rendered below for why no live
// publish/edit controls exist here.

function mentionsCompetitor(post: BlogPost): boolean {
  const haystack = [
    post.title,
    post.intro,
    ...post.sections.flatMap((s) => [s.heading, ...s.paragraphs, ...(s.list ?? [])]),
  ].join(" ");
  return /\bVela\b|\beRank\b|\bEvlista\b/i.test(haystack);
}

type SeoCheck = { label: string; pass: boolean };

function runSeoChecks(post: BlogPost): SeoCheck[] {
  return [
    { label: "Has title", pass: Boolean(post.title && post.metaTitle) },
    { label: "Has description", pass: Boolean(post.description) },
    { label: "Has canonical", pass: true }, // derived from slug at render time — always present
    { label: "Has target keywords", pass: post.targetKeywords.length > 0 },
    { label: "Has disclaimer where needed", pass: !mentionsCompetitor(post) || Boolean(post.disclaimer) },
    { label: "Has internal CTA", pass: Boolean(post.ctaTitle && post.ctaBody) },
    { label: "Has related posts", pass: post.related.length > 0 },
  ];
}

const PHASE_4B_PAGES = [
  { type: "Tool", title: "Free Etsy Seller Tools", path: "/tools" },
  ...FREE_TOOLS.map((t) => ({ type: "Tool", title: t.title, path: `/tools/${t.slug}` })),
  { type: "Comparison", title: "Compare Etsy Seller Tools", path: "/compare" },
  ...COMPARISON_PAGES.map((c) => ({ type: "Comparison", title: c.h1, path: `/compare/${c.slug}` })),
];

const CONTENT_ROADMAP = [
  "eRank comparison page (dedicated landing page — currently only covered in a blog post)",
  "Marmalead comparison page",
  "Etsy listing photo checklist",
  "Etsy variation cleanup guide",
  "Etsy shipping profile cleanup guide",
  "Etsy product video script templates",
];

const CSV_COLUMNS = [
  "type", "title", "slug_or_path", "category", "published_at", "updated_at", "canonical_url", "target_keywords", "metadata_status",
];

export default function OwnerContentPage() {
  const [checksOpenSlug, setChecksOpenSlug] = useState<string | null>(null);

  const categories = BLOG_CATEGORIES;
  const lastUpdated = BLOG_POSTS.reduce<string | null>((latest, p) => {
    const candidate = p.updatedAt ?? p.publishedAt;
    return !latest || candidate > latest ? candidate : latest;
  }, null);

  function handleExport() {
    const blogRows = BLOG_POSTS.map((p) => ({
      type: "Blog post",
      title: p.title,
      slug_or_path: `/blog/${p.slug}`,
      category: p.category,
      published_at: p.publishedAt,
      updated_at: p.updatedAt ?? "",
      canonical_url: `${PUBLIC_BASE}/blog/${p.slug}`,
      target_keywords: p.targetKeywords.join("; "),
      metadata_status: runSeoChecks(p).every((c) => c.pass) ? "OK" : "Review",
    }));
    const pageRows = PHASE_4B_PAGES.map((pg) => ({
      type: pg.type,
      title: pg.title,
      slug_or_path: pg.path,
      category: pg.type,
      published_at: "",
      updated_at: "",
      canonical_url: `${PUBLIC_BASE}${pg.path}`,
      target_keywords: "",
      metadata_status: "OK",
    }));
    downloadCsv(`owner-content-inventory-${todayStamp()}.csv`, [...blogRows, ...pageRows], CSV_COLUMNS);
  }

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Content" sub="Blog / SEO content audit — superuser only" />

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-6">
        <StatCard label="Total blog posts" value={BLOG_POSTS.length} />
        <StatCard label="Published posts" value={BLOG_POSTS.length} sub="No draft workflow yet — all typed posts are live" />
        <StatCard label="Categories" value={categories.length} />
        <StatCard label="Phase 4B SEO pages" value={PHASE_4B_PAGES.length} />
        <StatCard label="Last updated" value={lastUpdated ? fmt(lastUpdated) : "—"} />
      </div>

      <div className="mb-6">
        <Card>
          <p className="text-sm text-gray-700 font-medium mb-1">Public blog content is currently stored as typed static content in the repository.</p>
          <p className="text-sm text-gray-500 mb-3">
            This owner page audits and tracks content, but live CMS editing is intentionally not enabled yet.
          </p>
          <p className="text-xs text-gray-400">
            When live editing is needed, add a protected CMS backend here with drafts, review workflow, audit logs, and publish controls.
          </p>
        </Card>
      </div>

      <div className="mb-6">
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-800">Blog inventory ({BLOG_POSTS.length})</h2>
            <button
              type="button"
              onClick={handleExport}
              className="text-xs font-medium text-indigo-600 border border-indigo-200 rounded-lg px-3 py-1.5 hover:bg-indigo-50"
            >
              Export CSV
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                  <th className="pb-2 pr-4">Title</th>
                  <th className="pb-2 pr-4">Category</th>
                  <th className="pb-2 pr-4">Published</th>
                  <th className="pb-2 pr-4">Updated</th>
                  <th className="pb-2 pr-4">Reading time</th>
                  <th className="pb-2 pr-4">Keywords</th>
                  <th className="pb-2 pr-4">Metadata</th>
                  <th className="pb-2">Public URL</th>
                </tr>
              </thead>
              <tbody>
                {BLOG_POSTS.map((p) => {
                  const checks = runSeoChecks(p);
                  const allPass = checks.every((c) => c.pass);
                  const isOpen = checksOpenSlug === p.slug;
                  return (
                    <Fragment key={p.slug}>
                      <tr className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-2 pr-4 font-medium text-gray-800">
                          {p.title}
                          <p className="text-xs text-gray-400 font-mono">/blog/{p.slug}</p>
                        </td>
                        <td className="py-2 pr-4 text-gray-500">{p.category}</td>
                        <td className="py-2 pr-4 text-gray-400">{fmt(p.publishedAt)}</td>
                        <td className="py-2 pr-4 text-gray-400">{p.updatedAt ? fmt(p.updatedAt) : "—"}</td>
                        <td className="py-2 pr-4 text-gray-500">{p.readingTime}</td>
                        <td className="py-2 pr-4 text-gray-500">{p.targetKeywords.length}</td>
                        <td className="py-2 pr-4">
                          <button type="button" onClick={() => setChecksOpenSlug(isOpen ? null : p.slug)}>
                            <Badge status={allPass ? "true" : "false"} />
                          </button>
                        </td>
                        <td className="py-2">
                          <a
                            href={`${PUBLIC_BASE}/blog/${p.slug}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs text-indigo-600 hover:underline"
                          >
                            View →
                          </a>
                        </td>
                      </tr>
                      {isOpen && (
                        <tr className="bg-gray-50/60">
                          <td colSpan={8} className="px-4 py-3">
                            <p className="text-xs text-gray-400 mb-2">
                              Canonical: <span className="font-mono">{PUBLIC_BASE}/blog/{p.slug}</span>
                            </p>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                              {checks.map((c) => (
                                <span key={c.label} className="text-xs flex items-center gap-1.5">
                                  <Badge status={c.pass ? "true" : "false"} />
                                  {c.label}
                                </span>
                              ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <h2 className="text-base font-semibold text-gray-800 mb-4">Phase 4B SEO page inventory</h2>
          <ul className="space-y-2">
            {PHASE_4B_PAGES.map((pg) => (
              <li key={pg.path} className="flex items-center justify-between text-sm">
                <span className="text-gray-700">
                  {pg.title} <span className="text-xs text-gray-400 font-mono">{pg.path}</span>
                </span>
                <a href={`${PUBLIC_BASE}${pg.path}`} target="_blank" rel="noreferrer" className="text-xs text-indigo-600 hover:underline">
                  View →
                </a>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <h2 className="text-base font-semibold text-gray-800 mb-4">Content roadmap</h2>
          <ul className="space-y-2">
            {CONTENT_ROADMAP.map((item) => (
              <li key={item} className="text-sm text-gray-600 flex items-start gap-2">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-gray-300 flex-shrink-0" />
                {item}
              </li>
            ))}
          </ul>
          <p className="text-xs text-gray-400 mt-4">Not built yet — future content ideas only.</p>
        </Card>
      </div>
    </main>
  );
}
