# StubHub Playwright Scraper — Design Spec

## Goal

Add StubHub as a 3rd price comparison platform alongside Vivid Seats and TickPick. StubHub renders ticket listings via JavaScript SPA, so we need Playwright (headless Chromium) instead of httpx.

## Data Collected

Same as existing scrapers — cheapest ticket price per match:
- `lowest_price` (cheapest available listing)
- `highest_price` (if available)
- `listing_url` (link to buy on StubHub)
- `is_transferable` (StubHub default: "unknown" — research during implementation)

## Architecture

### New file: `collector/stubhub.py`

Follows the same pattern as `collector/seatgeek.py` (Vivid Seats) and `collector/tickpick.py`:

```
collect() -> int
    1. Launch headless Chromium via Playwright
    2. Discover World Cup events (category page or per-team search — determined during implementation based on StubHub's site structure)
    3. For each event page:
       a. Navigate and wait for price elements to render
       b. Extract lowest/highest price from the DOM
       c. Match to a DB match using team-name matching (reuse logic from seatgeek.py)
       d. Call upsert_platform_price(platform="stubhub", ...)
    4. Close browser
    5. Return count of updated matches
```

### Browser resource optimization

- Block image, CSS, font, and media requests via `page.route()` — reduces bandwidth and page load time by 30-50%
- Use a single browser instance with one context for the entire scrape run
- Set realistic viewport (1280x800) and user agent

### Anti-bot strategy (start simple)

- `headless=True` with a realistic Chrome user agent string
- Random delays between page loads (2-5 seconds)
- Block unnecessary resources to reduce fingerprint surface
- Graceful failure: if a page times out or returns a CAPTCHA/block page, log warning and skip — don't crash the entire scrape run
- No proxies or stealth plugins in v1 — add later if blocking becomes a problem

### Event-to-match matching

Reuse the team-name matching approach from `seatgeek.py`:
- Normalize event names (lowercase, strip suffixes)
- Check if both team names appear in the event title
- Use `TEAM_ALIASES` dict for alternate spellings (e.g., "Korea Republic" -> "Korea", "South Korea")
- Require both teams to match (or one team + TBD opponent)

## Files Changed

| File | Change |
|---|---|
| `collector/stubhub.py` | **New** — Playwright-based StubHub scraper |
| `scripts/scrape.py` | Add `from collector import stubhub` and `stubhub.collect()` call |
| `.github/workflows/scrape.yml` | Add `playwright install --with-deps chromium` step after `uv sync` |
| `pyproject.toml` | Add `playwright` to dependencies |
| `public/index.html` | Add StubHub as a 3rd platform card in the dashboard |
| `CLAUDE.md` | Update architecture section to include StubHub |

## GitHub Actions Workflow Changes

Current workflow:
```yaml
steps:
  - uses: actions/checkout@v4
  - uses: astral-sh/setup-uv@v4
  - run: uv sync --frozen
  - run: uv run python scripts/scrape.py
```

Updated workflow adds one step:
```yaml
steps:
  - uses: actions/checkout@v4
  - uses: astral-sh/setup-uv@v4
  - run: uv sync --frozen
  - run: uv run playwright install --with-deps chromium
  - run: uv run python scripts/scrape.py
```

### Performance impact

- `playwright install --with-deps chromium`: ~30s download + system deps
- Each StubHub page load: 5-15s (JS rendering + delays)
- Estimated total for ~50-100 events: 5-15 minutes
- Well within GHA free tier (2,000 min/month) and per-job timeout (6 hours)

## Dashboard Changes

`public/index.html` updates:
- Add "StubHub" to the platform card rendering logic
- StubHub cards appear alongside Vivid Seats and TickPick cards
- Grid adjusts from 2-column to 3-column layout for matches with all 3 platforms
- "BEST" tag logic already compares all platforms — StubHub automatically participates

## What This Does NOT Include

- Residential proxies or stealth plugins (add later if needed)
- Individual listing data (sections, rows, seat numbers)
- SeatGeek API integration (separate effort)
- Headless scraping for other blocked platforms (Gametime, ViaGoGo)

## Risks

1. **StubHub blocks headless Chrome** — Mitigation: graceful failure, log and skip. If persistent, add residential proxy as a follow-up.
2. **StubHub DOM structure changes** — Mitigation: selectors will need maintenance. Use data attributes or stable class names where possible.
3. **Slower scrape runs** — Mitigation: Playwright adds minutes, not hours. GHA has plenty of headroom.
4. **StubHub URL/search structure unclear** — Mitigation: discovery approach (category vs per-team) will be determined during implementation by testing what StubHub's site actually exposes.
