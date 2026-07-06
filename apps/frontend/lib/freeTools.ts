// Registry for the public /tools hub. Each tool is a fully client-side
// calculator/checklist — no backend, no database, no account, no saved data.
// Every numeric input is user-editable and labeled as an estimate/assumption;
// nothing here claims to be official Etsy data.

export type FreeTool = {
  slug: string;
  title: string;
  description: string;
  metaTitle: string;
  metaDescription: string;
  targetKeywords: string[];
};

export const FREE_TOOLS: FreeTool[] = [
  {
    slug: "etsy-fee-calculator",
    title: "Etsy Fee Calculator",
    description: "Estimate Etsy marketplace fees and profit inputs before making pricing changes.",
    metaTitle: "Etsy Fee Calculator — Bulk Edit App",
    metaDescription:
      "Estimate Etsy seller fees, costs, and profit before making pricing updates across your listings.",
    targetKeywords: [
      "Etsy fee calculator",
      "Etsy profit calculator",
      "calculate Etsy profit",
      "Etsy seller fees",
      "Etsy pricing cleanup",
    ],
  },
  {
    slug: "etsy-tag-cleanup-checklist",
    title: "Etsy Tag Cleanup Checklist",
    description: "Review duplicate, vague, and inconsistent tags before applying bulk listing updates.",
    metaTitle: "Etsy Tag Cleanup Checklist — Bulk Edit App",
    metaDescription:
      "Review Etsy listing tags for duplicates, vague phrases, missing attributes, and bulk cleanup opportunities.",
    targetKeywords: [
      "Etsy tag cleanup checklist",
      "Etsy tag generator",
      "Etsy SEO tags",
      "Etsy tag optimization",
      "Etsy listing tags",
      "Etsy SEO tips",
    ],
  },
];

export function getFreeTool(slug: string): FreeTool | undefined {
  return FREE_TOOLS.find((t) => t.slug === slug);
}
