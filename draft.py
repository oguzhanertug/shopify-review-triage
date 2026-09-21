import os

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

DRAFT_TOOL = {
    "name": "yanit_taslagi",
    "description": "Bir müşteri yorumuna, mağaza adına gönderilecek herkese açık bir yanıt taslağı üretir.",
    "input_schema": {
        "type": "object",
        "properties": {
            "reply": {
                "type": "string",
                "description": "Müşteriye gönderilecek, herkese açık yanıt metni.",
            }
        },
        "required": ["reply"],
    },
}

SYSTEM_PROMPT = """Sen bir e-ticaret mağazasının müşteri yorumlarına yanıt yazan asistanısın.
Bu fonksiyon SADECE otomatik-yanıtlanabilir olarak triyaj edilmiş (genel,
olumlu/nötr) yorumlar için çağrılır — şikayet, iade veya kusur içeren yorumlar
buraya hiç gelmemeli.

Kurallar:
- Sadece yorumda gerçekten söylenenlere dayan; asla yeni bir bilgi, söz veya vaat
  uydurma (ör. indirim kodu, kargo tarihi, iade sözü teklif etme).
- Sıcak ama profesyonel bir ton kullan; abartılı veya yapay övgüden kaçın.
- Kısa tut (1-3 cümle).
- Müşterinin adını kullanma (gizlilik nedeniyle genel hitap tercih et).
- Yorumda somut bir detay varsa (ör. hızlı kargo, belirli bir ürün), ona değin —
  şablon gibi hissettirme.
"""


def draft_reply(review):
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        tools=[DRAFT_TOOL],
        tool_choice={"type": "tool", "name": "yanit_taslagi"},
        messages=[
            {
                "role": "user",
                "content": f"Puan: {review['rating']}/5\nYorum: {review['body']}",
            }
        ],
    )
    tool_use_block = next(b for b in message.content if b.type == "tool_use")
    return tool_use_block.input["reply"]


if __name__ == "__main__":
    from classify import classify_review

    test_reviews = [
        {"rating": 5, "title": "Harika", "body": "Cok memnun kaldim, hizli kargo."},
        {"rating": 5, "title": "Tesekkurler", "body": "Guzel urun, tavsiye ederim."},
        {"rating": 1, "title": "Kotu", "body": "Urun bozuk geldi, calismiyor, param geri istiyorum."},
    ]
    for review in test_reviews:
        triage = classify_review(review)
        if not triage["auto_answerable"]:
            print("Yorum:", review["body"])
            print("-> insana gitmeli:", triage["reason"])
            print("-" * 40)
            continue
        reply = draft_reply(review)
        print("Yorum:", review["body"])
        print("-> taslak yanit:", reply)
        print("-" * 40)
