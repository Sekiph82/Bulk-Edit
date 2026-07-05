"use client";

import Link from "next/link";
import { Anton } from "next/font/google";
import { useEffect, useMemo, useState } from "react";

// Anton isn't loaded anywhere else in the project — scoped here for the
// ghost/display text only. Body copy intentionally stays on the site's
// existing system-font stack rather than adding a second webfont.
const anton = Anton({ subsets: ["latin"], weight: "400", display: "swap" });

// ── Inline SVG icons ─────────────────────────────────────────────────────────
// The project has no icon library dependency anywhere else (AppShell,
// MarketingNav, etc. all use inline SVG) — matching that instead of adding
// lucide-react just for this one component.
type IconProps = { className?: string };
const ArrowLeftIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.25} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M19 12H5M12 19l-7-7 7-7" /></svg>
);
const ArrowRightIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.25} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
);
const ListChecksIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3 6l2 2 4-4M3 14l2 2 4-4M11 6h10M11 14h10M11 18h10M3 18l2 2 4-4" /></svg>
);
const TagsIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M20.59 13.41L11 3.83A2 2 0 009.58 3H4a1 1 0 00-1 1v5.59a2 2 0 00.59 1.41l9.59 9.59a2 2 0 002.82 0l4.59-4.59a2 2 0 000-2.82z" /><circle cx="7.5" cy="7.5" r="1.5" /></svg>
);
const WandIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M15 4V2M15 16v-2M8 9h2M20 9h2M17.8 11.8L19 13M15 9h0M17.8 6.2L19 5M3 21l9-9M12.2 6.2L11 5" /></svg>
);
const FileSpreadsheetIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><path d="M14 2v6h6M8 13h8M8 17h8M8 13v4" /></svg>
);
const SparklesIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5z" /><path d="M19 15l.75 2.25L22 18l-2.25.75L19 21l-.75-2.25L16 18l2.25-.75z" /></svg>
);
const ShieldCheckIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6z" /><path d="M9 12l2 2 4-4" /></svg>
);
const BarChartIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3 3v18h18M8 17V10M13 17V6M18 17v-4" /></svg>
);
const ImagePlusIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="9" cy="9" r="2" /><path d="M21 15l-5-5L5 21" /><path d="M16 5h4M18 3v4" /></svg>
);
const VideoIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M23 7l-7 5 7 5V7z" /><rect x="1" y="5" width="15" height="14" rx="2" /></svg>
);
const UndoIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3 7v6h6" /><path d="M3 13a9 9 0 1 0 3-7.7L3 7" /></svg>
);
const DollarIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" /></svg>
);
const CalendarClockIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="17" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /><circle cx="16" cy="16" r="3" /><path d="M16 15v1.5l1 .5" /></svg>
);

type HeroItem = {
  key: string;
  ghost: string;
  label: string;
  headline: string;
  subtitle: string;
  bg: string;
  panel: string;
  icon: React.ComponentType<IconProps>;
  features: { title: string; href: string; icon: React.ComponentType<IconProps> }[];
  visual: "bulk" | "ai" | "media" | "safety";
};

