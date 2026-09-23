# İlerleme Notları

## Modül 1 — Ortam kurulumu ✅
- venv, pip, .env ile secret yönetimi
- Judge.me API bağlantısı, Claude API key, Slack bot token+kanal hazır

## Modül 2 — Yorum verisi okuma ✅ (kısmen)
- Judge.me'den GET ile yorum listeleme çalışıyor
- Test ürünü (Snowboard) üzerinde POST ile örnek yorum oluşturuldu
- Yorum objesinin yapısını öğrendim:
  - review["rating"], review["body"] → direkt üstte
  - review["reviewer"]["name"] → iç içe (nested)
  - review["verified"] → "verified" / "nothing" değerleri var
  - review["product_title"] → düz, ayrı obje değil
- Not: Konsepti tam ezbere bilmiyorum ama mantığı biliyorum, ileride pratikte pekişecek

## Modül 3 — Webhook'lar ve olay alma ✅ (yaklaşım değişti: polling)
- main.py'de gerçek bir hata bulundu: SHOP_DOMAIN env değişkeni yanlış isimle okunuyordu
  (.env'de JUDGEME_SHOP_DOMAIN var, kod SHOP_DOMAIN okuyordu) → doğrulama hep None'a
  karşı kıyaslıyordu, her istek 403 dönüyordu. Düzeltildi.
- ngrok kuruldu (winget ile), authtoken ayarlandı, tünel çalışıyor.
- Judge.me webhook'ları sadece ücretli Awesome planında açık (ücretsiz planda
  Settings > Integrations altında hiç görünmüyor). Şimdilik gerçek webhook yerine
  **polling**'e geçtik: poll.py, Judge.me'yi periyodik olarak GET ile sorguluyor,
  son görülen yorumun created_at zaman damgasını poll_state.json'da tutuyor, sadece
  ondan daha yeni yorumları "yeni" sayıyor.
- Test: API üzerinden sahte bir yorum oluşturuldu, poll.py bir sonraki turda
  yakalayıp yazdırdı — checkpoint doğrulandı.
- Not: Judge.me POST edilen yorumu hemen değil, birkaç dakika içinde asenkron
  işliyor — hemen görünmeyebilir.
- main.py (FastAPI + shop_domain doğrulama) silinmedi; Modül 6'da Slack'in
  interaktif buton endpoint'i için işe yarayabilir.

## Modül 4 — Claude API ile triyaj ⏸ (kod hazır, canlı test bekliyor)
- classify.py yazıldı: triyaj_karari tool'u ile sentiment/topic/auto_answerable/reason
  döndüren yapılandırılmış bir çağrı. tool_choice zorlanarak Claude'un her zaman
  bu aracı çağırması sağlandı (serbest metin ayrıştırma yok).
- Sistem promptu "şüphede kal, insana yönlendir" mantığıyla fail-closed tasarlandı.
- ÇALIŞTIRAMADIK: Anthropic hesabının kredi bakiyesi yetersiz
  ("credit balance is too low"). Bu, Claude.ai aboneliğinden ayrı, ayrıca
  console.anthropic.com'dan bakiye/ödeme yöntemi eklenmesi gereken bir şey.
- KARAR: Gerçek projeyi hayata geçirirken (billing eklendiğinde) Modül 4 ve 5'in
  canlı testini birlikte yapacağız. Şimdilik kodu yazıp mantığını gözden geçirerek,
  Anthropic'e ihtiyaç duymayan modüllerle (Slack, state/idempotency, deployment)
  devam ediyoruz.

## Modül 5 — Claude API ile yanıt taslağı hazırlama ⏸ (kod hazır, canlı test bekliyor)
- draft.py yazıldı: yanit_taslagi tool'u ile sadece auto_answerable=true olan
  yorumlar için herkese açık bir yanıt taslağı üretiyor.
- Sistem promptu yeni bilgi/vaat uydurmayı yasaklıyor, kısa ve genel hitap
  kuralları var (KVKK/gizlilik nedeniyle müşteri adı kullanılmıyor).
- __main__ bloğunda classify.py'nin çıktısını kullanıp zincirliyor: önce triyaj,
  auto_answerable ise taslak üret, değilse "insana gitmeli" diyip atla.
- ÇALIŞTIRAMADIK (Modül 4 ile aynı sebep: Anthropic bakiyesi). Modül 4 ile
  birlikte, billing eklendiğinde canlı test edilecek.

## Modül 6 — Slack üzerinden insan onayı ✅
- Önce HTTP + ngrok + imza doğrulama (Slack signing secret) ile deneyecektik ama
  Slack app'te Socket Mode zaten açıkmış — bu durumda Request URL alanı devre dışı
  kalıyor. Bolt + Socket Mode'a geçtik (App-Level Token, xapp-...), ngrok/HTTP
  endpoint'ine gerek kalmadı.
