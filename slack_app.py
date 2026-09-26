import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from judgeme import post_reply
from state import claim_pending, get_connection, get_decision, set_status

load_dotenv()

app = App(token=os.getenv("SLACK_BOT_TOKEN"))


def _review_id(body):
    # Eski test mesajlarındaki "TEST-1" gibi sayı olmayan değerlerde çökmeyiz.
    try:
        return int(body["actions"][0]["value"])
    except (KeyError, ValueError):
        return None


def _resolve_message(client, body, status_text):
    # Düğmeleri kaldırıp sonucu mesajın altına yazar; tekrar tıklanamasın.
    blocks = [b for b in body["message"]["blocks"] if b["type"] != "actions"]
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": status_text}]})
    client.chat_update(
        channel=body["channel"]["id"],
        ts=body["message"]["ts"],
        blocks=blocks,
        text="Karar verildi",
    )


def _tell_user(client, body, text):
    client.chat_postEphemeral(channel=body["channel"]["id"], user=body["user"]["id"], text=text)


@app.action("onayla")
def handle_onayla(ack, body, client):
    ack()  # Slack'e "aldım" yanıtı — 3 saniye içinde verilmeli
    review_id = _review_id(body)
    user = body["user"]["username"]

    conn = get_connection()
    try:
        decision = get_decision(conn, review_id) if review_id is not None else None
        # Önce "sahiplen": iki kişi aynı anda basarsa yalnızca biri devam eder.
        if decision is None or not claim_pending(conn, review_id, "sending", user):
            print(f"[SLACK] {user} onayla: kayıt yok ya da zaten karara bağlanmış (review_id={review_id})")
            _tell_user(client, body, "Bu yorum için bekleyen bir onay yok (zaten karara bağlanmış olabilir).")
            return

        # Gönderilen metin, Slack isteğinden değil veritabanından gelir.
        if post_reply(review_id, decision["draft_text"]):
            set_status(conn, review_id, "sent")
            print(f"[SLACK] {user} ONAYLADI, yanıt gönderildi (review_id={review_id})")
            _resolve_message(client, body, f"Onaylandı ve Judge.me'ye gönderildi — {user}")
        else:
            set_status(conn, review_id, "pending")  # butonlar duruyor, tekrar denenebilir
            _tell_user(client, body, "Yanıt Judge.me'ye gönderilemedi. Birazdan tekrar deneyebilirsiniz.")
    finally:
        conn.close()


@app.action("reddet")
def handle_reddet(ack, body, client):
    ack()
    review_id = _review_id(body)
    user = body["user"]["username"]

    conn = get_connection()
    try:
        if review_id is None or not claim_pending(conn, review_id, "rejected", user):
            print(f"[SLACK] {user} reddet: kayıt yok ya da zaten karara bağlanmış (review_id={review_id})")
            _tell_user(client, body, "Bu yorum için bekleyen bir onay yok (zaten karara bağlanmış olabilir).")
            return
        print(f"[SLACK] {user} REDDETTİ (review_id={review_id})")
        _resolve_message(client, body, f"Reddedildi, yanıt gönderilmedi — {user}")
    finally:
        conn.close()


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    print("Slack Socket Mode dinleniyor...")
    handler.start()
