# Product Requirements Document

## Product Name
Bulk-Edit

## Problem Statement
Etsy sellers with large catalogs spend hours manually editing listings one at a time. Existing tools (GetVela, Vela, Marmalead) are either expensive, limited in scope, or lack AI-powered optimization. Sellers need a fast, safe, and intelligent bulk editing tool.

## Target Users
- Etsy sellers with 25+ active listings
- Sellers who frequently update pricing, tags, or descriptions seasonally
- Power sellers managing multiple shops
- Sellers who want AI-optimized titles and tags for SEO

## Core Value Propositions
1. **Speed** — Edit 500 listings in the time it takes to edit 5 manually
2. **Safety** — Preview before publish, backup before write, revert anytime
3. **Intelligence** — AI tools that actually improve listing performance
4. **Reliability** — Never lose a listing to a bad bulk edit

## User Personas

### Persona 1: The Power Seller
- 200–2000 listings
- Updates prices seasonally (holiday, sales)
- Needs bulk tag and title optimization
- Values speed and safety

### Persona 2: The Growing Seller
- 25–200 listings
- Wants to improve SEO but doesn't know where to start
- Needs AI guidance on titles and tags
- Budget-conscious

### Persona 3: The Multi-Shop Manager
- Manages 2–5 Etsy shops
- Needs centralized management
- Values organization and filtering tools

## Functional Requirements

### Must Have (v1.0)
- Etsy OAuth connection
- Listing sync (full and incremental)
- Bulk edit: titles, descriptions, tags, prices, quantities
- Preview before publish
- Snapshot backup before write
- Magic Revert
- Subscription billing (Free, Pro)
- AI: title optimizer, tag generator

### Should Have (v1.1)
- Bulk edit: photos, videos, variations
- Media library
- AI: description writer, alt text, SEO scorer
- CSV import/export

### Nice to Have (v1.2)
- Dynamic pricing rules
- Scheduled jobs
- AI category suggester
- Admin panel

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| Page load time | < 2s for listings grid (500 rows) |
| Bulk edit apply time | < 30s for 100 listings |
| Etsy API rate limit compliance | Always |
| Uptime | 99.5% |
| Data backup | Daily |
| Revert window | 30 days of snapshots |

## Out of Scope (v1.0)
- Shopify integration
- Mobile app
- Email marketing
- Analytics dashboard
- Competitor monitoring
