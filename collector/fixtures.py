"""Static FIFA 2026 World Cup fixtures — all 104 matches.

No external API needed. Schedule sourced from FIFA's official match schedule.
6 team slots remain TBD pending UEFA/intercontinental playoffs (March 2026).
"""

from config import FACE_VALUES, MEXICO_VENUES
from db.database import upsert_match

# fmt: off
FIXTURES = [
    # ── GROUP STAGE — MATCHDAY 1 ──
    # Group A
    {"mn": 1,  "date": "2026-06-11", "home": "Mexico",       "away": "South Africa",  "venue": "Estadio Azteca",                  "city": "Mexico City",     "group": "A"},
    {"mn": 2,  "date": "2026-06-11", "home": "Korea Republic","away": "TBD",           "venue": "Estadio Akron",                   "city": "Guadalajara",     "group": "A"},
    # Group B
    {"mn": 3,  "date": "2026-06-12", "home": "Canada",       "away": "TBD",           "venue": "BMO Field",                       "city": "Toronto",         "group": "B"},
    {"mn": 4,  "date": "2026-06-12", "home": "Qatar",        "away": "Switzerland",   "venue": "BC Place",                        "city": "Vancouver",       "group": "B"},
    # Group C
    {"mn": 5,  "date": "2026-06-13", "home": "Brazil",       "away": "Morocco",       "venue": "MetLife Stadium",                 "city": "East Rutherford", "group": "C"},
    {"mn": 6,  "date": "2026-06-13", "home": "Scotland",     "away": "Haiti",         "venue": "Gillette Stadium",                "city": "Foxborough",      "group": "C"},
    # Group D
    {"mn": 7,  "date": "2026-06-12", "home": "United States","away": "Paraguay",      "venue": "SoFi Stadium",                    "city": "Inglewood",       "group": "D"},
    {"mn": 8,  "date": "2026-06-13", "home": "Australia",    "away": "TBD",           "venue": "Arrowhead Stadium",               "city": "Kansas City",     "group": "D"},
    # Group E
    {"mn": 9,  "date": "2026-06-14", "home": "Germany",      "away": "Curaçao",       "venue": "NRG Stadium",                     "city": "Houston",         "group": "E"},
    {"mn": 10, "date": "2026-06-14", "home": "Côte d'Ivoire","away": "Ecuador",       "venue": "Lincoln Financial Field",         "city": "Philadelphia",    "group": "E"},
    # Group F
    {"mn": 11, "date": "2026-06-14", "home": "Netherlands",  "away": "Japan",         "venue": "AT&T Stadium",                    "city": "Arlington",       "group": "F"},
    {"mn": 12, "date": "2026-06-14", "home": "TBD",          "away": "Tunisia",       "venue": "Estadio BBVA",                    "city": "Monterrey",       "group": "F"},
    # Group G
    {"mn": 13, "date": "2026-06-15", "home": "Belgium",      "away": "Egypt",         "venue": "Lumen Field",                     "city": "Seattle",         "group": "G"},
    {"mn": 14, "date": "2026-06-15", "home": "IR Iran",      "away": "New Zealand",   "venue": "Empower Field at Mile High",      "city": "Denver",          "group": "G"},
    # Group H
    {"mn": 15, "date": "2026-06-15", "home": "Spain",        "away": "Cabo Verde",    "venue": "Hard Rock Stadium",               "city": "Miami Gardens",   "group": "H"},
    {"mn": 16, "date": "2026-06-16", "home": "Saudi Arabia", "away": "Uruguay",       "venue": "Estadio BBVA",                    "city": "Monterrey",       "group": "H"},
    # Group I
    {"mn": 17, "date": "2026-06-16", "home": "France",       "away": "Senegal",       "venue": "Levi's Stadium",                  "city": "Santa Clara",     "group": "I"},
    {"mn": 18, "date": "2026-06-16", "home": "TBD",          "away": "Norway",        "venue": "Mercedes-Benz Stadium",           "city": "Atlanta",         "group": "I"},
    # Group J
    {"mn": 19, "date": "2026-06-17", "home": "Argentina",    "away": "Algeria",       "venue": "Levi's Stadium",                  "city": "Santa Clara",     "group": "J"},
    {"mn": 20, "date": "2026-06-17", "home": "Austria",      "away": "Jordan",        "venue": "Empower Field at Mile High",      "city": "Denver",          "group": "J"},
    # Group K
    {"mn": 21, "date": "2026-06-17", "home": "Portugal",     "away": "TBD",           "venue": "Gillette Stadium",                "city": "Foxborough",      "group": "K"},
    {"mn": 22, "date": "2026-06-17", "home": "Uzbekistan",   "away": "Colombia",      "venue": "Arrowhead Stadium",               "city": "Kansas City",     "group": "K"},
    # Group L
    {"mn": 23, "date": "2026-06-17", "home": "England",      "away": "Croatia",       "venue": "AT&T Stadium",                    "city": "Arlington",       "group": "L"},
    {"mn": 24, "date": "2026-06-18", "home": "Ghana",        "away": "Panama",        "venue": "NRG Stadium",                     "city": "Houston",         "group": "L"},

    # ── GROUP STAGE — MATCHDAY 2 ──
    # Group A
    {"mn": 25, "date": "2026-06-19", "home": "Mexico",       "away": "Korea Republic","venue": "Estadio Azteca",                  "city": "Mexico City",     "group": "A"},
    {"mn": 26, "date": "2026-06-19", "home": "South Africa", "away": "TBD",           "venue": "Estadio Akron",                   "city": "Guadalajara",     "group": "A"},
    # Group B
    {"mn": 27, "date": "2026-06-19", "home": "Canada",       "away": "Qatar",         "venue": "BMO Field",                       "city": "Toronto",         "group": "B"},
    {"mn": 28, "date": "2026-06-19", "home": "Switzerland",  "away": "TBD",           "venue": "Levi's Stadium",                  "city": "Santa Clara",     "group": "B"},
    # Group C
    {"mn": 29, "date": "2026-06-19", "home": "Brazil",       "away": "Haiti",         "venue": "Lincoln Financial Field",         "city": "Philadelphia",    "group": "C"},
    {"mn": 30, "date": "2026-06-20", "home": "Morocco",      "away": "Scotland",      "venue": "Gillette Stadium",                "city": "Foxborough",      "group": "C"},
    # Group D
    {"mn": 31, "date": "2026-06-20", "home": "United States","away": "Australia",     "venue": "Lumen Field",                     "city": "Seattle",         "group": "D"},
    {"mn": 32, "date": "2026-06-20", "home": "Paraguay",     "away": "TBD",           "venue": "Empower Field at Mile High",      "city": "Denver",          "group": "D"},
    # Group E
    {"mn": 33, "date": "2026-06-20", "home": "Germany",      "away": "Côte d'Ivoire", "venue": "AT&T Stadium",                   "city": "Arlington",       "group": "E"},
    {"mn": 34, "date": "2026-06-21", "home": "Ecuador",      "away": "Curaçao",       "venue": "Hard Rock Stadium",               "city": "Miami Gardens",   "group": "E"},
    # Group F
    {"mn": 35, "date": "2026-06-21", "home": "Netherlands",  "away": "TBD",           "venue": "NRG Stadium",                     "city": "Houston",         "group": "F"},
    {"mn": 36, "date": "2026-06-21", "home": "Japan",        "away": "Tunisia",       "venue": "Estadio BBVA",                    "city": "Monterrey",       "group": "F"},
    # Group G
    {"mn": 37, "date": "2026-06-21", "home": "Belgium",      "away": "IR Iran",       "venue": "Mercedes-Benz Stadium",           "city": "Atlanta",         "group": "G"},
    {"mn": 38, "date": "2026-06-22", "home": "Egypt",        "away": "New Zealand",   "venue": "Arrowhead Stadium",               "city": "Kansas City",     "group": "G"},
    # Group H
    {"mn": 39, "date": "2026-06-22", "home": "Spain",        "away": "Saudi Arabia",  "venue": "Lumen Field",                     "city": "Seattle",         "group": "H"},
    {"mn": 40, "date": "2026-06-22", "home": "Uruguay",      "away": "Cabo Verde",    "venue": "Hard Rock Stadium",               "city": "Miami Gardens",   "group": "H"},
    # Group I
    {"mn": 41, "date": "2026-06-22", "home": "France",       "away": "TBD",           "venue": "MetLife Stadium",                 "city": "East Rutherford", "group": "I"},
    {"mn": 42, "date": "2026-06-23", "home": "Senegal",      "away": "Norway",        "venue": "SoFi Stadium",                    "city": "Inglewood",       "group": "I"},
    # Group J
    {"mn": 43, "date": "2026-06-23", "home": "Argentina",    "away": "Austria",       "venue": "Lincoln Financial Field",         "city": "Philadelphia",    "group": "J"},
    {"mn": 44, "date": "2026-06-23", "home": "Algeria",      "away": "Jordan",        "venue": "BC Place",                        "city": "Vancouver",       "group": "J"},
    # Group K
    {"mn": 45, "date": "2026-06-23", "home": "Portugal",     "away": "Uzbekistan",    "venue": "Levi's Stadium",                  "city": "Santa Clara",     "group": "K"},
    {"mn": 46, "date": "2026-06-23", "home": "TBD",          "away": "Colombia",      "venue": "AT&T Stadium",                    "city": "Arlington",       "group": "K"},
    # Group L
    {"mn": 47, "date": "2026-06-24", "home": "England",      "away": "Panama",        "venue": "Mercedes-Benz Stadium",           "city": "Atlanta",         "group": "L"},
    {"mn": 48, "date": "2026-06-24", "home": "Croatia",      "away": "Ghana",         "venue": "BMO Field",                       "city": "Toronto",         "group": "L"},

    # ── GROUP STAGE — MATCHDAY 3 ──
    # Group A
    {"mn": 49, "date": "2026-06-24", "home": "Mexico",       "away": "TBD",           "venue": "Estadio Azteca",                  "city": "Mexico City",     "group": "A"},
    {"mn": 50, "date": "2026-06-24", "home": "South Africa", "away": "Korea Republic","venue": "Estadio Akron",                   "city": "Guadalajara",     "group": "A"},
    # Group B
    {"mn": 51, "date": "2026-06-25", "home": "Canada",       "away": "Switzerland",   "venue": "BMO Field",                       "city": "Toronto",         "group": "B"},
    {"mn": 52, "date": "2026-06-25", "home": "Qatar",        "away": "TBD",           "venue": "BC Place",                        "city": "Vancouver",       "group": "B"},
    # Group C
    {"mn": 53, "date": "2026-06-24", "home": "Brazil",       "away": "Scotland",      "venue": "Hard Rock Stadium",               "city": "Miami Gardens",   "group": "C"},
    {"mn": 54, "date": "2026-06-24", "home": "Morocco",      "away": "Haiti",         "venue": "Mercedes-Benz Stadium",           "city": "Atlanta",         "group": "C"},
    # Group D
    {"mn": 55, "date": "2026-06-25", "home": "United States","away": "TBD",           "venue": "SoFi Stadium",                    "city": "Inglewood",       "group": "D"},
    {"mn": 56, "date": "2026-06-25", "home": "Paraguay",     "away": "Australia",     "venue": "Arrowhead Stadium",               "city": "Kansas City",     "group": "D"},
    # Group E
    {"mn": 57, "date": "2026-06-25", "home": "Germany",      "away": "Ecuador",       "venue": "AT&T Stadium",                    "city": "Arlington",       "group": "E"},
    {"mn": 58, "date": "2026-06-25", "home": "Côte d'Ivoire","away": "Curaçao",       "venue": "NRG Stadium",                     "city": "Houston",         "group": "E"},
    # Group F
    {"mn": 59, "date": "2026-06-25", "home": "Netherlands",  "away": "Tunisia",       "venue": "Levi's Stadium",                  "city": "Santa Clara",     "group": "F"},
    {"mn": 60, "date": "2026-06-25", "home": "Japan",        "away": "TBD",           "venue": "Estadio BBVA",                    "city": "Monterrey",       "group": "F"},
    # Group G
    {"mn": 61, "date": "2026-06-26", "home": "Belgium",      "away": "New Zealand",   "venue": "Lumen Field",                     "city": "Seattle",         "group": "G"},
    {"mn": 62, "date": "2026-06-26", "home": "IR Iran",      "away": "Egypt",         "venue": "Empower Field at Mile High",      "city": "Denver",          "group": "G"},
    # Group H
    {"mn": 63, "date": "2026-06-26", "home": "Spain",        "away": "Uruguay",       "venue": "Hard Rock Stadium",               "city": "Miami Gardens",   "group": "H"},
    {"mn": 64, "date": "2026-06-26", "home": "Saudi Arabia", "away": "Cabo Verde",    "venue": "Lincoln Financial Field",         "city": "Philadelphia",    "group": "H"},
    # Group I
    {"mn": 65, "date": "2026-06-26", "home": "France",       "away": "Norway",        "venue": "MetLife Stadium",                 "city": "East Rutherford", "group": "I"},
    {"mn": 66, "date": "2026-06-26", "home": "Senegal",      "away": "TBD",           "venue": "SoFi Stadium",                    "city": "Inglewood",       "group": "I"},
    # Group J
    {"mn": 67, "date": "2026-06-27", "home": "Argentina",    "away": "Jordan",        "venue": "Empower Field at Mile High",      "city": "Denver",          "group": "J"},
    {"mn": 68, "date": "2026-06-27", "home": "Algeria",      "away": "Austria",       "venue": "Arrowhead Stadium",               "city": "Kansas City",     "group": "J"},
    # Group K
    {"mn": 69, "date": "2026-06-27", "home": "Portugal",     "away": "Colombia",      "venue": "NRG Stadium",                     "city": "Houston",         "group": "K"},
    {"mn": 70, "date": "2026-06-27", "home": "Uzbekistan",   "away": "TBD",           "venue": "BC Place",                        "city": "Vancouver",       "group": "K"},
    # Group L
    {"mn": 71, "date": "2026-06-27", "home": "England",      "away": "Ghana",         "venue": "Lincoln Financial Field",         "city": "Philadelphia",    "group": "L"},
    {"mn": 72, "date": "2026-06-27", "home": "Croatia",      "away": "Panama",        "venue": "BMO Field",                       "city": "Toronto",         "group": "L"},

    # ── ROUND OF 32 ──
    {"mn": 73,  "date": "2026-06-28", "home": "TBD", "away": "TBD", "venue": "SoFi Stadium",              "city": "Inglewood",       "group": None},
    {"mn": 74,  "date": "2026-06-28", "home": "TBD", "away": "TBD", "venue": "Gillette Stadium",          "city": "Foxborough",      "group": None},
    {"mn": 75,  "date": "2026-06-29", "home": "TBD", "away": "TBD", "venue": "Estadio Akron",             "city": "Guadalajara",     "group": None},
    {"mn": 76,  "date": "2026-06-29", "home": "TBD", "away": "TBD", "venue": "NRG Stadium",               "city": "Houston",         "group": None},
    {"mn": 77,  "date": "2026-06-30", "home": "TBD", "away": "TBD", "venue": "MetLife Stadium",           "city": "East Rutherford", "group": None},
    {"mn": 78,  "date": "2026-06-30", "home": "TBD", "away": "TBD", "venue": "AT&T Stadium",              "city": "Arlington",       "group": None},
    {"mn": 79,  "date": "2026-07-01", "home": "TBD", "away": "TBD", "venue": "Estadio Azteca",            "city": "Mexico City",     "group": None},
    {"mn": 80,  "date": "2026-07-01", "home": "TBD", "away": "TBD", "venue": "Mercedes-Benz Stadium",     "city": "Atlanta",         "group": None},
    {"mn": 81,  "date": "2026-07-01", "home": "TBD", "away": "TBD", "venue": "Levi's Stadium",            "city": "Santa Clara",     "group": None},
    {"mn": 82,  "date": "2026-07-01", "home": "TBD", "away": "TBD", "venue": "Lumen Field",               "city": "Seattle",         "group": None},
    {"mn": 83,  "date": "2026-07-02", "home": "TBD", "away": "TBD", "venue": "BMO Field",                 "city": "Toronto",         "group": None},
    {"mn": 84,  "date": "2026-07-02", "home": "TBD", "away": "TBD", "venue": "SoFi Stadium",              "city": "Inglewood",       "group": None},
    {"mn": 85,  "date": "2026-07-02", "home": "TBD", "away": "TBD", "venue": "BC Place",                  "city": "Vancouver",       "group": None},
    {"mn": 86,  "date": "2026-07-03", "home": "TBD", "away": "TBD", "venue": "Hard Rock Stadium",         "city": "Miami Gardens",   "group": None},
    {"mn": 87,  "date": "2026-07-03", "home": "TBD", "away": "TBD", "venue": "Arrowhead Stadium",         "city": "Kansas City",     "group": None},
    {"mn": 88,  "date": "2026-07-03", "home": "TBD", "away": "TBD", "venue": "AT&T Stadium",              "city": "Arlington",       "group": None},

    # ── ROUND OF 16 ──
    {"mn": 89,  "date": "2026-07-04", "home": "TBD", "away": "TBD", "venue": "MetLife Stadium",           "city": "East Rutherford", "group": None},
    {"mn": 90,  "date": "2026-07-04", "home": "TBD", "away": "TBD", "venue": "SoFi Stadium",              "city": "Inglewood",       "group": None},
    {"mn": 91,  "date": "2026-07-05", "home": "TBD", "away": "TBD", "venue": "AT&T Stadium",              "city": "Arlington",       "group": None},
    {"mn": 92,  "date": "2026-07-05", "home": "TBD", "away": "TBD", "venue": "Levi's Stadium",            "city": "Santa Clara",     "group": None},
    {"mn": 93,  "date": "2026-07-06", "home": "TBD", "away": "TBD", "venue": "Hard Rock Stadium",         "city": "Miami Gardens",   "group": None},
    {"mn": 94,  "date": "2026-07-06", "home": "TBD", "away": "TBD", "venue": "Lincoln Financial Field",   "city": "Philadelphia",    "group": None},
    {"mn": 95,  "date": "2026-07-07", "home": "TBD", "away": "TBD", "venue": "Mercedes-Benz Stadium",     "city": "Atlanta",         "group": None},
    {"mn": 96,  "date": "2026-07-07", "home": "TBD", "away": "TBD", "venue": "BC Place",                  "city": "Vancouver",       "group": None},

    # ── QUARTER-FINALS ──
    {"mn": 97,  "date": "2026-07-09", "home": "TBD", "away": "TBD", "venue": "Gillette Stadium",          "city": "Foxborough",      "group": None},
    {"mn": 98,  "date": "2026-07-10", "home": "TBD", "away": "TBD", "venue": "SoFi Stadium",              "city": "Inglewood",       "group": None},
    {"mn": 99,  "date": "2026-07-11", "home": "TBD", "away": "TBD", "venue": "Hard Rock Stadium",         "city": "Miami Gardens",   "group": None},
    {"mn": 100, "date": "2026-07-11", "home": "TBD", "away": "TBD", "venue": "Arrowhead Stadium",         "city": "Kansas City",     "group": None},

    # ── SEMI-FINALS ──
    {"mn": 101, "date": "2026-07-14", "home": "TBD", "away": "TBD", "venue": "AT&T Stadium",              "city": "Arlington",       "group": None},
    {"mn": 102, "date": "2026-07-15", "home": "TBD", "away": "TBD", "venue": "Mercedes-Benz Stadium",     "city": "Atlanta",         "group": None},

    # ── 3RD PLACE ──
    {"mn": 103, "date": "2026-07-18", "home": "TBD", "away": "TBD", "venue": "Hard Rock Stadium",         "city": "Miami Gardens",   "group": None},

    # ── FINAL ──
    {"mn": 104, "date": "2026-07-19", "home": "TBD", "away": "TBD", "venue": "MetLife Stadium",           "city": "East Rutherford", "group": None},
]
# fmt: on

