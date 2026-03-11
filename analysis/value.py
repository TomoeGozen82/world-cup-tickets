"""Match value scoring and fee calculator for investment analysis."""

from config import (
    ROUND_SCORES, VENUE_SCORES, POPULAR_TEAMS, MEXICO_VENUES,
    FIFA_BUYER_FEE, FIFA_SELLER_FEE,
)
from db.database import get_all_matches, update_value_score


def score_match(match: dict, breakdown: bool = False) -> int | dict:
    """
    Calculate value score (0-100) for a match.

    When resale data is available the weights shift to include market signal:
      - Round significance: 30% (was 40%)
      - Venue desirability: 15% (was 25%)
      - Team popularity: 15% (was 20%)
      - Country: 10% (was 15%)
      - Resale markup: 30% (new)

    Without resale data the original weights apply.

    If breakdown=True, returns a dict with total score and per-factor breakdown.
    """
    has_resale = bool(match.get("resale_median"))

    # Dynamic weights
    if has_resale:
        w_round, w_venue, w_team, w_country, w_resale = 0.30, 0.15, 0.15, 0.10, 0.30
    else:
        w_round, w_venue, w_team, w_country, w_resale = 0.40, 0.25, 0.20, 0.15, 0.0

    # Round significance
    round_name = match.get("round", "Group")
    round_raw = ROUND_SCORES.get(round_name, 30)
    round_score = round_raw * w_round

    # Venue desirability
    venue = match.get("venue", "")
    venue_raw = VENUE_SCORES.get(venue, 65)
    venue_score = venue_raw * w_venue

    # Team popularity
    teams = {match.get("home_team", ""), match.get("away_team", "")}
    teams.discard(None)
    teams.discard("TBD")
    team_raw = 0
    team_detail = "Unknown"
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
        team_detail = "Tier 1"
    elif team_raw == 70:
        team_detail = "Tier 2"
    elif team_raw == 50:
        team_detail = "TBD"
    else:
        team_detail = "Tier 3"
    team_score = team_raw * w_team

    # Country factor
    country = match.get("country", "USA")
    if country == "Mexico":
        country_raw = 0
    elif country == "Canada":
        country_raw = 80
    else:
        country_raw = 100
    country_score = country_raw * w_country

    # Resale markup factor — how much above face value the market is pricing
    resale_raw = 0
    resale_detail = "No data"
    markup_pct = 0
    if has_resale:
        face = match.get("face_value_cat3") or 100
        median = match["resale_median"]
        markup_pct = ((median - face) / face) * 100 if face > 0 else 0
        # Map markup % to 0-100 score: 0%=10, 100%=30, 300%=70, 500%+=100
        resale_raw = min(100, max(0, 10 + markup_pct * 0.18))
        resale_detail = f"+{int(markup_pct)}%" if markup_pct >= 0 else f"{int(markup_pct)}%"
    resale_score = resale_raw * w_resale

    total = min(100, max(0, int(round_score + venue_score + team_score + country_score + resale_score)))

    if not breakdown:
        return total

    factors = [
        {"name": "Round", "score": int(round_score), "max": int(w_round * 100), "detail": round_name},
        {"name": "Venue", "score": int(venue_score), "max": int(w_venue * 100), "detail": venue or "Unknown"},
        {"name": "Team", "score": int(team_score), "max": int(w_team * 100), "detail": team_detail},
        {"name": "Country", "score": int(country_score), "max": int(w_country * 100), "detail": country},
        {"name": "Resale", "score": int(resale_score), "max": int(w_resale * 100), "detail": resale_detail},
    ]
    # Remove resale factor if no resale data
    if not has_resale:
        factors = [f for f in factors if f["name"] != "Resale"]

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