const HERO_ITEMS: HeroItem[] = [
  {
    key: "bulk-listing-control",
    ghost: "BULK EDIT",
    label: "Bulk Listing Control",
    headline: "Bulk edit Etsy listings faster, safer, and smarter.",
    subtitle: "Edit titles, tags, descriptions, prices and variations across many Etsy listings with preview-first control.",
    bg: "#4F46E5",
    panel: "#6366F1",
    icon: ListChecksIcon,
    visual: "bulk",
    features: [
      { title: "Bulk Listing Editor", href: "/features/bulk-listing-editor", icon: ListChecksIcon },
      { title: "Bulk Tag Editor", href: "/features/bulk-tag-editor", icon: TagsIcon },
      { title: "Variation Editor", href: "/features/variation-editor", icon: WandIcon },
      { title: "CSV Import/Export", href: "/features/etsy-csv-import-export", icon: FileSpreadsheetIcon },
    ],
  },
  {
    key: "ai-seo-quality",
    ghost: "AI SEO",
    label: "AI SEO & Listing Quality",
    headline: "Turn messy listings into cleaner Etsy SEO.",
    subtitle: "Use AI suggestions for titles, tags and descriptions while keeping every change under your control.",
    bg: "#059669",
    panel: "#10B981",
    icon: SparklesIcon,
    visual: "ai",
    features: [
      { title: "AI Listing Optimization", href: "/features/ai-listing-optimization", icon: SparklesIcon },
      { title: "Listing Health Score", href: "/features/listing-health-score", icon: ShieldCheckIcon },
      { title: "Shop Insights", href: "/features/shop-insights", icon: BarChartIcon },
    ],
  },
  {
    key: "media-promotion",
    ghost: "MEDIA",
    label: "Media & Promotion",
    headline: "Clean up listing media without opening every product.",
    subtitle: "Bulk add, replace or delete listing photos, then generate MP4 product videos from listing images.",
    bg: "#EA580C",
    panel: "#F97316",
    icon: ImagePlusIcon,
    visual: "media",
    features: [
      { title: "Photo Bulk Editing", href: "/features/photo-bulk-editing", icon: ImagePlusIcon },
      { title: "Product Video Generator", href: "/features/product-video-generator", icon: VideoIcon },
      { title: "Social Promote", href: "/features/social-promote", icon: WandIcon },
    ],
  },
  {
    key: "safety-pricing-automation",
    ghost: "REVERT",
    label: "Safety, Pricing & Automation",
    headline: "Preview first. Apply with confidence. Revert when needed.",
    subtitle: "Review bulk changes before applying them, protect your pricing, and roll back using change history.",
    bg: "#0284C7",
    panel: "#0EA5E9",
    icon: UndoIcon,
    visual: "safety",
    features: [
      { title: "Safe Preview Engine", href: "/features/safe-preview-engine", icon: ShieldCheckIcon },
      { title: "Magic Revert", href: "/features/magic-revert", icon: UndoIcon },
      { title: "Backup Snapshots", href: "/features/backup-snapshots", icon: FileSpreadsheetIcon },
      { title: "Profit Calculator", href: "/features/profit-calculator", icon: DollarIcon },
      { title: "Dynamic Pricing", href: "/features/dynamic-pricing", icon: BarChartIcon },
      { title: "Scheduled Jobs", href: "/features/scheduled-jobs", icon: CalendarClockIcon },
    ],
  },
];

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const sync = () => setIsMobile(window.innerWidth < 640);
    sync();
    window.addEventListener("resize", sync);
    return () => window.removeEventListener("resize", sync);
  }, []);
  return isMobile;
}

function useReducedMotionPref() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const listener = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener("change", listener);
    return () => mq.removeEventListener("change", listener);
  }, []);
  return reduced;
}

function MiniListingRows() {
  return (
    <div className="space-y-2">
      {["Ceramic mug", "Boho wall art", "Personalized necklace"].map((name, index) => (
        <div key={name} className="grid grid-cols-[1fr_auto] gap-3 rounded-2xl bg-white/12 p-3 ring-1 ring-white/15">
          <div>
            <div className="mb-2 h-3 w-28 rounded-full bg-white/75" />
            <div className="flex gap-1.5">
              <span className="h-5 w-14 rounded-full bg-white/20" />
              <span className="h-5 w-10 rounded-full bg-white/20" />
              <span className="h-5 w-12 rounded-full bg-white/20" />
            </div>
          </div>
          <div className="text-right text-sm font-bold text-white/90">${index === 0 ? "24" : index === 1 ? "38" : "42"}</div>
        </div>
      ))}
    </div>
  );
}

