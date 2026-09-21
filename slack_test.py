import os

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
channel = os.getenv("SLACK_CHANNEL_ID")

try:
    response = client.chat_postMessage(
        channel=channel,
        text="Merhaba! Bu, İnceleme Triyaj hattının Slack bağlantı testidir.",
    )
    print("Gönderildi, mesaj zaman damgası:", response["ts"])
except SlackApiError as exc:
    print("Slack hatası:", exc.response["error"])
