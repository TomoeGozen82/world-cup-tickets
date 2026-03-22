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
