"""Standalone scraper entry point for GitHub Actions."""

import logging
import sys

sys.path.insert(0, ".")

import db.database as db
from collector import fixtures, seatgeek, tickpick
from analysis.value import score_all_matches

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

db.init_db()

n = fixtures.collect()
log.info(f"Seeded {n} fixtures")

score_all_matches()

n = seatgeek.collect()
log.info(f"Vivid Seats: {n} updates")

n = tickpick.collect()
log.info(f"TickPick: {n} updates")

score_all_matches()
log.info("Done — all scores recalculated")
