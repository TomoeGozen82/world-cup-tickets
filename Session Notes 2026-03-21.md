# World Cup Tickets — Session Notes

## Session: 2026-03-21

### What Was Done

1. **Researched headless browser scraping** — compared Playwright vs Selenium vs Puppeteer for scraping JS-rendered ticket sites (StubHub, SeatGeek, Gametime). Playwright is the clear winner for Python in 2026.

2. **Designed StubHub Playwright scraper** — brainstormed approach, wrote design spec (`docs/superpowers/specs/2026-03-21-stubhub-playwright-design.md`), passed spec review.

3. **Wrote implementation plan** — 8 tasks across 3 chunks (`docs/superpowers/plans/2026-03-21-stubhub-playwright.md`), reviewed and approved.

4. **Added Playwright dependency** — `playwright>=1.40` added to `pyproject.toml`, Firefox browser installed.

5. **Extracted shared matching module** — created `collector/matching.py` with centralized team-name matching (aliases, normalization). Refactored `seatgeek.py` and `tickpick.py` to use it. TickPick gains alias support it previously lacked.

6. **Added error isolation** — wrapped each collector in try/except in `scrape.py` so one scraper failure doesn't kill the others.

7. **Created StubHub scraper** (`collector/stubhub.py`):
   - Uses Playwright Firefox (not Chromium — missing system libs on WSL/GHA)
   - Discovered StubHub's category page (`/world-cup-tickets/grouping/45410`) embeds JSON-LD with prices
   - Single-page-load strategy (like TickPick) — no per-event crawling needed
   - Blocks images/CSS/fonts for faster loads

8. **Updated dashboard** — added StubHub as 3rd platform card (blue), changed grid from fixed 2-column to `auto-fit` for 2-3 platforms.

9. **Updated GitHub Actions workflow** — added `playwright install --with-deps firefox` step.

10. **Deployed and verified** — pushed to GitHub, deployed to Vercel, triggered GHA scraper manually. All 3 scrapers ran successfully:
    - Vivid Seats: 61 updates
    - TickPick: 13 updates
    - StubHub: 4 updates (only 4 events listed so far)

### Current State
- **Live:** https://ticket-reseller.vercel.app
- **Platforms:** Vivid Seats + TickPick + StubHub (3 cards per match)
- **GitHub:** up to date with 10 new commits
- **GHA scraper:** running every 6h, all 3 platforms healthy

### Next Steps
- Monitor StubHub scraper over next few days — more events should appear as tournament approaches
- Telegram bot for price alerts
- Best deals view (ranked by cross-platform price gap / recent drops)
- Consider SeatGeek API (free registration) for a 4th platform
