# Multi-Platform Price Comparison Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add StubHub and TickPick scrapers alongside Vivid Seats so the dashboard shows side-by-side pricing across 3 platforms.

**Architecture:** Each platform gets its own scraper module following the same pattern as `collector/seatgeek.py`. A new `platform_prices` table stores per-platform prices. The dashboard gets an updated resale section showing all 3 platforms with highlighted cheapest option.

**Tech Stack:** httpx (already installed), Playwright for JS-heavy pages (already installed), SQLite

---

### Task 1: Add platform_prices table to schema

**Files:**
- Modify: `db/schema.sql`
- Modify: `db/database.py`

**Step 1: Add new table to schema.sql**

Add after the `price_snapshots` table:

```sql
CREATE TABLE IF NOT EXISTS platform_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    platform TEXT NOT NULL,  -- 'vividseats', 'stubhub', 'tickpick'
    lowest_price INTEGER,
    median_price INTEGER,
    highest_price INTEGER,
    listing_count INTEGER DEFAULT 0,
    listing_url TEXT,
    is_transferable TEXT DEFAULT 'unknown',  -- 'yes', 'no', 'unknown'
    fetched_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (match_id) REFERENCES matches(id)
);
CREATE INDEX IF NOT EXISTS idx_platform_prices_match ON platform_prices(match_id, platform, fetched_at);
```

**Step 2: Add CRUD functions to database.py**

Add these functions:

```python
def upsert_platform_price(
    match_id: int,
    platform: str,
    lowest: int | None,
    median: int | None,
    highest: int | None,
    listing_count: int,
    listing_url: str | None,
    is_transferable: str = "unknown",
) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO platform_prices
                (match_id, platform, lowest_price, median_price, highest_price,
                 listing_count, listing_url, is_transferable)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (match_id, platform, lowest, median, highest,
             listing_count, listing_url, is_transferable),
        )


def get_latest_platform_prices(match_id: int) -> list[sqlite3.Row]:
    """Get the most recent price for each platform for a given match."""
    with get_conn() as conn:
        return conn.execute(
            """SELECT * FROM platform_prices
            WHERE id IN (
                SELECT MAX(id) FROM platform_prices
                WHERE match_id = ?
                GROUP BY platform
            )
            ORDER BY platform""",
            (match_id,),
        ).fetchall()


def get_all_latest_platform_prices() -> dict[int, list[dict]]:
    """Get latest prices per platform for ALL matches. Returns {match_id: [prices]}."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM platform_prices
            WHERE id IN (
                SELECT MAX(id) FROM platform_prices GROUP BY match_id, platform
            )
            ORDER BY match_id, platform"""
        ).fetchall()
    result = {}
    for row in rows:
        d = dict(row)
        result.setdefault(d["match_id"], []).append(d)
    return result
```

**Step 3: Run app to verify schema migration**

Run: `cd "/mnt/c/Users/jwtre/Desktop/Project/Claude Code/ticket-reseller/" && uv run python -c "import db.database as db; db.init_db(); print('Schema OK')"`
Expected: `Schema OK`

**Step 4: Commit**

```bash
git add db/schema.sql db/database.py
git commit -m "Add platform_prices table for multi-platform comparison"
```

---

### Task 2: Refactor Vivid Seats scraper to write to platform_prices

**Files:**
- Modify: `collector/seatgeek.py`

**Step 1: Add platform_prices writes alongside existing resale price updates**

In the `discover()` function, after the `update_resale_prices()` call (~line 249), add:

```python
from db.database import upsert_platform_price

upsert_platform_price(
    match_id=match["id"],
    platform="vividseats",
    lowest=data["lowest"],
    median=data["median"],
    highest=data["highest"],
    listing_count=0,
    listing_url=ev["url"],
)
```

Do the same in `collect_prices()` after the `update_resale_prices()` call (~line 297):

```python
upsert_platform_price(
    match_id=match_id,
    platform="vividseats",
    lowest=data["lowest"],
    median=data["median"],
    highest=data["highest"],
    listing_count=0,
    listing_url=url,
)
```

**Step 2: Run locally to verify it writes to new table**

Run: `cd "/mnt/c/Users/jwtre/Desktop/Project/Claude Code/ticket-reseller/" && uv run python -c "
import db.database as db
db.init_db()
# Verify table exists
with db.get_conn() as conn:
    conn.execute('SELECT COUNT(*) FROM platform_prices')
    print('platform_prices table accessible')
"`

