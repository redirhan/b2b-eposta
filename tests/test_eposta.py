"""B2B E-posta — birim testleri (python3 -m unittest discover -s tests). Bu bir hukuki görüş değildir."""
import copy
import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import eposta  # noqa: E402

R = eposta.load_rules()
EX = ROOT / "examples"
G = EX / "gonderen.yaml"
BUGUN, BAS = dt.date(2026, 10, 27), dt.date(2026, 10, 28)


def dump(d, path):
    """Basit YAML yazıcı (yalnız testler için: dict / list / str / bool / None / int)."""
    def sc(v):
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, int):
            return str(v)
        return '"' + str(v).replace('"', '\\"') + '"'

    def w(o, ind):
        out = []
        for k, v in o.items():
            if isinstance(v, dict):
                out.append(" " * ind + f"{k}:")
                out += w(v, ind + 2)
            elif isinstance(v, list):
                out.append(" " * ind + f"{k}:")
                for it in v:
                    if isinstance(it, dict):
                        first = True
                        for kk, vv in it.items():
                            out.append(" " * (ind + 2) + ("- " if first else "  ") + f"{kk}: {sc(vv)}")
                            first = False
                    else:
                        out.append(" " * (ind + 2) + f"- {sc(it)}")
            else:
                out.append(" " * ind + f"{k}: {sc(v)}")
        return out
    Path(path).write_text("\n".join(w(d, 0)) + "\n", encoding="utf-8")


BASE = eposta.load_yaml(EX / "01-kafe-sosyal-medya" / "profil.yaml")


def run(profil: dict, gonderen=None, n=1):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        paths = []
        for i in range(n):
            p = copy.deepcopy(profil)
            if n > 1:
                p["kanca"] = f"{p['kanca']} ({i})"
                p["firma_kisa"] = f"{p['firma_kisa']} {i}"
            dump(p, td / f"p{i}.yaml")
            paths.append(td / f"p{i}.yaml")
        gp = G
        if gonderen is not None:
            dump(gonderen, td / "g.yaml")
            gp = td / "g.yaml"
        kod = eposta.yaz(paths, gp, td / "out", BUGUN, BAS, R, sessiz=True)
        files = {p.relative_to(td / "out").as_posix(): p.read_text(encoding="utf-8")
                 for p in (td / "out").rglob("*") if p.is_file()}
        return kod, files


