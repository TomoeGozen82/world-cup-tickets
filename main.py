"""FastAPI app + scheduler for World Cup Tickets tracker."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

import db.database as db
from collector import fixtures, reddit, news_rss, seatgeek
from analysis.value import score_all_matches, calculate_fee
from config import RESALE_POLL_HOURS

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _collect_fixtures():
    n = fixtures.collect()
    if n > 0:
        score_all_matches()
    log.info(f"[scheduler] fixtures: {n} matches")


def _collect_news():
    n = news_rss.collect()
    log.info(f"[scheduler] news: +{n} new items")


def _collect_reddit():
    n = reddit.collect()
    log.info(f"[scheduler] reddit: +{n} new posts")


def _collect_resale():
    n = seatgeek.collect()
    if n > 0:
        score_all_matches()
    log.info(f"[scheduler] resale prices: {n} updates")


def _run_all():
    _collect_fixtures()
    _collect_news()
    _collect_reddit()
    _collect_resale()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    scheduler = BackgroundScheduler(daemon=True)

    scheduler.add_job(_collect_fixtures, trigger="interval", hours=24, id="fixtures", replace_existing=True)
    scheduler.add_job(_collect_news, trigger="interval", hours=4, id="news", replace_existing=True)
    scheduler.add_job(_collect_reddit, trigger="interval", hours=2, id="reddit", replace_existing=True)
    scheduler.add_job(_collect_resale, trigger="interval", hours=RESALE_POLL_HOURS, id="resale", replace_existing=True)

    scheduler.start()
    log.info(f"[scheduler] Started — fixtures/24h, news/4h, reddit/2h, resale/{RESALE_POLL_HOURS}h")

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
    return matches


@app.get("/api/news")
def get_news(limit: int = Query(50)):
    return [dict(n) for n in db.get_news(limit)]


@app.get("/api/reddit")
def get_reddit(limit: int = Query(50)):
    return [dict(r) for r in db.get_reddit_posts(limit)]


@app.get("/api/analysis/scores")
def get_scores():
    matches = [dict(m) for m in db.get_all_matches()]
    return sorted(matches, key=lambda m: m["value_score"], reverse=True)


class FeeCalcRequest(BaseModel):
    purchase_price: float
    sale_price: float


@app.post("/api/analysis/fee")
def calc_fee(body: FeeCalcRequest):
    return calculate_fee(body.purchase_price, body.sale_price)


@app.get("/api/prices/{match_id}")
def get_price_history(match_id: int, limit: int = Query(30)):
    rows = db.get_price_history(match_id, limit)
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
