# World Cup Tickets

FIFA 2026 World Cup ticket investment tracker.

@~/.claude/vps-instructions.md

## Stack
- FastAPI + SQLite + APScheduler + Docker
- Single-page dashboard (DM Sans + Outfit fonts, custom CSS)
- Port: 8200
- Domain: tickets.duchessnikki.com

## Data Sources (all zero-config, no API keys)
- **Static fixtures** — all 104 matches hardcoded from FIFA's official schedule, seeded on startup
- **Vivid Seats** (web scraping, JSON-LD) — resale ticket prices, refreshes every 6h
- **Reddit JSON API** (no auth) — ticket sentiment from r/WorldCup2026Tickets + r/fifatickets, every 2h
- **RSS feeds** (ESPN, Guardian, BBC) — World Cup news, every 4h

## Architecture
```
main.py              — FastAPI app + APScheduler + API routes
config.py            — All constants (face values, venue scores, team tiers)
db/schema.sql        — SQLite schema (matches, news_items, reddit_posts, price_snapshots)
db/database.py       — CRUD operations
collector/fixtures.py — Static fixture data (all 104 matches) + seeder
collector/seatgeek.py — Vivid Seats scraper (file named seatgeek.py for historical reasons)
collector/news_rss.py — RSS news collector
collector/reddit.py   — Reddit sentiment collector
analysis/value.py     — Value scoring (0-100) + FIFA fee calculator
viewer/static/index.html — Single-page dashboard (all HTML/CSS/JS inline)
```

## Value Scoring
Weighted factors (with resale data / without):
- Round significance: 30% / 40%
- Venue desirability: 15% / 25%
- Team popularity: 15% / 20%
- Country factor: 10% / 15%
- Resale markup: 30% / 0%

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
- Dashboard with score rings, country flags, resale prices, score breakdown tooltips
- Price snapshots stored for future trend analysis

## Next Steps
- Telegram bot for price alerts
- Price trend charts (data already being collected in price_snapshots table)
- Historical price tracking visualization on dashboard
