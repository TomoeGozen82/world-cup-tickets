# StubHub Playwright Scraper — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add StubHub as a 3rd ticket price comparison platform using Playwright headless browser to scrape JS-rendered pages.

**Architecture:** New `collector/stubhub.py` using Playwright sync API, shared matching module extracted from existing scrapers, error isolation in `scrape.py`, dashboard updated for 3-platform display.

**Tech Stack:** Python 3.12, Playwright (sync API), Turso/libsql, GitHub Actions

**Spec:** `docs/superpowers/specs/2026-03-21-stubhub-playwright-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `collector/matching.py` | **Create** | Shared team-name matching: normalize, aliases, match-to-DB |
| `collector/stubhub.py` | **Create** | Playwright-based StubHub scraper |
| `collector/seatgeek.py` | **Modify** | Import from `matching.py`, remove inline matching functions |
| `collector/tickpick.py` | **Modify** | Import from `matching.py`, remove inline matching |
| `scripts/scrape.py` | **Modify** | Add StubHub, wrap collectors in try/except |
| `pyproject.toml` | **Modify** | Add `playwright>=1.40` dependency |
| `.github/workflows/scrape.yml` | **Modify** | Add Playwright browser install step |
| `public/index.html` | **Modify** | Add StubHub platform card + 3-column grid |
| `CLAUDE.md` | **Modify** | Update architecture docs |

---

## Chunk 1: Shared Matching Module + Dependency Setup

### Task 1: Add Playwright dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add playwright to pyproject.toml**

In `pyproject.toml`, add `"playwright>=1.40"` to the `dependencies` list:

```toml
dependencies = [
    "fastapi>=0.135.1",
    "feedparser>=6.0.12",
    "httpx>=0.28.1",
    "libsql-experimental>=0.0.55",
    "playwright>=1.40",
]
```

- [ ] **Step 2: Run uv sync**

Run: `cd /mnt/c/Users/jwtre/Desktop/Project/Claude\ Code/ticket-reseller && uv sync`
Expected: Resolves and installs playwright package successfully.

- [ ] **Step 3: Install Chromium browser**

Run: `uv run playwright install chromium`
Expected: Downloads Chromium binary (~150MB). Prints install path.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "Add playwright dependency for headless browser scraping"
```

---

### Task 2: Extract shared matching module

**Files:**
- Create: `collector/matching.py`
- Modify: `collector/seatgeek.py` (lines 187-249 — matching functions)
- Modify: `collector/tickpick.py` (lines 61-76 — matching function)

- [ ] **Step 1: Create `collector/matching.py`**

Extract from `seatgeek.py` and generalize. This module provides all team-name matching logic used by all 3 scrapers:

```python
"""Shared team-name matching utilities for all ticket scrapers."""

import logging

log = logging.getLogger(__name__)

# Map fixture team names to how they appear on ticket sites
TEAM_ALIASES = {
    "korea republic": ["korea", "south korea"],
    "ir iran": ["iran"],
    "côte d'ivoire": ["ivory coast", "cote d'ivoire", "cote divoire"],
    "cabo verde": ["cape verde"],
    "curaçao": ["curacao"],
    "united states": ["usa", "u.s."],
}


def normalize_name(name: str) -> str:
    """Simplify team/event name for fuzzy matching."""
    name = name.lower().strip()
    for s in [
        " mens national soccer", " national soccer", " national football",
        " national team", " men's", " women's",
    ]:
        name = name.replace(s, "")
    return name


def team_in_event_name(team: str, event_name: str) -> bool:
    """Check if a team name (or any of its aliases) appears in the event name."""
    team_lower = team.lower()
    if team_lower in event_name:
        return True
    aliases = TEAM_ALIASES.get(team_lower, [])
    return any(alias in event_name for alias in aliases)


def match_event_to_db(
    event_name: str,
    event_date: str | None,
    db_matches: list[dict],
    *,
    require_date: bool = False,
    require_both_teams: bool = True,
    skip_mapped: bool = False,
) -> dict | None:
    """Match a scraped event to a DB match by team names.

    Args:
        event_name: The event title from the ticket site.
        event_date: The event date (YYYY-MM-DD) or None.
        db_matches: List of match dicts from the database.
        require_date: If True, date must match (used by TickPick).
        require_both_teams: If True, both teams must appear in event name
            (or one team + TBD). If False, a single team match is enough
            (TickPick uses this since it also requires date matching).
        skip_mapped: If True, skip matches that already have a seatgeek_id.
    """
    ev_name = normalize_name(event_name)
    ev_date = (event_date or "")[:10]

    for m in db_matches:
        if skip_mapped and m.get("seatgeek_id"):
            continue

        if require_date:
            db_date = (m.get("match_date") or "")[:10]
            if not db_date or db_date != ev_date:
                continue

        home = (m.get("home_team") or "").strip()
        away = (m.get("away_team") or "").strip()

        if not home or not away:
            continue

        home_match = home != "TBD" and team_in_event_name(home, ev_name)
        away_match = away != "TBD" and team_in_event_name(away, ev_name)

        if require_both_teams:
            # Both teams must match, or one team matches and the other is TBD
            if home_match and away_match:
                return m
            if home_match and away == "TBD":
                return m
            if away_match and home == "TBD":
                return m
        else:
            # Single team match is sufficient (when date is also required)
            if home_match or away_match:
                return m

    return None
```

