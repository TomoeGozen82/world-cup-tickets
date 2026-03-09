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
                median=event["lowest"],
                highest=event.get("highest"),
                listing_count=0,
                listing_url=url,
                is_transferable="yes",
            )
            updated += 1

    log.info(f"[tickpick] Updated prices for {updated} matches")
    return updated
