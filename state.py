import json
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
    # Her yorumun kararı: Slack'te gösterilen, onaylanınca gönderilen metin
    # buradaki draft_text ile birebir aynı olmak zorunda — Slack'ten gelen
    # isteğe asla güvenmeyiz, gönderilecek metni her zaman buradan okuruz.
    # status: pending (onay bekliyor) | needs_human | sending | sent | rejected
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS decisions (
            review_id INTEGER PRIMARY KEY,
            triage_json TEXT NOT NULL,
            draft_text TEXT,
            status TEXT NOT NULL,
            decided_by TEXT
        )
        """
    )
    # Mağaza içi destek/iade formundan (Modül 14) gelen ham talepler. Henüz
    # doğrulanmamış: email/order_number müşterinin kendi beyanı, kanıt değil
    # (Modül 15 bunu Shopify siparişleriyle eşleştirecek).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS support_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            order_number TEXT NOT NULL,
            message TEXT NOT NULL,
            received_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'yeni'
        )
        """
    )
    return conn


def save_support_request(conn, email, order_number, message):
    conn.execute(
        """
        INSERT INTO support_requests (email, order_number, message, received_at, status)
        VALUES (?, ?, ?, datetime('now'), 'yeni')
        """,
        (email, order_number, message),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


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


def get_decision(conn, review_id):
    row = conn.execute(
        "SELECT triage_json, draft_text, status FROM decisions WHERE review_id = ?",
        (review_id,),
    ).fetchone()
    if row is None:
        return None
    return {"triage": json.loads(row[0]), "draft_text": row[1], "status": row[2]}


def save_decision(conn, review_id, triage, draft_text):
    # INSERT OR IGNORE: ilk karar kalır. Slack gönderimi hata verip yorum
    # yeniden işlenirse LLM tekrar çağrılmaz, aynı karar kullanılır.
    status = "pending" if draft_text else "needs_human"
    conn.execute(
        "INSERT OR IGNORE INTO decisions (review_id, triage_json, draft_text, status) VALUES (?, ?, ?, ?)",
        (review_id, json.dumps(triage, ensure_ascii=False), draft_text, status),
    )
    conn.commit()


def claim_pending(conn, review_id, new_status, user):
    # Tek bir UPDATE ... WHERE status='pending': iki kişi aynı anda "Onayla"ya
    # bassa bile yalnızca biri rowcount==1 alır, ikinci yanıt gönderilmez.
    cursor = conn.execute(
        "UPDATE decisions SET status = ?, decided_by = ? WHERE review_id = ? AND status = 'pending'",
        (new_status, user, review_id),
    )
    conn.commit()
    return cursor.rowcount == 1


def set_status(conn, review_id, status):
    conn.execute("UPDATE decisions SET status = ? WHERE review_id = ?", (status, review_id))
    conn.commit()
