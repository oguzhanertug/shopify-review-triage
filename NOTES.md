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
  - **`nemotron-3-super-120b-a12b`** — çalışan TEK model. İlk yorumum "gerçek
    başarı %40-50, modelin doğal sınırı" idi; bu KISMEN yanlıştı, çünkü hata
    nedenini günlüğe yazmıyordum. Tanılama eklenince gerçek nedenler çıktı
    (5 başarısızlıktan): 4'ü `finish_reason=length` (model muhakemede döngüye
    girip tüm token bütçesini harcıyor), 1'i sağlayıcı aşırı yüklenmesi (503,
    HTTP 200 gövdesinde gelir). Yani hataların çoğu modelle ilgili, bir kısmı
    altyapı.
  - Müdahaleler denendi: `max_tokens` 4096→8192 İŞE YARAMADI (başarısız vakalar
    98 ve 54 sn harcayıp yine `length` ile bitti; başarılılar 3-7 sn'de bitiyor
    → sorun bütçe değil döngü). `reasoning.effort="low"` daha iyi göründü:
    gerçek yanıt 6/8 (önceki koşularda 3-4/8) ama örneklem küçük (n=8) ve
    temperature=0 olmasına rağmen aynı girdi koşudan koşuya farklı sonuç verdi
    (sağlayıcı tam deterministik değil). UMUT VERİCİ, KANITLANMIŞ DEĞİL.
    Varsayılan yapıldı (`REASONING_EFFORT="low"`, tek satırla geri alınır).
  - KARAR: `nemotron-3-super-120b-a12b:free` varsayılan model. Format/döngü
    hatası her zaman "insana git" ile sonuçlanıyor; gözlemlenen koşularda (~6
    koşu, 5 riskli vaka) riskli bir yorum hiçbir zaman auto_answerable=true
    olmadı — ama bu YAPISAL bir güvence (ayrıştırılamayan her şey insana gider),
    istatistiksel bir garanti değil: model kendinden emin şekilde YANLIŞ ama
    geçerli bir yanıt verirse (riskli yoruma true) tek engel insan onayıdır.
    İleride ücretli bir modele geçmek seçenek.
- HATA KAYDI (kendi hatam): koddaki DEFAULT_MODEL, yarıştan sonra da kalkmış
  `openai/gpt-oss-120b:free` olarak kaldı; ben NOTES'a "varsayılan nemotron"
  yazdım ama sabiti hiç değiştirmedim. Yarış betikleri modeli açıkça verdiği
  için hiçbir test yakalamadı; gerçek boru hattı 404 alınca ortaya çıktı. İlk
  404'ü de yanlışlıkla "geçici aksaklık" diye yorumlamıştım. Düzeltme:
  DEFAULT_MODEL artık llm.py'de TEK yerde (iki dosyada kopya olunca kaymıştı),
  404 artık "geçici" sayılmıyor (kalıcı yapılandırma hatası), HTTP hata
  gövdeleri günlüğe yazılıyor.
