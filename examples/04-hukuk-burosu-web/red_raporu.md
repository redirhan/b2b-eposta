# Kontrol listesi: Yıldız Hukuk

> **Bu bir hukuki görüş değildir.** Bilgilendirme amaçlı bir kontrol listesidir; kesin değerlendirme için bir hukukçuya danışın.

**Sonuç:** DURDU: taslak yazılmadı. Aşağıdaki DUR maddeleri bu alıcıya (ya da bu şekilde) soğuk ticari e-posta gönderilmemesi gerektiğini gösteriyor. Bunun yerine: eksik bilgiyi tamamlayın (tür, kaynak, gözlem) ya da alıcı uygun değilse yalnız onun sizinle iletişime geçtiği, tanışıklık ya da etkinlik gibi onaylı kanalları kullanın.

**Sayılar:** DUR 1 · ENGEL 1 · GEÇTİ 11

## Önce çözün (DUR / ENGEL / DÜZELT)

- [ ] **DUR · ALC-02 Serbest meslek sahibi değil (avukat, hekim, mali müşavir vb.)**: Alıcı serbest meslek sahibi (avukat, hekim, mali müşavir vb.): esnaf ya da tacir değil, onaysız ticari e-posta gönderilemez (KVK Kurulu 2022/861). → Bu alıcıya soğuk e-posta göndermeyin. Tanışıklık, etkinlik, açık bir 'bize yazın' çağrısı gibi onaylı kanalları kullanın. _Dayanak: KVK Kurulu 2022/861; 6563 s. Kanun m.6/1-2_
- [ ] **ENGEL · IYS-02 Alıcı adresi İYS'ye kaydedildi ve ret kontrolü yapıldı**: Alıcı adresi henüz İYS'ye tacir/esnaf olarak kaydedilip ret kontrolü yapılmadı (iys_kontrol.sonuc / tarih). → Adresi İYS'ye tacir/esnaf alıcı olarak yükleyin, ret durumunu kontrol edin; profilde iys_kontrol.sonuc (ret_yok / ret_var) ve tarih alanlarını doldurun. _Dayanak: Yönetmelik m.6/3, 6/6_

## Geçenler (otomatik kontrol)

- [x] **GEÇTİ · ALC-04 Toplu değil, firmaya özel**: 1 kaynaklı gözlem; ilk cümle firmaya özel. _Dayanak: 6563 s. Kanun m.12/2_
- [x] **GEÇTİ · ICR-01 Gönderen kimliği: MERSİS + ticaret unvanı ya da ad soyad + VKN**: Ticaret unvanı ve 16 haneli MERSİS numarası var; imzaya eklenir. _Dayanak: Yönetmelik m.8/2; 6563 s. Kanun m.7/2_
- [x] **GEÇTİ · ICR-02 Erişilebilir iletişim bilgisi**: İletişim bilgisi: deniz@kiyidijital-posta.example _Dayanak: Yönetmelik m.8/5; 6563 s. Kanun m.7/2_
- [x] **GEÇTİ · IYS-01 Gönderen İYS'ye kayıtlı**: Gönderen İYS'ye kayıtlı olarak işaretli. _Dayanak: Yönetmelik m.5/2_
- [x] **GEÇTİ · KVK-01 Adres firmanın yayımladığı iş iletişim adresi**: Genel kurumsal adres (info@yildizhukuk.example), kaynak: https://yildizhukuk.example/iletisim. _Dayanak: KVKK m.4, m.5/2; KVKK alenileştirme duyurusu duyuru; KVK Kurulu 2022/861_
- [x] **GEÇTİ · KVK-02 Kişisel cep telefonu ve gereksiz kişisel veri yok**: Profilde telefon ya da kişisel kimlik verisi yok. _Dayanak: KVKK m.4/2_
- [x] **GEÇTİ · KVK-03 Kısa aydınlatma**: Aydınlatma metninin yeri belli; ilk e-postada kısa satır, takiplerde yeri yazılır. _Dayanak: KVKK m.10, m.11_
- [x] **GEÇTİ · TES-01 Ayrı gönderim alan adı**: Ayrı gönderim alan adı: kiyidijital-posta.example (ana: kiyidijital.example). _Dayanak: Gmail gönderen şartları Requirements for all senders_
- [x] **GEÇTİ · TES-02 SPF, DKIM, DMARC**: SPF, DKIM, DMARC kurulu olarak işaretli. _Dayanak: Gmail gönderen şartları Requirements for all senders / 5,000+_
- [x] **GEÇTİ · TES-03 2 hafta ısınma**: Isınma 2026-10-06 tarihinde başlamış (21 gün).
- [x] **GEÇTİ · TES-04 Günde en fazla 20, elle gözden geçirilmiş**: Günlük limit 15 (≤ 20). _Dayanak: Gmail gönderen şartları spam rate_

