import os
from dotenv import load_dotenv
import requests

load_dotenv()

token = os.getenv("JUDGEME_API_TOKEN")
shop_domain = os.getenv("JUDGEME_SHOP_DOMAIN")

url = "https://judge.me/api/v1/reviews"
params = {
    "api_token": token,
    "shop_domain": shop_domain
}

response = requests.get(url, params=params)

print("Status code:", response.status_code)
data = response.json()
reviews = data["reviews"]
print("Toplam yorum sayısı:", len(reviews))
import json
print(json.dumps(reviews[0], indent=2, ensure_ascii=False))
for review in reviews:
    print(review["reviewer"]["name"], "-", review["rating"], "yıldız")
slack_token = os.getenv("SLACK_BOT_TOKEN")
channel_id = os.getenv("SLACK_CHANNEL_ID")
print("Slack token okundu mu?", slack_token is not None)
print("Kanal ID okundu mu?", channel_id is not None)
"""
create_payload = {
    "shop_domain": shop_domain,
    "platform": "shopify",
    "id": 10791013417241,
    "email": "test@example.com",
    "name": "Test Kullanici",
    "rating": 5,
    "title": "Harika urun",
    "body": "Cok memnun kaldim.",
    "api_token": token
}
create_response = requests.post(url, data=create_payload)
print("Yorum oluşturma status:", create_response.status_code)
print(create_response.json())
"""