**Step 3: Commit**

```bash
git add collector/seatgeek.py
git commit -m "Write Vivid Seats prices to platform_prices table"
```

---

### Task 3: Add StubHub scraper

**Files:**
- Create: `collector/stubhub.py`

**Step 1: Create StubHub scraper module**

StubHub uses structured data in their pages. The scraper should:
1. Search for "FIFA World Cup 2026" events
2. Parse event pages for pricing via JSON-LD or page JS
3. Match events to DB matches by date + team names
4. Write to `platform_prices` table

```python
"""Scrape resale ticket prices from StubHub."""

import json
import logging
import re
import time

import httpx

from db.database import get_all_matches, upsert_platform_price

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SEARCH_URL = "https://www.stubhub.com/find/s/?q=FIFA+World+Cup+2026"


def _parse_event_data(html: str) -> dict | None:
    """Extract event pricing from StubHub page data."""
    # StubHub embeds pricing in window.__data__ or JSON-LD
    for pattern in [
        r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
        r'"minPrice"\s*:\s*"?(\d+\.?\d*)',
    ]:
        m = re.search(pattern, html, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                if isinstance(data, list):
                    data = data[0]
                offers = data.get("offers", {})
                return {
                    "lowest": int(float(offers.get("lowPrice", 0))) or None,
                    "highest": int(float(offers.get("highPrice", 0))) or None,
                    "name": data.get("name", ""),
                    "start_date": (data.get("startDate") or "")[:10],
                    "venue": (data.get("location", {}).get("name", "")),
                }
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
    return None


def _discover_event_urls(client: httpx.Client) -> list[str]:
    """Find StubHub event URLs for World Cup matches."""
    try:
        resp = client.get(SEARCH_URL, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        log.error(f"[stubhub] Search failed: {e}")
        return []

    urls = set()
    for m in re.finditer(r'href="(https://www\.stubhub\.com/[^"]*world-cup[^"]*)"', resp.text, re.IGNORECASE):
        urls.add(m.group(1))
    # Also look for relative paths
    for m in re.finditer(r'href="(/[^"]*ticket[^"]*)"', resp.text):
        urls.add(f"https://www.stubhub.com{m.group(1)}")

    log.info(f"[stubhub] Found {len(urls)} event URLs")
    return list(urls)


def _match_event_to_db(event: dict, db_matches: list[dict]) -> dict | None:
    """Match a scraped event to a DB match by date + team name."""
    ev_date = event.get("start_date", "")[:10]
    ev_name = event.get("name", "").lower()

    for m in db_matches:
        db_date = (m.get("match_date") or "")[:10]
        if not db_date or db_date != ev_date:
            continue
        home = (m.get("home_team") or "").lower()
        away = (m.get("away_team") or "").lower()
        if home and home != "tbd" and home in ev_name:
            return m
        if away and away != "tbd" and away in ev_name:
            return m
    return None


def collect() -> int:
    """Scrape StubHub for World Cup ticket prices."""
    db_matches = [dict(m) for m in get_all_matches()]
    updated = 0

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        urls = _discover_event_urls(client)

        for url in urls:
            time.sleep(1.5)  # rate limit
            try:
                resp = client.get(url, timeout=15)
                resp.raise_for_status()
            except Exception as e:
                log.warning(f"[stubhub] Failed {url}: {e}")
                continue

            event = _parse_event_data(resp.text)
            if not event or not event.get("lowest"):
                continue

            match = _match_event_to_db(event, db_matches)
            if not match:
                continue

            upsert_platform_price(
                match_id=match["id"],
                platform="stubhub",
                lowest=event["lowest"],
                median=event.get("lowest"),  # StubHub doesn't expose median easily
                highest=event.get("highest"),
                listing_count=0,
                listing_url=url,
            )
            updated += 1

    log.info(f"[stubhub] Updated prices for {updated} matches")
    return updated
```

**Step 2: Commit**

```bash
git add collector/stubhub.py
git commit -m "Add StubHub scraper for multi-platform comparison"
```

---

### Task 4: Add TickPick scraper

**Files:**
- Create: `collector/tickpick.py`

