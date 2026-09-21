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

## Modül 10 — Dağıtım ve devreye alma ⏸ (hazırlık yapıldı, gerçek dağıtım bekliyor)
- requirements.txt düzeltildi: PowerShell'in UTF-16 sorunu olmadan, Bash'te
  `pip freeze` ile yeniden oluşturuldu; artık fastapi/uvicorn/anthropic/
  slack_bolt/slack_sdk/python-multipart dahil, gerçekten kurulu olan her şeyi
  içeriyor.
- app.py: poll.py'nin döngüsünü arka plan thread'inde, slack_app.py'nin
  Socket Mode dinleyicisini ana thread'de çalıştıran TEK bir giriş noktası.
  Railway/Render/Fly.io gibi platformlar tek bir başlatma komutu beklediği
  için ikisi birleştirildi. Duman testi yapıldı, ikisi de sorunsuz başladı.
- .env.example eklendi (gerçek değerler olmadan, hangi değişkenlerin gerektiğini
  gösteren bir referans).
- KARAR: gerçek hosting hesabı + canlı dağıtım + gölge mod, Anthropic bakiyesi
  eklenip Modül 4/5/9'un canlı testi yapıldıktan sonra yapılacak.

## Genel durum
Modül 1, 2 (kısmen), 3, 6, 7, 8: tamamlandı ve canlı test edildi.
Modül 4, 5, 9, 10: kod hazır, Anthropic bakiyesi eklenince tek seferde
canlı test edilip devreye alınacak.