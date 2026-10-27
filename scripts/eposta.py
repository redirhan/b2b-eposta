#!/usr/bin/env python3
"""B2B E-posta (İYS Uyumlu) — firma profili (YAML) -> 3 e-posta taslağı + uyum kontrol listesi.

Bu bir hukuki görüş değildir.

Yerel çalışır: e-posta GÖNDERMEZ, hesaba bağlanmaz, ağa çıkmaz. Taslakları kullanıcı kendi kutusundan elle gönderir.

Kullanım:
  python3 eposta.py doctor
  python3 eposta.py sablonlar
  python3 eposta.py yeni gonderen > gonderen.yaml
  python3 eposta.py yeni profil --sablon sosyal-medya > profil.yaml
  python3 eposta.py yaz profil.yaml --gonderen gonderen.yaml --cikti cikti/
  python3 eposta.py yaz a.yaml b.yaml --gonderen gonderen.yaml --cikti cikti/ --baslangic 2026-11-03
  python3 eposta.py kontrol cikti/epostalar.md --gonderen gonderen.yaml

Çıkış kodları: 0 = sorun yok (elle maddeler hariç) · 1 = kullanım/dosya hatası ·
               2 = taslak yazıldı ama ENGEL/DÜZELT var, göndermeyin · 3 = DURDU, taslak yazılmadı.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
RULES_PATH = SKILL_DIR / "rules" / "iys_kvkk.yaml"
TEMPLATES_DIR = SKILL_DIR / "templates"
UYARI = "Bu bir hukuki görüş değildir."

SIRA = {"DUR": 7, "ENGEL": 6, "DUZELT": 5, "UZMANA_SOR": 4, "UYARI": 3, "MANUEL": 2, "GECTI": 1, "BILGI": 0}
ETIKET = {"DUR": "DUR", "ENGEL": "ENGEL", "DUZELT": "DÜZELT", "UZMANA_SOR": "UZMANA SOR", "UYARI": "UYARI",
          "MANUEL": "ELLE", "GECTI": "GEÇTİ", "BILGI": "BİLGİ"}
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
KAYNAK_YERI = {"firma_sitesi": "sitenizde", "isletme_profili": "işletme profilinizde",
               "firma_sosyal_medya": "işletme hesabınızda"}
RET_SATIRI = ("Bu tür e-postaları almak istemezseniz bu e-postaya “RET” yazmanız yeterli; "
              "3 iş günü içinde listeden çıkarır, bir daha yazmam.")
AYDINLATMA_SATIRI = ("Adresinizi {yer} herkese açık yayımlanan iletişim bilgisinden aldım ve yalnız bu teklif için "
                     "kullanıyorum; silinmesini isterseniz “SİL” yazmanız yeterli.")
TAKIP1_ACILIS = ["Önceki e-postam gözden kaçmış olabilir diye kısaca tekrar yazıyorum.",
                 "Birkaç gün önce {teklif} için yazmıştım, kısaca hatırlatmak istedim.",
                 "Geçen e-postama kısa bir ek yapmak istedim."]
TAKIP1_KAPANIS = ["Göndermemi isterseniz tek satırlık bir yanıt yeterli.",
                  "Uygunsa yanıtlamanız yeterli, gerisini ben hazırlarım.",
                  "İsterseniz bu hafta hazırlayıp gönderebilirim, tek satır yanıt yeterli."]
TAKIP2_ACILIS = ["Son kez yazıyorum, sonra rahatsız etmeyeceğim.",
                 "Bu konuda yazdığım son e-posta bu, sonra rahatsız etmeyeceğim."]
TAKIP2_ORTA = ["{teklif} ileride işinize yararsa bu e-postayı yanıtlamanız yeterli.",
               "İleride {teklif} isterseniz bu yazışmayı yanıtlamanız yeterli."]
TAKIP2_KAPANIS = ["Şu an önceliğiniz değilse tamamen anlarım; iyi çalışmalar dilerim.",
                  "Şimdilik uygun değilse sorun değil; işlerinizde kolaylık dilerim."]
TR_MOBIL = re.compile(r"(?<!\d)(?:\+?90[\s-]?|0)?\(?5\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)")
EPOSTA_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
LINK_RE = re.compile(r"https?://|www\.|\b[a-z0-9-]+\.(?:com|net|org|com\.tr|tr|io|co|app|site|example)\b(?:/\S*)?",
                     re.I)


# ----------------------------------------------------------------------------- yardımcılar
def load_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import mini_yaml  # noqa: E402
        return mini_yaml.load(path)
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def s(v) -> str:
    return "" if v is None else str(v).strip()


def tr_lower(t: str) -> str:
    return t.replace("I", "ı").replace("İ", "i").lower()


def tr_cap(t: str) -> str:
    """İlk karakter harfse Türkçe kurala göre büyütür (i -> İ); sayıyla başlayan metne dokunmaz."""
    if t and t[0].isalpha():
        return {"i": "İ", "ı": "I"}.get(t[0], t[0].upper()) + t[1:]
    return t


def bitir(t: str) -> str:
    t = s(t)
    return t if not t or t[-1] in ".!?…" else t + "."


def sec(lst, *anahtar):
    """Firma adına göre sabit (deterministik) varyant seçimi: aynı firma hep aynı metni alır."""
    lst = [x for x in (lst or []) if s(x)]
    if not lst:
        return ""
    h = int(hashlib.md5("|".join(anahtar).encode("utf-8")).hexdigest(), 16)
    return lst[h % len(lst)]


_KISALTMA = ["Ltd.", "Şti.", "A.Ş.", "vb.", "vs.", "Dr.", "No.", "örn.", "ör.", "bkz.", "Sn.", "Av."]


def cumleler(text: str) -> list:
    t = " ".join(text.split())
    for k in _KISALTMA:
        t = t.replace(k, k.replace(".", "§"))
    t = re.sub(r"(\d)\.(\d)", r"\1§\2", t)
    parts = re.split(r"(?<=[.!?…])\s+", t)
    return [p.replace("§", ".") for p in parts if re.search(r"\w", p)]


def kelime_say(text: str) -> int:
    return len(re.findall(r"\w+", text))


def bul(text: str, ifadeler) -> list:
    """Kelime başından eşleşir: "garanti" -> "garantili" yakalanır, "çekirdekten" içindeki "ekte" yakalanmaz."""
    low = tr_lower(text)
    return [i for i in (ifadeler or []) if re.search(r"(?<!\w)" + re.escape(tr_lower(str(i))), low)]


def tarih(v):
    if v is None or v == "":
        return None
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def is_gunu(d: dt.date) -> dt.date:
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    return d


def slug(t: str) -> str:
    t = tr_lower(t)
    for a, b in (("ç", "c"), ("ğ", "g"), ("ı", "i"), ("ö", "o"), ("ş", "s"), ("ü", "u"), ("â", "a"), ("î", "i")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:40] or "firma"


# ----------------------------------------------------------------------------- kurallar / şablonlar
def load_rules(path: Path = RULES_PATH) -> dict:
    r = load_yaml(path)
    r["_kural"] = {k["id"]: k for k in r["kurallar"]}
    r["_kaynak"] = {k["id"]: k for k in r["kaynaklar"]}
    return r


def validate_rules(r: dict) -> list:
    err = []
    if r.get("uyari_metni") != UYARI:
        err.append("uyari_metni değişmiş")
    for k in r["kaynaklar"]:
        for f in ("id", "belge", "url", "okunma"):
            if not s(k.get(f)):
                err.append(f"kaynak {k.get('id')}: {f} yok")
    ids = set()
    for k in r["kurallar"]:
        for f in ("id", "baslik", "kategori", "aciklama", "duzeltme"):
            if not s(k.get(f)):
                err.append(f"kural {k.get('id')}: {f} yok")
        if k["id"] in ids:
            err.append(f"kural {k['id']} iki kez")
        ids.add(k["id"])
        for ref in k.get("kaynak") or []:
            kid = str(ref).split("|")[0].strip()
            if kid not in r["_kaynak"]:
                err.append(f"kural {k['id']}: bilinmeyen kaynak {kid}")
    for need in ("politika", "sozluk"):
        if need not in r:
            err.append(f"{need} bölümü yok")
    return err


def template_names() -> list:
    return sorted(p.stem for p in TEMPLATES_DIR.glob("*.yaml"))


def load_template(name: str) -> dict:
    p = TEMPLATES_DIR / f"{name}.yaml"
    if not p.is_file():
        raise FileNotFoundError(f"şablon yok: {name} (var olanlar: {', '.join(template_names())})")
    t = load_yaml(p)
    for f in ("ad", "baslik", "tanitim", "cta", "konu", "konu_kisa_varsayilan", "ek_deger_varsayilan",
              "teklif_ornekleri", "yasak_iddialar", "notlar"):
        if f not in t:
            raise ValueError(f"şablon {name}: {f} alanı yok")
    return t


def kaynak_metni(r: dict, kural_id: str) -> str:
    out = []
    for ref in r["_kural"][kural_id].get("kaynak") or []:
        kid, _, madde = str(ref).partition("|")
        kid = kid.strip()
        ad = {"K6563": "6563 s. Kanun", "YON": "Yönetmelik", "K6698": "KVKK", "KVKK-861": "KVK Kurulu",
              "KVKK-ALEN": "KVKK alenileştirme duyurusu", "TTK": "TTK/5362", "SMMM": "SMMM/YMM Reklam Yön.",
              "GOOGLE": "Gmail gönderen şartları", "CEZA2026": "2026 ceza tutarları"}.get(kid, kid)
        out.append(f"{ad} {madde.strip()}".strip())
    return "; ".join(out)


# ----------------------------------------------------------------------------- denetim
class Sonuc:
    def __init__(self):
        self.items = []  # {id, durum, bulgu, eposta}

    def ekle(self, kid, durum, bulgu="", eposta=None):
        self.items.append({"id": kid, "durum": durum, "bulgu": bulgu, "eposta": eposta})

    def en_kotu(self) -> str:
        return max((i["durum"] for i in self.items), key=lambda d: SIRA[d], default="GECTI")

    def say(self) -> dict:
        c = {}
        for i in self.items:
            c[i["durum"]] = c.get(i["durum"], 0) + 1
        return c


def gonderen_denetle(g: dict, r: dict, bugun: dt.date, res: Sonuc):
    pol, soz = r["politika"], r["sozluk"]
    if g.get("iys_kayitli") is True:
        res.ekle("IYS-01", "GECTI", "Gönderen İYS'ye kayıtlı olarak işaretli.")
    else:
        res.ekle("IYS-01", "ENGEL", "gonderen.yaml'da iys_kayitli: true değil.")
    tur = s(g.get("tur"))
    if tur == "tacir":
        mersis = re.sub(r"\D", "", s(g.get("mersis")))
        if s(g.get("ticari_unvan")) and len(mersis) == 16:
            res.ekle("ICR-01", "GECTI", "Ticaret unvanı ve 16 haneli MERSİS numarası var; imzaya eklenir.")
        else:
            res.ekle("ICR-01", "ENGEL", "Tacir gönderen için ticari_unvan ve 16 haneli mersis gerekli.")
    elif tur in ("esnaf", "serbest_meslek"):
        vkn = re.sub(r"\D", "", s(g.get("vkn")))
        if s(g.get("ad_soyad")) and len(vkn) == 10:
            res.ekle("ICR-01", "GECTI" if tur == "esnaf" else "UYARI",
                     "Ad soyad ve VKN var; imzaya eklenir." + (" Serbest meslek gönderen Yönetmelikte ayrıca "
                                                              "sayılmamış; daha sıkı yorum uygulandı." if tur != "esnaf" else ""))
        else:
            res.ekle("ICR-01", "ENGEL", "Esnaf/serbest meslek gönderen için ad_soyad ve 10 haneli vkn gerekli "
                                        "(TCKN yazmayın).")
        if s(g.get("tckn")):
            res.ekle("KVK-02", "UYARI", "gonderen.yaml'da tckn var; e-postalarda TCKN yerine VKN kullanın, alanı silin.")
    else:
        res.ekle("ICR-01", "ENGEL", "gonderen.yaml'da tur (tacir / esnaf / serbest_meslek) yok.")
    ep = s(g.get("eposta"))
    if EPOSTA_RE.fullmatch(ep or "-"):
        res.ekle("ICR-02", "GECTI", f"İletişim bilgisi: {ep}")
    else:
        res.ekle("ICR-02", "ENGEL", "gonderen.yaml'da geçerli bir eposta yok.")
    if s(g.get("aydinlatma_metni_yeri")):
        res.ekle("KVK-03", "GECTI", "Aydınlatma metninin yeri belli; ilk e-postada kısa satır, takiplerde yeri yazılır.")
    else:
        res.ekle("KVK-03", "UYARI", "aydinlatma_metni_yeri boş. Sitenize kısa bir KVKK aydınlatma sayfası koyun; "
                                    "istenirse metni gönderin.")
    t = g.get("teslimat") or {}
    gd, ad_ = s(t.get("gonderim_domaini")).lower(), s(t.get("ana_domain")).lower()
    ep_dom = ep.split("@")[-1].lower() if "@" in ep else ""
    if ep_dom.split(".")[0] in soz["ucretsiz_posta"]:
        res.ekle("TES-01", "UYARI", "Gönderen adres ücretsiz bir posta servisinde. Soğuk e-postayı kendi alan "
                                    "adınızdan ve ana alan adınızdan ayrı bir gönderim alan adından gönderin.")
    elif gd and ad_ and gd != ad_ and ep_dom == gd:
        res.ekle("TES-01", "GECTI", f"Ayrı gönderim alan adı: {gd} (ana: {ad_}).")
    else:
        res.ekle("TES-01", "UYARI", "Ayrı gönderim alan adı yok ya da gönderen adres o alan adında değil "
                                    "(teslimat.gonderim_domaini / ana_domain).")
    eksik = [k.upper() for k in ("spf", "dkim", "dmarc") if t.get(k) is not True]
    res.ekle("TES-02", "GECTI" if not eksik else "UYARI",
             "SPF, DKIM, DMARC kurulu olarak işaretli." if not eksik else f"Kurulu işaretlenmemiş: {', '.join(eksik)}.")
    ib = tarih(t.get("isinma_baslangic"))
    if ib is None:
        res.ekle("TES-03", "UYARI", "teslimat.isinma_baslangic yok. Yeni kutuyu 2 hafta ısıtın.")
    elif (bugun - ib).days >= int(pol["isinma_gun"]):
        res.ekle("TES-03", "GECTI", f"Isınma {ib.isoformat()} tarihinde başlamış ({(bugun - ib).days} gün).")
    else:
        res.ekle("TES-03", "UYARI", f"Isınma {(bugun - ib).days}. gününde; {pol['isinma_gun']} gün dolana kadar "
                                    "günde 5-10 e-postayı geçmeyin.")
    lim = t.get("gunluk_limit")
    try:
        lim = int(lim)
    except (TypeError, ValueError):
        lim = None
    if lim is None:
        res.ekle("TES-04", "UYARI", f"teslimat.gunluk_limit yok; önerilen en fazla {pol['gunluk_onerilen']}.")
    elif lim > int(pol["gunluk_ust"]):
        res.ekle("TES-04", "DUR", f"Günlük limit {lim}: toplu gönderim. Bu skill günde {pol['gunluk_ust']}'nin "
                                  f"üstü için taslak yazmaz; önerilen en fazla {pol['gunluk_onerilen']}.")
    elif lim > int(pol["gunluk_onerilen"]):
        res.ekle("TES-04", "UYARI", f"Günlük limit {lim}; önerilen en fazla {pol['gunluk_onerilen']}, elle gözden geçirilmiş.")
    else:
        res.ekle("TES-04", "GECTI", f"Günlük limit {lim} (≤ {pol['gunluk_onerilen']}).")


def profil_denetle(p: dict, g: dict, tpl: dict | None, r: dict, res: Sonuc):
    soz = r["sozluk"]
    if not isinstance(p, dict) or any(k in p for k in ("hedefler", "firmalar", "liste")):
        res.ekle("ALC-04", "DUR", "Bir profil dosyası tek bir firmayı anlatmalı; liste/toplu dosya kabul edilmez.")
        return
    ham = json.dumps(p, ensure_ascii=False, default=str)
    if TR_MOBIL.search(ham) or any(k in p for k in ("telefon", "cep", "tckn", "gsm")):
        res.ekle("KVK-02", "DUR", "Profilde telefon/cep numarası ya da TCKN var. Bu skill yalnız iş e-postası içindir; "
                                  "telefonu ve kişisel verileri profilden silin.")
    else:
        res.ekle("KVK-02", "GECTI", "Profilde telefon ya da kişisel kimlik verisi yok.")
    # --- alıcı türü
    at, tt = s(p.get("alici_turu")), s(p.get("tuzel_tur"))
    firma_sektor = f"{s(p.get('firma'))} {s(p.get('sektor'))}"
    sm_hits = bul(firma_sektor, soz["serbest_meslek"])
    if at in ("tacir", "esnaf"):
        if tt in ("limited", "anonim") and at != "tacir":
            res.ekle("ALC-01", "UYARI", f"tuzel_tur {tt} ise alıcı tacirdir; alici_turu: tacir yazın.")
        else:
            res.ekle("ALC-01", "GECTI", f"Alıcı {at}" + (f" ({tt})" if tt else "") + ": 6563 m.6/2 istisnası uygulanabilir.")
        if not s(p.get("tur_kaniti")):
            res.ekle("ALC-01", "UYARI", "tur_kaniti boş: sitede ticaret unvanı / MERSİS / şahıs işletmesi bilgisini "
                                        "nereden gördüğünüzü yazın (ispat için).")
        if sm_hits:
            res.ekle("ALC-02", "UZMANA_SOR", f"Firma adı/sektörde serbest meslek işareti: {', '.join(sm_hits)}. "
                                             "Alıcı gerçekten tacir/esnaf mı, meslek kuralları var mı, sorun.")
        else:
            res.ekle("ALC-02", "GECTI", "Serbest meslek işareti yok.")
        res.ekle("ALC-03", "GECTI", "Hedef bir işletme.")
    elif at == "serbest_meslek":
        if tt in ("limited", "anonim"):
            res.ekle("ALC-02", "UZMANA_SOR", "Serbest meslek faaliyeti şirket olarak yürütülüyor: şirket tacirdir ama "
                                             "meslek kuralları ayrıca uygulanabilir. Bir hukukçuya sorun.")
        else:
            res.ekle("ALC-02", "DUR", "Alıcı serbest meslek sahibi (avukat, hekim, mali müşavir vb.): esnaf ya da tacir "
                                      "değil, onaysız ticari e-posta gönderilemez (KVK Kurulu 2022/861).")
    elif at == "tuketici":
        res.ekle("ALC-03", "DUR", "Alıcı bir birey/tüketici. Önceden onay olmadan ticari e-posta gönderilemez; bu skill "
                                  "kişisel hedefleme için taslak yazmaz.")
    elif at in ("kamu", "dernek_vakif"):
        res.ekle("ALC-01", "DUR", f"Alıcı {at}: tacir/esnaf istisnası kapsamında görünmüyor. Onaylı bir kanal kullanın "
                                  "ya da bir hukukçuya sorun.")
    else:
        res.ekle("ALC-01", "DUR", "alici_turu boş ya da bilinmiyor. Önce firmanın tacir mi esnaf mı olduğunu sitesinden "
                                  "doğrulayın (Ltd. Şti., A.Ş., MERSİS, şahıs işletmesi).")
    # --- adres ve kaynağı
    ep = s(p.get("eposta"))
    kaynak, kt = s(p.get("eposta_kaynagi")), s(p.get("kaynak_turu"))
    if not EPOSTA_RE.fullmatch(ep or "-"):
        res.ekle("KVK-01", "DUR", "Profilde geçerli bir eposta yok.")
    elif not kaynak or kt not in KAYNAK_YERI:
        res.ekle("KVK-01", "DUR", "Adresin kaynağı belli değil. eposta_kaynagi (URL) ve kaynak_turu (firma_sitesi / "
                                  "isletme_profili / firma_sosyal_medya) zorunlu; satın alınmış ya da tahmin edilmiş "
                                  "adres kullanılmaz.")
    elif bul(kaynak, soz["yasak_kaynak"]):
        res.ekle("KVK-01", "DUR", f"Kabul edilmeyen adres kaynağı: {', '.join(bul(kaynak, soz['yasak_kaynak']))}. "
                                  "Yalnız firmanın kendi yayımladığı iş iletişim adresi.")
    else:
        local, dom = ep.lower().split("@", 1)
        if dom.split(".")[0] in soz["ucretsiz_posta"]:
            res.ekle("KVK-01", "UZMANA_SOR", "Adres ücretsiz bir posta servisinde: büyük olasılıkla bir gerçek kişinin "
                                             "adresi (kişisel veri). Firma bunu kendi sitesinde iş iletişimi için "
                                             "yayımlamışsa bile KVKK dayanağı belirsiz; bir uzmana sorun ve aydınlatma "
                                             "satırını kaldırmayın.")
        elif local.split("+")[0] in soz["genel_kutu"]:
            res.ekle("KVK-01", "GECTI", f"Genel kurumsal adres ({ep}), kaynak: {kaynak}.")
        else:
            res.ekle("KVK-01", "UYARI", f"Adres bir kişinin adını taşıyor olabilir ({ep}): kişisel veri. Firma bu adresi "
                                        "iş iletişimi için yayımlamış olmalı; varsa info@ gibi genel adresi tercih edin.")
    # --- İYS
    ik = p.get("iys_kontrol") or {}
    sonuc = s(ik.get("sonuc"))
    if sonuc == "ret_var":
        res.ekle("IYS-02", "DUR", "Alıcı İYS'de ret hakkını kullanmış: onay alınmadan ticari e-posta gönderilemez.")
    elif sonuc == "ret_yok" and tarih(ik.get("tarih")):
        res.ekle("IYS-02", "GECTI", f"Adres İYS'ye kaydedildi, ret yok ({tarih(ik.get('tarih')).isoformat()}).")
    else:
        res.ekle("IYS-02", "ENGEL", "Alıcı adresi henüz İYS'ye tacir/esnaf olarak kaydedilip ret kontrolü yapılmadı "
                                    "(iys_kontrol.sonuc / tarih).")
    # --- kişiselleştirme
    gz = [x for x in (p.get("gozlemler") or []) if isinstance(x, dict) and s(x.get("metin"))]
    kaynakli = [x for x in gz if re.match(r"https?://", s(x.get("kaynak")))]
    kanca = s(p.get("kanca"))
    if not kaynakli:
        res.ekle("ALC-04", "DUR", "Profilde kaynağı (URL) yazılı en az bir gözlem yok. Firmanın herkese açık sitesini "
                                  "okumadan yazılan e-posta toplu gönderimdir.")
    elif not kanca:
        res.ekle("YAZ-02", "DUR", "kanca (firmaya özel ilk cümle) boş.")
    elif kelime_say(kanca) > 30:
        res.ekle("YAZ-02", "DUZELT", f"kanca {kelime_say(kanca)} kelime; 30'u geçmesin.")
    else:
        res.ekle("ALC-04", "GECTI", f"{len(kaynakli)} kaynaklı gözlem; ilk cümle firmaya özel.")
    # --- şablon
    if tpl is None:
        res.ekle("HZM-01", "DUR", f"hizmet.sablon geçersiz. Var olanlar: {', '.join(template_names())}.")
    elif tpl.get("placeholder"):
        if g.get("meslek_mevzuati_kontrol_edildi") is True:
            res.ekle("HZM-01", "UYARI", f"'{tpl['ad']}' bir yer tutucu şablon; metni kendi hizmetinize göre yeniden yazın.")
        else:
            res.ekle("HZM-01", "DUR", f"'{tpl['ad']}' yer tutucu şablon. Mali müşavirlik meslek mevzuatında reklam "
                                      "sınırları var; SMMM/YMM değilseniz ve kontrol ettiyseniz gonderen.yaml'da "
                                      "meslek_mevzuati_kontrol_edildi: true yapın.")
    if not s((p.get("hizmet") or {}).get("teklif")) and tpl is not None:
        res.ekle("YAZ-03", "UYARI", f"hizmet.teklif boş; şablon örneği kullanıldı ('{tpl['teklif_ornekleri'][0]}'). "
                                    "Firmaya özel somut bir teklif yazın.")


# ----------------------------------------------------------------------------- üretim
def kimlik_satiri(g: dict) -> str:
    ep = s(g.get("eposta"))
    if s(g.get("tur")) == "tacir":
        parts = [s(g.get("ticari_unvan")), f"MERSİS {s(g.get('mersis'))}", ep]
    else:
        parts = [s(g.get("ad_soyad")), f"VKN {s(g.get('vkn'))}", ep]
    if s(g.get("telefon")):
        parts.append(s(g.get("telefon")))
    return " · ".join(x for x in parts if x)


def eposta_metni(hitap: str, paragraflar: list, g: dict, alt: list) -> str:
    lines = [hitap, ""]
    for par in paragraflar:
        if par:
            lines += [par, ""]
    lines += [s(g.get("ad_soyad")), s(g.get("marka")), "", "—"]
    lines += alt
    return "\n".join(lines).rstrip() + "\n"


def uret(p: dict, g: dict, tpl: dict, r: dict, baslangic: dt.date) -> list:
    pol = r["politika"]
    fk = s(p.get("firma_kisa")) or s(p.get("firma"))
    hz = p.get("hizmet") or {}
    teklif = s(hz.get("teklif")) or tpl["teklif_ornekleri"][0]
    ad = s(g.get("ad")) or s(g.get("ad_soyad")).split(" ")[0]
    alanlar = {"ad": ad, "marka": s(g.get("marka")), "firma": fk, "teklif": teklif,
               "sektor": s(p.get("sektor")), "sehir": s(p.get("sehir")),
               "konu_kisa": s(hz.get("konu_kisa")) or tpl["konu_kisa_varsayilan"]}

    def f(tmpl: str) -> str:
        return tr_cap(bitir(tmpl.format(**alanlar))) if tmpl else ""

    hitap = s(p.get("hitap")) or f"Merhaba {fk} ekibi,"
    if not hitap.endswith(","):
        hitap += ","
    konu = tr_cap(sec(tpl["konu"], fk, "konu").format(**alanlar))
    if g.get("konu_ibaresi", True) is not False:
        konu = f"Tanıtım: {konu}"
    kimlik = kimlik_satiri(g)
    ret = s(g.get("ret_satiri")) or RET_SATIRI
    ayd_yeri = s(g.get("aydinlatma_metni_yeri"))
    alt_takip = [ret, kimlik] + ([f"Aydınlatma metni: {ayd_yeri}"] if ayd_yeri else [])

    # E-posta 1: kanca + tanıtım | fırsat + soru
    s1 = tr_cap(bitir(s(p.get("kanca"))))
    s2 = tr_cap(bitir(s(g.get("tanitim_cumlesi")))) if s(g.get("tanitim_cumlesi")) else f(sec(tpl["tanitim"], fk, "tanitim"))
    s3 = tr_cap(bitir(s(p.get("firsat")))) if s(p.get("firsat")) else ""
    s4 = f(sec(tpl["cta"], fk, "cta"))
    if not s4.endswith("?"):
        s4 = s4.rstrip(".") + "?"
    ayd = AYDINLATMA_SATIRI.format(yer=KAYNAK_YERI.get(s(p.get("kaynak_turu")), "sitenizde"))
    e1 = eposta_metni(hitap, [" ".join(x for x in (s1, s2) if x), " ".join(x for x in (s3, s4) if x)], g,
                      [ret, ayd, kimlik])
    # E-posta 2: hatırlatma + küçük ek değer + kısa kapanış
    ek = tr_cap(bitir(s(p.get("ek_deger")))) or tr_cap(bitir(tpl["ek_deger_varsayilan"]))
    e2 = eposta_metni(hitap, [" ".join([f(sec(TAKIP1_ACILIS, fk, "t1a")), ek, f(sec(TAKIP1_KAPANIS, fk, "t1k"))])],
                      g, alt_takip)
    # E-posta 3: son, kibar kapanış
    e3 = eposta_metni(hitap, [" ".join([f(sec(TAKIP2_ACILIS, fk, "t2a")), f(sec(TAKIP2_ORTA, fk, "t2o")),
                                        f(sec(TAKIP2_KAPANIS, fk, "t2k"))])], g, alt_takip)
    d0 = is_gunu(baslangic)
    g1, g2 = (int(x) for x in pol["takip_gunleri"])
    d1 = is_gunu(d0 + dt.timedelta(days=g1))
    d2 = is_gunu(d0 + dt.timedelta(days=g2))
    if d2 <= d1:
        d2 = is_gunu(d1 + dt.timedelta(days=2))
    return [
        {"no": 1, "tur": "ilk temas", "gun": 0, "tarih": d0.isoformat(), "konu": konu, "metin": e1},
        {"no": 2, "tur": f"1. takip (gün {g1})", "gun": g1, "tarih": d1.isoformat(), "konu": f"Re: {konu}", "metin": e2},
        {"no": 3, "tur": f"2. takip, son (gün {g2})", "gun": g2, "tarih": d2.isoformat(), "konu": f"Re: {konu}", "metin": e3},
    ]


# ----------------------------------------------------------------------------- e-posta denetimi
def govde(metin: str, ad_soyad: str) -> str:
    lines = metin.strip("\n").split("\n")
    body = []
    for ln in lines[1:]:
        if ln.strip() == ad_soyad.strip() or ln.strip() == "—":
            break
        body.append(ln)
    return " ".join(x.strip() for x in body if x.strip())


def eposta_denetle(e: dict, g: dict, tpl: dict | None, r: dict, res: Sonuc, firma_kisa: str = ""):
    pol, soz = r["politika"], r["sozluk"]
    no, metin, konu = e["no"], e["metin"], e["konu"]
    ilk = no == 1
    body = govde(metin, s(g.get("ad_soyad")))
    cs = cumleler(body)
    lo, hi = (int(x) for x in (pol["ilk_eposta_cumle"] if ilk else pol["takip_cumle"]))
    res.ekle("YAZ-01", "GECTI" if lo <= len(cs) <= hi else "DUZELT",
             f"Gövde {len(cs)} cümle (hedef {lo}-{hi}).", no)
    ust = int(pol["ilk_eposta_kelime_ust"] if ilk else pol["takip_kelime_ust"])
    if kelime_say(body) > ust:
        res.ekle("YAZ-01", "UYARI", f"Gövde {kelime_say(body)} kelime (en fazla {ust}).", no)
    # konu
    kl = tr_lower(konu)
    if ilk and re.match(r"^\s*(re|ynt|fw|fwd|ilt)\s*:", kl):
        res.ekle("YAZ-05", "DUZELT", "İlk e-postanın konusu 'Re:/Ynt:/Fwd:' ile başlıyor: sahte yazışma izlenimi.", no)
    if len(konu) > int(pol["konu_karakter_ust"]) + (4 if not ilk else 0):
        res.ekle("YAZ-04", "UYARI", f"Konu {len(konu)} karakter (en fazla {pol['konu_karakter_ust']}).", no)
    if "!" in konu or re.search(r"\b[A-ZÇĞİÖŞÜ]{5,}\b", konu):
        res.ekle("YAZ-04", "UYARI", "Konuda ünlem ya da BÜYÜK HARF kelime var.", no)
    if re.search(r"\b(tanıtım|kampanya|bilgilendirme|reklam)\b", kl):
        res.ekle("ICR-03", "GECTI", "Konu satırında nitelik ibaresi var.", no)
    else:
        res.ekle("ICR-03", "UYARI", "Konu satırında 'Tanıtım' gibi bir ibare yok; gövdenin açıkça bir hizmet teklifi "
                                    "olduğundan emin olun.", no)
    # kimlik / iletişim / ret
    if s(g.get("tur")) == "tacir":
        ok = s(g.get("ticari_unvan")) in metin and re.search(r"MERSİS\s*\d{16}", metin)
    else:
        ok = s(g.get("ad_soyad")) in metin and re.search(r"VKN\s*\d{10}", metin)
    res.ekle("ICR-01", "GECTI" if ok else "ENGEL",
             "Kimlik bilgisi imzada." if ok else "İmzada MERSİS + ticaret unvanı ya da ad soyad + VKN yok.", no)
    gep = s(g.get("eposta"))
    res.ekle("ICR-02", "GECTI" if gep and gep in metin else "ENGEL",
             "Gönderen e-posta adresi metinde." if gep and gep in metin else "Gönderen e-posta adresi metinde yok.", no)
    if re.search(r"\bRET\b", metin) and re.search(r"yaz|yanıt", tr_lower(metin)):
        res.ekle("ICR-04", "GECTI", "Ret satırı var (yanıtla, aynı kanal, ücretsiz).", no)
    else:
        res.ekle("ICR-04", "ENGEL", "Ret satırı yok: her e-postada 'RET yazmanız yeterli' gibi bir satır olmalı.", no)
    if ilk:
        if re.search(r"aldı[mk]", tr_lower(metin)) and re.search(r"\bSİL\b|sil", metin):
            res.ekle("KVK-03", "GECTI", "Kısa aydınlatma satırı var (kaynak, amaç, silme talebi).", no)
        else:
            res.ekle("KVK-03", "UYARI", "İlk e-postada adresin nereden alındığını ve silme talebini anlatan satır yok.", no)
    # link / ek / promosyon
    temiz = EPOSTA_RE.sub("", metin if ilk else body)
    links = LINK_RE.findall(temiz)
    if links:
        res.ekle("TES-05", "DUZELT" if ilk else "UYARI",
                 f"{'Metinde' if ilk else 'Gövdede'} link var: {', '.join(sorted(set(links)))[:80]}.", no)
    else:
        res.ekle("TES-05", "GECTI", "Link yok.", no)
    if bul(body, soz["ek_ifadeler"]):
        res.ekle("TES-05", "DUZELT" if ilk else "UYARI", "Ek dosyadan söz ediliyor; ilk temasta ek göndermeyin.", no)
    promo = bul(body, soz["promosyon_ifadeler"])
    if promo:
        res.ekle("ICR-05", "DUZELT" if ilk else "UYARI", f"Promosyon ifadesi: {', '.join(promo)}. Şartlar için URL "
                                                         "gerekir; ilk e-postada promosyon koymayın.", no)
    # spam / abartı
    spam = bul(body + " " + konu, list(soz["spam_ifadeler"]) + list((tpl or {}).get("yasak_iddialar") or []))
    if spam:
        res.ekle("YAZ-04", "DUZELT", f"Abartılı/garanti ifadesi: {', '.join(spam)}.", no)
    if body.count("!") > 1 or len(re.findall(r"\b[A-ZÇĞİÖŞÜ]{5,}\b", body)) >= 2:
        res.ekle("YAZ-04", "UYARI", "Çok ünlem ya da BÜYÜK HARF kelime.", no)
    if ilk:
        if cs and cs[-1].rstrip().endswith("?"):
            res.ekle("YAZ-03", "GECTI", "Son cümle izin isteyen bir soru.", no)
        else:
            res.ekle("YAZ-03", "DUZELT", "İlk e-posta bir soruyla bitmeli (ör. '... göndereyim mi?').", no)
        mt = bul(body, soz["toplanti_ifadeler"])
        if mt:
            res.ekle("YAZ-03", "UYARI", f"İlk e-postada toplantı isteği ({', '.join(mt)}); önce somut değer teklif edin.", no)
        if firma_kisa and tr_lower(firma_kisa) not in tr_lower(body) and not cs:
            res.ekle("YAZ-02", "UYARI", "Gövdede firmaya özel bir ifade bulunamadı.", no)


def manuel_maddeler(res: Sonuc, tpl: dict | None):
    res.ekle("IYS-03", "MANUEL", "RET gelirse 3 iş günü içinde durdurun; takipleri iptal edin, engel listesine ekleyin.")
    res.ekle("IYS-04", "MANUEL", "Gelen RET'i 3 iş günü içinde İYS'ye bildirin.")
    res.ekle("IYS-05", "MANUEL", "kayit.json'a gönderim tarihlerini ve yanıtı işleyin; 3 yıl saklayın.")
    res.ekle("YAZ-05", "MANUEL", "Takipleri aynı yazışmayı yanıtlayarak gönderin; herhangi bir yanıt gelirse sırayı durdurun; "
                                 "3. e-postadan sonra yazmayın.")
    res.ekle("KVK-04", "MANUEL", "Adresi yurt dışı sunuculu CRM/ısınma/otomasyon aracına yüklüyorsanız KVKK m.9'u sorun.")
    res.ekle("KVK-05", "MANUEL", "Yanıt yoksa sıra bitince profili arşivleyin, gereksiz veriyi silin.")
    res.ekle("TES-06", "MANUEL", "Gmail Postmaster Tools'ta spam oranını %0,1 altında tutun.")
    if tpl is not None:
        for n in tpl.get("notlar") or []:
            res.ekle("HZM-01", "MANUEL", str(n))
    res.ekle("CEZ-01", "BILGI", "")


# ----------------------------------------------------------------------------- çıktı
def sonuc_cumlesi(durum: str) -> str:
    if durum == "DUR":
        return ("DURDU: taslak yazılmadı. Aşağıdaki DUR maddeleri bu alıcıya (ya da bu şekilde) soğuk ticari e-posta "
                "gönderilmemesi gerektiğini gösteriyor. Bunun yerine: eksik bilgiyi tamamlayın (tür, kaynak, gözlem) ya da "
                "alıcı uygun değilse yalnız onun sizinle iletişime geçtiği, tanışıklık ya da etkinlik gibi onaylı "
                "kanalları kullanın.")
    if durum in ("ENGEL", "DUZELT"):
        return "Taslaklar hazır ama GÖNDERMEYİN: önce ENGEL ve DÜZELT maddelerini çözün, sonra `kontrol` ile yeniden denetleyin."
    return "Göndermeye hazır görünüyor: ELLE maddelerini işaretleyin ve e-postaları kendi kutunuzdan tek tek gönderin."


def kontrol_listesi_md(res: Sonuc, r: dict, baslik: str, epostalar: list | None) -> str:
    K = r["_kural"]
    en = res.en_kotu()
    c = res.say()
    out = [f"# Kontrol listesi: {baslik}", "", f"> **{UYARI}** Bilgilendirme amaçlı bir kontrol listesidir; "
           "kesin değerlendirme için bir hukukçuya danışın.", "",
           f"**Sonuç:** {sonuc_cumlesi(en)}", "",
           "**Sayılar:** " + " · ".join(f"{ETIKET[k]} {c[k]}" for k in sorted(c, key=lambda x: -SIRA[x]) if k != "BILGI"), ""]

    def satir(i, kutu):
        k = K[i["id"]]
        ep = f" (e-posta {i['eposta']})" if i["eposta"] else ""
        bul_ = f" {i['bulgu']}" if i["bulgu"] else ""
        duz = f" → {k['duzeltme']}" if i["durum"] not in ("GECTI", "MANUEL", "BILGI") and s(k["duzeltme"]) != "-" else ""
        bel = f" _Belirsizlik: {k['belirsizlik']}_" if s(k.get("belirsizlik")) and i["durum"] in ("UZMANA_SOR", "UYARI") else ""
        dy = kaynak_metni(r, i["id"])
        return (f"- [{kutu}] **{ETIKET[i['durum']]} · {i['id']} {k['baslik']}**{ep}:{bul_}{duz}{bel}"
                + (f" _Dayanak: {dy}_" if dy else ""))

    gruplar = [("Önce çözün (DUR / ENGEL / DÜZELT)", ("DUR", "ENGEL", "DUZELT"), " "),
               ("Uyarılar ve uzmana sorulacaklar", ("UZMANA_SOR", "UYARI"), " "),
               ("Göndermeden önce ve sonra elle yapılacaklar", ("MANUEL",), " "),
               ("Geçenler (otomatik kontrol)", ("GECTI",), "x")]
    for ad, durumlar, kutu in gruplar:
        items = [i for i in res.items if i["durum"] in durumlar]
        if not items:
            continue
        items.sort(key=lambda i: (-SIRA[i["durum"]], i["id"], i["eposta"] or 0))
        out += [f"## {ad}", ""] + [satir(i, kutu) for i in items] + [""]
    if epostalar:
        out += ["## E-posta başına kontroller", "", "| Kontrol | " + " | ".join(f"E-posta {e['no']}" for e in epostalar) + " |",
                "|---|" + "---|" * len(epostalar)]
        ids = sorted({i["id"] for i in res.items if i["eposta"]})
        for kid in ids:
            row = []
            for e in epostalar:
                ds = [i["durum"] for i in res.items if i["id"] == kid and i["eposta"] == e["no"]]
                row.append(ETIKET[max(ds, key=lambda d: SIRA[d])] if ds else "–")
            out.append(f"| {kid} {K[kid]['baslik']} | " + " | ".join(row) + " |")
        out.append("")
    ceza = K["CEZ-01"]
    out += ["## Yaptırımlar (bilgi)", "", ceza["aciklama"], "", "## Kaynaklar", ""]
    for k in r["kaynaklar"]:
        out.append(f"- **{k['id']}** {k['belge']}. {k['url']} (okunma {k['okunma']})")
    out += ["", f"Kural dosyası sürümü {r['surum']}, tarih {r['kural_tarihi']}. {UYARI}", ""]
    return "\n".join(out)


def epostalar_md(p: dict, g: dict, tpl: dict, epostalar: list) -> str:
    fk = s(p.get("firma_kisa")) or s(p.get("firma"))
    out = [f"# E-posta taslakları: {fk}", "",
           f"> **{UYARI}** Bu taslaklar gönderilmedi. Göndermeden önce `kontrol_listesi.md` içindeki ENGEL ve DÜZELT "
           "maddelerini çözün; e-postaları kendi gönderim kutunuzdan tek tek, elle gönderin.", "",
           f"- **Firma:** {s(p.get('firma'))} ({s(p.get('alici_turu'))})",
           f"- **Kime:** {s(p.get('eposta'))} (kaynak: {s(p.get('eposta_kaynagi'))})",
           f"- **Gönderen:** {s(g.get('ad_soyad'))} <{s(g.get('eposta'))}>",
           f"- **Şablon:** {tpl['ad']}",
           "- **Sıra:** 3 e-posta. Takipleri aynı yazışmayı yanıtlayarak gönderin. Herhangi bir yanıt gelirse "
           "(olumlu ya da RET) sırayı durdurun.", ""]
    for e in epostalar:
        d = dt.date.fromisoformat(e["tarih"])
        out += [f"## E-posta {e['no']} · {e['tur']} · {e['tarih']} {GUNLER[d.weekday()]}", "",
                f"**Konu:** {e['konu']}", "", "```text", e["metin"].rstrip("\n"), "```", ""]
    out += ["İpucu: Salı-Perşembe 09.30-11.00 arası gönderin. Resmî tatile denk gelen günü bir iş günü kaydırın.", "",
            UYARI, ""]
    return "\n".join(out)


def epostalar_md_oku_text(t: str) -> list:
    return epostalar_md_ayristir(t)["epostalar"]


def epostalar_md_oku(path: Path) -> dict:
    return epostalar_md_ayristir(path.read_text(encoding="utf-8"))


def epostalar_md_ayristir(t: str) -> dict:
    m = re.search(r"\*\*Şablon:\*\*\s*(\S+)", t)
    fk = re.search(r"^# E-posta taslakları:\s*(.+)$", t, re.M)
    out = {"sablon": m.group(1) if m else None, "firma_kisa": fk.group(1).strip() if fk else "", "epostalar": []}
    for blk in re.split(r"^## E-posta ", t, flags=re.M)[1:]:
        no = int(re.match(r"(\d+)", blk).group(1))
        konu = re.search(r"\*\*Konu:\*\*\s*(.*)", blk)
        metin = re.search(r"```text\n(.*?)\n```", blk, re.S)
        if konu and metin:
            out["epostalar"].append({"no": no, "konu": konu.group(1).strip(), "metin": metin.group(1) + "\n"})
    return out


# ----------------------------------------------------------------------------- komutlar
def yaz(profil_yollari: list, gonderen_yolu: Path, cikti: Path, bugun: dt.date, baslangic: dt.date | None,
        r: dict | None = None, sessiz: bool = False) -> int:
    r = r or load_rules()
    pol = r["politika"]
    g = load_yaml(gonderen_yolu) or {}
    profiller = [(Path(pp), load_yaml(Path(pp)) or {}) for pp in profil_yollari]
    baslangic = baslangic or is_gunu(bugun + dt.timedelta(days=1))
    cikti.mkdir(parents=True, exist_ok=True)
    toplu = None
    if len(profiller) > int(pol["tek_seferde_profil"]):
        toplu = (f"{len(profiller)} profil verildi. Bu skill bir seferde en fazla {pol['tek_seferde_profil']} firmaya, "
                 f"günde en fazla {pol['gunluk_onerilen']} elle gözden geçirilmiş e-posta yazar. Toplu gönderim için "
                 "kullanılamaz.")
    kancalar = {}
    for pth, p in profiller:
        if isinstance(p, dict) and s(p.get("kanca")):
            kancalar.setdefault(tr_lower(s(p.get("kanca"))), []).append(pth.name)
    kod = 0
    for pth, p in profiller:
        res = Sonuc()
        if toplu:
            res.ekle("ALC-04", "DUR", toplu)
        if isinstance(p, dict) and len(kancalar.get(tr_lower(s(p.get("kanca"))), [])) > 1:
            res.ekle("ALC-04", "DUR", "Aynı kanca cümlesi birden fazla profilde: "
                                      + ", ".join(kancalar[tr_lower(s(p.get('kanca')))]) + ". Her firmaya ayrı gözlem yazın.")
        tpl = None
        if isinstance(p, dict):
            try:
                tpl = load_template(s((p.get("hizmet") or {}).get("sablon")))
            except (FileNotFoundError, ValueError):
                tpl = None
        gonderen_denetle(g, r, bugun, res)
        profil_denetle(p, g, tpl, r, res)
        fk = (s(p.get("firma_kisa")) or s(p.get("firma"))) if isinstance(p, dict) else pth.stem
        hedef = cikti / slug(fk or pth.stem) if len(profiller) > 1 else cikti
        hedef.mkdir(parents=True, exist_ok=True)
        epostalar = None
        if res.en_kotu() != "DUR":
            epostalar = uret(p, g, tpl, r, baslangic)
            for e in epostalar:
                eposta_denetle(e, g, tpl, r, res, fk)
        if res.en_kotu() != "DUR":
            manuel_maddeler(res, tpl)
        else:
            res.ekle("CEZ-01", "BILGI", "")
        en = res.en_kotu()
        for old in ("epostalar.md", "kayit.json", "red_raporu.md", "kontrol_listesi.md"):
            (hedef / old).unlink(missing_ok=True)
        liste = kontrol_listesi_md(res, r, fk or pth.stem, epostalar)
        if en == "DUR":
            (hedef / "red_raporu.md").write_text(liste, encoding="utf-8")
            pk = 3
        else:
            (hedef / "epostalar.md").write_text(epostalar_md(p, g, tpl, epostalar), encoding="utf-8")
            (hedef / "kontrol_listesi.md").write_text(liste, encoding="utf-8")
            kayit = {"uyari": UYARI, "firma": s(p.get("firma")), "alici_turu": s(p.get("alici_turu")),
                     "eposta": s(p.get("eposta")), "eposta_kaynagi": s(p.get("eposta_kaynagi")),
                     "kaynak_turu": s(p.get("kaynak_turu")), "kaynak_tarihi": s(p.get("kaynak_tarihi")),
                     "tur_kaniti": s(p.get("tur_kaniti")),
                     "gozlem_kaynaklari": [s(x.get("kaynak")) for x in (p.get("gozlemler") or []) if isinstance(x, dict)],
                     "iys_kontrol": {k: s(v) for k, v in (p.get("iys_kontrol") or {}).items()},
                     "sablon": tpl["ad"], "olusturma": bugun.isoformat(),
                     "plan": [{"no": e["no"], "tarih": e["tarih"], "konu": e["konu"]} for e in epostalar],
                     "gonderim": [], "yanit": None, "ret": None,
                     "not": "Gönderdikçe tarihleri 'gonderim'e, yanıtı/ret'i ilgili alana yazın; 3 yıl saklayın (Yönetmelik m.13/2)."}
            (hedef / "kayit.json").write_text(json.dumps(kayit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            pk = 2 if en in ("ENGEL", "DUZELT") else 0
        kod = max(kod, pk)
        if not sessiz:
            c = res.say()
            print(f"[{ETIKET[en] if en not in ('GECTI', 'MANUEL', 'UYARI', 'UZMANA_SOR') else 'HAZIR'}] {fk} -> {hedef}/")
            print("   " + sonuc_cumlesi(en))
            print("   " + " · ".join(f"{ETIKET[k]} {c[k]}" for k in sorted(c, key=lambda x: -SIRA[x]) if k != "BILGI"))
            for i in res.items:
                if i["durum"] in ("DUR", "ENGEL", "DUZELT"):
                    ep = f" (e-posta {i['eposta']})" if i["eposta"] else ""
                    print(f"   - {ETIKET[i['durum']]} {i['id']}{ep}: {i['bulgu']}")
    if not sessiz:
        print(UYARI)
    return kod


def kontrol(md_yolu: Path, gonderen_yolu: Path, r: dict | None = None, sessiz: bool = False) -> int:
    r = r or load_rules()
    g = load_yaml(gonderen_yolu) or {}
    d = epostalar_md_oku(md_yolu)
    if not d["epostalar"]:
        print(f"HATA: {md_yolu} içinde e-posta bloğu bulunamadı.", file=sys.stderr)
        return 1
    try:
        tpl = load_template(d["sablon"]) if d["sablon"] else None
    except (FileNotFoundError, ValueError):
        tpl = None
    res = Sonuc()
    for e in d["epostalar"]:
        eposta_denetle(e, g, tpl, r, res, d["firma_kisa"])
    en = res.en_kotu()
    if not sessiz:
        print(f"Kontrol: {md_yolu} ({len(d['epostalar'])} e-posta)")
        for i in sorted(res.items, key=lambda i: (i["eposta"], -SIRA[i["durum"]])):
            if i["durum"] != "GECTI":
                print(f"  E{i['eposta']} {ETIKET[i['durum']]} {i['id']} {r['_kural'][i['id']]['baslik']}: {i['bulgu']}")
        print("  " + ("Sorun yok (otomatik kontroller)." if SIRA[en] <= SIRA["UYARI"] else "ENGEL/DÜZELT var: göndermeyin."))
        print(UYARI)
    return 2 if en in ("ENGEL", "DUZELT", "DUR") else 0


PROFIL_ISKELET = """# Firma profili: TEK firma. Yalnız firmanın HERKESE AÇIK sitesinden / işletme profilinden okunanlar.
# {uyari}
firma: "TODO Ticaret unvanı (ör. Örnek Kahve Ltd. Şti.)"
firma_kisa: "TODO kısa ad (konu ve selamda)"
alici_turu: bilinmiyor        # tacir | esnaf | serbest_meslek | tuketici | kamu | dernek_vakif | bilinmiyor
tuzel_tur: bilinmiyor         # limited | anonim | sahis | kooperatif | diger | bilinmiyor
tur_kaniti: ""                # ör. "Site alt bilgisinde Ltd. Şti. unvanı ve MERSİS no"
sektor: ""
sehir: ""
web: "https://"
eposta: ""                    # firmanın yayımladığı İŞ adresi (info@, iletisim@ tercih)
eposta_kaynagi: "https://"    # adresi gördüğünüz sayfa
kaynak_turu: firma_sitesi     # firma_sitesi | isletme_profili | firma_sosyal_medya
kaynak_tarihi: "{bugun}"
hitap: ""                     # boşsa "Merhaba <firma_kisa> ekibi,"; kişi adı yalnız sitede iletişim kişisi olarak yazıyorsa
gozlemler:                    # sitede gördüğünüz somut şeyler, her biri kaynak URL'li
  - metin: "TODO"
    kaynak: "https://"
