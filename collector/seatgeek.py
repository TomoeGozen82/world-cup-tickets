"""Scrape resale ticket prices from Vivid Seats (no API key needed)."""

import json
import logging
import re
import time
from datetime import date, timedelta

import httpx

from db.database import (
    get_all_matches,
    get_matches_with_seatgeek_id,
    update_seatgeek_mapping,
    update_resale_prices,
    insert_price_snapshot,
    upsert_platform_price,
)

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.vividseats.com/",
}

BASE_SEARCH_URL = "https://www.vividseats.com/search?searchTerm="


def _get_search_terms(db_matches: list[dict]) -> list[str]:
    """Build per-team search terms to get full coverage of all matches."""
    teams = set()
    for m in db_matches:
        for side in ("home_team", "away_team"):
            team = m.get(side, "")
            if team and team != "TBD":
                teams.add(team)
    # Build search queries like "Ecuador+World+Cup"
    return [f"{team.replace(' ', '+')}+World+Cup" for team in sorted(teams)]


def _parse_jsonld(html: str) -> dict | None:
    """Extract event JSON-LD from page HTML."""
    # Match ld+json script tags with flexible whitespace
    for match in re.finditer(
        r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    ):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        # Could be a list or single object
        items = data if isinstance(data, list) else [data]
        for item in items:
            # Accept any event-like object with offers
            if item.get("offers") or item.get("startDate"):
                return item
    return None


def _parse_average(html: str) -> int | None:
    """Extract average price from page body text."""
    m = re.search(r"average ticket price[^$]*\$([\d,]+)", html, re.IGNORECASE)
    if m:
        return int(m.group(1).replace(",", ""))
    return None


