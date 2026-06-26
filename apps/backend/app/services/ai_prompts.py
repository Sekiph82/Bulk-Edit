"""Prompt builders for AI listing optimization tools."""
from __future__ import annotations


def build_title_prompt(context: dict) -> str:
    title = context.get("title", "")
    tags = ", ".join(context.get("tags", [])[:5])
    taxonomy = context.get("taxonomy_id", "")
    return (
        f"Optimize this Etsy listing title for SEO and buyer clarity.\n\n"
        f"Current title: {title}\n"
        f"Current tags (sample): {tags}\n"
        f"Taxonomy ID: {taxonomy}\n\n"
        f"Rules: max 140 chars, include primary keyword early, natural language, no keyword stuffing.\n"
        f"Return JSON with suggested_title and reasoning."
    )


def build_description_prompt(context: dict) -> str:
    title = context.get("title", "")
    description = (context.get("description") or "")[:800]
    materials = ", ".join(context.get("materials", []))
    return (
        f"Rewrite this Etsy listing description to be more compelling and SEO-friendly.\n\n"
        f"Listing title: {title}\n"
        f"Current description (truncated): {description}\n"
        f"Materials: {materials}\n\n"
        f"Rules: start with the key benefit, include keywords naturally, mention materials, "
        f"end with a call to action. Max 2000 chars.\n"
        f"Return JSON with suggested_description and reasoning."
    )


def build_tags_prompt(context: dict) -> str:
    title = context.get("title", "")
    current_tags = context.get("tags", [])
    materials = ", ".join(context.get("materials", []))
    return (
        f"Suggest optimized Etsy tags for this listing.\n\n"
        f"Title: {title}\n"
        f"Current tags: {', '.join(current_tags)}\n"
        f"Materials: {materials}\n\n"
        f"Rules: 13 tags max, each tag <=20 chars, use long-tail phrases, "
        f"mix broad and specific terms, no duplicate concepts.\n"
        f"Return JSON with suggested_tags (array of strings) and reasoning."
    )


def build_alt_text_prompt(context: dict) -> str:
    title = context.get("title", "")
    image_position = context.get("image_position", 1)
    current_alt = context.get("current_alt_text", "")
    return (
        f"Write descriptive alt text for an Etsy listing image.\n\n"
        f"Listing title: {title}\n"
        f"Image position: {image_position}\n"
        f"Current alt text: {current_alt or '(none)'}\n\n"
        f"Rules: max 125 chars, describe what is visually shown, include product name, "
        f"be specific about details/colors/materials if known, no keyword stuffing.\n"
        f"Return JSON with suggested_alt_text and reasoning."
    )


def build_seo_score_prompt(context: dict) -> str:
    title = context.get("title", "")
    description = (context.get("description") or "")[:500]
    tags = context.get("tags", [])
    return (
        f"Score this Etsy listing's SEO quality (0-100).\n\n"
        f"Title: {title}\n"
        f"Description (truncated): {description}\n"
        f"Tags: {', '.join(tags)}\n\n"
        f"Score each component and provide specific, actionable issues and suggestions.\n"
        f"Return JSON with: score, title_score, description_score, tags_score, "
        f"issues (array), suggestions (array)."
    )
