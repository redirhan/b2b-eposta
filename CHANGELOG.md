# Değişiklik günlüğü

## 1.0.0 — 2026-10-27
İlk sürüm. Bu bir hukuki görüş değildir.
- Firma profili (YAML) → 3 e-posta taslağı: ilk temas (3-4 cümle, link yok, gözlem + tanıtım + fırsat + izin isteyen
  soru) ve 3. / 7. gün takipleri (hafta sonu → pazartesi), aynı yazışmayı yanıtlayarak.
- Her e-postada RET satırı (aynı kanal, ücretsiz), kimlik satırı (ticaret unvanı + MERSİS ya da ad soyad + VKN),
  gönderen e-postası; ilk e-postada kısa aydınlatma satırı; konu "Tanıtım:" ile (kapatılabilir).
- Kontrol listesi: 32 kural (alıcı uygunluğu, İYS, içerik, KVKK, teslimat, yazım, hizmet), madde numaraları ve kaynak
  URL'leri (mevzuat.gov.tr, kvkk.gov.tr, Google), okunma tarihleri; DUR / ENGEL / DÜZELT / UZMANA SOR / UYARI / ELLE.
- Reddeder: tacir/esnaf olmayan alıcı, tüketici, serbest meslek (avukat, hekim, mali müşavir...), İYS'de ret, kaynaksız
  ya da satın alınmış adres, telefon/TCKN içeren profil, gözlemsiz (kişiselleştirilmemiş) e-posta, aynı kanca cümlesi,
  bir seferde 20'den fazla profil, günde 50'den fazla gönderim.
- `kayit.json` (adres kaynağı, tarih, İYS kontrolü, plan) — 3 yıl saklama için.
- `kontrol`: elle düzenlenmiş taslakları yeniden denetler.
- 5 şablon: sosyal-medya, video, web, urun-fotografi, muhasebe-danismanligi (yer tutucu).
- `doctor`, `sablonlar`, `yeni`; 4 kurgusal örnek (hazır, ENGEL + UZMANA SOR, hazır, DUR); 18 birim testi.
- Yalnız standart kütüphane; ağ kodu yok, e-posta göndermez.
