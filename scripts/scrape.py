"""Standalone scraper entry point for GitHub Actions."""

import logging
import sys

sys.path.insert(0, ".")

import db.database as db
from collector import fixtures, seatgeek, stubhub, tickpick
from analysis.value import score_all_matches

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

db.init_db()

n = fixtures.collect()
log.info(f"Seeded {n} fixtures")

score_all_matches()

for name, collect_fn in [
    ("Vivid Seats", seatgeek.collect),
    ("TickPick", tickpick.collect),
    ("StubHub", stubhub.collect),
]:
    try:
        n = collect_fn()
        log.info(f"{name}: {n} updates")
    except Exception:
        log.exception(f"{name}: scraper failed, continuing")

score_all_matches()
log.info("Done — all scores recalculated")
