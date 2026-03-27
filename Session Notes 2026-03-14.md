# World Cup Tickets — Session Notes

## Session: 2026-03-14

### What Was Done

1. **Reset local repo to match Vercel deployment** — discarded uncommitted local changes (local events feature, scraper utils, separate CSS/JS files) to sync with what's live on `origin/main`

2. **Removed StubHub scraper** (4 commits):
   - Deleted `collector/stubhub.py` (was already a no-op — StubHub requires JS rendering)
   - Removed StubHub from dashboard platform lists in both `public/index.html` and `viewer/static/index.html`
   - Updated CLAUDE.md, README.md architecture diagram
   - Removed Gametime from next steps (also not scrapable without headless browser)

3. **Attempted 3-card layout with median pricing** — added "Vivid Seats (mid)" as a 3rd price option using aggregate median data. User found this confusing since median ($6,893) wasn't the "next cheapest ticket" ($1,050) — it was the statistical middle of all listings.

4. **Reverted to 2-card layout** — each match shows up to 2 clickable cards (Vivid Seats + TickPick), cheapest price per platform only. Grid changed from 3-column to 2-column.

5. **Fixed iOS Safari tappability** — added `position: relative`, `z-index`, and `-webkit-tap-highlight-color` to platform cards.

6. **Deployed to Vercel** after each change set.

### Research: Alternative Ticket Platforms

Tested 8+ platforms as StubHub replacements. Results:
- **SeatGeek** — 403 (blocks automated requests)
- **Gametime** — JS SPA, no static data
- **ViaGoGo** — JS SPA, no static data
- **MegaSeats, TicketNetwork, GoTickets, TicketSmarter, CheapTickets** — 404 or 403

**Conclusion:** For simple httpx scraping (no headless browser, no API keys), only Vivid Seats and TickPick reliably return World Cup data in static HTML.

### Current State
- **Live:** https://ticket-reseller.vercel.app
- **Platforms:** Vivid Seats + TickPick (2 cards per match)
- **GitHub:** up to date with 5 new commits

### Potential Future Work
- Scrape individual listing prices (not just aggregates) to show multiple price tiers
- Add headless browser (Playwright) to unlock StubHub/SeatGeek/Gametime
- SeatGeek API (requires free client_id registration)
