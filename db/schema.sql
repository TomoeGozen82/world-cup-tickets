CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    home_team TEXT,
    away_team TEXT,
    match_date TEXT,
    venue TEXT,
    city TEXT,
    country TEXT,
    round TEXT,
    status TEXT DEFAULT 'scheduled',
    home_score INTEGER,
    away_score INTEGER,
    face_value_cat1 INTEGER,
    face_value_cat2 INTEGER,
    face_value_cat3 INTEGER,
    is_mexico_venue INTEGER DEFAULT 0,
    value_score INTEGER DEFAULT 0,
    seatgeek_id INTEGER,
    seatgeek_url TEXT,
    resale_lowest INTEGER,
    resale_median INTEGER,
    resale_average INTEGER,
    resale_highest INTEGER,
    listing_count INTEGER DEFAULT 0,
    resale_updated_at TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    fetched_at TEXT DEFAULT (datetime('now')),
    lowest_price INTEGER,
    median_price INTEGER,
    average_price INTEGER,
    highest_price INTEGER,
    listing_count INTEGER DEFAULT 0,
    FOREIGN KEY (match_id) REFERENCES matches(id)
);
CREATE INDEX IF NOT EXISTS idx_snapshots_match ON price_snapshots(match_id, fetched_at);

CREATE TABLE IF NOT EXISTS news_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TEXT,
    fetched_at TEXT DEFAULT (datetime('now')),
    external_id TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS reddit_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subreddit TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    num_comments INTEGER DEFAULT 0,
    published_at TEXT,
    fetched_at TEXT DEFAULT (datetime('now')),
    external_id TEXT UNIQUE,
    sentiment TEXT DEFAULT 'neutral'
);