**Step 1: Create TickPick scraper module**

TickPick is known for no buyer fees. Their pages also embed JSON-LD data.

```python
"""Scrape resale ticket prices from TickPick (no buyer fees)."""

import json
import logging
import re
import time

import httpx

from db.database import get_all_matches, upsert_platform_price

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SEARCH_URL = "https://www.tickpick.com/search?q=FIFA+World+Cup+2026"


def _parse_event_data(html: str) -> dict | None:
    """Extract event pricing from TickPick page."""
    for m in re.finditer(
        r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
        html, re.DOTALL,
    ):
        try:
            data = json.loads(m.group(1))
            if isinstance(data, list):
                data = data[0]
            offers = data.get("offers", {})
            if offers.get("lowPrice"):
                return {
                    "lowest": int(float(offers["lowPrice"])),
                    "highest": int(float(offers.get("highPrice", 0))) or None,
                    "name": data.get("name", ""),
                    "start_date": (data.get("startDate") or "")[:10],
                    "venue": (data.get("location", {}).get("name", "")),
                }
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    return None


def _discover_event_urls(client: httpx.Client) -> list[str]:
    """Find TickPick event URLs for World Cup matches."""
    try:
        resp = client.get(SEARCH_URL, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        log.error(f"[tickpick] Search failed: {e}")
        return []

    urls = set()
    for m in re.finditer(r'href="(https://www\.tickpick\.com/[^"]*(?:world-cup|fifa)[^"]*)"', resp.text, re.IGNORECASE):
        urls.add(m.group(1))
    for m in re.finditer(r'href="(/buy/[^"]*)"', resp.text):
        urls.add(f"https://www.tickpick.com{m.group(1)}")

    log.info(f"[tickpick] Found {len(urls)} event URLs")
    return list(urls)


def _match_event_to_db(event: dict, db_matches: list[dict]) -> dict | None:
    """Match a scraped event to a DB match by date + team name."""
    ev_date = event.get("start_date", "")[:10]
    ev_name = event.get("name", "").lower()

    for m in db_matches:
        db_date = (m.get("match_date") or "")[:10]
        if not db_date or db_date != ev_date:
            continue
        home = (m.get("home_team") or "").lower()
        away = (m.get("away_team") or "").lower()
        if home and home != "tbd" and home in ev_name:
            return m
        if away and away != "tbd" and away in ev_name:
            return m
    return None


def collect() -> int:
    """Scrape TickPick for World Cup ticket prices."""
    db_matches = [dict(m) for m in get_all_matches()]
    updated = 0

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        urls = _discover_event_urls(client)

        for url in urls:
            time.sleep(1.5)
            try:
                resp = client.get(url, timeout=15)
                resp.raise_for_status()
            except Exception as e:
                log.warning(f"[tickpick] Failed {url}: {e}")
                continue

            event = _parse_event_data(resp.text)
            if not event or not event.get("lowest"):
                continue

            match = _match_event_to_db(event, db_matches)
            if not match:
                continue

            upsert_platform_price(
                match_id=match["id"],
                platform="tickpick",
                lowest=event["lowest"],
                median=event["lowest"],  # TickPick shows BIN price, use as median
                highest=event.get("highest"),
                listing_count=0,
                listing_url=url,
                is_transferable="yes",  # TickPick guarantees transferable
            )
            updated += 1

    log.info(f"[tickpick] Updated prices for {updated} matches")
    return updated
```

**Step 2: Commit**

```bash
git add collector/tickpick.py
git commit -m "Add TickPick scraper for multi-platform comparison"
```

---

### Task 5: Wire new scrapers into scheduler

**Files:**
- Modify: `main.py`

**Step 1: Import and schedule new scrapers**

Add imports at top of main.py:

```python
from collector import stubhub, tickpick
```

Add collection functions:

```python
def _collect_stubhub():
    n = stubhub.collect()
    log.info(f"[scheduler] stubhub: {n} updates")


def _collect_tickpick():
    n = tickpick.collect()
    log.info(f"[scheduler] tickpick: {n} updates")
```

Update `_run_all()` to include new scrapers:

```python
def _run_all():
    _collect_news()
    _collect_reddit()
    _collect_resale()
    _collect_stubhub()
    _collect_tickpick()
```

Add scheduler jobs in `lifespan()`, after the existing scheduler jobs:

