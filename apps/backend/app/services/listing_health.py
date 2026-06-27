"""
Listing Health Score engine.
Rule-based. Does not require AI or Etsy API access.
Score: 0-100. Grades: excellent(90+), good(75+), needs_work(50+), critical(<50).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import re


@dataclass
class HealthIssue:
    category: str
    severity: str  # low / medium / high / critical
    field: str
    message: str
    recommended_fix: str
    ai_can_help: bool = False
    points_lost: int = 0


def _grade(score: int) -> str:
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "good"
    if score >= 50:
        return "needs_work"
    return "critical"


def _priority(issues: List[HealthIssue]) -> str:
    sevs = {i.severity for i in issues}
    for sev in ("critical", "high", "medium"):
        if sev in sevs:
            return sev
    return "low"


def score_listing(
    listing_id: str,
    title: Optional[str],
    description: Optional[str],
    tags: Optional[list],
    photo_count: int = 0,
    has_video: bool = False,
    price: Optional[float] = None,
    has_cost_data: bool = False,
) -> dict:
    issues: List[HealthIssue] = []
    score = 100

    # ── Title ─────────────────────────────────────────────────────────────────
    if not title or not title.strip():
        issues.append(HealthIssue(
            category="title", severity="critical", field="title",
            message="Listing has no title.",
            recommended_fix="Add a descriptive title with primary keywords.",
            ai_can_help=True, points_lost=25,
        ))
        score -= 25
    else:
        t = title.strip()
        if len(t) < 20:
            issues.append(HealthIssue(
                category="title", severity="high", field="title",
                message=f"Title is too short ({len(t)} chars). Etsy allows up to 140.",
                recommended_fix="Expand the title to include product type, style, material, and use case.",
                ai_can_help=True, points_lost=15,
            ))
            score -= 15
        elif len(t) > 140:
            issues.append(HealthIssue(
                category="title", severity="medium", field="title",
                message=f"Title exceeds 140 characters ({len(t)} chars).",
                recommended_fix="Trim the title to under 140 characters.",
                ai_can_help=True, points_lost=5,
            ))
            score -= 5

        words = re.findall(r"\b\w{3,}\b", t.lower())
        counts: dict[str, int] = {}
        for w in words:
            counts[w] = counts.get(w, 0) + 1
        dupes = [w for w, c in counts.items() if c > 2]
        if dupes:
            issues.append(HealthIssue(
                category="title", severity="low", field="title",
                message=f"Title repeats words: {', '.join(dupes[:3])}.",
                recommended_fix="Remove duplicate words and use unique descriptive terms.",
                ai_can_help=True, points_lost=5,
            ))
            score -= 5

        upper = [w for w in t.split() if len(w) > 2 and w.isupper()]
        if len(upper) > 3:
            issues.append(HealthIssue(
                category="title", severity="low", field="title",
                message="Title contains many ALL CAPS words, which can look spammy.",
                recommended_fix="Use title case instead of ALL CAPS.",
                ai_can_help=True, points_lost=3,
            ))
            score -= 3

    # ── Tags ──────────────────────────────────────────────────────────────────
    tag_list: list = tags or []
    tag_count = len(tag_list)

    if tag_count == 0:
        issues.append(HealthIssue(
            category="tags", severity="critical", field="tags",
            message="Listing has no tags. Tags are essential for Etsy search.",
            recommended_fix="Add 13 relevant long-tail tags.",
            ai_can_help=True, points_lost=20,
        ))
        score -= 20
    elif tag_count < 5:
        issues.append(HealthIssue(
            category="tags", severity="high", field="tags",
            message=f"Listing has only {tag_count} tags. Etsy allows 13.",
            recommended_fix=f"Add {13 - tag_count} more long-tail tags.",
            ai_can_help=True, points_lost=12,
        ))
        score -= 12
    elif tag_count < 10:
        issues.append(HealthIssue(
            category="tags", severity="medium", field="tags",
            message=f"Listing uses {tag_count} of 13 Etsy tags.",
            recommended_fix=f"Add {13 - tag_count} more long-tail tags to maximize reach.",
            ai_can_help=True, points_lost=8,
        ))
        score -= 8
    elif tag_count < 13:
        issues.append(HealthIssue(
            category="tags", severity="low", field="tags",
            message=f"Listing uses {tag_count} of 13 Etsy tags.",
            recommended_fix=f"Add {13 - tag_count} more tags.",
            ai_can_help=True, points_lost=3,
        ))
        score -= 3

    if tag_list:
        lower_tags = [str(t).lower().strip() for t in tag_list]
        if len(lower_tags) != len(set(lower_tags)):
            issues.append(HealthIssue(
                category="tags", severity="low", field="tags",
                message="Listing has duplicate tags.",
                recommended_fix="Remove duplicate tags and replace with unique terms.",
                ai_can_help=True, points_lost=3,
            ))
            score -= 3

        short = [t for t in tag_list if len(str(t).strip()) < 3]
        if short:
            issues.append(HealthIssue(
                category="tags", severity="low", field="tags",
                message=f"{len(short)} tag(s) are very short (< 3 chars).",
                recommended_fix="Replace short tags with descriptive multi-word phrases.",
                ai_can_help=True, points_lost=2,
            ))
            score -= 2

    # ── Description ───────────────────────────────────────────────────────────
    desc = (description or "").strip()
    if not desc:
        issues.append(HealthIssue(
            category="description", severity="high", field="description",
            message="Listing has no description.",
            recommended_fix="Write a detailed description covering materials, dimensions, use case, and care instructions.",
            ai_can_help=True, points_lost=15,
        ))
        score -= 15
    elif len(desc) < 100:
        issues.append(HealthIssue(
            category="description", severity="high", field="description",
            message=f"Description is too short ({len(desc)} chars).",
            recommended_fix="Expand the description with product details, sizing, materials, and shipping info.",
            ai_can_help=True, points_lost=10,
        ))
        score -= 10
    elif len(desc) < 300:
        issues.append(HealthIssue(
            category="description", severity="medium", field="description",
            message=f"Description is brief ({len(desc)} chars). Consider expanding.",
            recommended_fix="Add details about materials, care instructions, and shipping/processing times.",
            ai_can_help=True, points_lost=5,
        ))
        score -= 5

    # ── Photos ────────────────────────────────────────────────────────────────
    if photo_count == 0:
        issues.append(HealthIssue(
            category="media", severity="critical", field="photos",
            message="Listing has no photos.",
            recommended_fix="Add at least 5-10 high-quality photos.",
            ai_can_help=False, points_lost=15,
        ))
        score -= 15
    elif photo_count < 3:
        issues.append(HealthIssue(
            category="media", severity="high", field="photos",
            message=f"Listing has only {photo_count} photo(s). Etsy allows up to 10.",
            recommended_fix="Add more photos showing different angles, scale, and context.",
            ai_can_help=False, points_lost=10,
        ))
        score -= 10
    elif photo_count < 5:
        issues.append(HealthIssue(
            category="media", severity="medium", field="photos",
            message=f"Listing has {photo_count} photos. Adding more improves conversion.",
            recommended_fix="Add lifestyle and detail photos.",
            ai_can_help=False, points_lost=5,
        ))
        score -= 5

    if not has_video and photo_count >= 5:
        issues.append(HealthIssue(
            category="media", severity="low", field="video",
            message="No video. Listings with video often convert better.",
            recommended_fix="Add a short product video or GIF.",
            ai_can_help=False, points_lost=2,
        ))
        score -= 2

    # ── Price ─────────────────────────────────────────────────────────────────
    if price is None or price == 0:
        issues.append(HealthIssue(
            category="pricing", severity="critical", field="price",
            message="Listing has no price set.",
            recommended_fix="Set a price for this listing.",
            ai_can_help=False, points_lost=10,
        ))
        score -= 10

    # ── Cost data signal (informational only — not counted in issue_count) ────
    informational: list = []
    if not has_cost_data:
        informational.append({
            "category": "pricing",
            "field": "costs",
            "message": "No cost data configured for this listing.",
            "recommended_fix": "Add cost data in the Profit Calculator to check your margin.",
        })

    score = max(0, min(100, score))

    return {
        "listing_id": listing_id,
        "score": score,
        "grade": _grade(score),
        "priority": _priority(issues),
        "issue_count": len(issues),
        "issues": issues,
        "top_issues": issues[:3],
        "suggested_actions": [i.recommended_fix for i in issues[:5]],
        "tag_count": tag_count,
        "photo_count": photo_count,
        "has_video": has_video,
        "informational": informational,
    }