- [ ] **Step 2: Refactor `collector/seatgeek.py` to use `matching.py`**

Remove the following functions/constants from `seatgeek.py`:
- `_normalize_name()` (lines 187-196)
- `TEAM_ALIASES` (lines 200-207)
- `_team_in_event_name()` (lines 210-216)
- `_match_to_db()` (lines 219-249)

Replace with imports and update the call site:

At the top of the file, add:
```python
from collector.matching import match_event_to_db
```

In `discover()` (line 270), change:
```python
match = _match_to_db(data, db_matches)
```
to:
```python
match = match_event_to_db(
    event_name=data.get("name", ""),
    event_date=data.get("start_date"),
    db_matches=db_matches,
    skip_mapped=True,
)
```

- [ ] **Step 3: Refactor `collector/tickpick.py` to use `matching.py`**

Remove `_match_event_to_db()` (lines 61-76).

At the top of the file, add:
```python
from collector.matching import match_event_to_db
```

In `collect()` (line 96), change:
```python
match = _match_event_to_db(event, db_matches)
```
to:
```python
match = match_event_to_db(
    event_name=event.get("name", ""),
    event_date=event.get("start_date"),
    db_matches=db_matches,
    require_date=True,
    require_both_teams=False,  # Preserve original behavior: single team + date is enough
)
```

- [ ] **Step 4: Test that existing scrapers still work**

Run: `cd /mnt/c/Users/jwtre/Desktop/Project/Claude\ Code/ticket-reseller && uv run python -c "from collector import seatgeek, tickpick; print('imports OK')"`
Expected: `imports OK`

Verify matching logic is correct by running a quick smoke test:
```bash
uv run python -c "
from collector.matching import match_event_to_db
matches = [{'home_team': 'United States', 'away_team': 'Mexico', 'match_date': '2026-06-15', 'id': 1}]
result = match_event_to_db('USA vs Mexico - FIFA World Cup', '2026-06-15', matches, require_date=True)
print(f'Matched: {result is not None}')  # Should be True (alias: USA -> United States)
"
```
Expected: `Matched: True`

- [ ] **Step 5: Commit**

```bash
git add collector/matching.py collector/seatgeek.py collector/tickpick.py
git commit -m "Extract shared team-name matching into collector/matching.py"
```

---

### Task 3: Add error isolation to `scrape.py`

**Files:**
- Modify: `scripts/scrape.py`

- [ ] **Step 1: Wrap each collector in try/except**

Replace the current `scrape.py` contents with:

```python
"""Standalone scraper entry point for GitHub Actions."""

import logging
import sys

sys.path.insert(0, ".")

import db.database as db
from collector import fixtures, seatgeek, tickpick
from analysis.value import score_all_matches

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

db.init_db()

n = fixtures.collect()
log.info(f"Seeded {n} fixtures")

score_all_matches()

for name, collect_fn in [
    ("Vivid Seats", seatgeek.collect),
    ("TickPick", tickpick.collect),
]:
    try:
        n = collect_fn()
        log.info(f"{name}: {n} updates")
    except Exception:
        log.exception(f"{name}: scraper failed, continuing")

score_all_matches()
log.info("Done — all scores recalculated")
```