```python
scheduler.add_job(_collect_stubhub, trigger="interval", hours=RESALE_POLL_HOURS, id="stubhub", replace_existing=True)
scheduler.add_job(_collect_tickpick, trigger="interval", hours=RESALE_POLL_HOURS, id="tickpick", replace_existing=True)
```

**Step 2: Add API endpoint for platform prices**

Add to main.py API routes:

```python
@app.get("/api/platform-prices")
def get_platform_prices():
    """Get latest prices from all platforms for all matches."""
    return db.get_all_latest_platform_prices()


@app.get("/api/platform-prices/{match_id}")
def get_match_platform_prices(match_id: int):
    """Get latest prices from all platforms for a specific match."""
    rows = db.get_latest_platform_prices(match_id)
    return [dict(r) for r in rows]
```

**Step 3: Include platform prices in the matches API response**

In `get_matches()` and `get_scores()`, add platform prices:

```python
# After scoring, add platform prices
all_platform_prices = db.get_all_latest_platform_prices()
for m in matches:
    m["platform_prices"] = all_platform_prices.get(m["id"], [])
```

**Step 4: Commit**

```bash
git add main.py
git commit -m "Wire StubHub and TickPick scrapers into scheduler and API"
```

---

### Task 6: Update dashboard to show multi-platform comparison

**Files:**
- Modify: `viewer/static/index.html`

**Step 1: Update renderResaleSection to show per-platform prices**

Replace the `renderResaleSection()` function with a version that shows all platforms:

```javascript
function renderResaleSection(m) {
    // Legacy single-source display if no platform data
    const platforms = m.platform_prices || [];

    if (!platforms.length && !m.resale_lowest && !m.resale_median) return '';

    // If we have platform data, show multi-platform view
    if (platforms.length > 0) {
        return renderMultiPlatformPrices(m, platforms);
    }

    // Fallback to legacy single-source
    const face = m.face_value_cat3 || 100;
    const median = m.resale_median || 0;
    const markupPct = Math.round(((median - face) / face) * 100);
    const markupClass = markupPct >= 0 ? 'up' : 'down';
    const markupArrow = markupPct >= 0 ? '↑' : '↓';

    return `
        <div class="resale-section">
            <div class="resale-header">
                <span class="resale-label">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--gold-dim)" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
                    Resale Market
                </span>
                <span class="markup-badge ${markupClass}">${markupArrow} ${Math.abs(markupPct)}% vs face</span>
            </div>
            <div class="resale-row">
                <div class="resale-cell">
                    <div class="price-label">Low</div>
                    <div class="price-value">$${m.resale_lowest || '—'}</div>
                </div>
                <div class="resale-cell">
                    <div class="price-label">Median</div>
                    <div class="price-value">$${m.resale_median || '—'}</div>
                </div>
                <div class="resale-cell">
                    <div class="price-label">High</div>
                    <div class="price-value">$${m.resale_highest || '—'}</div>
                </div>
            </div>
        </div>`;
}

const PLATFORM_NAMES = {
    vividseats: 'Vivid Seats',
    stubhub: 'StubHub',
    tickpick: 'TickPick',
};

const PLATFORM_COLORS = {
    vividseats: '#a855f7',
    stubhub: '#3b82f6',
    tickpick: '#22c55e',
};

function renderMultiPlatformPrices(m, platforms) {
    // Find cheapest across platforms
    const withPrices = platforms.filter(p => p.lowest_price);
    const cheapest = withPrices.length
        ? withPrices.reduce((a, b) => (a.lowest_price < b.lowest_price ? a : b))
        : null;

    const rows = platforms.map(p => {
        const isCheapest = cheapest && p.platform === cheapest.platform;
        const transferIcon = p.is_transferable === 'yes'
            ? '<span title="Transferable" style="color:#4ade80">✓</span>'
            : p.is_transferable === 'no'
            ? '<span title="Non-transferable" style="color:#f87171">✗</span>'
            : '';

        return `
            <div class="platform-row${isCheapest ? ' cheapest' : ''}">
                <div class="platform-name">
                    <span class="platform-dot" style="background:${PLATFORM_COLORS[p.platform] || '#6b7280'}"></span>
                    ${PLATFORM_NAMES[p.platform] || p.platform}
                    ${transferIcon}
                    ${isCheapest ? '<span class="best-price-tag">BEST</span>' : ''}
                </div>
                <div class="platform-prices">
                    <span class="platform-price">$${p.lowest_price || '—'}</span>
                    ${p.listing_url ? `<a href="${p.listing_url}" target="_blank" rel="noopener" class="platform-link">→</a>` : ''}
                </div>
            </div>`;
    }).join('');

    return `
        <div class="resale-section">
            <div class="resale-header">
                <span class="resale-label">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--gold-dim)" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
                    Resale Comparison
                </span>
            </div>
            <div class="platform-comparison">
                ${rows}
            </div>
        </div>`;
}
```

