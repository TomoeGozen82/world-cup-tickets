# FIFA World Cup 2026 — Ticket Investment Tracker

A real-time dashboard that tracks resale ticket prices across multiple platforms for all 104 FIFA World Cup 2026 matches. Compares prices, scores investment value, and tracks price trends to help find the best deals.

**Live:** [ticket-reseller.vercel.app](https://ticket-reseller.vercel.app)

## What It Does

- Tracks **104 matches** across all rounds (Group stage through Final)
- Scrapes resale prices from **Vivid Seats** and **TickPick** every 6 hours
- Calculates a **value score (0–100)** for each match based on round significance, venue desirability, team popularity, and resale markup
- Compares prices across platforms with a **"BEST" tag** on the cheapest option
- Tracks **price history** over time with trend charts
- Flags **Mexico venue resale caps** (Mexican law limits resale to face value)
- Shows **ticket transferability** by platform

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML/CSS/JS (single-page, no framework) |
| API | FastAPI on Vercel serverless |
| Database | Turso (cloud SQLite via libsql) |
| Scrapers | GitHub Actions cron (every 6h) |
| Fonts | DM Sans + Outfit (Google Fonts) |

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Vercel     │     │    Turso     │     │   GitHub     │
│  (Frontend   │────▶│  (Cloud DB)  │◀────│   Actions    │
│   + API)     │     │  104 matches │     │  (Scrapers)  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                                    ┌───────────┤
                                    ▼           ▼
                              Vivid Seats   TickPick
```

## Value Scoring

Each match gets a 0–100 score based on weighted factors:

| Factor | With Resale Data | Without |
|--------|:---:|:---:|
| Round significance | 30% | 40% |
| Venue desirability | 15% | 25% |
| Team popularity | 15% | 20% |
| Country factor | 10% | 15% |
| Resale markup | 30% | — |

## Project Structure

```
main.py                  FastAPI app with API routes
api/index.py             Vercel serverless entry point
config.py                Constants (face values, venue scores, team tiers)
db/schema.sql            Database schema
db/database.py           CRUD operations (Turso/libsql)
collector/fixtures.py    All 104 match fixtures (static data)
collector/seatgeek.py    Vivid Seats scraper (JSON-LD extraction)
collector/tickpick.py    TickPick scraper (JSON-LD extraction)
analysis/value.py        Value scoring algorithm + FIFA fee calculator
public/index.html        Dashboard (all HTML/CSS/JS inline)
scripts/scrape.py        Standalone scraper for GitHub Actions
.github/workflows/       Cron workflow (every 6h)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/matches` | All matches (filterable by `round`, `country`) |
| GET | `/api/analysis/scores` | Matches sorted by value score |
| GET | `/api/prices/{match_id}` | Price history for a match |
| GET | `/api/platform-prices` | Latest prices from all platforms |
| GET | `/api/platform-prices/{match_id}` | Platform prices for a specific match |

## Local Development

```bash
# Install dependencies
uv sync

# Set environment variables
export TURSO_DATABASE_URL="libsql://your-db.turso.io"
export TURSO_AUTH_TOKEN="your-token"

# Run scrapers locally
uv run python scripts/scrape.py

# Run API locally
uv run uvicorn main:app --reload
```

## Deployment

The app runs on three independent services:

1. **Vercel** — Serves the frontend and API (auto-deploys on push)
2. **Turso** — Cloud SQLite database (no maintenance needed)
3. **GitHub Actions** — Runs scrapers every 6 hours on a cron schedule

Environment variables (`TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`) are set in both Vercel and GitHub Secrets.

## Built With

- [FastAPI](https://fastapi.tiangolo.com/) — Python web framework
- [Turso](https://turso.tech/) — Edge SQLite database
- [Vercel](https://vercel.com/) — Serverless hosting
- [uv](https://docs.astral.sh/uv/) — Python package manager