- Hata türleri ayrıldı (llm.py): geçici (408/429/5xx + HTTP 200 içinde gelen
  sağlayıcı hataları) → 5 sn sonra BİR kez yeniden denenir; format hatası
  (araç çağrısı yok) yeniden DENENMEZ (aynı girdiye aynı cevabı verir, günlük
  kotayı boşa harcar). Zaman aşımı 30→90 sn (ölçülen yanıt süresi ~45 sn'ye çıkıyor).
- Tür doğrulaması eklendi: alanın var olması yetmez, türü de doğru olmalı.
  `"auto_answerable": "false"` (yazı) Python'da doğru sayılır ve "insana git"i
  "otomatik yanıtla"ya çevirirdi — güvenlik ağındaki gerçek bir delikti, kapatıldı.
- Modül 4 ve 9 canlı doğrulandı. Modül 5 (`draft_reply`) ise ancak Modül 11
  sırasında İLK KEZ gerçekten çalıştı (bkz. aşağı).

## Modül 11 — Zinciri uçtan uca bağlamak ✅
GÖZETİMSİZ TAM KOŞU YAPILDI (2026-09-26): yeni test yorumu 19:10:04'te
gönderildi → 19:10:24'te app.py yakaladı, gerçek model sınıflandırdı
(olumlu/kargo, otomatik yanıtlanabilir), gerçek taslak yazdı, Slack'e düştü →
kullanıcı "Onayla"ya bastı → günlük "ONAYLADI, yanıt gönderildi", durum `sent`.
DİKKAT: bu TEK bir koşu (n=1) ve model o sefer döngüye girmedi. Önceki
ölçümlerde zincir ~yarı yarıya "Teknik hata"ya düşüyordu; bu tek başarı bunu
değiştirmez. Judge.me bu sefer yorumu saniyeler içinde işledi (önceden 30-40
dk sürmüştü) → gecikme sabit değil, "30-40 dk" iddiası fazla kesindi.
Taslak kalitesi: "Ürünün beklentilerinizi karşıladığını ve kargo hızımızın
beğeninizi aldığını görmek çok mutlu edici" — uydurma bilgi yok ama Türkçesi
kasıntı. Slack akışında yalnızca Onayla/Reddet var, DÜZENLE yok; taslak kötü
ama fikir doğruysa tek seçenek olduğu gibi göndermek ya da reddedip Judge.me'de
elle yazmak. Düzenle düğmesi mantıklı bir sonraki iyileştirme.
(Aşağıdaki "HENÜZ DOĞRULANMAYAN" maddesi bu koşuyla kapandı.)
Yeni/yeniden yazılan: pipeline.py (process_review), judgeme.py (post_reply),
notify_slack.py, slack_app.py, poll.py, state.py (decisions tablosu), app.py.
- Akış: poll → sınıflandır → (güvenliyse) taslak → Slack → insan tıklaması →
  Judge.me'ye herkese açık yanıt.
- Onay kapısının değişmezi: Slack'te gösterilen metin == veritabanında saklanan
  metin == gönderilen metin. Gönderilecek metin Slack isteğinden DEĞİL, hep
  `decisions` tablosundan okunur. Anormal uzun taslak (>1000 karakter)
  gösterirken kısaltılmaz, baştan reddedilip insana gönderilir (kısaltırsak
  değişmez bozulur).
- Çift tıklama: `claim_pending` tek bir `UPDATE ... WHERE status='pending'`.
  20 eşzamanlı tıklamayla test edildi → 1 kazanan, 1 yanıt.
- Karar kalıcı (`decisions`): Slack gönderimi hata verirse yorum yeniden denenir
  ama LLM tekrar çağrılmaz (kota korunur).
- Watermark tuzağı: bir yorum hata verirse zaman damgası ilerlemez; yoksa daha
  yeni bir yorum başarılı olunca `>=` filtresi hatalı yorumu bir daha hiç
  göstermez (sessiz kayıp).
- Slack güvenliği: yorum ve model çıktısı güvenilmeyen girdi. `<!channel>`,
  `<@kullanici>` gibi kalıplar kaçırılıyor (yorum yazan biri kanalda herkesi
  etiketleyemez); uzun yorum kısaltılıyor (Slack sınırını aşıp mesajı
  reddettirmesin). Eski "TEST-1" butonu artık çökmüyor, gizli uyarı veriyor.
- Format hatası ile gerçek triyaj Slack'te ayrı gösteriliyor ("Teknik hata:
  otomatik triyaj tamamlanamadı" — yorum riskli olmayabilir, model yanıtı
  okunamadı).
- CANLI DOĞRULANANLAR: (1) Slack "Onayla" → veritabanı → Judge.me'de herkese
  açık yanıt (kullanıcı Judge.me'de gördü); (2) "Teknik hata" mesajı (kullanıcı
  okunaklı buldu); (3) gerçek model + gerçek taslak, Slack'e göndermeden 4
  yorumda: 2/4 zincir tam çalıştı, 2/4 model döngüsü (`length`) → güvenle insana.
- Gerçek taslaklar (ilk kez): kibar, uydurma bilgi yok. Ama "Daha iyi hizmet
  sunmaya devam edeceğiz" hafif bir söz sayılabilir (istem söz vermeyi
  yasaklıyor) ve "umarım alışveriş deneyiminiz keyifli olur" kalıp. İleride
  istem sıkılaştırılabilir.
- (KAPANDI, bkz. yukarıdaki tam koşu) Önceden doğrulanmayan: hepsi bir arada gözetimsiz koşu (yeni bir yorum
  Judge.me'de belirir → app.py yakalar → gerçek model → Slack → tıklama →
  yanıt). Judge.me yeni yorumları 30-40 dk gecikmeyle işlediği için bu test
  uzun sürüyor. Testlerde gerçek zincir hep elle tetiklendi (poll_once ise
  sahte verilerle birim testinden geçti).
