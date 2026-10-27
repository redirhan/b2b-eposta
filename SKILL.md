---
name: b2b-eposta
description: Türk küçük ajans ve serbest çalışanlar için İYS uyumlu B2B ilk temas e-postası yazar. Hedef firmanın HERKESE AÇIK sitesini okur, firmaya özel kısa bir ilk e-posta (3-4 cümle, link yok, önce değer, izin isteyen soru) ve 3. ve 7. gün iki takip e-postası hazırlar; her e-postada RET satırı ve MERSİS/VKN kimlik bilgisi bulunur. Türkiye için madde numaralı kontrol listesi çıkarır (6563 sayılı Kanun ve Ticari Elektronik İletiler Yönetmeliği - tacir/esnaf istisnası, gönderen İYS kaydı, alıcının İYS ret kontrolü, 3 iş günü; KVKK - yalnız firmanın yayımladığı iş adresi, cep telefonu yok, aydınlatma; teslimat - ayrı alan adı, SPF/DKIM/DMARC, ısınma, günde en fazla 20). Toplu gönderimi, tüketici ve serbest meslek (avukat, hekim, mali müşavir) hedeflemeyi reddeder. 5 şablon (sosyal medya, video, web, ürün fotoğrafı, muhasebe danışmanlığı yer tutucu). Kullanıcı "soğuk e-posta yaz", "bu firmaya teklif maili", "takip maili", "İYS'ye uygun mu" dediğinde kullan. E-posta göndermez. Bu bir hukuki görüş değildir.
---

# B2B E-posta (İYS Uyumlu)

Firma sitesi (herkese açık) → **profil.yaml** → `eposta.py yaz` → `epostalar.md` (3 taslak), `kontrol_listesi.md`
(madde numaralı uyum listesi), `kayit.json` (ispat kaydı). Profili sen (Claude) siteyi okuyarak yazarsın; e-postaları,
kimlik/ret satırlarını, tarihleri ve kontrolleri script üretir. **Bu bir hukuki görüş değildir.** Bu cümle kullanıcıya
verdiğin her çıktıda (özet, kontrol listesi, rapor) yer alır; alıcıya gidecek e-posta metnine eklenmez.

## Kurallar (değişmez)

- **E-posta gönderme.** SMTP, Gmail/Outlook API, otomasyon servisi, CRM yok. Hesaba girme, ücretli API çağırma.
  Taslakları kullanıcı kendi kutusundan tek tek, elle gönderir.
- **Tarayıcı açma.** Chrome/Chromium ya da Playwright/Selenium başlatma. Siteyi yalnız **WebFetch** ile oku; WebFetch
  yoksa `curl -sL URL` çıktısını metne çevir. Giriş gerektiren sayfa, kişisel sosyal medya, LinkedIn kişi profili yok.
- **Toplu gönderime yardım etme.** Günde en fazla **20** elle gözden geçirilmiş e-posta. Şunları **reddet** ve uyumlu
  yolu öner: yüzlerce adreslik liste, Google Maps/Apify/Apollo kazıma ya da satın alınmış liste, tahmin edilmiş adres
  (ad.soyad@), spam filtresini atlatma (spintax, gizli metin, sahte "Re:" konu, RET satırını gizleme), WhatsApp/SMS
  toplu mesajı, kullanıcı adına gönderme ya da zamanlama.
- **Kişisel hedefleme yok.** Tüketiciye (bireye), kişisel Gmail/Hotmail adresine ya da cep numarasına soğuk ticari
  ileti yazılmaz. Serbest meslek sahipleri (avukat, hekim, diş hekimi, veteriner, eczacı, mali müşavir, noter) esnaf
  ya da tacir değildir: onlara da yazılmaz (KVK Kurulu 2022/861).
- **Uydurma yok.** Gözlem, rakam, referans iş yalnız sitede gördüğün ya da kullanıcının verdiği bilgiden. Her gözlem
  kaynak URL'siyle profile girer. Sonuç vaadi (takipçi, sıralama, satış garantisi) yazma.
