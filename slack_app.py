import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

app = App(token=os.getenv("SLACK_BOT_TOKEN"))


@app.action("onayla")
def handle_onayla(ack, body):
    ack()  # Slack'e "isteği aldım" onayı — 3 saniye içinde gönderilmeli
    review_id = body["actions"][0]["value"]
    user = body["user"]["username"]
    print(f"[SLACK AKSİYONU] {user} -> ONAYLA (review_id={review_id})")
    # Modül 7'de burada Judge.me'nin reply endpoint'i çağrılacak.


@app.action("reddet")
def handle_reddet(ack, body):
    ack()
    review_id = body["actions"][0]["value"]
    user = body["user"]["username"]
    print(f"[SLACK AKSİYONU] {user} -> REDDET (review_id={review_id})")


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    print("Slack Socket Mode dinleniyor...")
    handler.start()