Note: StubHub will be added to this loop in Task 4.

- [ ] **Step 2: Verify scrape.py still runs (dry import check)**

Run: `uv run python -c "import scripts.scrape; print('nope')" 2>&1 || echo "expected — scrape.py runs on import"`

This will attempt to run the scraper (which needs Turso env vars). Just verify no syntax errors:
Run: `uv run python -c "import ast; ast.parse(open('scripts/scrape.py').read()); print('syntax OK')"`
Expected: `syntax OK`

- [ ] **Step 3: Commit**

```bash
git add scripts/scrape.py
git commit -m "Add error isolation: wrap each collector in try/except"
```

---

## Chunk 2: StubHub Scraper

### Task 4: Create StubHub Playwright scraper

**Files:**
- Create: `collector/stubhub.py`
- Modify: `scripts/scrape.py`

- [ ] **Step 1: Research StubHub's World Cup page structure**

Before writing the scraper, manually inspect StubHub to determine the discovery strategy. Use Playwright to load StubHub and examine what's available:

```python
# Run interactively to investigate page structure
uv run python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        viewport={'width': 1280, 'height': 800},
    )
    # Try category/search URLs
    for url in [
        'https://www.stubhub.com/fifa-world-cup-tickets/grouping/460981/',
        'https://www.stubhub.com/secure/search?q=FIFA+World+Cup+2026',
    ]:
        print(f'Trying: {url}')
        resp = page.goto(url, wait_until='domcontentloaded', timeout=20000)
        print(f'Status: {resp.status if resp else \"no response\"}')
        print(f'Title: {page.title()}')
        # Check for event links
        links = page.query_selector_all('a[href*=\"/event/\"]') or page.query_selector_all('a[href*=\"tickets\"]')
        print(f'Event links found: {len(links)}')
        if links:
            for link in links[:3]:
                print(f'  {link.get_attribute(\"href\")}')
    browser.close()
"
```

Use the results to determine:
- Which URL pattern lists World Cup events
- What CSS selectors find event links
- What CSS selectors find prices on event pages

Document findings as comments in the scraper code.

- [ ] **Step 2: Create `collector/stubhub.py`**

The exact selectors will depend on Step 1's findings. The structure below uses placeholder selectors marked with `# SELECTOR:` comments — replace with actual selectors from Step 1:

