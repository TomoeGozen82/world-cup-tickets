# World Cup Tickets — Session Notes

## Session: 2026-03-08

### What Was Done
1. **Brainstormed** project direction — confirmed: research dashboard for World Cup 2026, nationwide, price comparison + trends, web scraping, data-driven (no AI), deployed at tickets.duchessnikki.com

2. **Discovered existing MVP** was already substantial:
   - 104 match fixtures, Vivid Seats scraper, value scoring, price trend charts, Reddit/news/calculator tabs
   - Deployed on VPS at port 8200

3. **Added multi-platform price comparison** (6 atomic commits):
   - New `platform_prices` DB table with transferability tracking
   - StubHub scraper (`collector/stubhub.py`)
   - TickPick scraper (`collector/tickpick.py`)
   - Vivid Seats writes to new table too
   - All wired into scheduler (6h interval) + new API endpoints
   - Dashboard shows side-by-side pricing with "BEST" tag on cheapest

4. **Added resale-only filter** — checkbox (default on) hides matches without resale data

5. **Removed News, Reddit, Calculator tabs** — simplified dashboard to focus on match cards with pricing

6. **Updated all documentation** — CLAUDE.md, design doc, session notes

### Current State
- **Live:** https://tickets.duchessnikki.com
- **GitHub:** https://github.com/jinsoowhang/world-cup-tickets
- **Scrapers:** Vivid Seats + StubHub + TickPick (every 6h each)
- **Dashboard:** Match cards with multi-platform comparison, score rings, price trend charts, resale-only filter

### Next Steps
- **Best deals view** — rank matches by cross-platform price gap or recent price drops
- **Telegram bot** — price alerts when prices drop below threshold
- **Gametime** — add as 4th scraping platform
- **Scraper monitoring** — check if StubHub/TickPick scrapers are actually finding and matching events (may need tuning of search URLs or matching logic)
