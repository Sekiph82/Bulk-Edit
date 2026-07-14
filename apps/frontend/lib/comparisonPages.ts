// Content for dedicated /compare/[slug] pages. Cautious, non-attack
// comparison copy only — no "better than X", no unverified claims about a
// competitor's features or pricing, no Etsy/Vela/Evlista endorsement or
// affiliation claims. "Other tool considerations" deliberately never states
// a competitor lacks something; it asks the reader to verify with the
// provider instead.

export type ComparisonRow = {
  need: string;
  bulkEditApproach: string;
  otherConsiderations: string;
};

export type ComparisonFaqItem = { q: string; a: string };

export type ComparisonPage = {
  slug: string;
  competitorName: string;
  metaTitle: string;
  metaDescription: string;
  h1: string;
  targetKeywords: string[];
  introHeading: string;
  introParagraphs: string[];
  whenToLookHeading: string;
  whenToLookParagraphs: string[];
  whereBulkEditFocusesHeading: string;
  whereBulkEditFocusesParagraphs: string[];
  featureSections: { heading: string; paragraphs: string[] }[];
  table: ComparisonRow[];
  questionsToAsk: string[];
  faq: ComparisonFaqItem[];
  disclaimer: string;
};

export const COMPARISON_PAGES: ComparisonPage[] = [
  {
    slug: "bulk-edit-app-vs-vela",
    competitorName: "Vela",
    metaTitle: "Bulk Edit App vs Vela — Etsy Bulk Editing Workflow Comparison",
    metaDescription:
      "Compare Bulk Edit App and Vela from an Etsy seller workflow perspective, including bulk editing, previews, listing cleanup, and safer updates.",
    h1: "Bulk Edit App vs Vela",
    targetKeywords: [
      "Bulk Edit App vs Vela",
      "Vela alternative",
      "Etsy bulk edit tool",
      "Etsy bulk editing",
      "Etsy seller tools",
    ],
    introHeading: "Choosing the right Etsy workflow tool",
    introParagraphs: [
      "Etsy sellers evaluating tools are usually solving for one of a few things: research, listing editing, or applying bulk changes safely. This page compares workflow fit, not every feature — feature availability varies by tool and plan, and changes over time, so always verify current Vela features and pricing on Vela's website.",
    ],
    whenToLookHeading: "When a seller may look at Vela",
    whenToLookParagraphs: [
      "Vela is generally known among Etsy sellers as a listing editing tool. Sellers whose main need is editing and managing listing content directly often come across it during research.",
    ],
    whereBulkEditFocusesHeading: "Where Bulk Edit App focuses",
    whereBulkEditFocusesParagraphs: [
      "Bulk Edit App is built around a preview-first bulk editing workflow: select listings, define a change once, review a full before/after diff, apply, and revert individual listings from an automatic backup snapshot if needed.",
    ],
    featureSections: [
      {
        heading: "Preview-first bulk editing",
        paragraphs: [
          "Every bulk edit in Bulk Edit App — whether it changes titles, tags, prices, or descriptions — generates a full before/after diff for every affected listing before anything is written to Etsy.",
        ],
      },
      {
        heading: "Reversible workflows and backup snapshots",
        paragraphs: [
          "Every apply automatically creates a backup snapshot of each affected listing beforehand. If a change doesn't work out, Magic Revert restores that listing to its exact pre-edit state with one click.",
        ],
      },
      {
        heading: "Media workflow: Add Video, Replace Video, Delete Video",
        paragraphs: [
          "Bulk Edit App's media tools support adding a new listing video, replacing an existing one, or deleting a video — each previewed before the change is applied, with a backup snapshot taken first.",
        ],
      },
      {
        heading: "Pricing transparency: Free, Basic $19, Pro $49",
        paragraphs: [
          "Bulk Edit App publishes its pricing directly: Free at $0/month, Basic at $19/month, and Pro at $49/month. See the pricing page for current plan details.",
        ],
      },
    ],
    table: [
      { need: "Bulk listing updates", bulkEditApproach: "Core focus — preview-first bulk updates across titles, tags, prices, and more", otherConsiderations: "Check whether your plan supports this workflow and how it's applied." },
      { need: "Preview before apply", bulkEditApproach: "Full before/after diff on every bulk edit, before anything is sent to Etsy", otherConsiderations: "Verify preview and rollback workflow before making bulk changes." },
      { need: "Revert / backup snapshots", bulkEditApproach: "Automatic snapshot before every apply; one-click Magic Revert", otherConsiderations: "Feature availability varies by tool and plan." },
      { need: "Listing cleanup", bulkEditApproach: "Bulk edit titles, tags, and descriptions across your catalog, reviewed before applying", otherConsiderations: "Feature availability varies by tool and plan." },
      { need: "Media/video updates", bulkEditApproach: "Add Video, Replace Video, and Delete Video, previewed before applying", otherConsiderations: "Verify current media workflow support." },
      { need: "Pricing clarity", bulkEditApproach: "Free $0, Basic $19/mo, Pro $49/mo — published on our pricing page", otherConsiderations: "Verify current pricing on the provider's website." },
      { need: "Safety-first workflow", bulkEditApproach: "No blind writes — preview, confirmation, and a snapshot on every Etsy write", otherConsiderations: "Check whether your plan supports this workflow and how previews/rollback are handled." },
    ],
    questionsToAsk: [
      "Does this tool solve my actual bottleneck — research, editing, or applying changes safely?",
      "Can I preview a change before it's sent to Etsy, or does it write immediately?",
      "Is there a way to undo a change if something goes wrong?",
      "What does the free plan actually include, and what requires a paid plan?",
      "Does the current feature list on the provider's own site match what I need today?",
    ],
    faq: [
      { q: "Is Bulk Edit App affiliated with Vela?", a: "No. Bulk Edit App is an independent tool and is not affiliated with or endorsed by Vela. Vela is a trademark of its respective owner." },
      { q: "Is this page saying Bulk Edit App is better than Vela?", a: "No. This page compares workflow fit, not every feature, so sellers can decide what matches their own shop. Feature availability varies by tool and plan and changes over time." },
      { q: "What should Etsy sellers compare before choosing a tool?", a: "Whether the tool solves your actual bottleneck, whether it previews changes before writing to Etsy, whether changes can be undone, and what's actually included in the free plan versus a paid one." },
      { q: "Does Bulk Edit App support preview and revert workflows?", a: "Yes. Every bulk edit shows a full before/after diff before applying, and every apply creates an automatic backup snapshot that Magic Revert can restore from." },
      { q: "Can I start free?", a: "Yes. Bulk Edit App has a Free plan at $0/month, alongside Basic at $19/month and Pro at $49/month." },
    ],
    disclaimer:
      "Vela is a trademark of its respective owner. Bulk Edit App is not affiliated with or endorsed by Vela. Feature availability varies by tool and plan and changes over time — always verify current Vela features and pricing on Vela's website.",
  },
  {
    slug: "bulk-edit-app-vs-evlista",
    competitorName: "Evlista",
    metaTitle: "Bulk Edit App vs Evlista — Etsy Listing Workflow Comparison",
    metaDescription:
      "Compare Bulk Edit App and Evlista from an Etsy seller workflow perspective, including listing cleanup, bulk updates, previews, and safer edits.",
    h1: "Bulk Edit App vs Evlista",
    targetKeywords: [
      "Bulk Edit App vs Evlista",
      "Evlista alternative",
      "Etsy listing tool",
      "Etsy bulk edit tool",
      "Etsy seller tools",
    ],
    introHeading: "Comparing Etsy listing workflows",
    introParagraphs: [
      "Etsy sellers researching listing tools are usually comparing how each one handles editing, cleanup, and applying changes across a shop. This page compares workflow fit, not every feature — feature availability varies by tool and plan, and changes over time, so always verify current Evlista features and pricing on Evlista's website.",
    ],
    whenToLookHeading: "When a seller may look at Evlista",
    whenToLookParagraphs: [
      "Sellers researching Etsy listing management tools often come across Evlista during that search. As with any third-party tool, exact feature and plan details should be verified directly on Evlista's own site.",
    ],
    whereBulkEditFocusesHeading: "Where Bulk Edit App focuses",
    whereBulkEditFocusesParagraphs: [
      "Bulk Edit App is built around safe, reversible bulk updates: select listings, define a change, preview the full result, apply it, and revert individual listings from an automatic backup snapshot if something doesn't work out.",
    ],
    featureSections: [
      {
        heading: "Bulk updates with preview",
        paragraphs: [
          "Titles, tags, prices, and descriptions can all be updated in bulk, with a full before/after diff shown for every affected listing before anything reaches Etsy.",
        ],
      },
      {
        heading: "Magic Revert / backup snapshots",
        paragraphs: [
          "Every bulk apply automatically snapshots each affected listing beforehand. Magic Revert restores any listing to that exact pre-edit state with one click.",
        ],
      },
      {
        heading: "Media and video operations",
        paragraphs: [
          "Bulk Edit App supports adding, replacing, or deleting listing video, each previewed before the change is applied and backed by the same snapshot safety net as other bulk edits.",
        ],
      },
      {
        heading: "Pricing transparency: Free, Basic $19, Pro $49",
        paragraphs: [
          "Pricing is published directly on our pricing page: Free at $0/month, Basic at $19/month, Pro at $49/month.",
        ],
      },
    ],
    table: [
      { need: "Listing cleanup", bulkEditApproach: "Bulk edit titles, tags, and descriptions across your catalog, reviewed before applying", otherConsiderations: "Feature availability varies by tool and plan." },
      { need: "Bulk edits", bulkEditApproach: "Core focus — preview-first bulk updates across titles, tags, prices, and more", otherConsiderations: "Check whether your plan supports this workflow and how it's applied." },
      { need: "Preview before apply", bulkEditApproach: "Full before/after diff on every bulk edit, before anything is sent to Etsy", otherConsiderations: "Verify preview and rollback workflow before making bulk changes." },
      { need: "Revert / backup snapshots", bulkEditApproach: "Automatic snapshot before every apply; one-click Magic Revert", otherConsiderations: "Feature availability varies by tool and plan." },
      { need: "Media/video operations", bulkEditApproach: "Add Video, Replace Video, and Delete Video, previewed before applying", otherConsiderations: "Verify current media workflow support." },
      { need: "Pricing clarity", bulkEditApproach: "Free $0, Basic $19/mo, Pro $49/mo — published on our pricing page", otherConsiderations: "Verify current pricing on the provider's website." },
      { need: "Safety-first workflow", bulkEditApproach: "No blind writes — preview, confirmation, and a snapshot on every Etsy write", otherConsiderations: "Check whether your plan supports this workflow and how previews/rollback are handled." },
    ],
    questionsToAsk: [
      "Does this tool solve my actual bottleneck — research, editing, or applying changes safely?",
      "Can I preview a change before it's sent to Etsy, or does it write immediately?",
      "Is there a way to undo a change if something goes wrong?",
      "What does the free plan actually include, and what requires a paid plan?",
      "Does the current feature list on the provider's own site match what I need today?",
    ],
    faq: [
      { q: "Is Bulk Edit App affiliated with Evlista?", a: "No. Bulk Edit App is an independent tool and is not affiliated with or endorsed by Evlista. Evlista is a trademark of its respective owner." },
      { q: "Is this page saying Bulk Edit App is better than Evlista?", a: "No. This page compares workflow fit, not every feature, so sellers can decide what matches their own shop. Feature availability varies by tool and plan and changes over time." },
      { q: "What should Etsy sellers compare before choosing?", a: "Whether the tool solves your actual bottleneck, whether it previews changes before writing to Etsy, whether changes can be undone, and what's actually included in the free plan versus a paid one." },
      { q: "Does Bulk Edit App support reversible edits?", a: "Yes. Every bulk apply creates an automatic backup snapshot, and Magic Revert can restore any listing to its exact pre-edit state." },
      { q: "Can I start free?", a: "Yes. Bulk Edit App has a Free plan at $0/month, alongside Basic at $19/month and Pro at $49/month." },
    ],
    disclaimer:
      "Evlista is a trademark of its respective owner. Bulk Edit App is not affiliated with or endorsed by Evlista. Feature availability varies by tool and plan and changes over time — always verify current Evlista features and pricing on Evlista's website.",
  },
];

export function getComparisonPage(slug: string): ComparisonPage | undefined {
  return COMPARISON_PAGES.find((c) => c.slug === slug);
}