```python
"""Scrape resale ticket prices from StubHub using Playwright (headless browser).

StubHub renders listings via JavaScript SPA, so we need a real browser
to execute JS and extract prices from the rendered DOM.
"""

import logging
import random
import time

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from collector.matching import match_event_to_db
from db.database import get_all_matches, upsert_platform_price

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# SELECTOR: Update these after Step 1 research
SEARCH_URL = "https://www.stubhub.com/secure/search?q=FIFA+World+Cup+2026"
EVENT_LINK_SELECTOR = 'a[href*="/event/"]'  # Links to individual event pages
PRICE_SELECTOR = '[data-testid="listing-price"]'  # Price elements on event page
EVENT_TITLE_SELECTOR = 'h1'  # Event title on event page


def _block_unnecessary_resources(route):
    """Abort requests for images, CSS, fonts, media to speed up page loads."""
    if route.request.resource_type in ("image", "stylesheet", "font", "media"):
        route.abort()
    else:
        route.fallback()


def _random_delay(min_sec: float = 2.0, max_sec: float = 5.0):
    """Sleep for a random duration to avoid bot detection."""
    time.sleep(random.uniform(min_sec, max_sec))


def _discover_events(page) -> list[dict]:
    """Load StubHub search/category page and extract event URLs."""
    try:
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector(EVENT_LINK_SELECTOR, timeout=15000)
    except PlaywrightTimeout:
        log.warning("[stubhub] Search page timed out or no events found")
        return []

    links = page.query_selector_all(EVENT_LINK_SELECTOR)
    events = []
    seen = set()

    for link in links:
        href = link.get_attribute("href") or ""
        if not href or href in seen:
            continue
        # Make absolute URL if relative
        if href.startswith("/"):
            href = f"https://www.stubhub.com{href}"

        text = link.inner_text().strip()
        seen.add(href)
        events.append({"url": href, "name": text})

    log.info(f"[stubhub] Found {len(events)} event links")
    return events


def _scrape_event_price(page, url: str) -> dict | None:
    """Navigate to an event page and extract the lowest price."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_selector(PRICE_SELECTOR, timeout=15000)
    except PlaywrightTimeout:
        log.warning(f"[stubhub] Timed out loading {url}")
        return None
    except Exception as e:
        log.warning(f"[stubhub] Failed to load {url}: {e}")
        return None

    # Extract event title
    title_el = page.query_selector(EVENT_TITLE_SELECTOR)
    title = title_el.inner_text().strip() if title_el else ""

    # Extract all visible prices
    price_elements = page.query_selector_all(PRICE_SELECTOR)
    prices = []
    for el in price_elements:
        text = el.inner_text().strip()
        # Parse "$1,234" or "1234" format
        cleaned = text.replace("$", "").replace(",", "").strip()
        try:
            prices.append(int(float(cleaned)))
        except ValueError:
            continue

    if not prices:
        log.debug(f"[stubhub] No prices found on {url}")
        return None

    prices.sort()
    return {
        "name": title,
        "lowest": prices[0],
        "highest": prices[-1] if len(prices) > 1 else None,
        "url": url,
    }


def collect() -> int:
    """Scrape StubHub for World Cup ticket prices using Playwright."""
    db_matches = get_all_matches()
    updated = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.route("**/*", _block_unnecessary_resources)

        # Discover events
        events = _discover_events(page)
        if not events:
            browser.close()
            return 0

        # Scrape each event
        for event in events:
            _random_delay()

            data = _scrape_event_price(page, event["url"])
            if not data:
                continue

            # Use event name from the detail page if available, else from listing
            name = data["name"] or event.get("name", "")
            match = match_event_to_db(
                event_name=name,
                event_date=None,  # StubHub may not expose date in a parseable way
                db_matches=db_matches,
            )
            if not match:
                continue

            upsert_platform_price(
                match_id=match["id"],
                platform="stubhub",
                lowest=data["lowest"],
                median=data["lowest"],  # Same workaround as TickPick
                highest=data["highest"],
                listing_count=0,
                listing_url=data["url"],
                is_transferable="unknown",
            )
            updated += 1

        browser.close()

    log.info(f"[stubhub] Updated prices for {updated} matches")
    return updated
```

- [ ] **Step 3: Add StubHub to `scrape.py`**

Add the import and add StubHub to the collector loop:

At the top, change:
```python
from collector import fixtures, seatgeek, tickpick
```
to:
```python
from collector import fixtures, seatgeek, stubhub, tickpick
```

In the collector loop, add StubHub:
```python
for name, collect_fn in [
    ("Vivid Seats", seatgeek.collect),
    ("TickPick", tickpick.collect),
    ("StubHub", stubhub.collect),
]:
```

- [ ] **Step 4: Verify imports work**

Run: `uv run python -c "from collector import stubhub; print('import OK')"`
Expected: `import OK`

Run: `uv run python -c "import ast; ast.parse(open('scripts/scrape.py').read()); print('syntax OK')"`
Expected: `syntax OK`

- [ ] **Step 5: Test scraper locally (if Turso env vars available)**

Run:
```bash
TURSO_DATABASE_URL=... TURSO_AUTH_TOKEN=... uv run python -c "
from collector import stubhub
n = stubhub.collect()
print(f'StubHub: {n} matches updated')
"
```

If StubHub blocks the request, you'll see timeout warnings in the logs — this is expected and gracefully handled. The important thing is that the scraper doesn't crash.

- [ ] **Step 6: Commit**

```bash
git add collector/stubhub.py scripts/scrape.py
git commit -m "Add StubHub scraper using Playwright headless browser"
```

