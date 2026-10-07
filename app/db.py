import sqlite3
from pathlib import Path

from app.models import Novel


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "diviner.db"


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    base_url TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS novels (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT 'Unknown',
    source_id INTEGER NOT NULL,
    url TEXT NOT NULL UNIQUE,
    rating REAL NOT NULL DEFAULT 0,
    rating_count INTEGER NOT NULL DEFAULT 0,
    views INTEGER NOT NULL DEFAULT 0,
    favorites INTEGER NOT NULL DEFAULT 0,
    follows INTEGER NOT NULL DEFAULT 0,
    bookmarks INTEGER NOT NULL DEFAULT 0,
    kudos INTEGER NOT NULL DEFAULT 0,
    reviews INTEGER NOT NULL DEFAULT 0,
    comments INTEGER NOT NULL DEFAULT 0,
    popularity_score REAL NOT NULL DEFAULT 0,
    chapters INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'unknown',
    synopsis TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS novel_genres (
    novel_id TEXT NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (novel_id, genre_id),
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS novel_tags (
    novel_id TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (novel_id, tag_id),
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    items_found INTEGER NOT NULL DEFAULT 0,
    message TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS novel_search USING fts5(
    novel_id UNINDEXED,
    title,
    author,
    source,
    genres,
    tags,
    synopsis,
    status
);
"""


def connect(path: Path = DATABASE) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize(path: Path = DATABASE) -> None:
    with connect(path) as db:
        db.executescript(SCHEMA)


def get_or_create_id(db: sqlite3.Connection, table: str, name: str) -> int:
    clean_name = name.strip()
    row = db.execute(f"SELECT id FROM {table} WHERE name = ?", (clean_name,)).fetchone()
    if row:
        return int(row["id"])
    cursor = db.execute(f"INSERT INTO {table} (name) VALUES (?)", (clean_name,))
    return int(cursor.lastrowid)


def source_id(db: sqlite3.Connection, source: str) -> int:
    return get_or_create_id(db, "sources", source)


def calculate_popularity(novel: Novel) -> float:
    score = novel.popularity_score
    score += novel.rating * 10
    score += min(novel.views / 10000, 50)
    score += min((novel.favorites + novel.follows + novel.bookmarks + novel.kudos) / 100, 50)
    score += min((novel.reviews + novel.comments) / 50, 30)
    return round(score, 3)
