from llm import call_tool
from classify import classify_review

DEFAULT_MODEL = "openai/gpt-oss-120b:free"

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

TOOL_NAME = "yanit_taslagi"
TOOL_DESCRIPTION = "Bir müşteri yorumuna, mağaza adına gönderilecek herkese açık bir yanıt taslağı üretir."
PARAMETERS = {
    "reply": {
        "type": "string",
        "description": "Müşteriye gönderilecek, herkese açık yanıt metni.",
    }
}
REQUIRED = ["reply"]


def draft_reply(review, model=DEFAULT_MODEL):
    user_content = f"Puan: {review['rating']}/5\nYorum: {review['body']}"
    result = call_tool(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        user_content=user_content,
        tool_name=TOOL_NAME,
        tool_description=TOOL_DESCRIPTION,
        parameters=PARAMETERS,
        required=REQUIRED,
    )
    # None: model beklenen formatta yanit vermedi. Sessizce bos bir yanit
    # dondurmek yerine, cagiran tarafin bunu "taslak uretilemedi, insana
    # birak" olarak ele almasi gerekiyor.
    if result is None:
        return None
    return result["reply"]


if __name__ == "__main__":
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
        if reply is None:
            print("-> taslak uretilemedi, insana birakildi")
        else:
            print("-> taslak yanit:", reply)
        print("-" * 40)
