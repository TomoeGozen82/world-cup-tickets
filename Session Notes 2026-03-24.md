# World Cup Tickets — Session Notes

## Session: 2026-03-24

### What Was Done

1. **5-person review panel** — Spawned 5 parallel agents to review the live site from different perspectives:
   - Alex (casual buyer), Marcus (ticket reseller), Sarah (UX designer), David (market analyst), Ray (devil's advocate)
   - All 5 unanimously flagged fee transparency as the #1 issue — the "BEST" tag was comparing raw prices across platforms with wildly different fee structures

2. **Fee transparency** (P0) — Added `PLATFORM_FEES` config and fee-adjusted all-in pricing:
   - TickPick: 0% fees, Vivid Seats: ~28%, StubHub: ~25%
   - BEST tag now compares after fees
   - Each platform card shows fee label ("No fees" in green, "+28% fees" in muted)
   - All-in price shown as primary, raw price as secondary

3. **Fixed misleading data labels** (P0) — Chart labels changed from "Median" to "Average" since scrapers don't actually collect true medians

4. **Fixed sort-by-price** (P1) — Now sorts by cheapest all-in resale price across platforms, not by face value

5. **Data freshness indicators** (P1/P2):
   - "Data from Xh ago" replaces fake Refresh button in header
   - Per-platform timestamps on each card with orange stale warning (>12h)
   - "Showing X of 104 matches" filter count always visible
   - Resale-only unchecked by default — all 104 matches visible on first load

6. **Collapsible mobile filters** (P2) — Search always visible, other filters collapse behind "Filters" button on mobile

7. **Scraper health monitoring** (P1) — Per-scraper result tracking, ALERT logging on zero results, `sys.exit(1)` if all scrapers fail (triggers GitHub email), `/api/health` endpoint

8. **Buyer/Reseller dual mode** (P3):
   - Toggle in header switches between Deal Score (buyer) and Investment Score (reseller)
   - Buyer mode: low markup = high score (inverted from reseller)
   - Score rings, stats bar, and sorting all mode-aware

9. **Table view** (P3) — Dense sortable table alongside card grid, with columns for all platforms, best price, markup %, and score

10. **Deployed** — 4 atomic commits pushed to main, deployed to Vercel

### Current State
- **Live:** https://ticket-reseller.vercel.app
- **Platforms:** Vivid Seats + TickPick + StubHub (fee-adjusted comparison)
- **Views:** Card grid (default) + Table view toggle
- **Modes:** Buyer (Deal Score) + Reseller (Investment Score)
- **GitHub:** up to date with 4 new commits
- **API:** Envelope response `{matches, last_scraped}`, health endpoint at `/api/health`

### Next Steps
- Telegram bot for price alerts (price drop notifications)
- Best deals view (ranked by cross-platform price gap / recent drops)
- "When to Buy" analysis from historical price data
- Consider SeatGeek API for 4th platform
- Add affiliate links for monetization
