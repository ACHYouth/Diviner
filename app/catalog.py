import json
from pathlib import Path
from typing import Optional

from app.db import DATABASE, calculate_popularity, connect, get_or_create_id, initialize, source_id
from app.models import Novel


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA = ROOT / "data" / "sample_novels.json"
DEFAULT_SOURCE_LIMIT = 100


class Catalog:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or DATABASE
        initialize(self.path)
        self.seed_if_empty()

    def seed_if_empty(self) -> None:
        with connect(self.path) as db:
            count = db.execute("SELECT COUNT(*) AS total FROM novels").fetchone()["total"]
        if count == 0 and SAMPLE_DATA.exists():
            rows = json.loads(SAMPLE_DATA.read_text(encoding="utf-8"))
            self.upsert_many([Novel(**row) for row in rows])

    def load(self) -> list[Novel]:
        with connect(self.path) as db:
            rows = db.execute(
                """
                SELECT
                    novels.*,
                    sources.name AS source
                FROM novels
                JOIN sources ON sources.id = novels.source_id
                ORDER BY novels.title COLLATE NOCASE
                """
            ).fetchall()

            novels = []
            for row in rows:
                genres = [
                    item["name"]
                    for item in db.execute(
                        """
                        SELECT genres.name
                        FROM genres
                        JOIN novel_genres ON novel_genres.genre_id = genres.id
                        WHERE novel_genres.novel_id = ?
                        ORDER BY genres.name COLLATE NOCASE
                        """,
                        (row["id"],),
                    )
                ]
                tags = [
                    item["name"]
                    for item in db.execute(
                        """
                        SELECT tags.name
                        FROM tags
                        JOIN novel_tags ON novel_tags.tag_id = tags.id
                        WHERE novel_tags.novel_id = ?
                        ORDER BY tags.name COLLATE NOCASE
                        """,
                        (row["id"],),
                    )
                ]
                novels.append(
                    Novel(
                        id=row["id"],
                        title=row["title"],
                        author=row["author"],
                        source=row["source"],
                        url=row["url"],
                        genres=genres,
                        tags=tags,
                        rating=row["rating"],
                        rating_count=row["rating_count"],
                        views=row["views"],
                        favorites=row["favorites"],
                        follows=row["follows"],
                        bookmarks=row["bookmarks"],
                        kudos=row["kudos"],
                        reviews=row["reviews"],
                        comments=row["comments"],
                        popularity_score=row["popularity_score"],
                        chapters=row["chapters"],
                        status=row["status"],
                        synopsis=row["synopsis"],
                    )
                )

            return novels

    def save(self, novels: list[Novel]) -> None:
        with connect(self.path) as db:
            db.execute("DELETE FROM novel_search")
            db.execute("DELETE FROM novel_genres")
            db.execute("DELETE FROM novel_tags")
            db.execute("DELETE FROM novels")
        self.upsert_many(novels)

    def upsert_many(self, incoming: list[Novel]) -> list[Novel]:
        with connect(self.path) as db:
            for novel in incoming:
                sid = source_id(db, novel.source)
                popularity = calculate_popularity(novel)
                db.execute(
                    """
                    INSERT INTO novels (
                        id, title, author, source_id, url, rating, rating_count, views,
                        favorites, follows, bookmarks, kudos, reviews, comments,
                        popularity_score, chapters, status, synopsis, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        author = excluded.author,
                        source_id = excluded.source_id,
                        url = excluded.url,
                        rating = excluded.rating,
                        rating_count = excluded.rating_count,
                        views = excluded.views,
                        favorites = excluded.favorites,
                        follows = excluded.follows,
                        bookmarks = excluded.bookmarks,
                        kudos = excluded.kudos,
                        reviews = excluded.reviews,
                        comments = excluded.comments,
                        popularity_score = excluded.popularity_score,
                        chapters = excluded.chapters,
                        status = excluded.status,
                        synopsis = excluded.synopsis,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        novel.id,
                        novel.title,
                        novel.author,
                        sid,
                        novel.url,
                        novel.rating,
                        novel.rating_count,
                        novel.views,
                        novel.favorites,
                        novel.follows,
                        novel.bookmarks,
                        novel.kudos,
                        novel.reviews,
                        novel.comments,
                        popularity,
                        novel.chapters,
                        novel.status,
                        novel.synopsis,
                    ),
                )

                db.execute("DELETE FROM novel_genres WHERE novel_id = ?", (novel.id,))
                db.execute("DELETE FROM novel_tags WHERE novel_id = ?", (novel.id,))
                for genre in novel.genres:
                    gid = get_or_create_id(db, "genres", genre)
                    db.execute(
                        "INSERT OR IGNORE INTO novel_genres (novel_id, genre_id) VALUES (?, ?)",
                        (novel.id, gid),
                    )
                for tag in novel.tags:
                    tid = get_or_create_id(db, "tags", tag)
                    db.execute(
                        "INSERT OR IGNORE INTO novel_tags (novel_id, tag_id) VALUES (?, ?)",
                        (novel.id, tid),
                    )

                self.update_search_index(db, novel)

        return self.load()

    def update_search_index(self, db, novel: Novel) -> None:
        db.execute("DELETE FROM novel_search WHERE novel_id = ?", (novel.id,))
        db.execute(
            """
            INSERT INTO novel_search (novel_id, title, author, source, genres, tags, synopsis, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                novel.id,
                novel.title,
                novel.author,
                novel.source,
                " ".join(novel.genres),
                " ".join(novel.tags),
                novel.synopsis,
                novel.status,
            ),
        )

    def source_counts(self) -> list[dict]:
        with connect(self.path) as db:
            return [
                {"source": row["source"], "count": row["count"]}
                for row in db.execute(
                    """
                    SELECT sources.name AS source, COUNT(novels.id) AS count
                    FROM sources
                    LEFT JOIN novels ON novels.source_id = sources.id
                    GROUP BY sources.id
                    ORDER BY count DESC, source COLLATE NOCASE
                    """
                )
            ]

    def count_for_source(self, source: str) -> int:
        with connect(self.path) as db:
            row = db.execute(
                """
                SELECT COUNT(novels.id) AS total
                FROM novels
                JOIN sources ON sources.id = novels.source_id
                WHERE sources.name = ?
                """,
                (source,),
            ).fetchone()
        return int(row["total"]) if row else 0

    def log_ingestion_run(self, source: str, status: str, items_found: int, message: str = "") -> None:
        with connect(self.path) as db:
            db.execute(
                """
                INSERT INTO ingestion_runs (source, status, items_found, message, finished_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (source, status, items_found, message),
            )

    def ensure_default_sources(self, limit: int = DEFAULT_SOURCE_LIMIT) -> None:
        from app.scrapers.registry import STARTUP_SOURCES

        for source_class in STARTUP_SOURCES.values():
            source = source_class()
            if self.count_for_source(source.name) >= limit:
                continue

            try:
                novels = source.fetch(limit)
                self.upsert_many(novels)
                self.log_ingestion_run(source.name, "success", len(novels))
            except Exception as exc:
                self.log_ingestion_run(source.name, "failed", 0, str(exc))

    def ingestion_runs(self, limit: int = 10) -> list[dict]:
        with connect(self.path) as db:
            return [
                dict(row)
                for row in db.execute(
                    """
                    SELECT source, status, items_found, message, started_at, finished_at
                    FROM ingestion_runs
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            ]
