"use client";

import { useMemo, useState } from "react";

// Fully client-side. No backend call, no Etsy search-volume data, nothing
// saved anywhere (no localStorage, no account). This is a tag-idea helper,
// not an official Etsy tag generator or ranking tool — see disclaimers
// rendered alongside this component and on the page.

const VAGUE_WORDS = new Set([
  "cute", "nice", "best", "new", "gift", "cool", "great", "unique", "custom", "handmade", "love",
]);

const ATTRIBUTE_FIELDS: { key: keyof Attributes; label: string; placeholder: string }[] = [
  { key: "productType", label: "Product type", placeholder: "e.g. tote bag" },
  { key: "material", label: "Material", placeholder: "e.g. cotton" },
  { key: "style", label: "Style", placeholder: "e.g. minimalist" },
  { key: "occasion", label: "Occasion", placeholder: "e.g. wedding" },
  { key: "recipient", label: "Recipient", placeholder: "e.g. new mom" },
  { key: "color", label: "Color", placeholder: "e.g. sage green" },
  { key: "size", label: "Size", placeholder: "e.g. large" },
];

type Attributes = {
  productType: string;
  material: string;
  style: string;
  occasion: string;
  recipient: string;
  color: string;
  size: string;
};

const EMPTY_ATTRS: Attributes = {
  productType: "", material: "", style: "", occasion: "", recipient: "", color: "", size: "",
};

function parseTags(raw: string): string[] {
  return raw
    .split(/[\n,]/)
    .map((t) => t.trim())
    .filter((t) => t.length > 0);
}

