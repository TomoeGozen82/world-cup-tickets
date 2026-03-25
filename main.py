"""FastAPI app for World Cup Tickets tracker.

This module defines the API routes. For Vercel deployment, the app is
imported from api/index.py which handles sys.path setup.
For local development, run: uvicorn main:app --reload
"""

import logging

from fastapi import FastAPI, Query

import db.database as db
from analysis.value import score_match, score_match_buyer
from config import PLATFORM_FEES

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="World Cup Tickets")

db.init_db()


def _enrich_fees(platform_prices: list[dict]) -> list[dict]:
    """Add estimated all-in pricing to each platform price entry."""
    for pp in platform_prices:
        fee_pct = PLATFORM_FEES.get(pp.get("platform", ""), 0)
        pp["fee_pct"] = fee_pct
        if pp.get("lowest_price"):
            pp["estimated_all_in"] = int(pp["lowest_price"] * (1 + fee_pct))
        else:
            pp["estimated_all_in"] = None
    return platform_prices


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
        buyer = score_match_buyer(m, breakdown=True)
        m["buyer_score"] = buyer["total"]
        m["buyer_breakdown"] = buyer["factors"]
    all_platform_prices = db.get_all_latest_platform_prices()
    for m in matches:
        m["platform_prices"] = _enrich_fees(all_platform_prices.get(m["id"], []))
    return {"matches": matches, "last_scraped": db.get_latest_scrape_time()}


@app.get("/api/analysis/scores")
def get_scores():
    matches = list(db.get_all_matches())
    for m in matches:
        result = score_match(m, breakdown=True)
        m["score_breakdown"] = result["factors"]
        buyer = score_match_buyer(m, breakdown=True)
        m["buyer_score"] = buyer["total"]
        m["buyer_breakdown"] = buyer["factors"]
    all_platform_prices = db.get_all_latest_platform_prices()
    for m in matches:
        m["platform_prices"] = _enrich_fees(all_platform_prices.get(m["id"], []))
    return {
        "matches": sorted(matches, key=lambda m: m["value_score"], reverse=True),
        "last_scraped": db.get_latest_scrape_time(),
    }


@app.get("/api/prices/{match_id}")
def get_price_history(match_id: int, limit: int = Query(30)):
    return list(db.get_price_history(match_id, limit))


@app.get("/api/platform-prices")
def get_platform_prices():
    return db.get_all_latest_platform_prices()


@app.get("/api/platform-prices/{match_id}")
def get_match_platform_prices(match_id: int):
    return list(db.get_latest_platform_prices(match_id))


@app.get("/api/health")
def health():
    return {"last_scraped": db.get_latest_scrape_time()}
