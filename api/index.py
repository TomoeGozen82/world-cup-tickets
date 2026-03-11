import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from fastapi import FastAPI, Query
import db.database as db
from analysis.value import score_match

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="World Cup Tickets")

# Init DB schema on cold start
db.init_db()


@app.get("/api/matches")
def get_matches(round: str | None = Query(None), country: str | None = Query(None)):
    matches = list(db.get_all_matches())
    if round:
        matches = [m for m in matches if m["round"] == round]
    if country:
        matches = [m for m in matches if m["country"] == country]
    for m in matches:
        result = score_match(m, breakdown=True)
        m["score_breakdown"] = result["factors"]
    all_platform_prices = db.get_all_latest_platform_prices()
    for m in matches:
        m["platform_prices"] = all_platform_prices.get(m["id"], [])
    return matches


@app.get("/api/analysis/scores")
def get_scores():
    matches = list(db.get_all_matches())
    for m in matches:
        result = score_match(m, breakdown=True)
        m["score_breakdown"] = result["factors"]
    all_platform_prices = db.get_all_latest_platform_prices()
    for m in matches:
        m["platform_prices"] = all_platform_prices.get(m["id"], [])
    return sorted(matches, key=lambda m: m["value_score"], reverse=True)


@app.get("/api/prices/{match_id}")
def get_price_history(match_id: int, limit: int = Query(30)):
    return list(db.get_price_history(match_id, limit))


@app.get("/api/platform-prices")
def get_platform_prices():
    return db.get_all_latest_platform_prices()


@app.get("/api/platform-prices/{match_id}")
def get_match_platform_prices(match_id: int):
    return list(db.get_latest_platform_prices(match_id))


@app.post("/api/refresh")
def trigger_refresh():
    return {"message": "Scrapers run on schedule via GitHub Actions"}