function wordsOf(text: string): string[] {
  return text.toLowerCase().match(/[a-z0-9']+/g) ?? [];
}

export default function EtsyTagCleanupChecklist() {
  const [rawTags, setRawTags] = useState("");
  const [attrs, setAttrs] = useState<Attributes>(EMPTY_ATTRS);

  const analysis = useMemo(() => {
    const tags = parseTags(rawTags);

    const seen = new Map<string, string>();
    const duplicates: string[] = [];
    const cleaned: string[] = [];
    for (const tag of tags) {
      const key = tag.toLowerCase();
      if (seen.has(key)) {
        if (!duplicates.includes(seen.get(key)!)) duplicates.push(seen.get(key)!);
        continue;
      }
      seen.set(key, tag);
      cleaned.push(tag);
    }

    const vague = tags.filter((t) => {
      const lower = t.toLowerCase().trim();
      return lower.length <= 3 || VAGUE_WORDS.has(lower);
    });

    const tooLong = tags.filter((t) => t.length > 20);

    const wordCounts = new Map<string, number>();
    for (const tag of tags) {
      for (const w of new Set(wordsOf(tag))) {
        wordCounts.set(w, (wordCounts.get(w) ?? 0) + 1);
      }
    }
    const repeatedWords = Array.from(wordCounts.entries())
      .filter(([, count]) => count > 1)
      .map(([word]) => word);

    const attributeEntries = ATTRIBUTE_FIELDS.filter((f) => attrs[f.key].trim().length > 0);
    const allTagWords = new Set(tags.flatMap((t) => wordsOf(t)));
    const missingAttributes = attributeEntries.filter((f) => {
      const attrWords = wordsOf(attrs[f.key]);
      return !attrWords.some((w) => allTagWords.has(w));
    });

    const productType = attrs.productType.trim();
    const ideaPrompts: string[] = [];
    for (const f of attributeEntries) {
      if (f.key === "productType") continue;
      const value = attrs[f.key].trim();
      if (!value) continue;
      ideaPrompts.push(productType ? `${value} ${productType}` : value);
    }

    const softUnrelated = attributeEntries.length > 0
      ? tags.filter((t) => {
          const tw = new Set(wordsOf(t));
          const attrWords = new Set(attributeEntries.flatMap((f) => wordsOf(attrs[f.key])));
          return ![...tw].some((w) => attrWords.has(w));
        })
      : [];

    return { tags, duplicates, cleaned, vague, tooLong, repeatedWords, missingAttributes, ideaPrompts, softUnrelated };
  }, [rawTags, attrs]);

  function copyCleanedList() {
    navigator.clipboard?.writeText(analysis.cleaned.join(", ")).catch(() => {});
  }

  return (
    <div className="be-card p-6 sm:p-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Inputs */}
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">Your tags</h2>
          <p className="text-xs text-gray-400 mb-3">Paste your tags, one per line or comma-separated.</p>
          <textarea
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-6 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            rows={8}
            placeholder={"handmade tote bag\ncanvas tote\ncute\ncute\ngift for mom"}
            value={rawTags}
            onChange={(e) => setRawTags(e.target.value)}
          />

          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">Product attributes (optional)</h2>
          <p className="text-xs text-gray-400 mb-3">Used only to suggest coverage ideas — nothing is saved.</p>
          <div className="grid grid-cols-2 gap-3">
            {ATTRIBUTE_FIELDS.map((f) => (
              <div key={f.key}>
                <label className="block text-xs font-medium text-gray-500 mb-1">{f.label}</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  placeholder={f.placeholder}
                  value={attrs[f.key]}
                  onChange={(e) => setAttrs((a) => ({ ...a, [f.key]: e.target.value }))}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Results */}
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Cleanup review</h2>

          {analysis.tags.length === 0 ? (
            <p className="text-sm text-gray-400">Paste some tags to see a review.</p>
          ) : (
            <div className="space-y-5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Tags entered</span>
                <span className={`font-medium ${analysis.tags.length > 13 ? "text-amber-600" : "text-gray-900"}`}>
                  {analysis.tags.length}{analysis.tags.length > 13 ? " (Etsy allows 13 per listing)" : ""}
                </span>
              </div>

              <div>
                <p className="text-xs font-semibold text-gray-600 mb-1.5">Duplicate tags found</p>
                {analysis.duplicates.length === 0 ? (
                  <p className="text-xs text-gray-400">None found.</p>
                ) : (
                  <p className="text-sm text-red-600">{analysis.duplicates.join(", ")}</p>
                )}
              </div>

              <div>
                <p className="text-xs font-semibold text-gray-600 mb-1.5">Tags that may be too vague</p>
                {analysis.vague.length === 0 ? (
                  <p className="text-xs text-gray-400">None found.</p>
                ) : (
                  <p className="text-sm text-amber-600">{analysis.vague.join(", ")}</p>
                )}
              </div>

              <div>
                <p className="text-xs font-semibold text-gray-600 mb-1.5">Tags that may be too long for Etsy tag guidance</p>
                {analysis.tooLong.length === 0 ? (
                  <p className="text-xs text-gray-400">None found.</p>
                ) : (
                  <p className="text-sm text-amber-600">{analysis.tooLong.join(", ")}</p>
                )}
              </div>

              {analysis.softUnrelated.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-600 mb-1.5">Tags that don&apos;t clearly relate to your attributes</p>
                  <p className="text-xs text-gray-400 mb-1">Soft warning only — review before removing.</p>
                  <p className="text-sm text-gray-600">{analysis.softUnrelated.join(", ")}</p>
                </div>
              )}

              {analysis.missingAttributes.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-600 mb-1.5">Missing attribute coverage</p>
                  <ul className="space-y-1">
                    {analysis.missingAttributes.map((f) => (
                      <li key={f.key} className="text-sm text-gray-600">
                        No tag mentions your stated {f.label.toLowerCase()}: &ldquo;{attrs[f.key]}&rdquo;
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {analysis.ideaPrompts.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-600 mb-1.5">Tag ideas, not guaranteed keywords</p>
                  <div className="flex flex-wrap gap-2">
                    {analysis.ideaPrompts.map((idea) => (
                      <span key={idea} className="text-xs bg-indigo-50 text-indigo-700 border border-indigo-100 px-2.5 py-1 rounded-full">
                        {idea}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-xs font-semibold text-gray-600">Cleaned tag list (duplicates removed)</p>
                  <button type="button" onClick={copyCleanedList} className="text-xs font-medium text-indigo-600 hover:underline">
                    Copy
                  </button>
                </div>
                <p className="text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-lg p-3">
                  {analysis.cleaned.join(", ") || "—"}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      <p className="mt-8 text-xs text-gray-500 leading-relaxed border-t border-gray-100 pt-5">
        This is not an official Etsy tag generator and does not use Etsy search volume data.
        Review suggestions before applying them — treat everything above as tag ideas, not
        guaranteed keywords. Nothing entered here is saved or sent anywhere; everything runs in
        your browser.
      </p>
    </div>
  );
}
