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

results = {}
for name, collect_fn in [
    ("Vivid Seats", seatgeek.collect),
    ("TickPick", tickpick.collect),
    ("StubHub", stubhub.collect),
]:
    try:
        n = collect_fn()
        results[name] = n or 0
        log.info(f"{name}: {n} updates")
    except Exception:
        results[name] = 0
        log.exception(f"{name}: scraper failed, continuing")

# Health check: warn on zero-result scrapers
for name, count in results.items():
    if count == 0:
        log.warning(f"ALERT: {name} returned 0 results")

score_all_matches()
log.info("Done — all scores recalculated")

# Fail the workflow if ALL scrapers returned 0 (triggers GitHub notification)
if all(c == 0 for c in results.values()):
    log.error("ALL scrapers returned 0 results — site data may be stale")
    sys.exit(1)
