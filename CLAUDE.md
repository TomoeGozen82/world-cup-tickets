# World Cup Tickets

FIFA 2026 World Cup ticket investment tracker.

## Stack
- FastAPI (Vercel serverless) + Turso (cloud SQLite) + GitHub Actions (scrapers)
- Single-page dashboard (DM Sans + Outfit fonts, custom CSS)
- GitHub: https://github.com/jinsoowhang/world-cup-tickets

## Data Sources (all zero-config, no API keys)
- **Static fixtures** — all 104 matches hardcoded from FIFA's official schedule, seeded on startup
- **Vivid Seats** (web scraping, JSON-LD) — resale ticket prices, refreshes every 6h
- **TickPick** (web scraping, JSON-LD) — resale ticket prices (no buyer fees), refreshes every 6h

## Architecture
```
main.py                — FastAPI app (serverless on Vercel)
api/index.py           — Vercel serverless entry point
config.py              — All constants (face values, venue scores, team tiers)
db/schema.sql          — SQLite schema (matches, price_snapshots, platform_prices)
db/database.py         — CRUD operations (Turso/libsql)
collector/fixtures.py  — Static fixture data (all 104 matches) + seeder
collector/seatgeek.py  — Vivid Seats scraper (file named seatgeek.py for historical reasons)
collector/tickpick.py  — TickPick scraper
analysis/value.py      — Value scoring (0-100) + FIFA fee calculator
public/index.html      — Single-page dashboard (all HTML/CSS/JS inline)
scripts/scrape.py      — Standalone scraper (GitHub Actions)
.github/workflows/scrape.yml — Cron scraper workflow (every 6h)
vercel.json            — Vercel routing config
docs/plans/            — Design docs and implementation plans
```

## Database (Turso)
- Cloud SQLite via libsql — same SQL dialect, no schema changes needed
- Env vars: `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`

### Tables
- `matches` — 104 fixtures with face values, resale prices, value scores
- `price_snapshots` — historical price aggregates per match (for trend charts)
- `platform_prices` — per-platform prices (vividseats, tickpick) with transferability flag
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
- Multi-platform price comparison (Vivid Seats, TickPick) with "BEST" tag on cheapest
- Transferability indicators (TickPick = always transferable)
- Price trend charts (SVG modal with low/median/high lines)
- Resale-only filter (default on), round filters, team search, country filter, sorting
- Mexico venue resale-cap warnings
- Manual refresh button

## Deployment
- **Frontend:** Vercel serves `public/index.html` as static
- **API:** FastAPI on Vercel serverless (`/api/*` routes)
- **Scrapers:** GitHub Actions cron (every 6h) runs `scripts/scrape.py`
- **Env vars needed:** `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` (set in both Vercel and GitHub Secrets)

```bash
# Deploy to Vercel
vercel --prod

# Run scrapers locally
TURSO_DATABASE_URL=... TURSO_AUTH_TOKEN=... uv run python scripts/scrape.py

# Trigger scraper manually on GitHub
gh workflow run scrape.yml
```

## Current State (March 2026)
- All 104 matches seeded from static data (72 group + 32 knockout)
- 6 team slots TBD pending UEFA/intercontinental playoffs (March 26-31, 2026)
- Multi-platform scraping: Vivid Seats, TickPick (every 6h via GitHub Actions)
- Dashboard focused on match cards with resale pricing (News/Reddit/Calculator removed)
- Price history being collected in price_snapshots + platform_prices tables

## Next Steps
- Telegram bot for price alerts
- Best deals view (ranked by cross-platform price gap / recent drops)
