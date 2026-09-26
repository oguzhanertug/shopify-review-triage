"""
Tek dağıtılabilir süreç: polling döngüsü bir arka plan thread'inde,
Slack Socket Mode dinleyicisi ana thread'de çalışır. Railway/Render/Fly.io gibi
platformlar tek bir "başlat" komutu bekler — ikisini burada birleştiriyoruz.
"""

import os
import threading

from dotenv import load_dotenv
from slack_bolt.adapter.socket_mode import SocketModeHandler

from poll import main as poll_main
from slack_app import app as slack_app
from state import get_connection

load_dotenv()


def start_polling_in_background():
    thread = threading.Thread(target=poll_main, daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    get_connection()  # state.db tablolarının var olduğundan emin ol
    start_polling_in_background()
    print("Polling arka planda başladı, Slack Socket Mode ana thread'de dinliyor...")
    handler = SocketModeHandler(slack_app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