- **Script'in DUR kararını delme.** `yaz` çıkış kodu 3 (DUR) ise taslağı elle yazıp verme; nedenini ve uyumlu
  seçeneği anlat.

## Akış

`S=~/.claude/skills/b2b-eposta/scripts`, `PY=python3` (yalnız standart kütüphane; PyYAML varsa kullanılır).

1. **Kontrol:** `$PY $S/eposta.py doctor`.
2. **Gönderen (bir kez):** `$PY $S/eposta.py yeni gonderen > gonderen.yaml`. Kullanıcıdan iste: ad soyad, marka,
   tür (tacir → ticaret unvanı + MERSİS; esnaf/serbest meslek → VKN, TCKN değil), gönderim adresi, İYS kaydı var mı,
   ayrı gönderim alan adı, SPF/DKIM/DMARC, ısınma başlangıcı, günlük limit (≤ 20). Bilmediklerini `false` bırak;
   kontrol listesi ne yapacağını söyler.
3. **Hizmet ve firma:** hizmet türünü (`$PY $S/eposta.py sablonlar`) ve **tek** hedef firmanın sitesini sor.
   Birden fazla firma verilirse bir oturumda en fazla 20, her biri ayrı profil.
4. **Önce uygunluk:** sitenin alt bilgisinde/iletişim sayfasında ticaret unvanı (Ltd. Şti., A.Ş.), MERSİS, şahıs
   işletmesi bilgisini ara. Avukat, hekim, mali müşavir gibi serbest meslekse dur ve söyle. Belirsizse `bilinmiyor`.
5. **Siteyi oku (en fazla 5 sayfa):** ana sayfa, hakkımızda, iletişim, ürün/hizmet, blog/duyurular. WebFetch
   istemine "işletme türü, ticaret unvanı, MERSİS, iş e-posta adresi, öne çıkan 3 somut şey, eksik görünen şey"
   yaz. Not al: iş adresi (info@, iletisim@ tercih), adresin göründüğü URL, 1-3 somut gözlem + URL.
6. **Profili yaz:** `$PY $S/eposta.py yeni profil --sablon <sablon> > profil.yaml` ve doldur:
   - `kanca` = 1. cümle, firmaya özel, sitede görülen somut şey (≤ 30 kelime). Övgü kalıbı değil, gözlem.
   - `firsat` = 3. cümle (isteğe bağlı): gözleme bağlı somut fırsat. Eleştiri gibi değil, olasılık gibi.
   - `hizmet.teklif` = ücretsiz, küçük, somut değer ("3 reel fikri", "5 maddelik mobil kontrol notu"); cümleye
     "... hazırlayıp göndereyim mi?" diye oturmalı. `ek_deger` = 2. e-postadaki küçük ek fikir.
   - `iys_kontrol`: kullanıcı adresi İYS'ye kaydedip ret kontrolü yaptıysa `ret_yok` + tarih; yapmadıysa `yapilmadi`.
   - Profile telefon, kişisel bilgi, TCKN yazma (script durdurur).
7. **Üret:** `$PY $S/eposta.py yaz profil.yaml --gonderen gonderen.yaml --cikti eposta_cikti/`
   Çıkış 0 = hazır · 2 = taslak var ama ENGEL/DÜZELT (göndermeden çöz) · 3 = DUR (taslak yok, `red_raporu.md`).
8. **Oku ve düzelt (zorunlu):** `epostalar.md`'yi baştan sona oku. Türkçe doğal mı, ekler doğru mu, kanca gerçekten
   firmaya özel mi, teklif cümleye oturuyor mu, iki e-posta aynı şeyi mi söylüyor? Gerekirse profili düzelt ve
   yeniden üret ya da `epostalar.md`'yi elle düzenleyip `$PY $S/eposta.py kontrol eposta_cikti/epostalar.md --gonderen gonderen.yaml` çalıştır.
