#!/usr/bin/env python3
"""
Henter og analyserer SSBs historiske grenserapport (rapp_9913) for å bygge
en oversettingstabell fra historiske kommunenummer (1987–1998) til dagens koder.

Bruk:
  python scripts/grenser.py

Krever:
  pip install anthropic pymupdf
  ANTHROPIC_API_KEY satt i miljøet

Output:
  data/raw/grenser_mapping.csv
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import anthropic
import pymupdf

PDF_URL = "https://www.ssb.no/a/publikasjoner/pdf/rapp_9913/rapp_9913.pdf"
PDF_PATH = Path("data/raw/rapp_9913.pdf")
OUTPUT_PATH = Path("data/raw/grenser_mapping.csv")
CHUNK_PAGES = 8   # sider per API-kall
MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """Du er en ekspert på norsk kommunehistorie og SSBs kommuneinndelinger.
Din jobb er å lese tekst fra SSBs rapport om historiske endringer i kommuneinndelingen,
og trekke ut alle kommunegrenseendringer på en strukturert måte.

For hvert tekstutdrag skal du returnere et JSON-objekt med nøkkelen "endringer" som
inneholder en liste med endringer. Hver endring har disse feltene:

- gammelt_nr: (string) det gamle 4-sifrede kommunenummeret, f.eks. "0101"
- nytt_nr: (string) det nye 4-sifrede kommunenummeret, eller samme som gammelt_nr
  hvis kommunen fortsetter uendret
- navn_gammelt: (string) det gamle kommunenavnet
- navn_nytt: (string) det nye kommunenavnet (kan være likt)
- aar: (integer) årstallet da endringen trådte i kraft
- type: (string) en av: "sammenslåing", "deling", "navneendring", "grenseendring",
  "overføring", "ny_kommune"
- notis: (string) eventuell tilleggsinformasjon, ellers tom streng

Viktig:
- Kun endringer i perioden 1987–1998 er relevant for dette prosjektet.
- Hvis en gammel kommune A og B slås sammen til C: lag én rad per gammel kommune
  (A→C og B→C).
- Hvis en kommune deles i X og Y: lag én rad per ny kommune (A→X og A→Y).
- Rene navneendringer uten kodenummerbytte er også interessante.
- Grenseendringer med liten befolkningsoverføring kan ha notis "liten overføring".
- Dersom tekstutdraget ikke inneholder relevante endringer, returner {"endringer": []}.
- Svar BARE med gyldig JSON, ingen annen tekst."""


def last_ned_pdf() -> None:
    if PDF_PATH.exists():
        print(f"  PDF allerede nedlastet: {PDF_PATH}")
        return
    print(f"  Prøver å laste ned {PDF_URL} ...")
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)

    for forsok, headers in enumerate([
        {"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"},
        {"User-Agent": "curl/7.88.1"},
        {},
    ]):
        try:
            req = urllib.request.Request(PDF_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if len(data) < 10_000:
                raise ValueError(f"Filen er for liten ({len(data)} bytes) — mulig blokkering")
            PDF_PATH.write_bytes(data)
            print(f"  Lagret til {PDF_PATH} ({PDF_PATH.stat().st_size // 1024} KB)")
            return
        except Exception as e:
            print(f"  Forsøk {forsok+1} feilet: {e}")

    print(f"""
FEIL: Kunne ikke laste ned PDF automatisk.
Last ned filen manuelt fra:
  {PDF_URL}
og lagre den som:
  {PDF_PATH.resolve()}