ROUND_MAP = {
    range(1, 73): "Group",
    range(73, 89): "Round of 32",
    range(89, 97): "Round of 16",
    range(97, 101): "Quarter-final",
    range(101, 103): "Semi-final",
    range(103, 104): "3rd Place",
    range(104, 105): "Final",
}

MEXICO_CITIES = {"Mexico City", "Monterrey", "Guadalajara"}
CANADA_CITIES = {"Vancouver", "Toronto"}


def _get_round(match_number: int) -> str:
    for rng, name in ROUND_MAP.items():
        if match_number in rng:
            return name
    return "Group"


def _detect_country(venue: str, city: str) -> str:
    if venue in MEXICO_VENUES:
        return "Mexico"
    if city in MEXICO_CITIES:
        return "Mexico"
    if city in CANADA_CITIES:
        return "Canada"
    return "USA"


def collect() -> int:
    """Seed all 104 World Cup fixtures into the database. Returns count upserted."""
    count = 0
    for f in FIXTURES:
        mn = f["mn"]
        round_name = _get_round(mn)
        country = _detect_country(f["venue"], f["city"])
        is_mexico = country == "Mexico"
        face = FACE_VALUES.get(round_name, FACE_VALUES["Group"])

        upsert_match(
            external_id=str(mn),
            home_team=f["home"],
            away_team=f["away"],
            match_date=f["date"],
            venue=f["venue"],
            city=f["city"],
            country=country,
            round=round_name,
            status="scheduled",
            home_score=None,
            away_score=None,
            face_value_cat1=face["cat1"],
            face_value_cat2=face["cat2"],
            face_value_cat3=face["cat3"],
            is_mexico_venue=is_mexico,
        )
        count += 1
    return count
