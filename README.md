# B2B E-posta (İYS Uyumlu) — ücretsiz Claude Code skill'i

> **Bu bir hukuki görüş değildir.** Bilgilendirme amaçlıdır; kesin değerlendirme için bir hukukçuya danışın.

Küçük ajanslar ve serbest çalışanlar için: hedef firmanın **herkese açık** sitesini okuyup firmaya özel, kısa ve önce
değer veren bir **ilk e-posta** ile **2 takip e-postası** yazar. Türkiye kurallarına göre madde numaralı bir
**kontrol listesi** çıkarır. E-posta göndermez; taslakları siz kendi kutunuzdan tek tek gönderirsiniz.

Redirhan Studio tarafından hazırlandı. Ücretsiz, MIT lisanslı.

## Ne üretir?

| Dosya | İçerik |
|---|---|
| `epostalar.md` | 3 taslak: ilk temas (3-4 cümle, link yok, izin isteyen soru) + 3. gün ve 7. gün takipleri, konu satırları ve gönderim günleri |
| `kontrol_listesi.md` | Uyum listesi: DUR / ENGEL / DÜZELT / UZMANA SOR / UYARI / ELLE, her maddede dayanak (madde no) ve kaynak URL'leri |
| `kayit.json` | İspat kaydı: adres nereden, hangi tarihte alındı, İYS kontrolü, gönderim planı (3 yıl saklayın) |
| `red_raporu.md` | Alıcı uygun değilse taslak yerine nedenleri |

## Hangi kurallar?

- **6563 sayılı Kanun m.6/2, Yönetmelik m.6/3:** esnaf ve tacirlere önceden onaysız ticari e-posta gönderilebilir.
  Ama: **gönderen İYS'ye kaydolur** (Yön. m.5/2), alıcının adresi **göndermeden önce İYS'ye kaydedilip ret kontrolü
  yapılır** (m.6/6), **her iletide kolay ve ücretsiz ret imkânı** aynı kanaldan sunulur (Kanun m.8/2, Yön. m.9/3-4),
  ret gelince **3 iş günü içinde durulur** (Kanun m.8/3, Yön. m.10) ve ret **3 iş günü içinde İYS'ye bildirilir**
  (m.9/6). İletide **MERSİS + ticaret unvanı** ya da **ad soyad + VKN** (m.8/2) ve bir iletişim bilgisi (m.8/5) yer alır.
- **Serbest meslek sahipleri** (avukat, hekim, mali müşavir...) esnaf ya da tacir değildir: onaysız yazılmaz
  (KVK Kurulu 2022/861, 150.000 TL ceza).
- **KVKK:** yalnız firmanın kendi yayımladığı iş iletişim adresi; alenileştirilmiş veri yalnız o amaçla işlenebilir;
  kişisel cep numarası yok; kısa aydınlatma (m.10).
- **Teslimat:** ayrı gönderim alan adı, SPF/DKIM/DMARC, 2 hafta ısınma, günde en fazla 20 elle gözden geçirilmiş e-posta,
  link ve izleme yok, spam oranı %0,1 altında.

Kaynakların tamamı, URL'leri ve okunma tarihleri `rules/iys_kvkk.yaml` dosyasında (mevzuat.gov.tr'den 27.10.2026'da
okundu).

## Neyi reddeder?

Toplu gönderim (bir seferde 20'den fazla firma, günde 50'den fazla), satın alınmış ya da kazınmış liste, tahmin edilmiş
adres, tüketici/kişisel hedefleme, serbest meslek sahipleri, İYS'de reddi olan alıcı, telefon numarası içeren profil,
firmaya özel gözlemi olmayan (kopyala-yapıştır) e-posta, sahte "Re:" konu satırı.

## Kurulum

```bash
unzip b2b-eposta-v1.0.zip -d ~/.claude/skills/
```

Ya da `b2b-eposta/` klasörünü `~/.claude/skills/` içine kopyalayın, Claude Code'u yeniden başlatın.
Gereken: Python 3.8+. Başka paket gerekmez (PyYAML varsa kullanılır).

## Kullanım

Claude Code'da:

> fincanalti.example için sosyal medya hizmetimi anlatan bir soğuk e-posta yaz, İYS'ye uygun olsun.

Claude önce gönderen bilgilerinizi (bir kez) sorar, firmanın tacir/esnaf olup olmadığını sitesinden kontrol eder,
en fazla 5 sayfayı okur, profili yazar, taslakları üretir, okur ve kontrol listesiyle sunar.

Elle:

```bash
S=~/.claude/skills/b2b-eposta/scripts
python3 $S/eposta.py doctor
python3 $S/eposta.py yeni gonderen > gonderen.yaml
python3 $S/eposta.py yeni profil --sablon sosyal-medya > profil.yaml
python3 $S/eposta.py yaz profil.yaml --gonderen gonderen.yaml --cikti eposta_cikti/
python3 $S/eposta.py kontrol eposta_cikti/epostalar.md --gonderen gonderen.yaml
```

## Örnekler (kurgusal firmalar)

| Örnek | Sonuç |
|---|---|
| `01-kafe-sosyal-medya` (Ltd. Şti., info@ adresi, İYS kontrolü yapılmış) | Hazır |
| `02-mobilya-urun-fotografi` (şahıs işletmesi, ücretsiz posta adresi, İYS kontrolü yok) | ENGEL (İYS) + UZMANA SOR (kişisel veri) |
| `03-otel-video` (A.Ş., satis@ adresi) | Hazır |
| `04-hukuk-burosu-web` (avukatlık bürosu) | DUR: serbest meslek, taslak yazılmadı |

## Şablonlar

`sosyal-medya`, `video`, `web`, `urun-fotografi`, `muhasebe-danismanligi` (yer tutucu; mali müşavirler için değildir,
meslek mevzuatında reklam sınırları vardır). Yeni bir hizmet için bir şablonu kopyalayıp düzenleyin.

## Neyi yapmaz?

E-posta göndermez, zamanlamaz, hesaba bağlanmaz, ağa çıkmaz (siteyi Claude okur), ücretli API kullanmaz, tarayıcı
açmaz. İYS kaydını ve alıcı kontrolünü sizin yerinize yapmaz; nasıl yapılacağını ve yapılmadan gönderilmemesi gerektiğini
söyler. Hukuki görüş vermez.

## Lisans

MIT © 2026 Redirhan Studio. Bu bir hukuki görüş değildir.