Kjør deretter scriptet på nytt.
""")
    sys.exit(1)


def hent_sider(pdf_path: Path) -> list[str]:
    doc = pymupdf.open(str(pdf_path))
    sider = []
    for side in doc:
        tekst = side.get_text() or ""
        sider.append(tekst)
    doc.close()
    print(f"  Leste {len(sider)} sider fra PDF")
    return sider


def analyser_chunk(client: anthropic.Anthropic, chunk_tekst: str, chunk_nr: int) -> list[dict]:
    prompt = (
        f"Her er tekst fra sidene i SSBs rapport om historiske kommunegrenseendringer "
        f"(utdrag nr. {chunk_nr}):\n\n"
        f"---\n{chunk_tekst}\n---\n\n"
        f"Trekk ut alle kommunegrenseendringer fra perioden 1987–1998 "
        f"og returner dem som JSON."
    )

    for forsok in range(3):
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                svar = stream.get_final_message()

            tekst = svar.content[0].text.strip()
            # Fjern ev. markdown-kodeblokkmarkeringer
            if tekst.startswith("```"):
                tekst = tekst.split("```")[1]
                if tekst.startswith("json"):
                    tekst = tekst[4:]

            data = json.loads(tekst)
            endringer = data.get("endringer", [])
            if endringer:
                print(f"    Chunk {chunk_nr}: {len(endringer)} endringer funnet")
            return endringer

        except json.JSONDecodeError as e:
            print(f"    Chunk {chunk_nr} forsøk {forsok+1}: JSON-feil ({e}), prøver igjen...")
            time.sleep(2 ** forsok)
        except Exception as e:
            print(f"    Chunk {chunk_nr} forsøk {forsok+1}: Feil ({e}), prøver igjen...")
            time.sleep(2 ** forsok)

    print(f"    Chunk {chunk_nr}: ga opp etter 3 forsøk")
    return []


def dedupliser(endringer: list[dict]) -> list[dict]:
    sett = set()
    unik = []
    for e in endringer:
        nokkel = (e.get("gammelt_nr"), e.get("nytt_nr"), e.get("aar"), e.get("type"))
        if nokkel not in sett:
            sett.add(nokkel)
            unik.append(e)
    return unik


def skriv_csv(endringer: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    kolonner = ["gammelt_nr", "nytt_nr", "navn_gammelt", "navn_nytt", "aar", "type", "notis"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(kolonner) + "\n")
        for e in endringer:
            rad = [str(e.get(k, "")).replace('"', '""') for k in kolonner]
            f.write(",".join(f'"{v}"' for v in rad) + "\n")
    print(f"\n  Skrev {len(endringer)} endringer til {path}")


def main():
    print("=== grenser.py: SSB kommunegrense-ekstraksjon ===\n")

    client = anthropic.Anthropic()

    print("1. Laster ned PDF...")
    last_ned_pdf()

    print("\n2. Leser PDF-tekst...")
    sider = hent_sider(PDF_PATH)

    print(f"\n3. Analyserer {len(sider)} sider i biter på {CHUNK_PAGES} sider...")
    alle_endringer: list[dict] = []

    chunks = [sider[i:i + CHUNK_PAGES] for i in range(0, len(sider), CHUNK_PAGES)]
    for nr, chunk in enumerate(chunks, 1):
        chunk_tekst = "\n\n[--- Sideskift ---]\n\n".join(chunk)
        if len(chunk_tekst.strip()) < 100:
            continue
        print(f"  Chunk {nr}/{len(chunks)} ({len(chunk_tekst)} tegn)...")
        endringer = analyser_chunk(client, chunk_tekst, nr)
        alle_endringer.extend(endringer)
        # Kort pause mellom kall for å unngå rate-limiting
        if nr < len(chunks):
            time.sleep(0.5)

    print(f"\n4. Funnet totalt {len(alle_endringer)} endringer (inkl. duplikater)")
    alle_endringer = dedupliser(alle_endringer)
    print(f"   Etter deduplisering: {len(alle_endringer)} unike endringer")

    # Sorter etter år og gammelt kommunenummer
    alle_endringer.sort(key=lambda e: (e.get("aar") or 0, e.get("gammelt_nr") or ""))

    print("\n5. Skriver til CSV...")
    skriv_csv(alle_endringer, OUTPUT_PATH)

    print("\nFerdig!")


if __name__ == "__main__":
    main()