- BİLİNEN SINIRLAR: yorumlar sırayla işleniyor; model 90 sn'ye kadar
  sürebildiği için bir tur uzayabilir (gerçek zamanlı değil, sorun olmaz).
  Ücretsiz kota (günde ~50 istek) yorum hacmi artarsa yetmez. Slack'te
  kanaldaki HERKES butona basabilir (kullanıcı listesi kısıtlaması yok).
  `send_reply_email=False`: yorumcuya e-posta gitmiyor (ürün kararı,
  değiştirilebilir).
- Küçük temizlik: `anthropic` paketi requirements.txt'te hâlâ duruyor ama artık
  kullanılmıyor.

## Modül 12 — Shopify uygulaması iskeleti ✅
- `@shopify/cli@4.8.2` global kuruldu (kaynağı doğrulandı: shopify.com yayıncıları,
  github.com/Shopify/cli). Node 24.15 zaten uyumlu (gereken ≥22.12).
- `shopify app init --template none` ile "extension-only" resmi şablonundan
  başlatıldı, organizasyon 234396556'ya bağlandı, `destek-triyaj-app/` altına,
  mevcut git deposunun İÇİNE (ayrı bir repo değil).
- DÜZELTME: scaffold kendi iç içe `.git` deposu açmıştı — ana depoyla
  çakışırdı (git status onu görmezdi, dosyalar sessizce izlenmezdi).
  Kaldırıldı; normal alt klasör olarak eklendi. Kendi `.gitignore`'ı
  (node_modules, .shopify/, .env) doğru çalışıyor, üst depodan `git add`
  edildi, node_modules commit'e girmedi (kontrol edildi).
- AGENTS.md (şablonun kendi dosyası) Shopify API işleri için resmi "Shopify
  Dev MCP" eklentisini kullanmamı istiyor. Tam eşleşen isimde bulamadım ama
  Shopify'ın kendi yayınladığı MCP eklentisini (plugin_01RELKgn8qpC38UA3rBhCAtU)
  buldum, öneri kartı gösterildi — kurulumu kullanıcıya bağlı.
- Şablon varsayılan olarak bir örnek gömülü admin uygulaması getiriyor (FAQ
  metaobject + Sidekick "app-tools" uzantısı, `write_products` yetkisiyle).
  Bu bizim tasarımımızın parçası DEĞİL — Modül 14/18'de kendi uzantılarımızla
  (theme app extension, customer account UI extension) değiştirilecek.
  `shopify.app.toml`'daki `write_products` yetkisi de o örneğe ait, Modül 16'da
  gerçek ihtiyacımıza göre (muhtemelen `read_orders`) değişecek.
- `shopify app dev` çalıştırıldı, doğrulandı: **test-store-e3uhspdt gerçekten
  bir development store olarak organizasyonda kayıtlı**, CLI onu otomatik
  varsayılan seçti ("Using your default dev store, test store"). Bu, planın
  başından beri açık duran soruyu kapatıyor. Süreç tam ekran TUI olduğu için
  (tünel URL'si "P" tuşuyla açılıyor, etkileşimli terminal gerektiriyor) daha
  ileri gidemedik; ayrı bir oturumda elle çalıştırılabilir.
- Şablonun `SECURITY.md` dosyası alakasız bir jenerik şablon (bir Ruby gem'inden
  kalma metin) — proje için anlamlı değil, dokunmadım, sadece not düşüyorum.

## Modül 13 — Sunucusuza taşıma: ERTELENDİ
Kişisel Google Cloud hesabı bu iş için kullanılmak istenmiyor (haklı bir
ayrım — iş ile kişisel hesabı karıştırmamak). Ayrı bir GCP hesabı/projesi
netleşince ele alınacak. O zamana kadar sistem yerel makinede (`app.py`)
çalışmaya devam ediyor, bu bir engel değil.

## Sıradaki
Modül 14 (B: mağaza içi destek formu) — GCP gerektirmiyor, doğrudan devam. Yorum kanalının açık iyileştirmeleri
(acil değil): Slack'e "Düzenle" düğmesi, taslak isteminin sıkılaştırılması,
buton yetkisinin kısıtlanması, kullanılmayan `anthropic` paketinin temizliği.

## Genel durum
Faz 1 ve Faz 2'nin yorum kanalı tamamlandı: Modül 1-11 canlı test edildi
(`draft_reply` ancak Modül 11'de ilk kez gerçekten çalıştı). Modül 12-22:
başlanmadı. Bilinen zayıf nokta: ücretsiz modelin döngü hatası nedeniyle
yorumların önemli bir kısmı "Teknik hata" ile insana gidiyor.