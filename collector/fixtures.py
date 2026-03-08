"""Fetch FIFA 2026 World Cup fixtures from TheSportsDB (free, no key needed)."""

import logging
import httpx

from config import (
    SPORTSDB_BASE, SPORTSDB_LEAGUE_ID, SPORTSDB_SEASON,
    FACE_VALUES, MEXICO_VENUES,
)
from db.database import upsert_match

log = logging.getLogger(__name__)
HEADERS = {"User-Agent": "world-cup-tickets/1.0"}


def _normalize_round(raw: str | None) -> str:
    """Map TheSportsDB round descriptions to our standard round names."""
    if not raw:
        return "Group"
    r = raw.strip().lower()
    if "final" in r and "semi" not in r and "quarter" not in r and "3rd" not in r:
        return "Final"
    if "semi" in r:
        return "Semi-final"
    if "quarter" in r:
        return "Quarter-final"
    if "16" in r or "round of 16" in r:
        return "Round of 16"
    if "3rd" in r or "third" in r:
        return "3rd Place"
    return "Group"


def _detect_country(venue: str | None, city: str | None) -> str:
    """Determine country from venue/city for Mexico flagging."""
    mexico_cities = {"mexico city", "monterrey", "guadalajara"}
    canada_cities = {"vancouver", "toronto"}

    if venue and venue in MEXICO_VENUES:
        return "Mexico"
    if city:
        c = city.lower()
        if c in mexico_cities:
            return "Mexico"
        if c in canada_cities:
            return "Canada"
    return "USA"


def collect() -> int:
    """Fetch all World Cup 2026 fixtures. Returns count of upserted matches."""
    url = f"{SPORTSDB_BASE}/eventsseason.php?id={SPORTSDB_LEAGUE_ID}&s={SPORTSDB_SEASON}"
    try:
        response = httpx.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        log.error(f"[fixtures] Failed to fetch: {e}")
        return 0

    data = response.json()
    events = data.get("events") or []
    if not events:
        log.warning("[fixtures] No events found for FIFA WC 2026")
        return 0

    count = 0
    for event in events:
        venue = event.get("strVenue")
        city = event.get("strCity")
        country = _detect_country(venue, city)
        is_mexico = country == "Mexico"

        round_name = _normalize_round(event.get("intRound") or event.get("strResult"))
        face = FACE_VALUES.get(round_name, FACE_VALUES["Group"])

        home = event.get("strHomeTeam")
        away = event.get("strAwayTeam")
        # TheSportsDB may use "TBD" or None for unset teams
        if home and home.lower() in ("tbd", "to be determined"):
            home = "TBD"
        if away and away.lower() in ("tbd", "to be determined"):
            away = "TBD"

        upsert_match(
            external_id=str(event.get("idEvent", "")),
            home_team=home,
            away_team=away,
            match_date=event.get("dateEvent"),
            venue=venue,
            city=city,
            country=country,
            round=round_name,
            status=event.get("strStatus") or "scheduled",
            home_score=event.get("intHomeScore"),
            away_score=event.get("intAwayScore"),
            face_value_cat1=face["cat1"],
            face_value_cat2=face["cat2"],
            face_value_cat3=face["cat3"],
            is_mexico_venue=is_mexico,
        )
        count += 1

    log.info(f"[fixtures] Upserted {count} matches")
    return count