**Step 2: Add CSS for multi-platform display**

Add these styles inside the `<style>` block:

```css
/* ── Multi-Platform Comparison ── */
.platform-comparison {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
}
.platform-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.45rem 0.65rem;
    background: rgba(255,255,255,0.03);
    border-radius: 6px;
    border: 1px solid rgba(255,255,255,0.04);
    transition: border-color 0.2s;
}
.platform-row.cheapest {
    border-color: rgba(34,197,94,0.3);
    background: rgba(34,197,94,0.06);
}
.platform-name {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--text-secondary);
}
.platform-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
}
.best-price-tag {
    font-size: 0.58rem;
    font-weight: 700;
    color: #4ade80;
    background: rgba(34,197,94,0.15);
    padding: 0.08rem 0.35rem;
    border-radius: 3px;
    letter-spacing: 0.04em;
}
.platform-prices {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.platform-price {
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    font-size: 0.88rem;
    color: var(--gold);
}
.platform-link {
    color: var(--text-muted);
    text-decoration: none;
    font-size: 0.85rem;
    transition: color 0.2s;
}
.platform-link:hover { color: var(--gold); }
```

**Step 3: Commit**

```bash
git add viewer/static/index.html
git commit -m "Add multi-platform price comparison UI to match cards"
```

---

### Task 7: Push to GitHub and deploy to VPS

**Step 1: Push all commits**

```bash
git push origin main
```

**Step 2: Deploy to VPS**

Copy updated files and restart container:

```bash
# Copy files to VPS
scp db/schema.sql db/database.py collector/stubhub.py collector/tickpick.py collector/seatgeek.py main.py viewer/static/index.html root@187.77.7.89:/tmp/wc-update/

# Copy into container
ssh root@187.77.7.89 "
  for f in schema.sql database.py; do docker cp /tmp/wc-update/\$f world-cup-tickets:/app/db/\$f; done
  for f in stubhub.py tickpick.py seatgeek.py; do docker cp /tmp/wc-update/\$f world-cup-tickets:/app/collector/\$f; done
  docker cp /tmp/wc-update/main.py world-cup-tickets:/app/main.py
  docker cp /tmp/wc-update/index.html world-cup-tickets:/app/viewer/static/index.html
  docker restart world-cup-tickets
"
```

**Step 3: Verify deployment**

Check: `https://tickets.duchessnikki.com` — match cards should show multi-platform pricing once scrapers run.

**Step 4: Commit any deployment config changes**

---

## Summary of Changes

| File | Action | Purpose |
|---|---|---|
| `db/schema.sql` | Modify | Add `platform_prices` table |
| `db/database.py` | Modify | CRUD for platform prices |
| `collector/seatgeek.py` | Modify | Also write to `platform_prices` |
| `collector/stubhub.py` | Create | StubHub scraper |
| `collector/tickpick.py` | Create | TickPick scraper |
| `main.py` | Modify | Wire scrapers + new API endpoints |
| `viewer/static/index.html` | Modify | Multi-platform comparison UI |

## Important Notes

- **Rate limiting**: All scrapers use 1-1.5s delays between requests. If any site blocks, the scraper logs the error and moves on.
- **Scraper fragility**: Web scraping is inherently fragile. If a site changes its HTML structure, the relevant `_parse_event_data()` function needs updating. The JSON-LD approach is the most stable.
- **TickPick has no buyer fees**: This is a key selling point — their listed price IS the final price. The dashboard should note this.
- **Transferability**: TickPick guarantees transferable tickets. StubHub and Vivid Seats vary — the `is_transferable` field defaults to "unknown" and shows a warning icon.
