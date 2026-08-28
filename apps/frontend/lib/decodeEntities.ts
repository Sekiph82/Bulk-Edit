// Display-safe HTML entity decode for Etsy-sourced text (title, description, tags, materials).
// Text-only: never parses or renders HTML. Defense-in-depth for records synced before the
// backend normalization fix (backend now decodes on import; this covers already-synced rows).
const NAMED_ENTITIES: Record<string, string> = {
  "&amp;": "&",
  "&lt;": "<",
  "&gt;": ">",
  "&quot;": '"',
  "&#39;": "'",
  "&apos;": "'",
  "&nbsp;": " ",
};

const NAMED_PATTERN = /&amp;|&lt;|&gt;|&quot;|&#39;|&apos;|&nbsp;/g;

export function decodeEntities(input: string | null | undefined): string {
  if (!input) return input ?? "";
  let out = input.replace(/&#(\d+);/g, (_, dec: string) => {
    try {
      return String.fromCodePoint(parseInt(dec, 10));
    } catch {
      return _;
    }
  });
  out = out.replace(/&#x([0-9a-fA-F]+);/g, (_, hex: string) => {
    try {
      return String.fromCodePoint(parseInt(hex, 16));
    } catch {
      return _;
    }
  });
  out = out.replace(NAMED_PATTERN, (m) => NAMED_ENTITIES[m] ?? m);
  return out;
}

export function decodeEntitiesList(input: (string | null | undefined)[] | null | undefined): string[] {
  if (!input) return [];
  return input.map((v) => decodeEntities(v));
}
