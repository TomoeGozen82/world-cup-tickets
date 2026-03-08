import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "tickets.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA_PATH.read_text())


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------

def upsert_match(
    external_id: str,
    home_team: str | None,
    away_team: str | None,
    match_date: str | None,
    venue: str | None,
    city: str | None,
    country: str | None,
    round: str | None,
    status: str = "scheduled",
    home_score: int | None = None,
    away_score: int | None = None,
    face_value_cat1: int | None = None,
    face_value_cat2: int | None = None,
    face_value_cat3: int | None = None,
    is_mexico_venue: bool = False,
    value_score: int = 0,
) -> bool:
    """Insert or update a match. Returns True if newly inserted."""
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO matches (
                external_id, home_team, away_team, match_date, venue, city, country,
                round, status, home_score, away_score,
                face_value_cat1, face_value_cat2, face_value_cat3,
                is_mexico_venue, value_score, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(external_id) DO UPDATE SET
                home_team=excluded.home_team,
                away_team=excluded.away_team,
                match_date=excluded.match_date,
                venue=excluded.venue,
                city=excluded.city,
                country=excluded.country,
                round=excluded.round,
                status=excluded.status,
                home_score=excluded.home_score,
                away_score=excluded.away_score,
                face_value_cat1=excluded.face_value_cat1,
                face_value_cat2=excluded.face_value_cat2,
                face_value_cat3=excluded.face_value_cat3,
                is_mexico_venue=excluded.is_mexico_venue,
                value_score=excluded.value_score,
                updated_at=datetime('now')
            """,
            (
                external_id, home_team, away_team, match_date, venue, city, country,
                round, status, home_score, away_score,
                face_value_cat1, face_value_cat2, face_value_cat3,
                int(is_mexico_venue), value_score,
            ),
        )
        return cursor.rowcount > 0


def get_all_matches() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM matches ORDER BY match_date, id"
        ).fetchall()


def get_matches_by_round(round: str) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM matches WHERE round = ? ORDER BY match_date",
            (round,),
        ).fetchall()


def update_value_score(match_id: int, score: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE matches SET value_score = ? WHERE id = ?",
            (score, match_id),
        )


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------

def insert_news(source_name: str, title: str, url: str, published_at: str | None, external_id: str) -> bool:
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO news_items (source_name, title, url, published_at, external_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (source_name, title, url, published_at, external_id),
        )
        return cursor.rowcount > 0


def get_news(limit: int = 50) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM news_items ORDER BY published_at DESC LIMIT ?",
            (limit,),
        ).fetchall()


# ---------------------------------------------------------------------------
# Reddit
# ---------------------------------------------------------------------------

def insert_reddit_post(
    subreddit: str, title: str, url: str, score: int, num_comments: int,
    published_at: str | None, external_id: str, sentiment: str = "neutral",
) -> bool:
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO reddit_posts
                (subreddit, title, url, score, num_comments, published_at, external_id, sentiment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (subreddit, title, url, score, num_comments, published_at, external_id, sentiment),
        )
        return cursor.rowcount > 0


def get_reddit_posts(limit: int = 50) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM reddit_posts ORDER BY published_at DESC LIMIT ?",
            (limit,),
        ).fetchall()


# ---------------------------------------------------------------------------
# SeatGeek / Price Snapshots
# ---------------------------------------------------------------------------

def update_seatgeek_mapping(match_id: int, seatgeek_id: int, seatgeek_url: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE matches SET seatgeek_id = ?, seatgeek_url = ? WHERE id = ?",
            (seatgeek_id, seatgeek_url, match_id),
        )


def update_resale_prices(
    match_id: int,
    lowest: int | None,
    median: int | None,
    average: int | None,
    highest: int | None,
    listing_count: int,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """UPDATE matches SET
                resale_lowest = ?, resale_median = ?, resale_average = ?,
                resale_highest = ?, listing_count = ?,
                resale_updated_at = datetime('now')
            WHERE id = ?""",
            (lowest, median, average, highest, listing_count, match_id),
        )


def insert_price_snapshot(
    match_id: int,
    lowest: int | None,
    median: int | None,
    average: int | None,
    highest: int | None,
    listing_count: int,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO price_snapshots
                (match_id, lowest_price, median_price, average_price, highest_price, listing_count)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (match_id, lowest, median, average, highest, listing_count),
        )


def get_price_history(match_id: int, limit: int = 30) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """SELECT * FROM price_snapshots
            WHERE match_id = ? ORDER BY fetched_at DESC LIMIT ?""",
            (match_id, limit),
        ).fetchall()


def get_matches_with_seatgeek_id() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, seatgeek_id FROM matches WHERE seatgeek_id IS NOT NULL"
        ).fetchall()
