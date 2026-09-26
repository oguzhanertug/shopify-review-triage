import json

from llm import DEFAULT_MODEL, call_tool

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

TOOL_NAME = "triyaj_karari"
TOOL_DESCRIPTION = (
    "Bir müşteri yorumunu triyaj eder: duygu durumu, konusu ve otomatik "
    "yanıtlanabilir olup olmadığına dair kararı döndürür."
)
PARAMETERS = {
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
}
REQUIRED = ["sentiment", "topic", "auto_answerable", "reason"]

FAIL_CLOSED_RESULT = {
    "sentiment": "belirsiz",
    "topic": "belirsiz",
    "auto_answerable": False,
    "reason": "Model yanıtı beklenen formatta değildi; güvenlik gereği insana yönlendirildi.",
    "format_error": True,
}


def classify_review(review, model=DEFAULT_MODEL):
    user_content = (
        f"Puan: {review['rating']}/5\n"
        f"Başlık: {review.get('title', '')}\n"
        f"Yorum: {review['body']}"
    )
    result = call_tool(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        user_content=user_content,
        tool_name=TOOL_NAME,
        tool_description=TOOL_DESCRIPTION,
        parameters=PARAMETERS,
        required=REQUIRED,
    )
    if result is None:
        return dict(FAIL_CLOSED_RESULT)
    return result


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
