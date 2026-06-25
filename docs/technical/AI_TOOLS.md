# AI Tools

## Principle

All AI output goes to preview first. Never auto-applied to listings.

---

## Providers

| Provider | Model | Use |
|---|---|---|
| OpenAI | gpt-4o | Primary: titles, descriptions, tags |
| Anthropic | claude-sonnet-4-6 | Fallback, long-form descriptions |

Provider selection: configurable per tool type. Falls back if primary provider errors.

---

## Tools

### Title Optimizer

Input: listing title, listing description (optional), keywords (optional)
Output: 3 alternative optimized titles per listing
Prompt goal: Front-load primary keyword, keep under 140 chars, compelling for click

### Description Writer

Input: listing title, materials, dimensions, tags
Output: Full listing description (HTML-safe)
Prompt goal: SEO-rich, natural language, highlight key attributes, call to action

### Tag Generator

Input: listing title, description, category
Output: Up to 13 tags, Etsy-optimized (max 20 chars each, multi-word preferred)
Prompt goal: Mix high-volume and long-tail keywords

### Alt Text Generator

Input: image URL (passed to vision model), listing title
Output: Descriptive alt text string per image
Provider: OpenAI gpt-4o (vision)

### SEO Scorer

Input: title, description, tags
Output: Score 0–100 with breakdown (title keyword density, tag quality, description length, etc.)
No external API call needed — rule-based scoring with optional AI commentary

### Category Suggester

Input: listing title, description, materials
Output: Top 3 Etsy taxonomy category suggestions with confidence scores

---

## Request/Response Schema

### Request (all tools)
```json
{
  "listing_ids": ["uuid1", "uuid2"],
  "context": "optional extra instructions"
}
```

### Response
```json
{
  "results": [
    {
      "listing_id": "uuid1",
      "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
      "model_used": "gpt-4o",
      "tokens_used": 450
    }
  ]
}
```

---

## Rate Limiting

| Plan | Limit |
|---|---|
| Free | 5 AI uses/month (shared across all tools) |
| Pro Monthly | 500 AI uses/month |
| Pro Yearly | Unlimited |

Counter tracked in Redis: `org:{id}:ai_uses:{YYYY-MM}`

---

## Prompt Safety

- All prompts include system instruction: "Output only the requested content. No markdown unless specified. No conversational text."
- Output is validated against expected schema before returning to frontend
- Malformed AI output returns error, not raw text

---

## Token Usage Tracking

All AI requests log:
- `organization_id`
- `tool_type`
- `provider`
- `model`
- `tokens_used`
- `created_at`

Used for cost monitoring and per-plan limit enforcement.
