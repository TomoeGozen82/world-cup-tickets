# World Cup Tickets — Session Notes

## Session: 2026-03-26

### What Was Done

1. **Default to "With prices only" filter** — checkbox now checked on page load, hiding ~40+ matches with no listings across any platform. Reduces clutter for first-time visitors.

2. **Renamed filter label** — changed "Resale only" to "With prices only" after 5-agent review panel unanimously flagged the old label as misleading (sounded like ticket-type filter, not listing availability).

3. **Tightened filter logic** — removed legacy `resale_lowest || resale_median` fallback that could show matches with no platform cards. Now strictly requires `platform_prices.length > 0`.

4. **"Show all" link in match counter** — counter now reads "Showing X of 104 matches - Show all" when filter is active. Clicking clears the filter without needing to find the checkbox (critical for mobile where filters are collapsed).

5. **Mobile filter badge** — "Filters" button shows "Filters (1)" when the pricing filter is active, so mobile users know a filter is on.

6. **Improved empty state** — if filter hides all matches (e.g., scrapers down), message says "No matches with listings found. Show all matches" instead of generic "No matches found."

7. **Deployed** — 1 atomic commit pushed to main, deployed to Vercel.

8. **Scoring system overhaul** — 3-agent review panel (reseller, data scientist, devil's advocate) identified root causes of scores clustering below 50. Implemented:
   - **Matchup factor** (15% weight) — scores the team *pairing*, not just the best individual team. Brazil vs Morocco ≠ Scotland vs Haiti. Lookup table for all 10 tier-pair combinations.
   - **Piecewise resale markup curve** — 100% markup now scores 70/100 instead of 28. Much more generous for the 50-200% range where most real data lives.
   - **Raised Group stage floor** — from 30 to 50. Group matches (69% of all) were getting crushed by the round factor.
   - **Mexico flat penalty** — replaced the Country weighted factor (which double-penalized Mexico) with a flat -10 for Mexico venues. Non-Mexico venues get +10 bonus.
   - **Buyer mode updated** — inverse piecewise deal curve + matchup factor + reduced Country to 5%.
   - **Semantic labels** — Hot (75+), Solid (55+), Fair (35+), Cold (<35) shown below score rings.
   - **Updated thresholds** — score ring colors, table view colors, stats bar all use new 75/55/35 breakpoints.

9. **Deployed** — 2 atomic commits (backend scoring + frontend labels) pushed to main, deployed to Vercel.

### Current State
- **Live:** https://ticket-reseller.vercel.app
- **Default view:** Only matches with at least one platform listing shown
- **Scoring:** 6-factor system with semantic labels (Hot/Solid/Fair/Cold), wider score distribution
- **Filter UX:** Renamed label, show-all link, mobile badge, smart empty state
- **GitHub:** up to date with 3 new commits today

### Next Steps
- Telegram bot for price drop alerts
- Best deals view (ranked by cross-platform price gap / recent drops)
- "When to Buy" analysis from historical price data
- Consider SeatGeek API for 4th platform
- Affiliate links for monetization
