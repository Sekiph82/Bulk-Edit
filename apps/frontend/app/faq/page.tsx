"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";

type FaqItem = { q: string; a: string };

const FAQ_DATA: Array<{ category: string; items: FaqItem[] }> = [
  {
    category: "General",
    items: [
      {
        q: "What is Bulk-Edit?",
        a: "Bulk-Edit is a SaaS tool for Etsy sellers that lets you update, optimize, and manage listings in bulk — safely. You can edit titles, tags, prices, descriptions, photos, and more across your entire shop, with a preview-first workflow that protects you from accidental changes.",
      },
      {
        q: "Who is Bulk-Edit for?",
        a: "Bulk-Edit is designed for Etsy sellers who manage more than a handful of listings and want to save time on repetitive updates. It's useful for small-shop owners and high-volume sellers alike.",
      },
      {
        q: "Is Bulk-Edit officially affiliated with Etsy?",
        a: "No. Bulk-Edit is an independent third-party tool that connects to Etsy through the official Etsy API. The term \"Etsy\" is a trademark of Etsy, Inc. This application uses the Etsy API but is not endorsed or certified by Etsy, Inc.",
      },
    ],
  },
  {
    category: "Etsy Connection",
    items: [
      {
        q: "How does the Etsy connection work?",
        a: "Bulk-Edit uses Etsy's OAuth2 PKCE flow — the same secure login standard used by major apps. You log into Etsy directly on Etsy's own website, grant limited permission, and Bulk-Edit receives a time-limited access token. We never see your Etsy password.",
      },
      {
        q: "Does Bulk-Edit store my Etsy credentials?",
        a: "No. We never receive or store your Etsy username or password. Only an OAuth access token (time-limited, revocable) is stored, and it is used only to perform actions you explicitly initiate.",
      },
      {
        q: "Can I disconnect my shop?",
        a: "Yes. You can revoke access at any time from within Bulk-Edit or directly from your Etsy account under Apps & Permissions. Disconnecting removes all access immediately.",
      },
    ],
  },
  {
    category: "Safety",
    items: [
      {
        q: "Will Bulk-Edit change my listings automatically?",
        a: "No — never. Every write to Etsy requires your explicit confirmation. The workflow is: Select → Build edits → Preview → Confirm → Apply. Nothing is written to Etsy without you clicking through the confirmation step.",
      },
      {
        q: "Can I preview changes before applying?",
        a: "Yes. Previewing is mandatory, not optional. Before any bulk edit is applied, Bulk-Edit generates a full diff of every affected listing — showing you exactly what will change, field by field. You review the preview and then decide whether to apply.",
      },
      {
        q: "Can I undo changes after applying?",
        a: "Yes. Bulk-Edit automatically creates a backup snapshot of every listing before writing to Etsy. If you want to undo, use the Magic Revert feature to restore any listing to its exact pre-edit state.",
      },
      {
        q: "Do scheduled jobs publish changes to Etsy automatically?",
        a: "No. Scheduled jobs are designed to be safe by construction. They can trigger syncs (pulling data from Etsy) and create draft bulk edit sessions — but they never apply changes to Etsy. Every Etsy write still requires your manual approval.",
      },
    ],
  },
  {
    category: "Billing",
    items: [
      {
        q: "Is there a free plan?",
        a: "Yes. Bulk-Edit offers a free plan with enough features to get started — including basic listing sync and a limited number of bulk edits per month. No credit card required to start.",
      },
      {
        q: "What features require a paid plan?",
        a: "Photo and video bulk editing, variation editing, Magic Revert, AI listing optimization, Dynamic Pricing, and Scheduled Jobs are available on paid plans. Check the pricing page for full plan details.",
      },
      {
        q: "Can I cancel my subscription?",
        a: "Yes, at any time. You can cancel from the billing page inside your Bulk-Edit account. Your subscription remains active until the end of the current billing period.",
      },
    ],
  },
  {
    category: "AI Tools",
    items: [
      {
        q: "Does AI publish changes to my listings automatically?",
        a: "No. AI suggestions are generated for your review. You see each suggestion — title rewrite, description improvement, new tags, alt text — and choose which ones to accept or reject. Only accepted suggestions are converted to a draft bulk edit, which still requires your confirmation before applying.",
      },
      {
        q: "Can I review AI suggestions before they go live?",
        a: "Yes. All AI suggestions go through the same preview-first workflow as manual edits. You accept suggestions individually, then convert to a bulk edit session, then preview, then confirm. Multiple checkpoints before anything touches Etsy.",
      },
    ],
  },
  {
    category: "CSV & Dynamic Pricing",
    items: [
      {
        q: "Can I import and export listings via CSV?",
        a: "Yes. You can export your listings to a CSV file, make changes in any spreadsheet tool, and import the file back into Bulk-Edit. The import creates a draft bulk edit session — which you still review and confirm before any Etsy writes occur.",
      },
      {
        q: "Does Dynamic Pricing automatically change my Etsy prices?",
        a: "No. Dynamic Pricing generates price recommendations based on rules you define. You review each recommendation and decide which ones to accept. Accepted recommendations are converted to a draft bulk edit session — which still goes through the standard preview and confirmation flow before any Etsy prices are changed.",
      },
    ],
  },
  {
    category: "Insights & Credits",
    items: [
      {
        q: "What does the Shop Insights page show?",
        a: "The Insights page shows date-range analytics for your shop — including views, favourites, and revenue trends. You choose the date range and the data updates immediately. Insights data comes from your connected Etsy shop.",
      },
      {
        q: "What are AI credits and bulk edit credits?",
        a: "AI credits are consumed each time Bulk-Edit calls an AI model to generate suggestions (titles, tags, descriptions). Bulk edit credits are consumed when you apply a bulk edit session to Etsy. Your plan includes a monthly allowance of each. You can see your current usage in the dashboard.",
      },
    ],
  },
  {
    category: "Promote & Video",
    items: [
      {
        q: "Does the Promote feature automatically post to Pinterest or Instagram?",
        a: "No — never. The Promote feature generates captions and prepares images from your listings. You can copy the caption, download the image, or explicitly confirm before anything is shared. Nothing is auto-posted to any social platform.",
      },
      {
        q: "Does the Video Generator automatically upload videos to Etsy?",
        a: "No. The Video Generator creates a short product showcase video from your listing photos. You preview and download the video first, then manually decide whether to add it to your Etsy listing. Videos are never auto-uploaded.",
      },
    ],
  },
  {
    category: "Bulk Create",
    items: [
      {
        q: "What is Bulk Create and how does it work?",
        a: "Bulk Create lets you upload a folder of product photos and quickly fill in listing details to create multiple Etsy listings at once. Each upload creates a draft for your review. No listing is published to Etsy without your explicit confirmation — the same preview-and-confirm workflow applies here.",
      },
      {
        q: "Can Bulk Create publish listings to Etsy automatically?",
        a: "No. Bulk Create creates draft listings for your review. You check each draft, make any edits, and then choose to publish when you are ready. Publishing always requires your explicit action — nothing goes live automatically.",
      },
    ],
  },
];

