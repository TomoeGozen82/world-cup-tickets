"""Match value scoring and fee calculator for investment analysis."""

from config import (
    ROUND_SCORES, VENUE_SCORES, POPULAR_TEAMS, MEXICO_VENUES,
    FIFA_BUYER_FEE, FIFA_SELLER_FEE,
)
from db.database import get_all_matches, update_value_score


def _team_tier(team: str | None) -> int:
    """Return tier number: 1=popular, 2=notable, 3=other, 0=TBD/unknown."""
    if not team or team == "TBD":
        return 0
    if team in POPULAR_TEAMS["tier1"]:
        return 1
    if team in POPULAR_TEAMS["tier2"]:
        return 2
    return 3


def _team_raw_and_detail(teams: set[str]) -> tuple[int, str]:
    """Score based on the best individual team in the match."""
    team_raw = 0
    for team in teams:
        if team in POPULAR_TEAMS["tier1"]:
            team_raw = max(team_raw, 100)
        elif team in POPULAR_TEAMS["tier2"]:
            team_raw = max(team_raw, 70)
        else:
            team_raw = max(team_raw, 40)
    if not teams:
        team_raw = 50

    if team_raw == 100:
        detail = "Tier 1"
    elif team_raw == 70:
        detail = "Tier 2"
    elif team_raw == 50:
        detail = "TBD"
    else:
        detail = "Tier 3"
    return team_raw, detail


_MATCHUP_TABLE = {
    (1, 1): (100, "Tier 1 vs Tier 1"),
    (1, 2): (85, "Tier 1 vs Tier 2"),
    (1, 3): (65, "Tier 1 vs Other"),
    (1, 0): (60, "Tier 1 vs TBD"),
    (2, 2): (70, "Tier 2 vs Tier 2"),
    (2, 3): (45, "Tier 2 vs Other"),
    (2, 0): (40, "Tier 2 vs TBD"),
    (3, 3): (25, "Other vs Other"),
    (3, 0): (20, "Other vs TBD"),
    (0, 0): (30, "TBD vs TBD"),
}


def _matchup_score(home: str | None, away: str | None) -> tuple[int, str]:
    """Score based on which two teams are playing each other."""
    tiers = sorted([_team_tier(home), _team_tier(away)])
    return _MATCHUP_TABLE.get(tuple(tiers), (25, "Unknown"))


def _resale_raw_score(markup_pct: float) -> float:
    """Piecewise resale markup curve — generous for 50-200% range."""
    if markup_pct <= 0:
        return 5
    elif markup_pct <= 100:
        return 15 + markup_pct * 0.55       # 0%→15, 100%→70
    elif markup_pct <= 300:
        return 70 + (markup_pct - 100) * 0.125  # 100%→70, 300%→95
    else:
        return min(100, 95 + (markup_pct - 300) * 0.025)


def _deal_raw_score(markup_pct: float) -> float:
    """Inverse piecewise deal curve — low markup = high score."""
    if markup_pct <= 0:
        return 100
    elif markup_pct <= 100:
        return 100 - markup_pct * 0.55       # 0%→100, 100%→45
    elif markup_pct <= 200:
        return 45 - (markup_pct - 100) * 0.35   # 100%→45, 200%→10
    else:
        return max(0, 10 - (markup_pct - 200) * 0.05)


def score_match(match: dict, breakdown: bool = False) -> int | dict:
    """
    Calculate investment score (0-100) for a match.

    With resale data:
      Round 25% + Venue 10% + Team 10% + Matchup 15% + Resale 30% = 90%
      +10 bonus for non-Mexico venues (flat), +0 for Mexico (resale cap)

    Without resale data:
      Round 35% + Venue 15% + Team 15% + Matchup 20% + Country 15% = 100%
    """
    has_resale = bool(match.get("resale_median"))
    is_mexico = match.get("country") == "Mexico"

    # Round
    round_name = match.get("round", "Group")
    round_raw = ROUND_SCORES.get(round_name, 50)

    # Venue
    venue = match.get("venue", "")
    venue_raw = VENUE_SCORES.get(venue, 65)

    # Team (best individual)
    teams = {match.get("home_team", ""), match.get("away_team", "")}
    teams.discard(None)
    teams.discard("TBD")
    team_raw, team_detail = _team_raw_and_detail(teams)

    # Matchup (pairing quality)
    matchup_raw, matchup_detail = _matchup_score(
        match.get("home_team"), match.get("away_team"))

    # Resale markup
    resale_raw = 0
    resale_detail = "No data"
    markup_pct = 0
    if has_resale:
        face = match.get("face_value_cat3") or 100
        median = match["resale_median"]
        markup_pct = ((median - face) / face) * 100 if face > 0 else 0
        resale_raw = _resale_raw_score(markup_pct)
        resale_detail = f"+{int(markup_pct)}%" if markup_pct >= 0 else f"{int(markup_pct)}%"

    if has_resale:
        w_round, w_venue, w_team, w_matchup, w_resale = 0.25, 0.10, 0.10, 0.15, 0.30
        market_bonus = 0 if is_mexico else 10
        total_raw = (round_raw * w_round + venue_raw * w_venue + team_raw * w_team
                     + matchup_raw * w_matchup + resale_raw * w_resale + market_bonus)
    else:
        w_round, w_venue, w_team, w_matchup, w_country = 0.35, 0.15, 0.15, 0.20, 0.15
        country = match.get("country", "USA")
        if country == "Mexico":
            country_raw = 0
        elif country == "Canada":
            country_raw = 80
        else:
            country_raw = 100
        total_raw = (round_raw * w_round + venue_raw * w_venue + team_raw * w_team
                     + matchup_raw * w_matchup + country_raw * w_country)

    total = min(100, max(0, int(total_raw)))

    if not breakdown:
        return total

    # Build breakdown for tooltip
    if has_resale:
        factors = [
            {"name": "Round", "score": int(round_raw * w_round), "max": int(w_round * 100), "detail": round_name},
            {"name": "Venue", "score": int(venue_raw * w_venue), "max": int(w_venue * 100), "detail": venue or "Unknown"},
            {"name": "Team", "score": int(team_raw * w_team), "max": int(w_team * 100), "detail": team_detail},
            {"name": "Matchup", "score": int(matchup_raw * w_matchup), "max": int(w_matchup * 100), "detail": matchup_detail},
            {"name": "Resale", "score": int(resale_raw * w_resale), "max": int(w_resale * 100), "detail": resale_detail},
            {"name": "Market", "score": market_bonus, "max": 10,
             "detail": "Resale capped" if is_mexico else "No cap"},
        ]
    else:
        factors = [
            {"name": "Round", "score": int(round_raw * w_round), "max": int(w_round * 100), "detail": round_name},
            {"name": "Venue", "score": int(venue_raw * w_venue), "max": int(w_venue * 100), "detail": venue or "Unknown"},
            {"name": "Team", "score": int(team_raw * w_team), "max": int(w_team * 100), "detail": team_detail},
            {"name": "Matchup", "score": int(matchup_raw * w_matchup), "max": int(w_matchup * 100), "detail": matchup_detail},
            {"name": "Country", "score": int(country_raw * w_country), "max": int(w_country * 100), "detail": country},
        ]

    return {"total": total, "factors": factors}


