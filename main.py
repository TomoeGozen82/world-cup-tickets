"""FastAPI app + scheduler for World Cup Tickets tracker."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

import db.database as db
from collector import fixtures, seatgeek
from collector import stubhub, tickpick
from analysis.value import score_all_matches, score_match
from config import RESALE_POLL_HOURS

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _seed_fixtures():
    n = fixtures.collect()
    score_all_matches()
    log.info(f"[startup] seeded {n} fixtures")


def _collect_resale():
    n = seatgeek.collect()
    if n > 0:
        score_all_matches()
    log.info(f"[scheduler] resale prices: {n} updates")


def _collect_stubhub():
    n = stubhub.collect()
    log.info(f"[scheduler] stubhub: {n} updates")


def _collect_tickpick():
    n = tickpick.collect()
    log.info(f"[scheduler] tickpick: {n} updates")


def _run_all():
    _collect_resale()
    _collect_stubhub()
    _collect_tickpick()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    _seed_fixtures()

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(_collect_resale, trigger="interval", hours=RESALE_POLL_HOURS, id="resale", replace_existing=True)
    scheduler.add_job(_collect_stubhub, trigger="interval", hours=RESALE_POLL_HOURS, id="stubhub", replace_existing=True)
    scheduler.add_job(_collect_tickpick, trigger="interval", hours=RESALE_POLL_HOURS, id="tickpick", replace_existing=True)

    scheduler.start()
    log.info(f"[scheduler] Started — resale/{RESALE_POLL_HOURS}h, stubhub/{RESALE_POLL_HOURS}h, tickpick/{RESALE_POLL_HOURS}h")

    # Immediate collection on startup
    import threading
    threading.Thread(target=_run_all, daemon=True).start()

    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="World Cup Tickets", lifespan=lifespan)

# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/api/matches")
def get_matches(round: str | None = Query(None), country: str | None = Query(None)):
    matches = [dict(m) for m in db.get_all_matches()]
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
    matches = [dict(m) for m in db.get_all_matches()]
    for m in matches:
        result = score_match(m, breakdown=True)
        m["score_breakdown"] = result["factors"]
    all_platform_prices = db.get_all_latest_platform_prices()
    for m in matches:
        m["platform_prices"] = all_platform_prices.get(m["id"], [])
    return sorted(matches, key=lambda m: m["value_score"], reverse=True)


@app.get("/api/prices/{match_id}")
def get_price_history(match_id: int, limit: int = Query(30)):
    rows = db.get_price_history(match_id, limit)
    return [dict(r) for r in rows]


@app.get("/api/platform-prices")
def get_platform_prices():
    """Get latest prices from all platforms for all matches."""
    return db.get_all_latest_platform_prices()


@app.get("/api/platform-prices/{match_id}")
def get_match_platform_prices(match_id: int):
    """Get latest prices from all platforms for a specific match."""
    rows = db.get_latest_platform_prices(match_id)
    return [dict(r) for r in rows]


@app.post("/api/refresh")
def trigger_refresh():
    import threading
    threading.Thread(target=_run_all, daemon=True).start()
    return {"ok": True, "message": "Refresh started"}


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).parent / "viewer" / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
