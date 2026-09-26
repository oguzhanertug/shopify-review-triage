import os

from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv()

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
CHANNEL = os.getenv("SLACK_CHANNEL_ID")
MAX_BODY_CHARS = 1500  # Slack bölüm metni sınırı 3000; uzun yorum mesajı reddettirmesin


def escape(text):
    # Slack & < > karakterlerini özel işaretleme sayar (<!channel>, <@kullanici>,
    # bağlantılar). Yorum ve model çıktısı güvenilmez girdidir; kaçmadan
    # basarsak yorum yazan biri kanalda herkesi etiketleyebilir.
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def quote(text):
    shown = escape(text[:MAX_BODY_CHARS])
    if len(text) > MAX_BODY_CHARS:
        shown += " …(kısaltıldı)"
    return "\n".join(f"> {line}" for line in shown.splitlines() or [""])


def post_auto_answerable(review_id, review, triage, draft_text):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Yeni yorum* — {review['rating']}/5, "
                    f"{escape(triage['sentiment'])} / {escape(triage['topic'])}\n"
                    f"{quote(review['body'])}\n\n"
                    f"*Önerilen yanıt:*\n{escape(draft_text)}"
                ),
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Onayla ve gönder"},
                    "style": "primary",
                    "action_id": "onayla",
                    "value": str(review_id),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reddet"},
                    "style": "danger",
                    "action_id": "reddet",
                    "value": str(review_id),
                },
            ],
        },
    ]
    client.chat_postMessage(channel=CHANNEL, blocks=blocks, text="Yeni yorum triyaj edildi")


def post_needs_human(review_id, review, triage):
    if triage.get("format_error"):
        header = (
            "*Teknik hata: otomatik triyaj tamamlanamadı.* "
            "Yorumun kendisi riskli olmayabilir; model yanıtı okunamadı, lütfen elle inceleyin."
        )
        detail = f"*Ayrıntı:* {escape(triage['reason'])}"
    else:
        header = f"*İnsana gitmesi gereken bir yorum* — {escape(triage['sentiment'])} / {escape(triage['topic'])}"
        detail = f"*Neden:* {escape(triage['reason'])}"

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{header}\n{review['rating']}/5\n{quote(review['body'])}\n\n{detail}",
            },
        }
    ]
    client.chat_postMessage(channel=CHANNEL, blocks=blocks, text="İnsana yönlendirilen yorum")
