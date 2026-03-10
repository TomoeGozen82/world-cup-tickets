"""StubHub scraper — currently disabled.

StubHub is fully JS-rendered (returns 202 with empty HTML for all event
and search pages).  Without a headless browser, we cannot extract prices.

TODO: Add Playwright/Selenium support, or find a StubHub API endpoint.
"""

import logging

log = logging.getLogger(__name__)


def collect() -> int:
    """No-op — StubHub requires JS rendering."""
    log.info("[stubhub] Skipped — site requires JS rendering (headless browser needed)")
    return 0