def score_match_buyer(match: dict, breakdown: bool = False) -> int | dict:
    """
    Calculate buyer deal score (0-100) — high score means good deal (low markup).

    Weights: Deal 45% + Round 15% + Matchup 15% + Venue 10% + Team 10% + Country 5%
    """
    has_resale = bool(match.get("resale_median"))

    w_deal, w_round, w_matchup, w_venue, w_team, w_country = 0.45, 0.15, 0.15, 0.10, 0.10, 0.05

    # Round
    round_name = match.get("round", "Group")
    round_raw = ROUND_SCORES.get(round_name, 50)

    # Venue
    venue = match.get("venue", "")
    venue_raw = VENUE_SCORES.get(venue, 65)

    # Team
    teams = {match.get("home_team", ""), match.get("away_team", "")}
    teams.discard(None)
    teams.discard("TBD")
    team_raw, team_detail = _team_raw_and_detail(teams)

    # Matchup
    matchup_raw, matchup_detail = _matchup_score(
        match.get("home_team"), match.get("away_team"))

    # Country
    country = match.get("country", "USA")
    if country == "Mexico":
        country_raw = 0
    elif country == "Canada":
        country_raw = 80
    else:
        country_raw = 100

    # Deal quality — low markup = high score
    deal_raw = 50  # default when no resale data
    deal_detail = "No data"
    if has_resale:
        face = match.get("face_value_cat3") or 100
        median = match["resale_median"]
        markup_pct = ((median - face) / face) * 100 if face > 0 else 0
        deal_raw = _deal_raw_score(markup_pct)
        deal_detail = f"+{int(markup_pct)}%" if markup_pct >= 0 else f"{int(markup_pct)}%"

    total_raw = (deal_raw * w_deal + round_raw * w_round + matchup_raw * w_matchup
                 + venue_raw * w_venue + team_raw * w_team + country_raw * w_country)
    total = min(100, max(0, int(total_raw)))

    if not breakdown:
        return total

    factors = [
        {"name": "Deal", "score": int(deal_raw * w_deal), "max": int(w_deal * 100), "detail": deal_detail},
        {"name": "Round", "score": int(round_raw * w_round), "max": int(w_round * 100), "detail": round_name},
        {"name": "Matchup", "score": int(matchup_raw * w_matchup), "max": int(w_matchup * 100), "detail": matchup_detail},
        {"name": "Venue", "score": int(venue_raw * w_venue), "max": int(w_venue * 100), "detail": venue or "Unknown"},
        {"name": "Team", "score": int(team_raw * w_team), "max": int(w_team * 100), "detail": team_detail},
        {"name": "Country", "score": int(country_raw * w_country), "max": int(w_country * 100), "detail": country},
    ]

    return {"total": total, "factors": factors}


def calculate_fee(purchase_price: float, sale_price: float) -> dict:
    """
    Calculate net profit after FIFA Exchange fees.
    Buyer pays purchase_price * (1 + buyer_fee).
    Seller receives sale_price * (1 - seller_fee).
    """
    total_cost = purchase_price * (1 + FIFA_BUYER_FEE)
    net_revenue = sale_price * (1 - FIFA_SELLER_FEE)
    net_profit = net_revenue - total_cost
    roi = (net_profit / total_cost * 100) if total_cost > 0 else 0

    return {
        "purchase_price": purchase_price,
        "total_cost": round(total_cost, 2),
        "sale_price": sale_price,
        "net_revenue": round(net_revenue, 2),
        "net_profit": round(net_profit, 2),
        "roi_percent": round(roi, 1),
    }


def score_all_matches() -> int:
    """Recalculate value scores for all matches. Returns count updated."""
    matches = get_all_matches()
    count = 0
    for m in matches:
        score = score_match(m)
        update_value_score(m["id"], score)
        count += 1
    return count