function BulkVisual({ panel }: { panel: string }) {
  return (
    <div className="relative h-full w-full overflow-hidden rounded-[2rem] bg-white/12 p-5 shadow-2xl ring-1 ring-white/25 backdrop-blur-xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-white/70">Bulk session</div>
          <div className="text-2xl font-bold text-white">128 listings selected</div>
        </div>
        <div className="rounded-full bg-white px-4 py-2 text-xs font-bold" style={{ color: panel }}>Preview ready</div>
      </div>
      <MiniListingRows />
      <div className="absolute bottom-5 right-5 w-[58%] rounded-3xl bg-white p-4 text-slate-900 shadow-2xl">
        <div className="mb-3 flex items-center gap-2 text-sm font-bold">
          <ListChecksIcon className="h-4 w-4" />
          Bulk edit drawer
        </div>
        <div className="space-y-2">
          <div className="h-3 w-full rounded-full bg-slate-200" />
          <div className="h-3 w-3/4 rounded-full bg-slate-200" />
          <div className="flex gap-2 pt-2">
            <span className="rounded-full bg-indigo-100 px-3 py-1 text-[11px] font-semibold text-indigo-700">tags</span>
            <span className="rounded-full bg-indigo-100 px-3 py-1 text-[11px] font-semibold text-indigo-700">prices</span>
            <span className="rounded-full bg-indigo-100 px-3 py-1 text-[11px] font-semibold text-indigo-700">CSV</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function AiVisual() {
  return (
    <div className="relative h-full w-full overflow-hidden rounded-[2rem] bg-white/12 p-5 shadow-2xl ring-1 ring-white/25 backdrop-blur-xl">
      <div className="rounded-3xl bg-white p-5 text-slate-900 shadow-xl">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-bold">
            <SparklesIcon className="h-4 w-4 text-emerald-600" />
            AI suggestions
          </div>
          <div className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">Score 86</div>
        </div>
        <div className="mb-4 h-3 w-full rounded-full bg-slate-200">
          <div className="h-3 w-[86%] rounded-full bg-emerald-500" />
        </div>
        <div className="space-y-3">
          {["Rewrite title for buyer intent", "Add missing occasion tags", "Improve description opening"].map((text) => (
            <div key={text} className="rounded-2xl border border-slate-200 p-3">
              <div className="mb-2 h-2.5 w-2/3 rounded-full bg-slate-200" />
              <p className="text-xs font-medium text-slate-600">{text}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="absolute -bottom-3 -right-3 rounded-3xl bg-emerald-950/35 p-4 text-white ring-1 ring-white/20">
        <div className="mb-2 text-xs font-bold uppercase tracking-widest text-white/70">Tag cleanup</div>
        <div className="flex flex-wrap gap-2">
          {["gift", "handmade", "minimalist", "wedding"].map((tag) => (
            <span key={tag} className="rounded-full bg-white/15 px-3 py-1 text-xs font-semibold">{tag}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function MediaVisual() {
  return (
    <div className="relative h-full w-full overflow-hidden rounded-[2rem] bg-white/12 p-5 shadow-2xl ring-1 ring-white/25 backdrop-blur-xl">
      <div className="grid grid-cols-3 gap-3">
        {Array.from({ length: 9 }).map((_, index) => (
          <div
            key={index}
            className="aspect-square rounded-2xl bg-white/20 ring-1 ring-white/20"
            style={{
              background: index % 3 === 0
                ? "linear-gradient(135deg, rgba(255,255,255,.9), rgba(255,255,255,.25))"
                : "linear-gradient(135deg, rgba(255,255,255,.35), rgba(255,255,255,.12))",
            }}
          />
        ))}
      </div>
      <div className="absolute bottom-5 left-5 right-5 rounded-3xl bg-white p-4 text-slate-900 shadow-2xl">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-sm font-bold">Product video ready</div>
            <div className="text-xs text-slate-500">MP4 preview and download</div>
          </div>
          <div className="rounded-full bg-orange-100 px-3 py-1 text-xs font-bold text-orange-700">MP4</div>
        </div>
      </div>
    </div>
  );
}

function SafetyVisual() {
  return (
    <div className="relative h-full w-full overflow-hidden rounded-[2rem] bg-white/12 p-5 shadow-2xl ring-1 ring-white/25 backdrop-blur-xl">
      <div className="rounded-3xl bg-white p-5 text-slate-900 shadow-xl">
        <div className="mb-4 flex items-center gap-2 text-sm font-bold">
          <ShieldCheckIcon className="h-4 w-4 text-sky-600" />
          Safe preview
        </div>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="rounded-2xl bg-red-50 p-3 text-red-800">
            <div className="mb-2 font-bold">Before</div>
            <div className="h-2 w-24 rounded-full bg-red-200" />
          </div>
          <div className="rounded-2xl bg-green-50 p-3 text-green-800">
            <div className="mb-2 font-bold">After</div>
            <div className="h-2 w-28 rounded-full bg-green-200" />
          </div>
        </div>
        <div className="mt-4 rounded-2xl border border-slate-200 p-3">
          <div className="mb-2 flex items-center justify-between text-xs font-semibold">
            <span>Snapshot created</span>
            <span>Magic Revert ready</span>
          </div>
          <div className="h-2 rounded-full bg-slate-200">
            <div className="h-2 w-full rounded-full bg-sky-500" />
          </div>
        </div>
      </div>
      <div className="absolute bottom-5 right-5 rounded-full bg-white px-4 py-2 text-sm font-bold text-sky-700 shadow-xl">No blind writes</div>
    </div>
  );
}

function HeroVisual({ item }: { item: HeroItem }) {
  if (item.visual === "bulk") return <BulkVisual panel={item.panel} />;
  if (item.visual === "ai") return <AiVisual />;
  if (item.visual === "media") return <MediaVisual />;
  return <SafetyVisual />;
}

function SmallVisualCard({ item }: { item: HeroItem }) {
  const Icon = item.icon;
  return (
    <div className="flex h-full w-full flex-col justify-between rounded-[1.5rem] bg-white/16 p-4 text-white shadow-xl ring-1 ring-white/20 backdrop-blur-lg">
      <div className="flex items-center justify-between">
        <Icon className="h-6 w-6" />
        <span className="rounded-full bg-white/15 px-2 py-1 text-[10px] font-bold uppercase tracking-widest">
          {item.label.split(" ")[0]}
        </span>
      </div>
      <div>
        <div className="mb-2 h-2.5 w-20 rounded-full bg-white/45" />
        <div className="h-2 w-28 rounded-full bg-white/25" />
      </div>
    </div>
  );
}

function GrainOverlay() {
  const svg =
    "data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.08'/%3E%3C/svg%3E";
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 z-50 opacity-40"
      style={{ backgroundImage: `url("${svg}")`, backgroundSize: "200px 200px", backgroundRepeat: "repeat" }}
    />
  );
}

export default function BulkEditHero() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const isMobile = useIsMobile();
  const reducedMotion = useReducedMotionPref();

  const item = HERO_ITEMS[activeIndex];
  const ActiveIcon = item.icon;

  const roles = useMemo(
    () => ({
      center: activeIndex,
      left: (activeIndex + 3) % HERO_ITEMS.length,
      right: (activeIndex + 1) % HERO_ITEMS.length,
      back: (activeIndex + 2) % HERO_ITEMS.length,
    }),
    [activeIndex],
  );

  function navigate(direction: "next" | "prev") {
    if (isAnimating) return;
    setIsAnimating(true);
    setActiveIndex((current) =>
      direction === "next"
        ? (current + 1) % HERO_ITEMS.length
        : (current + HERO_ITEMS.length - 1) % HERO_ITEMS.length,
    );
    window.setTimeout(() => setIsAnimating(false), reducedMotion ? 0 : 650);
  }

  function getRole(index: number) {
    if (index === roles.center) return "center";
    if (index === roles.left) return "left";
    if (index === roles.right) return "right";
    return "back";
  }

  function roleStyle(index: number): React.CSSProperties {
    const role = getRole(index);
    const duration = reducedMotion ? "0ms" : "650ms";

    const base: React.CSSProperties = {
      position: "absolute",
      aspectRatio: "1.05 / 1",
      transition: `transform ${duration} cubic-bezier(0.4,0,0.2,1), filter ${duration} cubic-bezier(0.4,0,0.2,1), opacity ${duration} cubic-bezier(0.4,0,0.2,1), left ${duration} cubic-bezier(0.4,0,0.2,1), bottom ${duration} cubic-bezier(0.4,0,0.2,1), height ${duration} cubic-bezier(0.4,0,0.2,1)`,
      willChange: "transform, filter, opacity",
    };

    if (role === "center") {
      return {
        ...base,
        left: "50%",
        bottom: isMobile ? "30%" : "10%",
        height: isMobile ? "38%" : "56%",
        transform: `translateX(-50%) scale(${isMobile ? 1.1 : 1.28})`,
        filter: "blur(0px)",
        opacity: 1,
        zIndex: 20,
      };
    }
    if (role === "left") {
      return {
        ...base,
        left: isMobile ? "18%" : "24%",
        bottom: isMobile ? "38%" : "18%",
        height: isMobile ? "16%" : "26%",
        transform: "translateX(-50%) scale(1)",
        filter: "blur(2px)",
        opacity: 0.82,
        zIndex: 10,
      };
    }
    if (role === "right") {
      return {
        ...base,
        left: isMobile ? "82%" : "76%",
        bottom: isMobile ? "38%" : "18%",
        height: isMobile ? "16%" : "26%",
        transform: "translateX(-50%) scale(1)",
        filter: "blur(2px)",
        opacity: 0.82,
        zIndex: 10,
      };
    }
    return {
      ...base,
      left: "50%",
      bottom: isMobile ? "40%" : "21%",
      height: isMobile ? "13%" : "21%",
      transform: "translateX(-50%) scale(1)",
      filter: "blur(4px)",
      opacity: 0.55,
      zIndex: 5,
    };
  }

  return (
    <section
      className="relative w-full overflow-hidden text-white"
      style={{ backgroundColor: item.bg, transition: reducedMotion ? "none" : "background-color 650ms cubic-bezier(0.4,0,0.2,1)" }}
    >
      <div className="relative h-screen min-h-[720px] w-full overflow-hidden">
        <GrainOverlay />

        <div className="absolute left-4 top-6 z-[60] sm:left-8">
          <Link href="/" className="text-xs font-semibold uppercase tracking-[0.18em] text-white/90 no-underline" aria-label="Bulk Edit App home">
            Bulk Edit App
          </Link>
        </div>

        <div
          aria-hidden="true"
          className={`pointer-events-none absolute inset-x-0 top-[16%] z-[2] flex select-none items-center justify-center whitespace-nowrap uppercase leading-none text-white ${anton.className}`}
          style={{ fontSize: "clamp(72px, 20vw, 300px)", letterSpacing: "-0.02em", opacity: 0.92 }}
        >
          {item.ghost}
        </div>

        <div className="absolute inset-0 z-[3]" aria-hidden="true">
          {HERO_ITEMS.map((heroItem, index) => (
            <div key={heroItem.key} style={roleStyle(index)}>
              {getRole(index) === "center" ? <HeroVisual item={heroItem} /> : <SmallVisualCard item={heroItem} />}
            </div>
          ))}
        </div>

        <div className="absolute left-4 top-24 z-[60] max-w-[92vw] sm:left-24 sm:top-28 sm:max-w-xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/14 px-4 py-2 text-xs font-bold uppercase tracking-[0.18em] ring-1 ring-white/20 backdrop-blur-md">
            <ActiveIcon className="h-4 w-4" />
            {item.label}
          </div>

          <h1 className="max-w-2xl text-4xl font-black leading-[0.96] tracking-tight sm:text-6xl lg:text-7xl">
            {item.headline}
          </h1>

          <p className="mt-5 max-w-xl text-sm font-medium leading-7 text-white/86 sm:text-base">{item.subtitle}</p>

          <div className="mt-6 flex flex-wrap gap-2">
            {item.features.map((feature) => {
              const FeatureIcon = feature.icon;
              return (
                <Link
                  key={feature.href}
                  href={feature.href}
                  className="inline-flex items-center gap-2 rounded-full bg-white/14 px-3 py-2 text-xs font-bold text-white no-underline ring-1 ring-white/18 transition hover:bg-white/22"
                >
                  <FeatureIcon className="h-3.5 w-3.5" />
                  {feature.title}
                </Link>
              );
            })}
          </div>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/register" className="inline-flex items-center justify-center rounded-full bg-white px-6 py-3 text-sm font-black text-slate-950 no-underline shadow-xl transition hover:scale-[1.02]">
              Try Bulk Edit App
            </Link>
            <Link href="/features" className="inline-flex items-center justify-center rounded-full border border-white/35 bg-white/10 px-6 py-3 text-sm font-bold text-white no-underline backdrop-blur-md transition hover:bg-white/18">
              Explore features
            </Link>
          </div>
        </div>

        <div className="absolute bottom-6 left-4 z-[60] max-w-[320px] sm:bottom-20 sm:left-24">
          <p className="mb-2 text-base font-bold uppercase tracking-[0.02em] text-white/95 sm:mb-3 sm:text-[22px]">Etsy bulk editing</p>
          <p className="mb-4 hidden text-sm leading-[1.6] text-white/85 sm:mb-5 sm:block">
            Edit titles, tags, prices, photos and variations across your Etsy listings. Preview every change before applying it, then roll back safely with Magic Revert.
          </p>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => navigate("prev")}
              className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-white bg-transparent text-white transition hover:scale-[1.08] hover:bg-white/12 sm:h-16 sm:w-16"
              aria-label="Show previous Bulk Edit App hero"
            >
              <ArrowLeftIcon className="h-[26px] w-[26px]" />
            </button>
            <button
              type="button"
              onClick={() => navigate("next")}
              className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-white bg-transparent text-white transition hover:scale-[1.08] hover:bg-white/12 sm:h-16 sm:w-16"
              aria-label="Show next Bulk Edit App hero"
            >
              <ArrowRightIcon className="h-[26px] w-[26px]" />
            </button>
          </div>
        </div>

        <Link
          href="/register"
          className={`absolute bottom-6 right-4 z-[60] flex items-center gap-3 text-white no-underline opacity-95 transition-opacity hover:opacity-100 sm:bottom-20 sm:right-10 ${anton.className}`}
          style={{ fontSize: "clamp(20px, 4vw, 56px)", letterSpacing: "-0.02em", lineHeight: 1, textTransform: "uppercase" }}
        >
          Start editing
          <ArrowRightIcon className="h-5 w-5 sm:h-8 sm:w-8" />
        </Link>
      </div>
    </section>
  );
}