- notify_slack.py: Block Kit ile "Onayla ve gönder" / "Reddet" butonlu mesaj
  gönderiyor (şimdilik Anthropic bakiyesi olmadığı için simüle edilmiş bir triyaj
  sonucuyla test edildi, gerçek classify.py/draft.py çıktısı bağlanacak).
- slack_app.py: Bolt App + SocketModeHandler, @app.action("onayla") /
  @app.action("reddet") ile buton tıklamalarını yakalıyor.
- Test edildi: gerçek bir Slack tıklaması handler'da doğru şekilde loglandı
  (review_id ile birlikte).
- main.py'a eklenmiş olan geçici /slack/interactions HTTP endpoint'i geri alındı
  (Socket Mode'a geçince gereksiz kaldı).

## Modül 7 — Döngüyü kapatmak ✅ (araştırma + reply endpoint doğrulandı)
- Resmi API dokümantasyonunu (judge.me/api/docs) tarayıcıyla inceledik — panel
  UI'da görünmeyen ama gerçekten var olan endpoint'leri bulduk:
  GET /shops/info (plan bilgisi), POST /webhooks (webhook oluşturma),
  POST /replies (herkese açık yanıt), POST /private_replies (özel e-posta yanıtı).
- GET /shops/info ile hesabın gerçekten "awesome": false (ücretsiz plan) olduğu
  doğrulandı.
- DÜZELTME: POST /webhooks denendi, 201 ile kabul edildi. İlk 12 dakikada teslimat
  gelmedi diye "muhtemelen Awesome plana bağlı" sonucuna vardık — YANLIŞ ÇIKTI.
  Gerçekte webhook ~30-40 dakika sonra geldi ve 200 OK aldı (main.py'daki
  shop_domain doğrulamasını da doğru geçti). Sonuç: webhook hem kayıt hem
  gerçek tetikleme olarak ücretsiz planda ÇALIŞIYOR — sadece bu test/dev
  mağazasında gecikme beklenenden çok uzun (dakikalar değil, onlarca dakika).
  KARAR: yine de polling'de kalıyoruz — üretimde dakikalar mertebesinde
  öngörülemeyen bir gecikmeye güvenmek riskli; polling zaten çalışıyor ve
  gecikme kontrol bizde. Ama artık "webhook Awesome'a kısıtlı" iddiası YANLIŞ,
  bunu böyle not düşüyoruz ki ileride yanlış hatırlamayalım.
- POST /replies denendi: gerçek bir yoruma (id=1324162521) yanıt gönderildi,
  200 OK döndü — bu endpoint ücretsiz planda ÇALIŞIYOR. Modül 7'nin asıl
  ihtiyacı bu; webhook'a göre çok daha önemli bir doğrulama.
- close_loop.py henüz yazılmadı: Anthropic bakiyesi eklenip Modül 4/5 canlı
  test edildiğinde, Slack "onayla" aksiyonunu POST /replies çağrısına
  bağlayacağız (slack_app.py'deki handle_onayla fonksiyonunun içine).

## Modül 8 — Durum yönetimi ve idempotency ✅
- state.py: SQLite (state.db), processed_reviews tablosu (review_id PRIMARY KEY).
  is_processed() / mark_processed() — mark_processed INSERT OR IGNORE kullanıyor,
  aynı ID'yi iki kez işaretlemek hata vermiyor.
- poll.py güncellendi: created_at watermark artık sadece sorguyu daraltan kaba bir
  ön filtre (>=, kesin değil); asıl tekilleştirme garantisi her yorumun ID'sini
  state.db'de kontrol etmekten geliyor. Böylece bir çökme yarım işlenmiş bir
  grubu bıraksa bile, zaten işlenenler tekrar işlenmiyor.
- Test: state.py'nin is_processed/mark_processed'ı izole test edildi. Sonra
  gerçek poll_once() iki kez art arda çalıştırıldı — ilk turda (yeni sisteme
  geçiş nedeniyle) iki eski yorum bir kerelik tekrar yazdırıldı, ikinci turda
  HİÇBİR ŞEY yazdırılmadı — checkpoint doğrulandı.

## Modül 9 — Güvenlik önlemleri ve gözlemlenebilirlik ⏸ (kod hazır, canlı test bekliyor)
- PII incelemesi: poll.py sadece rating/body/reviewer adını yazdırıyor —
  e-posta, telefon, IP adresi (Judge.me payload'ında var ama) hiçbir yerde
  loglanmıyor. Ek bir değişiklik gerekmedi, mevcut kod zaten temiz.
- adversarial_tests.py yazıldı: 8 vaka — güvenli olumlu/nötr (2), ürün kusuru,
  iade/hukuki dil, küfür, çok düşük puan + nazik dil, prompt-injection denemesi
  (yorum içine gömülü "önceki talimatları yok say" saldırısı), belirsiz/karışık
  duygu. Her vaka için beklenen auto_answerable değeri var, PASS/FAIL raporluyor.
- ÇALIŞTIRAMADIK (Modül 4/5 ile aynı sebep). Anthropic bakiyesi eklenince
  Modül 4/5 ile birlikte tek seferde koşturulacak.

## NOT: numaralandırma değişti
Rehber artifact'i 22 modüllük, 5 fazlı yeni bir yapıya geçti (reviews +
iadeler + teknik destek, üç kanal). Modül 1-9 aynı kaldı. Aşağıdaki
"Modül 10"'dan itibaren numaralar YENİ yapıya göre — eski "Modül 10
(Dağıtım)" içeriği artık Modül 13'ün bir parçası olarak yeniden etiketlendi.

## Modül 10 — OpenRouter'a geçiş ve model seçimi ✅
- llm.py: OpenRouter'a doğrudan `requests` ile bağlanan ortak bir yardımcı
  (`call_tool`). Yeni bağımlılık eklemedik — mevcut requests kütüphanesi
  yeterli. Zorunlu araç çağrısı (`tool_choice`), `max_tokens=4096`,
  `temperature=0` (güvenliğe kritik bir sınıflandırmada tutarlılık, rastgele
  yaratıcılıktan daha değerli).
- classify.py ve draft.py OpenRouter'a taşındı, Anthropic tamamen bırakıldı.
- KRİTİK GÜVENLİK ÖZELLİĞİ: model beklenen şemaya uymayan bir yanıt verirse
  (`tool_calls` eksik, JSON bozuk, zorunlu alan eksik), `call_tool` None döner
  ve çağıran taraf bunu "hataya kapalı, insana yönlendir" olarak yorumlar —
  asla güvenli/otomatik bir varsayılana düşmez.
- Model yarışı — `adversarial_tests.py` 8 vakayla 4 aday ücretsiz modeli test
  etti (gerçek, canlı openrouter.ai/api/v1/models sorgusuyla seçildi, eski
  blog yazılarından değil):
  - `openai/gpt-oss-120b:free` — artık mevcut değil, kaldırılmış (404, "the
    paid version is available now").
  - `nemotron-3-ultra-550b-a55b` — 8/8 zaman aşımı (30sn), ücretsiz katmanda
    aşırı yüklü.
  - `gemma-4-31b-it`, `qwen3.8-27b` — 8/8 "429 Too Many Requests", birkaç gün
    arayla iki kez denendi, hep aynı sonuç — muhtemelen bu modellerin küresel
    ücretsiz kotası (bizim hesabımızdan bağımsız, tüm OpenRouter kullanıcıları
    için paylaşılan) tükenmiş durumda.
  - **`nemotron-3-super-120b-a12b`** — dört farklı denemede de (4096/varsayılan,
    8192/varsayılan, 4096/temp=0) gerçekten çalışan TEK model. Gerçek başarı
    oranı ısrarla %40-50 civarında kaldı — max_tokens'ı artırmak (8192'ye
    çıkarmak daha da kötüleştirdi) ya da temperature=0 vermek bunu değiştirmedi;
    modelin kendi doğal sınırı gibi görünüyor (çok uzun iç muhakeme üretip
    bazen araç çağrısına hiç ulaşmıyor, "reasoning" alanında binlerce token
    harcıyor).
  - KARAR: `nemotron-3-super-120b-a12b:free` varsayılan model
    (DEFAULT_MODEL). ~yarı yarıya format hatası VAR ama bu her zaman "insana
    git" ile sonuçlanıyor — hiçbir zaman riskli bir yorumu kaçırmadı. Kabul
    edilen ödün: güvenlik tam, verimlilik düşük (yorumların önemli kısmı
    gereksiz yere insana gidecek). İleride ücretli bir modele geçmek ya da
    openrouter/free otomatik yönlendiriciyi denemek bir seçenek.
- Modül 4, 5 ve 9 böylece ilk kez GERÇEKTEN çalıştırıldı — Faz 1'in askıda
  kalan son parçaları kapandı.

## Sıradaki: Modül 11 — Zinciri uçtan uca bağlamak
poll.py → classify.py → draft.py → notify_slack.py, ve Slack "Onayla" →
POST /replies bağlantılarını kurmak.

## Genel durum (Faz 1 tamamlandı)
Modül 1-9: tamamlandı ve canlı test edildi (4, 5, 9 nihayet OpenRouter ile
gerçek veriyle çalıştırıldı).
Modül 10: tamamlandı (bu not).
Modül 11-22: henüz başlanmadı — sırada Modül 11.
Eski "Modül 10 (Dağıtım)" hazırlığı (requirements.txt, app.py, .env.example)
hâlâ geçerli, yeni yapıda Modül 13'ün bir kısmını karşılıyor.