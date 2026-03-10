"""Scrape resale ticket prices from TickPick (no buyer fees).

Strategy: the category page at /world-cup-soccer-tickets/ embeds JSON-LD
SportsEvent blocks with lowPrice/highPrice and buy URLs for every listed
match.  One GET fetches all events — no per-event crawling needed.
"""

import json
import logging
import re

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

CATEGORY_URL = "https://www.tickpick.com/world-cup-soccer-tickets/"


def _parse_all_events(html: str) -> list[dict]:
    """Extract all SportsEvent JSON-LD blocks from the category page."""
    events = []
    for m in re.finditer(
        r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
        html, re.DOTALL,
    ):
        try:
            data = json.loads(m.group(1))
            if isinstance(data, list):
                data = data[0]
            if data.get("@type") != "SportsEvent":
                continue
            offers = data.get("offers", {})
            low = offers.get("lowPrice")
            if not low:
                continue
            events.append({
                "lowest": int(float(low)),
                "highest": int(float(offers.get("highPrice", 0))) or None,
                "name": data.get("name", ""),
                "start_date": (data.get("startDate") or "")[:10],
                "venue": (data.get("location", {}).get("name", "")),
                "url": offers.get("url") or data.get("url", ""),
            })
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    return events


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
    """Scrape TickPick category page for World Cup ticket prices."""
    db_matches = [dict(m) for m in get_all_matches()]
    updated = 0

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        try:
            resp = client.get(CATEGORY_URL, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            log.error(f"[tickpick] Category page failed: {e}")
            return 0

        events = _parse_all_events(resp.text)
        log.info(f"[tickpick] Parsed {len(events)} events from category page")

        for event in events:
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
                listing_url=event.get("url", ""),
                is_transferable="yes",
            )
            updated += 1

    log.info(f"[tickpick] Updated prices for {updated} matches")
    return updated
