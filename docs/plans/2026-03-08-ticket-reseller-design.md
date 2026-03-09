# Ticket Reseller Dashboard — Design

**Date:** 2026-03-08
**Status:** Implemented

## Goal

A web dashboard for FIFA World Cup 2026 ticket resale research. Tracks match value scores, scrapes resale prices from multiple platforms, and helps identify the best ticket investment opportunities.

- **Live at:** `tickets.duchessnikki.com` (port 8200)
- **Focus:** World Cup 2026, all 104 matches
- **No AI features for v1** — pure data-driven

## Architecture
Monolith: single FastAPI app with SQLite, APScheduler for background scrapes, single-page dashboard with custom CSS (Outfit + DM Sans fonts).

## Tech Stack
- Python 3.12 / uv
- FastAPI + uvicorn
- SQLite (WAL mode)
- httpx + regex-based scraping (JSON-LD)
- APScheduler (resale scraping every 6h for all 3 platforms)
- Custom CSS + vanilla JS, SVG charts

## Data Sources
1. **Static fixtures** — all 104 matches hardcoded from FIFA schedule
2. **Vivid Seats** — resale prices via JSON-LD scraping
3. **StubHub** — resale prices via JSON-LD scraping
4. **TickPick** — resale prices via JSON-LD scraping (no buyer fees, guaranteed transferable)

## Database (SQLite)
- `matches` — 104 fixtures with face values, resale prices, value scores
- `price_snapshots` — historical price aggregates per match
- `platform_prices` — per-platform prices with transferability flag
- `news_items` / `reddit_posts` — legacy tables (collectors removed from UI)

## Dashboard Features (implemented)
- Match cards with score rings (0-100 value score) and breakdown tooltips
- Multi-platform price comparison (Vivid Seats, StubHub, TickPick) with "BEST" tag
- Transferability indicators
- Price trend charts (SVG modal)
- Resale-only filter (default on), round/country/team filters, sorting
- Mexico resale-cap warnings
- Manual refresh button

## Value Scoring (weighted 0-100)
With resale data: Round 30%, Venue 15%, Team 15%, Country 10%, Resale markup 30%
Without: Round 40%, Venue 25%, Team 20%, Country 15%

## What's Next

### Priority 1: Best Deals View
- Ranked view of matches by resale opportunity
- Biggest cross-platform price gaps, steepest recent drops

### Priority 2: Telegram Bot for Price Alerts
- Notify when prices drop below threshold
- Daily summary of best deals

### Future
- Gametime as 4th platform
- AI-powered analysis (when enough historical data accumulated)
