import os
import json
import time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
import requests

from pipeline import process_review
from state import get_connection, is_processed, mark_processed

load_dotenv()

API_TOKEN = os.getenv("JUDGEME_API_TOKEN")
SHOP_DOMAIN = os.getenv("JUDGEME_SHOP_DOMAIN")
REVIEWS_URL = "https://judge.me/api/v1/reviews"
STATE_FILE = Path(__file__).parent / "poll_state.json"
POLL_INTERVAL_SECONDS = 30  # test için kısa; gerçek kullanımda 5-15 dk yeterli


def load_last_seen():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text()).get("last_seen_created_at")
    return None


def save_last_seen(created_at):
    STATE_FILE.write_text(json.dumps({"last_seen_created_at": created_at}))


def fetch_reviews():
    params = {"api_token": API_TOKEN, "shop_domain": SHOP_DOMAIN, "per_page": 20}
    response = requests.get(REVIEWS_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()["reviews"]


def poll_once(conn, last_seen):
    reviews = fetch_reviews()
    last_seen_dt = datetime.fromisoformat(last_seen) if last_seen else None

    # created_at watermark: sorguyu makul bir pencereye daraltmak için kaba bir
    # ön filtre (>=, kesin değil — aynı saniyede iki yorum olabilir). Asıl
    # tekilleştirme garantisi state.db'deki review_id kontrolünden geliyor.
    candidates = [
        r for r in reviews
        if last_seen_dt is None or datetime.fromisoformat(r["created_at"]) >= last_seen_dt
    ]
    candidates.sort(key=lambda r: r["created_at"])

    advance = True
    for review in candidates:
        if not is_processed(conn, review["id"]):
            try:
                process_review(conn, review)
            except Exception as exc:  # tek bir yorum döngüyü durdurmasın
                # Watermark artık ilerlemez: aksi halde daha yeni bir yorum
                # başarılı olunca >= filtresi bu yorumu bir daha hiç göstermezdi.
                advance = False
                print(f"[HATA] review_id={review['id']} işlenemedi, sonraki turda tekrar denenecek: {exc}")
                continue
            mark_processed(conn, review["id"])
            print(f"[İŞLENDİ] review_id={review['id']} puan={review['rating']}")
        if advance:
            last_seen = review["created_at"]

    if last_seen:
        save_last_seen(last_seen)

    return last_seen


def main():
    last_seen = load_last_seen()
    conn = get_connection()
    print("Polling başladı. Beklenen mağaza:", SHOP_DOMAIN)
    while True:
        try:
            last_seen = poll_once(conn, last_seen)
        except requests.RequestException as exc:
            print("Judge.me isteği başarısız:", exc)
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
