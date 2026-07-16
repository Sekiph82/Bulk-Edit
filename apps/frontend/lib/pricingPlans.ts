// Shared public pricing display data — single source of truth for the
// plan name/price/badge shown on both /pricing and the homepage pricing
// preview, so the two never drift out of sync. Feature *limits* (shops,
// listings, bulk edits, etc.) are fetched live from the backend billing API
// (`GET /api/v1/billing/plans`) — this file only holds the price/label
// strings, which mirror what's configured in Stripe
// (see apps/backend/app/core/config.py STRIPE_PRICE_*).

export interface PlanPriceDisplay {
  label: string;
  price: string;
  badge?: string;
}

export const PLAN_PRICE_DISPLAY: Record<string, PlanPriceDisplay> = {
  free: { label: "Free", price: "$0/month" },
  basic_monthly: { label: "Basic", price: "$19/month" },
  pro_monthly: { label: "Pro", price: "$49/month", badge: "Popular" },
  basic_yearly: { label: "Basic (Yearly)", price: "$15/month", badge: "Save 20%" },
  pro_yearly: { label: "Pro (Yearly)", price: "$39/month", badge: "Save 20%" },
};

export const PLAN_ORDER = ["free", "basic_monthly", "pro_monthly", "basic_yearly", "pro_yearly"];

export type HomepagePlanKey = "free" | "basic_monthly" | "pro_monthly";

// Short, honest feature highlights for the homepage's 3-card summary —
// numbers here match the real limits shown in full on /pricing
// (apps/backend/app/core/plans.py PLAN_LIMITS).
export const HOMEPAGE_PLAN_SUMMARIES: { key: HomepagePlanKey; highlights: string[] }[] = [
  {
    key: "free",
    highlights: ["1 shop, up to 25 listings", "10 bulk edits / month", "5 suggestion credits / month"],
  },
  {
    key: "basic_monthly",
    highlights: ["3 shops, up to 1,000 listings", "250 bulk edits / month", "Photo bulk edit, Magic Revert"],
  },
  {
    key: "pro_monthly",
    highlights: ["10 shops, up to 10,000 listings", "5,000 bulk edits / month", "Variation edit, Dynamic Pricing"],
  },
];
