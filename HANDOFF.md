# HANDOFF — Destek Triyaj Sistemi

> Bu dosya, yeni bir oturumda "devam et" dendiğinde okunacak **anlık durum
> özeti**. Bir kararın *neden* öyle alındığını, hangi yanlış yolların
> denenip elenmiş olduğunu görmek için **NOTES.md**'ye bakın — orası
> kronolojik, ayrıntılı bir günlük. Bu dosya ise sadece "şu an neredeyiz,
> sırada ne var" sorusuna cevap verir.

Son güncelleme: 2026-09-28

## Proje nedir

Shopify mağazası için üç kanallı müşteri destek/triyaj sistemi: ürün
yorumları, iade talepleri, teknik destek. Her mesaj sınıflandırılır,
güvenliyse bir yanıt taslağı hazırlanır, hassas olan her şey Slack
üzerinden bir insana gider — hiçbir şey insan onayı olmadan müşteriye
ulaşmaz. Gas Finder ile hiçbir ilgisi yok, tamamen ayrı bir girişim.

Eğitim rehberi (22 modül, 5 faz, canlı durum takibi):
**https://claude.ai/artifact/4dcAP4F3ogb7xDX9ksuiod**

## Şu anki durum

**Tamamlanan ve canlı test edilen modüller:** 1, 2, 3, 4, 5, 6, 7, 8, 9,
10, 11, 12, 14, 15, 16.

**Ertelenen modüller:**
- **Modül 13 (sunucusuza taşıma / GCP)** — kişisel Google Cloud hesabı bu
  iş için kullanılmak istenmiyor (haklı bir ayrım). Ayrı bir hesap/proje
  netleşince ele alınacak.
- **Modül 17 (iade politikası motoru)** — politika taslağı yazıldı ama
  **hukukçu onayı bekliyor**. Onay gelmeden kodlanmayacak.

**Sırada: Modül 18 — A: Müşteri hesabı eklentisi.** `customer_account_ui`
tipinde bir uzantı (`shopify app generate extension` ile — tam şablon adını
CLI'nin kendi hata mesajından doğrula, dokümandaki isim Modül 14'te yanlış
çıkmıştı). Müşteri giriş yapmış olduğu için kimlik/sipariş seçimi
kendiliğinden çözülüyor — B formundaki "kullanıcı beyanı kanıt değil"
sorunu burada yok.

## Açık kararlar (kimseye sorulmadan ilerlenmemeli)

- Hangi GCP hesabı/projesi kullanılacak (Modül 13 için).
- İade politikası metninin hukukçu onayı (Modül 17 için) — taslak
  NOTES.md'de ilk sohbet geçmişinde var, ayrı bir dosyaya çıkarılmadı.
- Yanıt müşteriye nasıl ulaşacak: sadece hesap panelinde mi, yoksa bir
  e-posta bildirimi de mi (küçük bir gönderim servisi gerektirir).
- Hiçbir kategori tam otomatiğe (insan onayı olmadan) geçmeli mi? Şu an
  hepsi insan onaylı — bu, gerçek gölge mod verisi görülmeden karara
  bağlanmayacak.

## Bilinen sınırlar / izlenmesi gerekenler

- **Model güvenilirliği:** `nvidia/nemotron-3-super-120b-a12b:free`
  (OpenRouter, ücretsiz) triyaj kararlarının ~%40-50'sinde yapılandırılmış
  yanıt üretemiyor (uzun iç muhakemede döngüye giriyor). Bu GÜVENLİ (her
  zaman "insana git"e düşüyor) ama VERİMSİZ. `reasoning.effort="low"`
  küçük bir iyileşme gösterdi ama kanıtlanmış değil. `llm.py`'de
  `DEFAULT_MODEL` / `REASONING_EFFORT` tek satırla değiştirilebilir.
- **Ücretsiz OpenRouter kotası:** günde ~50 istek (ödeme yapılmadıkça).
  Hacim artarsa yetmeyebilir.
- **ngrok URL'si kalıcı değil:** süreç yeniden başlarsa adres değişir —
  değişirse `destek-formu.liquid`'deki varsayılan `endpoint_url` ve
  Judge.me'deki webhook kaydı güncellenmeli (bkz. aşağıdaki komutlar).
- **Slack onay yetkisi kısıtlı değil:** kanaldaki herkes Onayla/Reddet
  butonuna basabilir, kullanıcı bazlı bir izin kontrolü yok.