---

## Chunk 3: GitHub Actions + Dashboard + Docs

### Task 5: Update GitHub Actions workflow

**Files:**
- Modify: `.github/workflows/scrape.yml`

- [ ] **Step 1: Add Playwright install step**

Add the browser install step between `uv sync` and `scrape.py`:

```yaml
name: Scrape ticket prices

on:
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --frozen
      - run: uv run playwright install --with-deps chromium
      - run: uv run python scripts/scrape.py
        env:
          TURSO_DATABASE_URL: ${{ secrets.TURSO_DATABASE_URL }}
          TURSO_AUTH_TOKEN: ${{ secrets.TURSO_AUTH_TOKEN }}
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/scrape.yml
git commit -m "Add Playwright browser install to GitHub Actions workflow"
```

---

### Task 6: Add StubHub to the dashboard

**Files:**
- Modify: `public/index.html` (lines 1270-1278 — PLATFORM_NAMES and PLATFORM_COLORS)
- Modify: `public/index.html` (lines 520-524 — .platform-cards grid)

- [ ] **Step 1: Add StubHub to platform name/color maps**

In `public/index.html`, find the `PLATFORM_NAMES` and `PLATFORM_COLORS` objects (~line 1270) and add StubHub:

```javascript
    const PLATFORM_NAMES = {
        vividseats: 'Vivid Seats',
        tickpick: 'TickPick',
        stubhub: 'StubHub',
    };

    const PLATFORM_COLORS = {
        vividseats: '#a855f7',
        tickpick: '#22c55e',
        stubhub: '#3b82f6',
    };
```

- [ ] **Step 2: Update grid to handle 3 platforms**

Find the `.platform-cards` CSS rule (~line 520) and change from fixed 2-column to auto-fit:

```css
        .platform-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
            gap: 0.45rem;
            margin-bottom: 0.65rem;
        }
```

This renders 2 columns when there are 2 platforms, 3 columns when there are 3 — no layout breakage.

- [ ] **Step 3: Test locally**

Open `public/index.html` in a browser (or use the Vercel dev server) and verify:
- Existing Vivid Seats + TickPick cards still render correctly
- If StubHub data exists, it shows as a 3rd blue card
- "BEST" tag correctly highlights the cheapest across all 3 platforms
- Layout doesn't break on mobile (cards stack or fit in 2-3 columns)

- [ ] **Step 4: Commit**

```bash
git add public/index.html
git commit -m "Add StubHub platform card to dashboard with 3-column grid"
```

---

### Task 7: Update documentation

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md**

In the Architecture section, add `collector/stubhub.py` and `collector/matching.py`:

```
collector/stubhub.py   — StubHub scraper (Playwright headless browser)
collector/matching.py  — Shared team-name matching utilities
```

In the Data Sources section, add:
```
- **StubHub** (Playwright headless scraping) — resale ticket prices, refreshes every 6h
```

In the Stack section, update to mention Playwright:
```
- FastAPI (Vercel serverless) + Turso (cloud SQLite) + GitHub Actions (scrapers) + Playwright (StubHub)
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "Update docs to include StubHub scraper and matching module"
```

---

### Task 8: Deploy and verify

- [ ] **Step 1: Deploy to Vercel**

Run: `cd /mnt/c/Users/jwtre/Desktop/Project/Claude\ Code/ticket-reseller && vercel --prod`

Note: Playwright is NOT needed on Vercel — it only runs in GitHub Actions. Vercel just serves the API + static dashboard.

- [ ] **Step 2: Trigger GitHub Actions scraper manually**

Run: `gh workflow run scrape.yml`

Check workflow status: `gh run list --workflow=scrape.yml --limit=1`

Wait for completion, then check logs: `gh run view <run-id> --log`

- [ ] **Step 3: Verify dashboard shows StubHub data**

Visit https://ticket-reseller.vercel.app and check:
- StubHub cards appear for matches that were scraped
- "BEST" tag highlights cheapest across all 3 platforms
- Cards are tappable and link to StubHub listing pages

- [ ] **Step 4: Commit any fixes from deploy testing**

If any fixes were needed, commit them individually.
