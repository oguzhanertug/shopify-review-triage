import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "state.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_reviews (
            review_id INTEGER PRIMARY KEY,
            processed_at TEXT NOT NULL
        )
        """
    )
    return conn


def is_processed(conn, review_id):
    row = conn.execute(
        "SELECT 1 FROM processed_reviews WHERE review_id = ?", (review_id,)
    ).fetchone()
    return row is not None


def mark_processed(conn, review_id):
    # INSERT OR IGNORE: review_id zaten varsa sessizce hiçbir şey yapmaz —
    # aynı ID'yi iki kez işaretlemeye çalışmak hata fırlatmaz.
    conn.execute(
        "INSERT OR IGNORE INTO processed_reviews (review_id, processed_at) VALUES (?, datetime('now'))",
        (review_id,),
    )
    conn.commit()
