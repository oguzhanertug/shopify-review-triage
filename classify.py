import os
import json

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

TRIAGE_TOOL = {
    "name": "triyaj_karari",
    "description": (
        "Bir müşteri yorumunu triyaj eder: duygu durumu, konusu ve otomatik "
        "yanıtlanabilir olup olmadığına dair kararı döndürür."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sentiment": {
                "type": "string",
                "enum": ["olumlu", "notr", "olumsuz"],
                "description": "Yorumun genel duygu durumu.",
            },
            "topic": {
                "type": "string",
                "description": (
                    "Yorumun ana konusu, ör. 'urun kalitesi', 'kargo', "
                    "'musteri hizmetleri', 'iade talebi'."
                ),
            },
            "auto_answerable": {
                "type": "boolean",
                "description": "Bu yorum güvenle otomatik bir yanıtla karşılanabilir mi?",
            },
            "reason": {
                "type": "string",
                "description": "auto_answerable kararının kısa gerekçesi.",
            },
        },
        "required": ["sentiment", "topic", "auto_answerable", "reason"],
    },
}

SYSTEM_PROMPT = """Sen bir e-ticaret mağazası için müşteri yorumu triyaj asistanısın.
Görevin: gelen bir ürün yorumunu analiz edip triyaj_karari aracını çağırarak
yapılandırılmış bir karar döndürmek.

auto_answerable = false OLMALI (her zaman insana git) eğer yorumda şunlardan biri varsa:
- Ürün kusuru/arıza iddiası (ör. "bozuk geldi", "çalışmıyor")
- İade, para iadesi veya hukuki dille ilgili bir talep
- Küfür veya saldırgan dil
- Çok düşük bir puan (1-2 yıldız)
- Kararsız kaldığın herhangi bir durum — şüpheye düştüğünde her zaman insana yönlendir

auto_answerable = true sadece genel, olumlu/nötr geri bildirimler için olabilir
(ör. beğenme, hızlı kargo memnuniyeti, basit bir teşekkür)."""


def classify_review(review):
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        tools=[TRIAGE_TOOL],
        tool_choice={"type": "tool", "name": "triyaj_karari"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Puan: {review['rating']}/5\n"
                    f"Başlık: {review.get('title', '')}\n"
                    f"Yorum: {review['body']}"
                ),
            }
        ],
    )
    tool_use_block = next(b for b in message.content if b.type == "tool_use")
    return tool_use_block.input


if __name__ == "__main__":
    test_reviews = [
        {"rating": 5, "title": "Harika", "body": "Cok memnun kaldim, hizli kargo."},
        {"rating": 1, "title": "Kotu", "body": "Urun bozuk geldi, calismiyor, param geri istiyorum."},
        {"rating": 3, "title": "", "body": "Fena degil ama kutusu hasarli gelmisti."},
        {"rating": 5, "title": "Tesekkurler", "body": "Guzel urun, tavsiye ederim."},
    ]
    for review in test_reviews:
        result = classify_review(review)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("-" * 40)
