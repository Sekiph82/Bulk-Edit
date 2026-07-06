import type { Metadata } from "next";
import BlogIndexContent from "@/components/marketing/BlogIndexContent";
import { BLOG_POSTS } from "@/lib/blogPosts";

export const metadata: Metadata = {
  title: "Etsy Seller Guides — Bulk Edit App",
  description:
    "Practical guides for Etsy sellers on bulk editing, listing cleanup, tags, titles, product videos, pricing, and safer update workflows.",
  alternates: { canonical: "https://bulkeditapp.com/blog" },
  openGraph: {
    title: "Etsy Seller Guides — Bulk Edit App",
    description:
      "Practical guides for Etsy sellers on bulk editing, listing cleanup, tags, titles, product videos, pricing, and safer update workflows.",
    url: "https://bulkeditapp.com/blog",
    siteName: "Bulk Edit App",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Etsy Seller Guides — Bulk Edit App",
    description:
      "Practical guides for Etsy sellers on bulk editing, listing cleanup, tags, titles, product videos, pricing, and safer update workflows.",
  },
};

const BLOG_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "Blog",
  name: "Bulk Edit App Blog",
  url: "https://bulkeditapp.com/blog",
  description:
    "Practical guides for Etsy sellers on bulk editing, listing cleanup, tags, titles, product videos, pricing, and safer update workflows.",
  publisher: { "@type": "Organization", name: "Bulk Edit App" },
  blogPost: BLOG_POSTS.map((p) => ({
    "@type": "BlogPosting",
    headline: p.title,
    url: `https://bulkeditapp.com/blog/${p.slug}`,
    datePublished: p.publishedAt,
    dateModified: p.updatedAt ?? p.publishedAt,
    author: { "@type": "Organization", name: p.author },
  })),
};

export default function Page() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(BLOG_JSON_LD) }}
      />
      <BlogIndexContent />
    </>
  );
}