## Ortam durumu (2026-09-28 itibariyle çalışan süreçler)

Yeni oturumda önce şunu çalıştırıp güncel durumu doğrula (zaman geçmiş
olabilir, süreçler kapanmış olabilir):

```bash
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='ngrok.exe' OR Name='node.exe'\" | Select-Object ProcessId,Name,CommandLine"
```

Bu yazıldığı anda çalışanlar:
- `uvicorn main:app --reload` (port 8000) — main.py'yi sunuyor
- `ngrok http 8000` → `https://portfolio-yearning-stimuli.ngrok-free.dev`
- `shopify app dev` — kullanıcının kendi terminalinde, `destek-triyaj-app`
  için (o terminal bu oturumdan görünmüyor, farklı bir pencere)
- **ÇALIŞMIYOR:** `poll.py`, `slack_app.py`, `app.py` (elle durduruldu;
  istenirse `python app.py` ile tekrar başlatılır — ikisini de tek
  süreçte birleştirir)

## Kimlik bilgileri nerede (değerler değil, sadece konum)

- `.env` (triage/ kökünde, git'e hiç girmez): `JUDGEME_API_TOKEN`,
  `JUDGEME_SHOP_DOMAIN`, `ANTHROPIC_API_KEY` (artık kullanılmıyor, OpenRouter'a
  geçildi), `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID`, `SLACK_SIGNING_SECRET`
  (artık kullanılmıyor, Socket Mode'a geçildi), `SLACK_APP_TOKEN`,
  `OPENROUTER_API_KEY`, `SHOPIFY_SHOP_DOMAIN`, `SHOPIFY_CLIENT_ID`,
  `SHOPIFY_CLIENT_SECRET`.
- Shopify Dev Dashboard: organizasyon `234396556`, uygulama
  `destek-triyaj-app`, client_id `77fdf35b9336e4253101a622159e75ed`
  (gizli değil, `.env`'de de aynı değer var).
- GitHub: **https://github.com/oguzhanertug/shopify-review-triage**
  (private, oguzhanertug hesabı altında).
- Test mağazası: `test-store-e3uhspdt.myshopify.com` — gerçek bir sipariş
  var: **#1001**, `test-siparis@example.com`.

## Dosya haritası (`triage/`)

| Dosya | Ne işe yarar |
|---|---|
| `main.py` | FastAPI: `/webhook/review-created` (artık kullanılmıyor, polling'e geçildi, referans için duruyor), `/support/intake` (B formu + doğrulama) |
| `poll.py` | Judge.me'yi periyodik sorgular, yeni yorumları `pipeline.py`'ye yollar |
| `classify.py` / `draft.py` / `llm.py` | OpenRouter ile triyaj + taslak yanıt |
| `pipeline.py` | review → classify → draft → Slack akışını bağlar |
| `notify_slack.py` / `slack_app.py` | Slack mesajı + buton onayı (Socket Mode) |
| `judgeme.py` | Judge.me'ye yanıt gönderme (`POST /replies`) |
| `shopify_admin.py` | Shopify Admin API (Client Credentials Grant), sipariş doğrulama |
| `state.py` | SQLite (`state.db`): `processed_reviews`, `decisions`, `support_requests` |
| `adversarial_tests.py` | Triyaj mantığını zorlayan 8 test vakası + model karşılaştırma |
| `app.py` | `poll.py` + `slack_app.py`'yi tek süreçte birleştiren dağıtım sarmalayıcısı |
| `destek-triyaj-app/` | Shopify uygulaması (CLI ile oluşturuldu); `extensions/destek-formu` = B formu (theme app extension) |
| `NOTES.md` | Kronolojik günlük — her kararın "neden"i, denenip elenen yollar |
| `HANDOFF.md` | Bu dosya |

## Yeni oturumda "devam et" dendiğinde yapılacaklar

1. Bu dosyayı ve gerekirse NOTES.md'nin son bölümünü oku.
2. `cd` ile `triage/` klasörüne geç, `git log --oneline -10` ile son
   commit'leri doğrula (bu dosyadan sonra ilerleme olmuş olabilir).
3. Yukarıdaki süreç kontrolünü çalıştırıp neyin hâlâ açık olduğunu doğrula.
4. Kullanıcıya "kaldığımız yer: Modül 18, başlayalım mı?" diye sor —
   varsayma, onaylat.