kanca: ""                     # 1. cümle: firmaya özel gözlem (≤ 30 kelime)
firsat: ""                    # 3. cümle (isteğe bağlı): gözleme dayalı somut fırsat
ek_deger: ""                  # 2. e-posta için küçük ek fikir (isteğe bağlı)
hizmet:
  sablon: {sablon}
  teklif: "{teklif}"          # ücretsiz, somut; "... hazırlayıp göndereyim mi?" cümlesine oturmalı
  konu_kisa: ""
iys_kontrol:
  sonuc: yapilmadi            # ret_yok | ret_var | yapilmadi
  tarih: ""
"""

GONDEREN_ISKELET = """# Gönderen bilgileri (bir kez doldurulur). {uyari}
ad: "TODO"                    # e-postada "Ben ..." diye geçen ad
ad_soyad: "TODO"
marka: "TODO"
tur: tacir                    # tacir | esnaf | serbest_meslek
ticari_unvan: ""              # tacir: ör. "Örnek Ajans Ltd. Şti."
mersis: ""                    # tacir: 16 hane
vkn: ""                       # esnaf / serbest meslek: 10 hane (TCKN yazmayın)
eposta: ""                    # gönderim alan adındaki adresiniz
telefon: null                 # isteğe bağlı (iş telefonunuz)
tanitim_cumlesi: null         # isteğe bağlı: şablonun "Ben ..." cümlesi yerine
aydinlatma_metni_yeri: ""     # ör. markaniz.com/kvkk (takip e-postalarında yazılır)
iys_kayitli: false            # İYS'ye hizmet sağlayıcı olarak kaydoldunuz mu
konu_ibaresi: true            # konuya "Tanıtım:" ekle (önerilen)
meslek_mevzuati_kontrol_edildi: false   # yalnız muhasebe-danismanligi şablonu için
teslimat:
  gonderim_domaini: ""        # ör. markaniz-mail.com
  ana_domain: ""              # ör. markaniz.com
  spf: false
  dkim: false
  dmarc: false
  isinma_baslangic: ""        # YYYY-AA-GG
  gunluk_limit: 20
