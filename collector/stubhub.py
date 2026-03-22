"""Scrape resale ticket prices from StubHub using Playwright (headless browser).

StubHub renders listings via JavaScript SPA, so we need a real browser
to execute JS and extract prices from the rendered DOM.

Research findings (2026-03-21):
- Category page: https://www.stubhub.com/world-cup-tickets/grouping/45410
  Returns 200 with a JSON-LD <script> block containing an @graph array of
  SportsEvent objects, each with an AggregateOffer that includes lowPrice.
  This mirrors the TickPick strategy: one page load gives all events + prices.
- Event page: each event also embeds JSON-LD with lowPrice and a [data-price]
  DOM attribute on listing cards, but the category page is sufficient.
- Blocking: AWS WAF challenge fires on search URLs (/secure/search?) but the
  grouping/category page loads without triggering it in headless Firefox.
- Browser: Playwright Firefox only (Chromium headless-shell missing libnspr4
  on this host; Firefox only needs libasound2 which can be stubbed in CI).
"""

import json
import logging
import re

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from collector.matching import match_event_to_db
from db.database import get_all_matches, upsert_platform_price

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# Grouping page — single load gives all World Cup events with prices via JSON-LD
CATEGORY_URL = "https://www.stubhub.com/world-cup-tickets/grouping/45410"

# Fallback URL if grouping redirects
FALLBACK_URL = "https://www.stubhub.com/soccer-world-cup-tickets/"


def _parse_events_from_html(html: str) -> list[dict]:
    """Extract SportsEvent entries from the JSON-LD @graph block on the category page.

    The page embeds a script tag with type=application/ld+json whose content is
    a dict with key '@graph' containing a list of SportsEvent objects.  Each has:
        name       — "Team A vs Team B - World Cup - Group X (Match N)"
        offers     — AggregateOffer with lowPrice (float, USD, fees included)
        url        — canonical StubHub event URL
        startDate  — ISO-8601 datetime string
    """
    events = []
    for raw in re.finditer(
        r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    ):
        try:
            data = json.loads(raw.group(1).strip())
        except json.JSONDecodeError:
            continue

        graph = data.get("@graph") if isinstance(data, dict) else None
        if not graph:
            continue

        for item in graph:
            if item.get("@type") != "SportsEvent":
                continue

            name = item.get("name", "")
            # Skip parking-pass listings
            if "parking" in name.lower():
                continue

            offers = item.get("offers", {})
            low = offers.get("lowPrice")
            if not low:
                continue

            events.append({
                "name": name,
                "lowest": int(round(float(low))),
                "start_date": (item.get("startDate") or "")[:10],
                "url": offers.get("url") or item.get("url", ""),
            })

    return events


def collect() -> int:
    """Scrape StubHub for World Cup ticket prices using Playwright Firefox."""
    db_matches = get_all_matches()
    updated = 0

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        # Block images/CSS/fonts to speed up the load; keep JS and XHR
        page.route(
            "**/*",
            lambda route: (
                route.abort()
                if route.request.resource_type in ("image", "stylesheet", "font", "media")
                else route.fallback()
            ),
        )

        html = ""
        for url in (CATEGORY_URL, FALLBACK_URL):
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                status = resp.status if resp else 0
                log.info(f"[stubhub] {url} → {status}")
                if status == 200:
                    html = page.content()
                    break
                log.warning(f"[stubhub] Non-200 status {status} for {url}")
            except PlaywrightTimeout:
                log.warning(f"[stubhub] Timeout loading {url}")
            except Exception as e:
                log.warning(f"[stubhub] Error loading {url}: {e}")

        browser.close()

    if not html:
        log.error("[stubhub] Could not load any category page — skipping")
        return 0

    events = _parse_events_from_html(html)
    log.info(f"[stubhub] Parsed {len(events)} events from category page")

    for event in events:
        match = match_event_to_db(
            event_name=event["name"],
            event_date=event.get("start_date"),
            db_matches=db_matches,
        )
        if not match:
            log.debug(f"[stubhub] No DB match for: {event['name']!r}")
            continue

        upsert_platform_price(
            match_id=match["id"],
            platform="stubhub",
            lowest=event["lowest"],
            median=event["lowest"],
            highest=None,
            listing_count=0,
            listing_url=event.get("url", ""),
            is_transferable="unknown",
        )
        updated += 1

    log.info(f"[stubhub] Updated prices for {updated} matches")
    return updated
