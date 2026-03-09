# World Cup Tickets

FIFA 2026 World Cup ticket investment tracker.

@~/.claude/vps-instructions.md

## Stack
- FastAPI + SQLite + APScheduler + Docker
- Single-page dashboard (DM Sans + Outfit fonts, custom CSS)
- Port: 8200
- Domain: tickets.duchessnikki.com
- GitHub: https://github.com/jinsoowhang/world-cup-tickets

## Data Sources (all zero-config, no API keys)
- **Static fixtures** — all 104 matches hardcoded from FIFA's official schedule, seeded on startup
- **Vivid Seats** (web scraping, JSON-LD) — resale ticket prices, refreshes every 6h
- **StubHub** (web scraping, JSON-LD) — resale ticket prices, refreshes every 6h
- **TickPick** (web scraping, JSON-LD) — resale ticket prices (no buyer fees), refreshes every 6h

## Architecture
```
main.py                — FastAPI app + APScheduler + API routes
config.py              — All constants (face values, venue scores, team tiers)
db/schema.sql          — SQLite schema (matches, price_snapshots, platform_prices)
db/database.py         — CRUD operations
collector/fixtures.py  — Static fixture data (all 104 matches) + seeder
collector/seatgeek.py  — Vivid Seats scraper (file named seatgeek.py for historical reasons)
collector/stubhub.py   — StubHub scraper
collector/tickpick.py  — TickPick scraper
analysis/value.py      — Value scoring (0-100) + FIFA fee calculator
viewer/static/index.html — Single-page dashboard (all HTML/CSS/JS inline)
docs/plans/            — Design docs and implementation plans
```

## Database Tables
- `matches` — 104 fixtures with face values, resale prices, value scores
- `price_snapshots` — historical price aggregates per match (for trend charts)
- `platform_prices` — per-platform prices (vividseats, stubhub, tickpick) with transferability flag
- `news_items` — RSS articles (collectors removed from UI but table remains)
- `reddit_posts` — Reddit posts (collectors removed from UI but table remains)

## Value Scoring
Weighted factors (with resale data / without):
- Round significance: 30% / 40%
- Venue desirability: 15% / 25%
- Team popularity: 15% / 20%
- Country factor: 10% / 15%
- Resale markup: 30% / 0%

## Dashboard Features
- Match cards with score rings (0-100 value score) and breakdown tooltips
- Multi-platform price comparison (Vivid Seats, StubHub, TickPick) with "BEST" tag on cheapest
- Transferability indicators (TickPick = always transferable)
- Price trend charts (SVG modal with low/median/high lines)
- Resale-only filter (default on), round filters, team search, country filter, sorting
- Mexico venue resale-cap warnings
- Manual refresh button

## Deployment
```bash
# Build and run locally
uv run uvicorn main:app --host 0.0.0.0 --port 8200

# Deploy to VPS
scp <files> root@187.77.7.89:/tmp/wc-update/
ssh root@187.77.7.89 "docker cp /tmp/wc-update/<file> world-cup-tickets:/app/<file>"
ssh root@187.77.7.89 "docker restart world-cup-tickets"
```

## Current State (March 2026)
- All 104 matches seeded from static data (72 group + 32 knockout)
- 6 team slots TBD pending UEFA/intercontinental playoffs (March 26-31, 2026)
- Multi-platform scraping: Vivid Seats, StubHub, TickPick (every 6h)
- Dashboard focused on match cards with resale pricing (News/Reddit/Calculator removed)
- Price history being collected in price_snapshots + platform_prices tables

## Next Steps
- Telegram bot for price alerts
- Best deals view (ranked by cross-platform price gap / recent drops)
- Add Gametime as 4th platform
