from classify import classify_review
from draft import draft_reply
from notify_slack import post_auto_answerable, post_needs_human
from state import get_decision, save_decision

# Ekranda gösterilen metinle gönderilen metin aynı olmak zorunda, bu yüzden
# gösterirken kısaltmak yerine anormal uzun taslağı baştan reddediyoruz.
MAX_DRAFT_CHARS = 1000


def decide(review):
    triage = classify_review(review)
    if not triage["auto_answerable"]:
        return triage, None

    draft = draft_reply(review)
    if draft is None or not draft.strip() or len(draft) > MAX_DRAFT_CHARS:
        triage = {
            **triage,
            "auto_answerable": False,
            "format_error": True,
            "reason": "Taslak yanıt üretilemedi ya da beklenenden uzun/boş geldi.",
        }
        return triage, None
    return triage, draft


def process_review(conn, review):
    """Bir yorumu sınıflandırır, gerekirse taslak yazar, Slack'e gönderir.

    Slack gönderimi hata verirse istisna fırlar; yorum "işlendi" sayılmaz ve bir
    sonraki turda tekrar denenir. Karar zaten kaydedildiği için LLM tekrar
    çağrılmaz, yalnızca Slack mesajı yeniden denenir.
    """
    review_id = review["id"]

    decision = get_decision(conn, review_id)
    if decision is None:
        triage, draft = decide(review)
        save_decision(conn, review_id, triage, draft)
        decision = get_decision(conn, review_id)

    if decision["status"] == "pending":
        post_auto_answerable(review_id, review, decision["triage"], decision["draft_text"])
    elif decision["status"] == "needs_human":
        post_needs_human(review_id, review, decision["triage"])
    # sending / sent / rejected: bu yorum hakkında zaten karar verilmiş,
    # Slack'e ikinci kez düğmeli mesaj göndermeyiz.
