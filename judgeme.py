import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("JUDGEME_API_TOKEN")
SHOP_DOMAIN = os.getenv("JUDGEME_SHOP_DOMAIN")
REPLIES_URL = "https://api.judge.me/api/v1/replies"


def post_reply(review_id, text):
    """Yoruma herkese açık yanıt gönderir. Başarılıysa True döner."""
    try:
        response = requests.post(
            REPLIES_URL,
            headers={"X-Api-Token": API_TOKEN},
            params={"shop_domain": SHOP_DOMAIN},
            json={
                "review_id": review_id,
                "send_reply_email": False,  # sadece herkese açık yanıt; yorumcuya e-posta gitmesin
                "reply": {"content": text},
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        print(f"[JUDGE.ME HATASI] yanıt gönderilemedi (review_id={review_id}): {exc}")
        return False

    if response.status_code != 200:
        print(f"[JUDGE.ME HATASI] review_id={review_id} durum={response.status_code}")
        return False
    return True
