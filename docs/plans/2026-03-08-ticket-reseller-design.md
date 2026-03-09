# Ticket Reseller Dashboard — Design

**Date:** 2026-03-08
**Status:** Approved (updated to reflect existing MVP)

## Goal

A web dashboard for FIFA World Cup 2026 ticket resale research. Tracks match value scores, scrapes resale prices from Vivid Seats, monitors Reddit sentiment and RSS news. Helps identify the best ticket investment opportunities.

- **Live at:** `tickets.duchessnikki.com` (port 8200)
- **Focus:** World Cup 2026, all 104 matches
- **No AI features for v1** — pure data-driven

## What's Already Built (MVP)

### Architecture
Monolith: single FastAPI app with SQLite, APScheduler for background scrapes, single-page dashboard with custom CSS (Outfit + DM Sans fonts).

### Tech Stack
- Python 3.12 / uv
- FastAPI + uvicorn
- SQLite (WAL mode)
- httpx + regex-based scraping (Vivid Seats JSON-LD)
- APScheduler (news/4h, reddit/2h, resale/6h)
- Custom CSS + vanilla JS (no Tailwind, no Chart.js yet)

### Data Sources
1. **Static fixtures** — all 104 matches hardcoded from FIFA schedule
2. **Vivid Seats** — resale prices via JSON-LD scraping
3. **Reddit** — r/WorldCup2026Tickets + r/fifatickets (JSON API, no auth)
4. **RSS** — ESPN, Guardian, BBC sport feeds

### Database (SQLite)
- `matches` — 104 fixtures with face values, resale prices, value scores
- `price_snapshots` — historical price data per match (for future trend charts)
- `news_items` — RSS articles
- `reddit_posts` — Reddit sentiment

### Dashboard Features
- Match cards with score rings (0-100 value score)
- Score breakdown tooltips (Round, Venue, Team, Country, Resale factors)
- Country flags, venue info, Mexico resale-cap warnings
- Resale price display (lowest/median/highest from Vivid Seats)
- Filters by round
- Manual refresh button
- Fee calculator API endpoint

### Value Scoring (weighted 0-100)
With resale data: Round 30%, Venue 15%, Team 15%, Country 10%, Resale markup 30%
Without: Round 40%, Venue 25%, Team 20%, Country 15%

## What's Next (from brainstorming + CLAUDE.md)

### Priority 1: Price Trend Charts
- Data is already being collected in `price_snapshots` table
- Add Chart.js for line charts showing price over time per match
- Expandable chart on each match card or a match detail view

### Priority 2: Multi-Platform Price Comparison
- Add StubHub and TickPick scrapers alongside Vivid Seats
- Side-by-side pricing per match across all platforms
- Highlight cheapest option

### Priority 3: Transferability Flagging
- Scrape/flag whether listings are transferable
- Warning icons on non-transferable or unknown listings

### Priority 4: Best Deals View
- Ranked view of matches by resale opportunity
- Biggest cross-platform price gaps, steepest recent drops

### Future
- Telegram bot for price alerts
- Gametime as additional platform