9. **Sun:** 3 e-postanın konu ve metnini, gönderim günlerini, ENGEL/DÜZELT/UZMANA SOR maddelerini ve ELLE yapılacakları
   (RET gelirse 3 iş günü içinde dur + İYS'ye bildir, yanıt gelirse sırayı durdur, kayıtları 3 yıl sakla) kısaca yaz.
   Sonuna: **Bu bir hukuki görüş değildir.**

## İyi bir ilk e-posta (script'in kurduğu yapı)

1. **Gözlem** (kanca): "Sitenizde her perşembe yeni kavrumunuzu duyurduğunuzu gördüm, ..."
2. **Kim olduğun** (tek cümle): "Ben Deniz; Kıyı Dijital adıyla küçük işletmelerin Instagram hesaplarını yönetiyorum."
3. **Fırsat** (isteğe bağlı): gözleme bağlı, somut.
4. **İzin isteyen soru**: "... 3 kısa reel fikri hazırlayıp bu hafta göndermemi ister misiniz?"

Sonra imza, `—`, RET satırı, kısa aydınlatma satırı (adres nereden alındı, ne için, SİL), kimlik satırı
(ticaret unvanı + MERSİS ya da ad soyad + VKN + e-posta). Konu varsayılan olarak "Tanıtım:" ile başlar (Yön. m.8/6).
Link, ek, görsel, izleme yok. Toplantı istemek yerine önce değer; "evet" gelince örneği gönder.
Takipler (gün 3 ve 7, hafta sonu → pazartesi) aynı yazışmayı yanıtlayarak gider; 2-3 cümle, son e-posta kibarca kapatır.

## Kontrol listesindeki durumlar

| Durum | Anlamı |
|---|---|
| DUR | Taslak yazılmadı: alıcı tacir/esnaf değil, tüketici, serbest meslek, İYS'de ret var, kaynak/gözlem yok, telefon var, toplu |
| ENGEL | Taslak var ama çözülmeden gönderilmez: gönderen İYS kaydı, alıcının İYS kontrolü, MERSİS/VKN, RET satırı |
| DÜZELT | Taslakta yazım kuralı ihlali: cümle sayısı, ilk e-postada link/ek/promosyon, garanti ifadesi, soru yok |
| UZMANA SOR | Hukuki değerlendirme: ücretsiz posta adresi (kişisel veri), serbest meslek şirketi |
| UYARI | Risk ya da iyi uygulama eksiği (ayrı alan adı, SPF/DKIM/DMARC, ısınma, kişi adlı adres) |
| ELLE | Gönderen kendisi yapar: RET'te 3 iş günü içinde durdurma ve İYS bildirimi, kayıt saklama |

Kuralların tamamı, madde numaraları, kaynak URL'leri ve okunma tarihleri: `rules/iys_kvkk.yaml`.

## Alt komutlar

| Komut | İş |
|---|---|
| `doctor` | Python, kural dosyası doğrulama, şablonlar, ağ kodu yokluğu, örnek üretim testi |
| `sablonlar` | 5 hizmet şablonu |
| `yeni gonderen` / `yeni profil --sablon X` | doldurulacak YAML iskeletleri |
| `yaz PROFIL... --gonderen G --cikti DIR` | 3 e-posta + kontrol listesi + kayıt (`--baslangic`, `--bugun`) |
| `kontrol epostalar.md --gonderen G` | elle düzenlenmiş taslakları yeniden denetler |

## Şablonlar

`sosyal-medya`, `video`, `web`, `urun-fotografi`, `muhasebe-danismanligi` (yer tutucu: mali müşavirlik meslek
mevzuatında reklam sınırları var; SMMM/YMM için değildir, `meslek_mevzuati_kontrol_edildi: true` olmadan çalışmaz).
Her şablonun yasak iddiaları ve notları kontrol listesine girer. Yeni hizmet için bir şablonu kopyalayıp düzenleyin.

Bu bir hukuki görüş değildir.
