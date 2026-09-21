import os

from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv()

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
CHANNEL = os.getenv("SLACK_CHANNEL_ID")


def post_auto_answerable(review_id, review, triage, draft_text):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Yeni yorum* — {triage['sentiment']} / {triage['topic']}\n"
                    f"> {review['body']}\n\n"
                    f"*Önerilen yanıt:*\n{draft_text}"
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
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*İnsana gitmesi gereken bir yorum* — {triage['sentiment']} / {triage['topic']}\n"
                    f"> {review['body']}\n\n"
                    f"*Neden:* {triage['reason']}"
                ),
            },
        }
    ]
    client.chat_postMessage(channel=CHANNEL, blocks=blocks, text="İnsana yönlendirilen yorum")


if __name__ == "__main__":
    # NOT: Anthropic bakiyesi eklenene kadar classify.py / draft.py'nin gerçek
    # çıktısı yerine, Slack mesaj formatını ve buton akışını test etmek için
    # simüle edilmiş bir triyaj sonucu kullanıyoruz.
    fake_review = {"body": "Cok memnun kaldim, hizli kargo."}
    fake_triage = {
        "sentiment": "olumlu",
        "topic": "kargo",
        "auto_answerable": True,
        "reason": "Genel olumlu geri bildirim, risk yok.",
    }
    fake_draft = "Değerlendirmeniz için teşekkür ederiz, hızlı teslimattan memnun kaldığınıza sevindik!"

    post_auto_answerable(review_id="TEST-1", review=fake_review, triage=fake_triage, draft_text=fake_draft)
    print("Slack'e gönderildi.")
