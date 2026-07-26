"""
Lưu trữ bằng SQLite — chống gửi trùng bài, và theo dõi bài nào
đã đưa vào digest sáng / đã bắn alert HOT.
"""
import sqlite3
import time
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    link            TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    source          TEXT NOT NULL,
    published_ts    REAL NOT NULL,
    key_point       TEXT,
    insight         TEXT,
    skill_tip       TEXT,
    hot_score       INTEGER DEFAULT 0,
    sent_alert      INTEGER DEFAULT 0,
    sent_digest     INTEGER DEFAULT 0,
    created_ts      REAL NOT NULL
);
"""


@contextmanager
def _connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str):
    with _connect(db_path) as conn:
        conn.execute(SCHEMA)


def get_seen_urls(db_path: str) -> set:
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT link FROM articles").fetchall()
    return {row["link"] for row in rows}


def save_article(db_path: str, article: dict, insight: dict):
    """article: dict từ sources.fetch_new_articles(); insight: dict từ insight.extract_insight()"""
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO articles
                (link, title, source, published_ts, key_point, insight, skill_tip, hot_score, created_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                article["link"],
                article["title"],
                article["source"],
                article["published_ts"],
                insight.get("key_point", ""),
                insight.get("insight", ""),
                insight.get("skill_tip", ""),
                insight.get("hot_score", 0),
                time.time(),
            ),
        )


def mark_alert_sent(db_path: str, link: str):
    with _connect(db_path) as conn:
        conn.execute("UPDATE articles SET sent_alert = 1 WHERE link = ?", (link,))


def get_pending_digest_articles(db_path: str) -> list[dict]:
    """Lấy các bài chưa từng vào digest, mới nhất trước."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE sent_digest = 0 ORDER BY published_ts DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def mark_digest_sent(db_path: str, links: list[str]):
    if not links:
        return
    with _connect(db_path) as conn:
        placeholders = ",".join("?" for _ in links)
        conn.execute(
            f"UPDATE articles SET sent_digest = 1 WHERE link IN ({placeholders})", links
        )