"""


def doctor() -> int:
    ok = True

    def line(durum, msg):
        nonlocal ok
        ok = ok and durum
        print(f"{'ok ' if durum else 'HATA'} {msg}")

    line(sys.version_info >= (3, 8), f"Python {sys.version.split()[0]} (3.8+)")
    try:
        import yaml  # type: ignore  # noqa: F401
        print("ok  PyYAML var")
    except ImportError:
        print("ok  PyYAML yok: dahili mini_yaml kullanılıyor")
    try:
        r = load_rules()
        err = validate_rules(r)
        line(not err, f"kural dosyası {r['surum']} ({len(r['kurallar'])} kural, {len(r['kaynaklar'])} kaynak)"
             + ("" if not err else ": " + "; ".join(err)))
    except Exception as exc:  # noqa: BLE001
        line(False, f"kural dosyası okunamadı: {exc}")
        return 1
    for n in template_names():
        try:
            t = load_template(n)
            print(f"ok  şablon {n}{' (yer tutucu)' if t.get('placeholder') else ''}")
        except Exception as exc:  # noqa: BLE001
            line(False, f"şablon {n}: {exc}")
    line(len(template_names()) >= 5, f"{len(template_names())} şablon")
    src = Path(__file__).read_text(encoding="utf-8")
    yasak = re.findall(r"^\s*(?:import|from)\s+(smtplib|imaplib|poplib|urllib|requests|http|socket|webbrowser)\b", src, re.M)
    line(not yasak, "script ağa çıkmıyor, e-posta göndermiyor" + (f": {yasak}" if yasak else ""))
    ex = SKILL_DIR / "examples" / "01-kafe-sosyal-medya"
    if (ex / "profil.yaml").is_file() and (SKILL_DIR / "examples" / "gonderen.yaml").is_file():
        with tempfile.TemporaryDirectory() as td:
            kod = yaz([ex / "profil.yaml"], SKILL_DIR / "examples" / "gonderen.yaml", Path(td),
                      dt.date(2026, 10, 27), dt.date(2026, 10, 28), r, sessiz=True)
            md = (Path(td) / "epostalar.md").read_text(encoding="utf-8") if (Path(td) / "epostalar.md").exists() else ""
            line(kod == 0 and md.count("```text") == 3 and UYARI in md, f"örnek üretim (çıkış {kod}, 3 e-posta, uyarı satırı)")
    else:
        print("--  örnekler yok, üretim testi atlandı")
    print("doctor OK" if ok else "doctor: sorun var")
    print(UYARI)
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="eposta.py", description=f"B2B E-posta (İYS Uyumlu). {UYARI}")
    sub = ap.add_subparsers(dest="komut", required=True)
    sub.add_parser("doctor")
    sub.add_parser("sablonlar")
    y = sub.add_parser("yeni")
    y.add_argument("tur", choices=["profil", "gonderen"])
    y.add_argument("--sablon", default="sosyal-medya")
    w = sub.add_parser("yaz")
    w.add_argument("profiller", nargs="+")
    w.add_argument("--gonderen", required=True)
    w.add_argument("--cikti", default="eposta_cikti")
    w.add_argument("--bugun", help="YYYY-AA-GG (varsayılan: bugün)")
    w.add_argument("--baslangic", help="ilk e-posta günü YYYY-AA-GG (varsayılan: sonraki iş günü)")
    k = sub.add_parser("kontrol")
    k.add_argument("epostalar_md")
    k.add_argument("--gonderen", required=True)
    a = ap.parse_args(argv)
    if a.komut == "doctor":
        return doctor()
    if a.komut == "sablonlar":
        for n in template_names():
            t = load_template(n)
            print(f"{n:24s} {t['baslik']}{'  [yer tutucu]' if t.get('placeholder') else ''}  ·  {t['aciklama']}")
        print(UYARI)
        return 0
    if a.komut == "yeni":
        if a.tur == "gonderen":
            sys.stdout.write(GONDEREN_ISKELET.format(uyari=UYARI))
        else:
            t = load_template(a.sablon)
            sys.stdout.write(PROFIL_ISKELET.format(uyari=UYARI, bugun=dt.date.today().isoformat(), sablon=t["ad"],
                                                   teklif=t["teklif_ornekleri"][0]))
        return 0
    if a.komut == "yaz":
        bugun = tarih(a.bugun) or dt.date.today()
        for pp in a.profiller + [a.gonderen]:
            if not Path(pp).is_file():
                print(f"HATA: dosya yok: {pp}", file=sys.stderr)
                return 1
        return yaz(a.profiller, Path(a.gonderen), Path(a.cikti), bugun, tarih(a.baslangic))
    if a.komut == "kontrol":
        return kontrol(Path(a.epostalar_md), Path(a.gonderen))
    return 1


if __name__ == "__main__":
    sys.exit(main())
