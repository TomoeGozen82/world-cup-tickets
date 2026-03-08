"""Constants for World Cup Tickets MVP. No .env needed."""

# TheSportsDB free API (test key = "3")
SPORTSDB_BASE = "https://www.thesportsdb.com/api/v1/json/3"
SPORTSDB_LEAGUE_ID = "4429"  # FIFA World Cup
SPORTSDB_SEASON = "2026"

# Reddit subreddits for ticket sentiment
REDDIT_SUBS = ["WorldCup2026Tickets", "fifatickets"]

# RSS feeds for World Cup news
RSS_FEEDS = {
    "ESPN FC": "https://www.espn.com/espn/rss/soccer/news",
    "Guardian Football": "https://www.theguardian.com/football/rss",
    "BBC Sport": "https://feeds.bbci.co.uk/sport/football/rss.xml",
}

# FIFA face value by round (USD)
FACE_VALUES = {
    "Group":         {"cat1": 300, "cat2": 200, "cat3": 100},
    "Round of 16":   {"cat1": 400, "cat2": 275, "cat3": 125},
    "Quarter-final": {"cat1": 525, "cat2": 350, "cat3": 175},
    "Semi-final":    {"cat1": 775, "cat2": 500, "cat3": 250},
    "3rd Place":     {"cat1": 475, "cat2": 325, "cat3": 150},
    "Final":         {"cat1": 1500, "cat2": 900, "cat3": 400},
}

# Mexico venues — resale capped at face value by Mexican law
MEXICO_VENUES = {
    "Estadio Azteca",
    "Estadio BBVA",
    "Estadio Akron",
}

# Venue desirability scores (0-100) for investment analysis
VENUE_SCORES = {
    "MetLife Stadium": 100,       # Final
    "AT&T Stadium": 90,           # Semi-final
    "SoFi Stadium": 90,           # Semi-final + USMNT opener
    "Hard Rock Stadium": 85,      # Quarter-final
    "NRG Stadium": 80,
    "Mercedes-Benz Stadium": 80,
    "Lincoln Financial Field": 75,
    "Lumen Field": 75,
    "Gillette Stadium": 75,
    "BC Place": 70,               # Canada
    "BMO Field": 70,              # Canada
    "Levi's Stadium": 75,
    "TQL Stadium": 70,
    "Estadio Azteca": 60,         # Mexico (resale cap)
    "Estadio BBVA": 55,           # Mexico
    "Estadio Akron": 55,          # Mexico
}

# Team popularity tiers for resale demand
POPULAR_TEAMS = {
    "tier1": {"United States", "Mexico", "Canada", "Brazil", "Argentina", "England", "Germany", "France", "Spain"},
    "tier2": {"Portugal", "Netherlands", "Italy", "Japan", "South Korea", "Belgium", "Colombia", "Uruguay"},
}

# Round importance weights
ROUND_SCORES = {
    "Final": 100,
    "Semi-final": 85,
    "Quarter-final": 70,
    "Round of 16": 55,
    "3rd Place": 40,
    "Group": 30,
}

# FIFA Exchange fees
FIFA_BUYER_FEE = 0.15   # 15% buyer premium
FIFA_SELLER_FEE = 0.15  # 15% seller fee (net = sale * 0.85)

# Vivid Seats scraping (no API key needed)
RESALE_POLL_HOURS = 6  # how often to scrape for price updates

# World Cup news keywords for RSS filtering
WC_KEYWORDS = [
    "world cup", "fifa 2026", "world cup 2026", "fifa world cup",
    "copa del mundo", "mondial", "world cup ticket",
    "metlife", "azteca", "world cup draw", "world cup group",
    "world cup qualifier", "world cup squad",
]