def _discover_events(client: httpx.Client, search_terms: list[str]) -> list[dict]:
    """Scrape Vivid Seats search pages for World Cup event links using per-team searches."""
    seen = set()
    all_events = []

    for term in search_terms:
        url = f"{BASE_SEARCH_URL}{term}"
        try:
            resp = client.get(url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            log.warning(f"[vividseats] Search failed for '{term}': {e}")
            continue

        count = 0
        for m in re.finditer(r'href="(/[^"]*?/production/(\d+))"', resp.text):
            path, prod_id = m.group(1), int(m.group(2))
            # Skip parking, follow-my-team, and other non-match listings
            if "parking" in path.lower() or "follow-my-team" in path.lower():
                continue
            if prod_id not in seen:
                seen.add(prod_id)
                all_events.append({
                    "url": f"https://www.vividseats.com{path}",
                    "production_id": prod_id,
                })
                count += 1

        if count:
            log.info(f"[vividseats] '{term}': {count} new events")
        time.sleep(0.5)  # rate limit between searches

    log.info(f"[vividseats] Found {len(all_events)} unique events across {len(search_terms)} searches")
    return all_events


def _extract_prices(html: str, ld: dict | None) -> dict:
    """Extract prices from JSON-LD and/or page regex."""
    result = {"lowest": None, "highest": None, "average": None}

    # Try JSON-LD offers first
    if ld:
        offers = ld.get("offers", {})
        if offers.get("lowPrice"):
            result["lowest"] = int(float(offers["lowPrice"]))
        if offers.get("highPrice"):
            result["highest"] = int(float(offers["highPrice"]))

    # Regex fallback for prices embedded in page JS/HTML
    if result["lowest"] is None:
        m = re.search(r'"lowPrice"\s*[=:]\s*"?(\d+\.?\d*)', html)
        if m:
            result["lowest"] = int(float(m.group(1)))
    if result["highest"] is None:
        m = re.search(r'"highPrice"\s*[=:]\s*"?(\d+\.?\d*)', html)
        if m:
            result["highest"] = int(float(m.group(1)))

    # Average from page text
    avg_m = re.search(r"average ticket price[^$]*\$([\d,]+)", html, re.IGNORECASE)
    if avg_m:
        result["average"] = int(avg_m.group(1).replace(",", ""))

    return result


def _scrape_event(client: httpx.Client, url: str) -> dict | None:
    """Scrape a single event page for pricing data."""
    try:
        resp = client.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        log.warning(f"[vividseats] Failed to fetch {url}: {e}")
        return None

    ld = _parse_jsonld(resp.text)
    prices = _extract_prices(resp.text, ld)

    if prices["lowest"] is None:
        return None

    # Extract event metadata
    name = ""
    start_date = ""
    venue = ""

    if ld:
        name = ld.get("name", "")
        start_date = (ld.get("startDate") or "")[:10]
        venue = (ld.get("location") or {}).get("name", "")

    # Fallback: extract from <title>
    if not name:
        title_m = re.search(r"<title[^>]*>(.*?)</title>", resp.text)
        if title_m:
            name = title_m.group(1).split(" tickets")[0].strip()

    avg = prices["average"]
    return {
        "name": name,
        "start_date": start_date,
        "venue": venue,
        "lowest": prices["lowest"],
        "highest": prices["highest"],
        "average": avg,
        "median": avg,  # best approximation without full listing data
        "url": url,
    }


def _normalize_name(name: str) -> str:
    """Simplify team/event name for fuzzy matching."""
    name = name.lower().strip()
    # Remove common suffixes
    for s in [
        " mens national soccer", " national soccer", " national football",
        " national team", " men's", " women's",
    ]:
        name = name.replace(s, "")
    return name


# Map our fixture team names to how they appear on Vivid Seats
TEAM_ALIASES = {
    "korea republic": ["korea", "south korea"],
    "ir iran": ["iran"],
    "côte d'ivoire": ["ivory coast", "cote d'ivoire", "cote divoire"],
    "cabo verde": ["cape verde"],
    "curaçao": ["curacao"],
    "united states": ["usa", "u.s."],
}


def _team_in_event_name(team: str, ev_name: str) -> bool:
    """Check if a team name (or any of its aliases) appears in the event name."""
    team_lower = team.lower()
    if team_lower in ev_name:
        return True
    aliases = TEAM_ALIASES.get(team_lower, [])
    return any(alias in ev_name for alias in aliases)


def _match_to_db(event: dict, db_matches: list[dict]) -> dict | None:
    """Match a scraped event to a DB match by team names only.

    No venue/date fallback — our fixture venues may be stale vs what
    ticket sites show, so matching by venue causes wrong mappings.
    Requires BOTH teams to match (or one team + TBD opponent).
    """
    ev_name = _normalize_name(event.get("name", ""))

    for m in db_matches:
        if m.get("seatgeek_id"):
            continue  # already mapped

        home = (m.get("home_team") or "").strip()
        away = (m.get("away_team") or "").strip()

        if not home or not away:
            continue

        home_match = home != "TBD" and _team_in_event_name(home, ev_name)
        away_match = away != "TBD" and _team_in_event_name(away, ev_name)

        # Both teams must match, or one team matches and the other is TBD
        if home_match and away_match:
            return m
        if home_match and away == "TBD":
            return m
        if away_match and home == "TBD":
            return m

    return None


def discover() -> int:
    """Discover Vivid Seats events and map them to DB matches."""
    db_matches = get_all_matches()
    search_terms = _get_search_terms(db_matches)

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        events = _discover_events(client, search_terms)
        if not events:
            return 0

        mapped = 0

        for ev in events:
            time.sleep(1)  # rate limit
            data = _scrape_event(client, ev["url"])
            if not data:
                continue

            match = _match_to_db(data, db_matches)
            if match:
                update_seatgeek_mapping(
                    match_id=match["id"],
                    seatgeek_id=ev["production_id"],
                    seatgeek_url=ev["url"],
                )
                match["seatgeek_id"] = ev["production_id"]
                mapped += 1

                # Also store initial prices
                update_resale_prices(
                    match_id=match["id"],
                    lowest=data["lowest"],
                    median=data["median"],
                    average=data["average"],
                    highest=data["highest"],
                    listing_count=0,
                )
                insert_price_snapshot(
                    match_id=match["id"],
                    lowest=data["lowest"],
                    median=data["median"],
                    average=data["average"],
                    highest=data["highest"],
                    listing_count=0,
                )
                upsert_platform_price(
                    match_id=match["id"],
                    platform="vividseats",
                    lowest=data["lowest"],
                    median=data["median"],
                    highest=data["highest"],
                    listing_count=0,
                    listing_url=ev["url"],
                )

        log.info(f"[vividseats] Mapped {mapped}/{len(events)} events to matches")
        return mapped


def collect_prices() -> int:
    """Update prices for all previously mapped matches."""
    mapped = get_matches_with_seatgeek_id()
    if not mapped:
        log.info("[vividseats] No mapped matches — run discover() first")
        return 0

    # Build production_id → match_id lookup
    prod_to_match = {row["seatgeek_id"]: row["id"] for row in mapped}

    # We need the URLs — fetch from DB
    all_matches = {m["id"]: m for m in get_all_matches()}

    updated = 0
    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for row in mapped:
            match_id = row["id"]
            match = all_matches.get(match_id, {})
            url = match.get("seatgeek_url")
            if not url:
                continue

            time.sleep(1)  # rate limit
            data = _scrape_event(client, url)
            if not data or data["lowest"] is None:
                continue

            update_resale_prices(
                match_id=match_id,
                lowest=data["lowest"],
                median=data["median"],
                average=data["average"],
                highest=data["highest"],
                listing_count=0,
            )
            insert_price_snapshot(
                match_id=match_id,
                lowest=data["lowest"],
                median=data["median"],
                average=data["average"],
                highest=data["highest"],
                listing_count=0,
            )
            upsert_platform_price(
                match_id=match_id,
                platform="vividseats",
                lowest=data["lowest"],
                median=data["median"],
                highest=data["highest"],
                listing_count=0,
                listing_url=url,
            )
            updated += 1

    log.info(f"[vividseats] Updated prices for {updated}/{len(mapped)} matches")
    return updated


def collect() -> int:
    """Full cycle: discover new events + update prices."""
    discovered = discover()
    updated = collect_prices()
    return discovered + updated