## Yaptırımlar (bilgi)

6563 m.12: onaysız ileti ve ret yükümlülüğüne aykırılık için idari para cezası; bir defada birden fazla kişiye onaysız ileti cezası on katına kadar artırılabilir. 2026 tutarları (ikincil kaynak): m.12/1-a 2.859-14.309 TL, m.12/1-c 5.723-42.930 TL. KVKK ihlali ayrıca cezalandırılır (ör. 2022/861'de 150.000 TL).

## Kaynaklar

- **K6563** 6563 sayılı Elektronik Ticaretin Düzenlenmesi Hakkında Kanun (RG 05.11.2014, sayı 29166). https://www.mevzuat.gov.tr/MevzuatMetin/1.5.6563.htm (okunma 2026-10-27)
- **YON** Ticari İletişim ve Ticari Elektronik İletiler Hakkında Yönetmelik (RG 15.07.2015, sayı 29417; RG 04.01.2020, sayı 30998 değişiklikleri işlenmiş metin). https://www.mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatNo=20914&MevzuatTertip=5&MevzuatTur=7 (okunma 2026-10-27)
- **K6698** 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK). https://www.mevzuat.gov.tr/MevzuatMetin/1.5.6698.htm (okunma 2026-10-27)
- **KVKK-861** KVK Kurulu 01.09.2022 tarihli ve 2022/861 sayılı karar özeti (arama motorundan bulunan iş e-postasına onaysız ticari ileti). https://www.kvkk.gov.tr/Icerik/7580/2022-861 (okunma 2026-10-27)
- **KVKK-ALEN** KVKK Alenileştirme Hakkında Kamuoyu Duyurusu. https://www.kvkk.gov.tr/Icerik/6843/-ALENILESTIRME-HAKKINDA-KAMUOYU-DUYURUSU (okunma 2026-10-27)
- **TTK** 6102 sayılı Türk Ticaret Kanunu m.16/1 (ticaret şirketleri tacir sayılır) ve 5362 sayılı Esnaf ve Sanatkârlar Meslek Kuruluşları Kanunu m.3 (esnaf tanımı). https://www.mevzuat.gov.tr/MevzuatMetin/1.5.6102.pdf (okunma 2026-10-27)
- **SMMM** Serbest Muhasebeci Mali Müşavirlik ve Yeminli Mali Müşavirlik Mesleklerine İlişkin Haksız Rekabet ve Reklam Yasağı Yönetmeliği (RG 21.11.2007, sayı 26707). https://turmob.org.tr/Arsiv/FCKEditor/userfiles/file/3568YASAYONETMELIK7NISAN2025/13-SMMM-YMMHaks%C4%B1zRekabet.pdf (okunma 2026-10-27)
- **GOOGLE** Google Workspace, Email sender guidelines (Gmail gönderen şartları). https://support.google.com/a/answer/81126?hl=en (okunma 2026-10-27)
- **CEZA2026** 6563 sayılı Kanun m.12 idari para cezalarının 2026 tutarları (ikincil kaynak: Moroğlu Arseven duyurusu). https://www.morogluarseven.com/tr/insights/yayinlar/6563-sayili-elektronik-ticaretin-duzenlenmesi-hakkinda-kanun-kapsaminda-2026-yilinda-uygulanacak-idari-para-cezalarina-iliskin-teblig-yayimlandi/ (okunma 2026-10-26)

Kural dosyası sürümü 1.0.0, tarih 2026-10-27. Bu bir hukuki görüş değildir.