function FaqAccordion({ items }: { items: FaqItem[] }) {
  const [open, setOpen] = useState<number | null>(null);
  const reduced = useReducedMotion();

  return (
    <div className="divide-y divide-gray-100">
      {items.map((item, i) => (
        <div key={i} className="be-faq-item">
          <button
            className="be-faq-trigger"
            onClick={() => setOpen(open === i ? null : i)}
            aria-expanded={open === i}
          >
            <span>{item.q}</span>
            <motion.span
              animate={{ rotate: open === i ? 45 : 0 }}
              transition={reduced ? { duration: 0 } : { duration: 0.2, ease: "easeOut" }}
              className="w-5 h-5 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center flex-shrink-0 ml-4 text-lg leading-none"
              aria-hidden="true"
            >
              +
            </motion.span>
          </button>

          <AnimatePresence initial={false}>
            {open === i && (
              <motion.div
                key="content"
                initial={reduced ? false : { height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={reduced ? {} : { height: 0, opacity: 0 }}
                transition={{ duration: 0.25, ease: "easeInOut" }}
                style={{ overflow: "hidden" }}
              >
                <p className="pb-4 text-sm text-gray-600 leading-relaxed pr-12">{item.a}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  );
}

export default function FaqPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <MarketingNav />

      {/* Hero */}
      <section className="be-hero-bg pt-16 pb-16 px-6 sm:px-8 text-center">
        <div className="max-w-2xl mx-auto">
          <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
            Help Center
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight mb-4">
            Frequently asked questions
          </h1>
          <p className="text-lg text-gray-500">
            Everything you need to know about Bulk-Edit. Can&apos;t find your answer?{" "}
            <Link href="/contact-us" className="text-indigo-600 hover:underline font-medium">
              Contact us.
            </Link>
          </p>
        </div>
      </section>

      {/* FAQ content */}
      <section className="py-16 px-6 sm:px-8">
        <div className="max-w-3xl mx-auto space-y-10">
          {FAQ_DATA.map((section) => (
            <div key={section.category}>
              <h2 className="text-lg font-bold text-gray-900 mb-4 pb-3 border-b border-gray-100">
                {section.category}
              </h2>
              <FaqAccordion items={section.items} />
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-6 sm:px-8 bg-white border-t border-gray-100">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-3">Still have questions?</h2>
          <p className="text-gray-500 mb-6">
            Our team is happy to help. Reach out and we&apos;ll get back to you.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/contact-us" className="be-btn-primary px-7 py-3">
              Contact us
            </Link>
            <Link href="/register" className="be-btn-secondary px-7 py-3">
              Start for free
            </Link>
          </div>
        </div>
      </section>

      <MarketingFooter />
    </div>
  );
}
