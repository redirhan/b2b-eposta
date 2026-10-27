# B2B E-posta (İYS Uyumlu) — free Claude Code skill

> **Bu bir hukuki görüş değildir.** (This is not legal advice.) For information only; ask a lawyer for a definitive opinion.

For Turkish small agencies and freelancers. The skill reads a target business's **public** website and writes a short,
personalised, value-first **first email** plus **two follow-ups**, and an article-cited **compliance checklist** for
Turkey. It never sends email: you send the drafts one by one from your own mailbox. Output is in Turkish.

Made by Redirhan Studio. Free, MIT licensed.

## Output

| File | Content |
|---|---|
| `epostalar.md` | 3 drafts: first touch (3-4 sentences, no links, ends with a permission question) + day-3 and day-7 follow-ups, subjects and send dates |
| `kontrol_listesi.md` | Checklist: DUR (stop) / ENGEL (blocker) / DÜZELT (fix) / UZMANA SOR (ask an expert) / UYARI (warning) / ELLE (manual), each with article numbers and source URLs |
| `kayit.json` | Evidence record: where and when the address was found, İYS check, send plan (keep 3 years) |
| `red_raporu.md` | Refusal reasons when the recipient is not eligible |

## Rules covered

- **Law 6563 art. 6(2), Regulation art. 6(3):** traders and craftsmen (tacir/esnaf) may receive commercial e-messages
  without prior consent, but the **sender must register with İYS** (Reg. art. 5(2)), the recipient's address must be
  **registered in İYS and checked for an opt-out before sending** (art. 6(6)), **every message must offer an easy,
  free opt-out** on the same channel (Law art. 8(2), Reg. art. 9(3)-(4)), sending must **stop within 3 business days**
  (Law art. 8(3), Reg. art. 10) and opt-outs must be **reported to İYS within 3 business days** (art. 9(6)).
  Messages carry the **MERSİS number + trade name** or **name + tax ID** (art. 8(2)) and a contact detail (art. 8(5)).
- **Liberal professions** (lawyers, doctors, accountants...) are neither traders nor craftsmen, so the exemption does
  not apply (KVKK Board decision 2022/861, TRY 150,000 fine).
- **KVKK (data protection):** only business addresses published by the company; publicly available data may only be used
  for the purpose it was published for; no personal mobile numbers; a short privacy notice (art. 10).
- **Deliverability:** separate sending domain, SPF/DKIM/DMARC, 2-week warm-up, at most 20 hand-reviewed emails a day,
  no links or tracking, spam rate under 0.1%.

All sources, URLs and read dates are in `rules/iys_kvkk.yaml` (read on mevzuat.gov.tr on 27 Oct 2026).

## What it refuses

Bulk sending (more than 20 companies per run, more than 50 a day), bought or scraped lists, guessed addresses, consumer
or personal targeting, liberal professions, recipients who opted out in İYS, profiles containing phone numbers, emails
without a company-specific observation, fake "Re:" subjects.

## Install

```bash
unzip b2b-eposta-v1.0.zip -d ~/.claude/skills/
```

Requires Python 3.8+. No other packages (PyYAML is used if present).

## Use

In Claude Code: *"Write a cold email for fincanalti.example about my social media service, İYS compliant."*

By hand:

```bash
S=~/.claude/skills/b2b-eposta/scripts
python3 $S/eposta.py doctor
python3 $S/eposta.py yeni gonderen > gonderen.yaml
python3 $S/eposta.py yeni profil --sablon sosyal-medya > profil.yaml
python3 $S/eposta.py yaz profil.yaml --gonderen gonderen.yaml --cikti eposta_cikti/
python3 $S/eposta.py kontrol eposta_cikti/epostalar.md --gonderen gonderen.yaml
```

Exit codes: 0 ready · 2 drafts written but blockers remain · 3 stopped, no drafts.

## Templates

`sosyal-medya` (social media), `video`, `web`, `urun-fotografi` (product photos), `muhasebe-danismanligi`
(placeholder; not for licensed accountants, whose professional rules restrict advertising).

## What it does not do

It does not send or schedule email, log in anywhere, make network calls (Claude reads the site), use paid APIs or open a
browser. It does not register you with İYS or check recipients for you; it tells you not to send until you have.
It is not legal advice.

## Licence

MIT © 2026 Redirhan Studio. Bu bir hukuki görüş değildir.
