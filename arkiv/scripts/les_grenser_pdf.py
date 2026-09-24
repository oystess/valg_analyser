#!/usr/bin/env python3
"""
les_grenser_pdf.py — ekstraher kommuneendringer 1987–1998 fra SSB rapp_9913.pdf
ved hjelp av Claude Haiku (billig modell for strukturert ekstraksjon).

Forutsetninger:
  - pdftotext installert (poppler-utils)
  - ANTHROPIC_API_KEY satt i miljøet

Kjøring:
  python3 scripts/les_grenser_pdf.py

Output: data/raw/grenser_fra_pdf.csv
"""

import subprocess
import re
import csv
import json
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    sys.exit("Mangler anthropic-pakke: pip install anthropic")

PDF = Path("data/raw/rapp_9913.pdf")
OUTPUT = Path("data/raw/grenser_fra_pdf.csv")
MODEL = "claude-haiku-4-5-20251001"

# Linjestarter for hvert fylke i pdftotext-output (uten -layout-flagg)
COUNTY_RANGES = [
    ("01 Østfold",          375,  750),
    ("02 Akershus",         751, 1102),
    ("03 Oslo",            1103, 1173),
    ("04 Hedmark",         1174, 1598),
    ("05 Oppland",         1599, 2085),
    ("06 Buskerud",        2086, 2470),
    ("07 Vestfold",        2471, 2948),
    ("08 Telemark",        2949, 3330),
    ("09 Aust-Agder",      3331, 3838),
    ("10 Vest-Agder",      3839, 4385),
    ("11 Rogaland",        4386, 5129),
    ("12 Hordaland",       5130, 6030),
    ("14 Sogn og Fjordane",6031, 6667),
    ("15 Møre og Romsdal", 6668, 7714),
    ("16 Sør-Trøndelag",   7715, 8388),
    ("17 Nord-Trøndelag",  8389, 8973),
    ("18 Nordland",        8974, 9867),
    ("19 Troms",           9868,10463),
    ("20 Finnmark",       10464,10813),
]

EXTRACT_PROMPT = """\
Du leser en del av SSB-rapporten "Historisk oversikt over endringer i kommune- og fylkesinndelingen" (rapp 99/13).

Fylke: {county}

Tekst:
---
{text}
---

Oppgave: Ekstraher ALLE kommuneendringer i dette fylket som skjedde mellom 1987 og 1998 (begge inkludert).

Endringstyper:
1. sammenslåing — to+ kommuner → én ny (lag én rad per inngående kommune)
2. deling — én kommune → to+ nye
3. overføring — del av en kommune overføres til en annen (grenseregulering)
4. navneendring — beholder kommunenummer, endrer navn
5. nummerendring — beholder navn, endrer kommunenummer

Returfelt per rad:
- gammelt_nr: 4-sifret kode med ledende nuller, f.eks. "0101"
- nytt_nr: koden etter endringen (= gammelt_nr ved ren navneendring)
- navn_gammelt: navn FØR endringen
- navn_nytt: navn ETTER endringen
- aar: årstall som heltall
- type: én av sammenslåing / deling / overføring / navneendring / nummerendring
- notis: kort beskrivelse, inkluder folkemengde og eksakt dato hvis oppgitt

Svar med BARE et JSON-array, ingen annen tekst:
[
  {{"gammelt_nr":"0703","nytt_nr":"0701","navn_gammelt":"Horten","navn_nytt":"Borre","aar":1988,"type":"sammenslåing","notis":"0703+0717 → 0701 Borre; 1.1.1988"}},
  ...
]

Ingen relevante endringer → returner []
"""


def extract_pdf_lines() -> list[str]:
    result = subprocess.run(
        ["pdftotext", str(PDF), "-"],  # uten -layout for å matche linjekart
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        sys.exit(f"pdftotext feilet: {result.stderr}")
    return result.stdout.splitlines()


def call_haiku(client: anthropic.Anthropic, county: str, text: str) -> list[dict]:
    prompt = EXTRACT_PROMPT.format(county=county, text=text[:15_000])  # maks ~4K tokens
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        result = json.loads(raw)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        print(f"  [ADVARSEL] JSON-feil for {county}: {raw[:200]}")
        return []


def main():
    client = anthropic.Anthropic()  # bruker ANTHROPIC_API_KEY fra miljøet

    print(f"Leser {PDF} …")
    lines = extract_pdf_lines()
    print(f"  {len(lines)} linjer\n")

    all_rows: list[dict] = []
    for county, start, end in COUNTY_RANGES:
        chunk = "\n".join(lines[start - 1 : end - 1])
        print(f"Prosesserer {county} ({len(chunk)} tegn) …", end=" ", flush=True)
        rows = call_haiku(client, county, chunk)
        # Filtrer til 1987-1998 i tilfelle modellen drifter
        rows = [r for r in rows if isinstance(r.get("aar"), int) and 1987 <= r["aar"] <= 1998]
        print(f"{len(rows)} endringer")
        all_rows.extend(rows)

    all_rows.sort(key=lambda r: (r.get("aar", 0), r.get("gammelt_nr", "")))

    fieldnames = ["gammelt_nr", "nytt_nr", "navn_gammelt", "navn_nytt", "aar", "type", "notis"]
    with open(OUTPUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n{len(all_rows)} endringer skrevet til {OUTPUT}")

    from collections import Counter
    year_counts = Counter(r["aar"] for r in all_rows)
    print("\nPer år:")
    for yr in sorted(year_counts):
        print(f"  {yr}: {year_counts[yr]}")


if __name__ == "__main__":
    main()