class Tests(unittest.TestCase):
    def test_rules_valid(self):
        self.assertEqual(eposta.validate_rules(R), [])

    def test_templates(self):
        self.assertEqual(len(eposta.template_names()), 5)
        for n in eposta.template_names():
            eposta.load_template(n)

    def test_ok_example(self):
        kod, f = run(BASE)
        self.assertEqual(kod, 0)
        md = f["epostalar.md"]
        self.assertEqual(md.count("```text"), 3)
        self.assertIn(eposta.UYARI, md)
        self.assertIn(eposta.UYARI, f["kontrol_listesi.md"])
        self.assertEqual(md.count("“RET”"), 3)
        self.assertEqual(md.count("MERSİS 0123000000000001"), 3)
        e1 = eposta.epostalar_md_oku_text(md)[0]["metin"]
        body = eposta.govde(e1, "Deniz Kaya")
        self.assertTrue(3 <= len(eposta.cumleler(body)) <= 4)
        self.assertFalse(eposta.LINK_RE.findall(eposta.EPOSTA_RE.sub("", e1)))
        self.assertTrue(body.endswith("?"))

    def test_lawyer_refused(self):
        kod, f = run(eposta.load_yaml(EX / "04-hukuk-burosu-web" / "profil.yaml"))
        self.assertEqual(kod, 3)
        self.assertNotIn("epostalar.md", f)
        self.assertIn("ALC-02", f["red_raporu.md"])

    def test_consumer_refused(self):
        p = dict(BASE, alici_turu="tuketici")
        kod, f = run(p)
        self.assertEqual(kod, 3)
        self.assertIn("ALC-03", f["red_raporu.md"])

    def test_unknown_type_refused(self):
        kod, _ = run(dict(BASE, alici_turu="bilinmiyor"))
        self.assertEqual(kod, 3)

    def test_phone_refused(self):
        p = dict(BASE, firsat="Bize 0532 123 45 67 numarasından da ulaşabilirsiniz.")
        kod, f = run(p)
        self.assertEqual(kod, 3)
        self.assertIn("KVK-02", f["red_raporu.md"])

    def test_bulk_refused(self):
        kod, f = run(BASE, n=21)
        self.assertEqual(kod, 3)
        self.assertTrue(all(k.endswith("red_raporu.md") for k in f))

    def test_duplicate_hook_refused(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            for i in range(2):
                dump(dict(BASE, firma_kisa=f"Firma {i}"), td / f"p{i}.yaml")
            kod = eposta.yaz([td / "p0.yaml", td / "p1.yaml"], G, td / "out", BUGUN, BAS, R, sessiz=True)
        self.assertEqual(kod, 3)

    def test_no_observation_refused(self):
        p = dict(BASE, gozlemler=[{"metin": "güzel site", "kaynak": "hatırlamıyorum"}])
        self.assertEqual(run(p)[0], 3)

    def test_bought_list_refused(self):
        p = dict(BASE, eposta_kaynagi="Apollo'dan satın alınan liste")
        self.assertEqual(run(p)[0], 3)

    def test_iys_ret_var(self):
        p = dict(BASE, iys_kontrol={"sonuc": "ret_var", "tarih": "2026-10-27"})
        self.assertEqual(run(p)[0], 3)

    def test_iys_missing_blocks(self):
        p = dict(BASE, iys_kontrol={"sonuc": "yapilmadi", "tarih": ""})
        kod, f = run(p)
        self.assertEqual(kod, 2)
        self.assertIn("epostalar.md", f)

    def test_sender_not_registered_blocks(self):
        g = eposta.load_yaml(G)
        g["iys_kayitli"] = False
        kod, f = run(BASE, gonderen=g)
        self.assertEqual(kod, 2)
        self.assertIn("IYS-01", f["kontrol_listesi.md"])

    def test_sender_high_volume_refused(self):
        g = eposta.load_yaml(G)
        g["teslimat"]["gunluk_limit"] = 500
        self.assertEqual(run(BASE, gonderen=g)[0], 3)

    def test_placeholder_template(self):
        p = dict(BASE, hizmet={"sablon": "muhasebe-danismanligi", "teklif": "5 maddelik kontrol listesi"})
        self.assertEqual(run(p)[0], 3)
        g = eposta.load_yaml(G)
        g["meslek_mevzuati_kontrol_edildi"] = True
        self.assertEqual(run(p, gonderen=g)[0], 0)

    def test_kontrol_detects_edits(self):
        kod, f = run(BASE)
        md = f["epostalar.md"]
        bad = md.replace("ister misiniz?", "ister misiniz? Örnekler: https://kiyidijital.example/isler", 1)
        bad = bad.replace("Bu tür e-postaları almak istemezseniz bu e-postaya “RET” yazmanız yeterli; "
                          "3 iş günü içinde listeden çıkarır, bir daha yazmam.\n", "", 1)
        with tempfile.TemporaryDirectory() as td:
            pth = Path(td) / "epostalar.md"
            pth.write_text(bad, encoding="utf-8")
            self.assertEqual(eposta.kontrol(pth, G, R, sessiz=True), 2)
            pth.write_text(md, encoding="utf-8")
            self.assertEqual(eposta.kontrol(pth, G, R, sessiz=True), 0)

    def test_tr_helpers(self):
        self.assertEqual(eposta.tr_cap("istanbul"), "İstanbul")
        self.assertEqual(eposta.tr_cap("3 reel"), "3 reel")
        self.assertEqual(len(eposta.cumleler("Örnek Ltd. Şti. iyi. 3.5 kat arttı. Olur mu?")), 3)
        self.assertEqual(eposta.bul("çekirdekten fincana", ["ekte"]), [])
        self.assertEqual(eposta.bul("garantili sonuç", ["garanti"]), ["garanti"])
        self.assertEqual(eposta.is_gunu(dt.date(2026, 10, 31)), dt.date(2026, 11, 2))


if __name__ == "__main__":
    unittest.main()
