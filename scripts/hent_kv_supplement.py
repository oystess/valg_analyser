#!/usr/bin/env python3
"""
hent_kv_supplement.py - Supplerende KV-datauttrekk (Del 1 av plan_kommunevalg.md).

Genererer tre CSV-er som IKKE fantes i repoet fra før:
  - data/processed/kv_fasit_nasjonal.csv  (nasjonal fasit, alle partier, 1987-2023)
  - data/processed/kv_deltakelse.csv      (valgdeltakelse per kommune, 1987-2023)
  - data/processed/kv_andre_lister.csv    (lokale/andre lister per kommune, 1987-2023)

DATAKILDER (hentet via SSB MCP, ssb_get_data, i Claude Code-sesjon 2026-07-03):

  Tabell 01180 "Kommunestyrevalget. Godkjente stemmer, etter parti/valgliste
  (K) 1945-2023" (SSB, sist oppdatert 2023-11-08).
  Brukt til BÅDE kv_fasit_nasjonal.csv OG kv_andre_lister.csv (samme uttrekk,
  to ulike aggregeringer av samme rådata - se hhv. build_fasit() og
  build_andre_lister() under).

  Selection per år (10 kall, ett per valgår):
    Region:      ["*"]  (codelist ikke satt -> default "vs_KommunerV",
                          dvs. ALLE historiske kommunekoder, kun de som er
                          gyldige for det aktuelle Tid returnerer stemmer > 0
                          - resten er nullpadding fra SSBs kryssprodukt)
    PolitParti:  ["*"]  (alle partier tabellen har - 61 koder totalt, ikke
                          bare de ni store)
    ContentsCode:["Godkjente1"]
    Tid:         [<valgår>]  (ett år per kall: 1987,1991,1995,1999,2003,
                               2007,2011,2015,2019,2023)
    value_display: UseCodesAndTexts

  MERK: 01180 har IKKE region "0 Hele landet" (bekreftet ved probing -
  ssb_get_data feiler med "Non-existent value" for Region=["0"]). Nasjonal
  fasit er derfor beregnet ved å summere Godkjente1 per parti på tvers av
  ALLE regionrader for det gitte året (kryssvalidert mot kjente 1987-tall:
  Ap 795 876 stemmer / 35,9 % - stemmer med historiske oppslag). Dette er
  UAVHENGIG av hent_data.py sin egen historisk->2024-mapping (kom_mapping.csv),
  siden det bare summerer rådata for ett Tid av gangen - god fasit-kandidat
  nettopp fordi den IKKE er kontaminert av samme mapping-pipeline som
  produserte kommunestyrevalg_2024.csv.

  Codelisten "agg_KommunerV1" ("Kommuner 2024-") ble utprøvd som snarvei til
  2024-struktur, men FORKASTET: den viste seg å IKKE bakoverberegne
  omdøpte/omnummererte kommuner (f.eks. Halden 1987 kom ut som 0 stemmer
  under 2024-koden 3101, fordi den gamle koden 0101 aldri summeres inn).
  Navnet antyder hvorfor: "Kommuner 2024-" = gjeldende struktur FREMOVER,
  ikke en sammenslått tidsserie (i motsetning til f.eks. "agg_KommSummer"
  som finnes for befolkningstabellen 07459). kv_andre_lister.csv mappes
  derfor via data/processed/kom_mapping.csv, samme mønster som hent_data.py.

  Tool-result-filer (rå JSON, {"rows": [...]}) brukt i denne økten - se
  FILES_01180 under for eksakt fil per år.

  ---

  Tabell 09475 "Kommunestyrevalget. Stemmer og valgdeltakelse (K) 1955-2023"
  (SSB, sist oppdatert 2023-11-08).
  Brukt til kv_deltakelse.csv.

  Selection per år (10 kall):
    Region:       ["*"]  (default codelist - alle historiske koder + fylker
                           + "0 Hele landet", filtrert til 4-sifrede
                           kommunekoder i parsingen)
    ContentsCode: ["*"]  (8 koder: AvgitteStemmer, Forkastede, Godkjente,
                           Rettede, Blanke, DeltaProsent, Forhand,
                           ForhandProsent)
    Tid:          [<valgår>]
    value_display: UseCodesAndTexts

  MERK: Tabellen har INGEN egen kolonne for "stemmeberettigede" (rå manntall)
  - kun avgitte/godkjente stemmer og DeltaProsent (valgdeltakelse i prosent).
  kv_deltakelse.csv sin "stemmeberettigede"-kolonne er derfor BEREGNET per
  historisk kommunekode som avgitte_stemmer / (DeltaProsent/100), FØR
  aggregering til 2024-struktur. Dette er en avledet, ikke en rå SSB-verdi -
  dokumentert eksplisitt her og i sluttrapporten. Etter aggregering til
  kom2024 er valgdeltakelse_prosent REGNET OM som
  sum(avgitte_stemmer)/sum(stemmeberettigede)*100 (stemmevektet, korrekt
  fremgangsmåte ved sammenslåtte kommuner), IKKE et gjennomsnitt av
  prosentene.

  ADVARSEL (verktøyfeil observert, ikke brukt i endelige data): et forsøk på
  å hente 09475 med Region=["0"] fast + flere Tid + flere ContentsCode i
  SAMME kall ga et MCP-parsingsbug der bare 10 av 30 forventede celler kom
  med (resten ble stille overskrevet/mistet i rad-sammenslåingen). Dette
  skjedde IKKE når Region var wildcard (mange rader - 1268 rader korrekt
  fylt ut med alle 8 feltene testet for Eigersund 1987). Alle uttrekk brukt
  i dette skriptet bruker wildcard Region, så bugen påvirker ikke dataene
  under - men er notert her som teknisk lærdom for senere uttrekk.

Kommunekartlegging:
  Historisk kommunekode -> 2024-kode hentes fra det EKSISTERENDE
  data/processed/kom_mapping.csv (bygget av hent_data.py i tidligere økt).
  Denne filen endres IKKE av dette skriptet - kun lest. Vang (3454) og
  Hamar (3403) er IKKE spesialbehandlet (identity-mapping som alle andre
  koder uten reform) - navnebror-kollisjonen håndteres i QA (Del 2), ikke her.

Bruk:
  python scripts/hent_kv_supplement.py [--tool-results-dir PATH]

Produserer:
  data/processed/kv_fasit_nasjonal.csv
  data/processed/kv_deltakelse.csv
  data/processed/kv_andre_lister.csv

PROVENIENS-ETTERNOTAT (2026-07-18): data/processed/kv_prosent_korrigert.csv
  produseres IKKE av dette skriptet, men proveniensen manglet dokumentasjon
  og noteres derfor her: filen ble avledet 2026-07-03 som
  stemmer / total_stemmer_alle_partier, der total_stemmer_alle_partier per
  kommune-år er summen av 9-partisummen i kommunestyrevalg_2024.csv OG
  bygdeliste-/andre-liste-stemmene i kv_andre_lister.csv (dvs. samme
  korreksjon som for STV i stv_prosent_korrigert.csv, se hent_stv_fiks.py).
  Brukes av scripts/analyse_kv_revidert.py.
"""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT / "data" / "processed"
KOM_MAPPING_CSV = PROCESSED_DIR / "kom_mapping.csv"

DEFAULT_TOOL_RESULTS = Path(
    "/root/.claude/projects/-home-user-valg-analyser"
    "/dfa9d122-9637-51c2-b3a4-a1ac4b665bf8/tool-results"
)

KOMMUNEVALG_YEARS = [1987, 1991, 1995, 1999, 2003, 2007, 2011, 2015, 2019, 2023]

# De ni "store" partiene (samme koder som PARTIES i hent_data.py) - alt annet
# regnes som "andre" i kv_andre_lister.csv.
NI_PARTIER = {"01", "02", "03", "04", "05", "06", "07", "08", "55"}

# --- Provenance: eksakt fil brukt per år, hentet i denne økten 2026-07-03 ---

FILES_01180 = {
    1987: "mcp-SSB_MCP-ssb_get_data-1783094233239.txt",
    1991: "mcp-SSB_MCP-ssb_get_data-1783094275098.txt",
    1995: "mcp-SSB_MCP-ssb_get_data-1783094279364.txt",
    1999: "mcp-SSB_MCP-ssb_get_data-1783094284538.txt",
    2003: "mcp-SSB_MCP-ssb_get_data-1783094289226.txt",
    2007: "mcp-SSB_MCP-ssb_get_data-1783094294250.txt",
    2011: "mcp-SSB_MCP-ssb_get_data-1783094298890.txt",
    2015: "mcp-SSB_MCP-ssb_get_data-1783094303208.txt",
    2019: "mcp-SSB_MCP-ssb_get_data-1783094307572.txt",
    2023: "mcp-SSB_MCP-ssb_get_data-1783094312633.txt",
}

FILES_09475 = {
    1987: "mcp-SSB_MCP-ssb_get_data-1783094375981.txt",
    1991: "mcp-SSB_MCP-ssb_get_data-1783094382525.txt",
    1995: "mcp-SSB_MCP-ssb_get_data-1783094384677.txt",
    1999: "mcp-SSB_MCP-ssb_get_data-1783094388692.txt",
    2003: "mcp-SSB_MCP-ssb_get_data-1783094392704.txt",
    2007: "mcp-SSB_MCP-ssb_get_data-1783094394947.txt",
    2011: "mcp-SSB_MCP-ssb_get_data-1783094396996.txt",
    2015: "mcp-SSB_MCP-ssb_get_data-1783094399060.txt",
    2019: "mcp-SSB_MCP-ssb_get_data-1783094401416.txt",
    2023: "mcp-SSB_MCP-ssb_get_data-1783094406342.txt",
}

_RE_CODE = re.compile(r"(\d{4})")


def extract_code(label: str) -> str | None:
    """Finn 4-sifret kommunekode i en regionetikett ('3101 Halden',
    '0101 Halden (-2019)', 'K-3101 Halden', '1101u Egersund (-1964)' -> koden).
    Bruker søk (ikke anker) slik at prefikser som 'K-' ikke er et problem."""
    m = _RE_CODE.search(label)
    return m.group(1) if m else None


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_kom_mapping() -> dict:
    """Leser EKSISTERENDE data/processed/kom_mapping.csv (bygget av
    hent_data.py). Skrives ikke til - kun lest."""
    mapping = {}
    with open(KOM_MAPPING_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            old = row["gammelt_nr"].strip()
            new = row["nr_2024"].strip()
            if old and new:
                mapping[old] = new
    return mapping


# --- 1. Nasjonal fasit (kv_fasit_nasjonal.csv) -----------------------------

def build_fasit(tool_results_dir: Path) -> list[dict]:
    rows_out = []
    for year in KOMMUNEVALG_YEARS:
        path = tool_results_dir / FILES_01180[year]
        data = load_json(path)
        sums: dict[str, int] = defaultdict(int)
        names: dict[str, str] = {}
        for r in data["rows"]:
            v = r.get("Godkjente1")
            if not v:
                continue
            parti = r.get("PolitParti", "")
            parts = parti.split(None, 1)
            kode = parts[0]
            navn = parts[1] if len(parts) > 1 else ""
            sums[kode] += v
            names[kode] = navn
        total = sum(sums.values())
        for kode, stemmer in sorted(sums.items()):
            rows_out.append({
                "aar": year,
                "parti_kode": kode,
                "parti_navn": names[kode],
                "stemmer": stemmer,
                "prosent": round(stemmer / total * 100, 2) if total else None,
            })
        print(f"  {year}: {len(sums)} partier, {total:,} stemmer totalt")
    return rows_out


# --- 2. Valgdeltakelse (kv_deltakelse.csv) ---------------------------------

_DELTAKELSE_FIELDS = [
    "AvgitteStemmer", "Godkjente", "Forkastede", "Blanke", "Rettede",
    "Forhand",
]


def build_deltakelse(tool_results_dir: Path, kom_mapping: dict) -> list[dict]:
    rows_out = []
    coverage = {}
    for year in KOMMUNEVALG_YEARS:
        path = tool_results_dir / FILES_09475[year]
        data = load_json(path)

        # Aggreger per kom2024: summer stemmetall, hold stemmeberettigede
        # (beregnet per historisk kode FØR summering).
        agg = defaultdict(lambda: defaultdict(float))
        agg_present = defaultdict(lambda: defaultdict(bool))
        unmapped = 0
        skipped_nonmuni = 0

        for r in data["rows"]:
            label = r.get("Region", "")
            code = extract_code(label)
            if not code:
                skipped_nonmuni += 1
                continue
            avgitte = r.get("AvgitteStemmer")
            delta_pct = r.get("DeltaProsent")
            if avgitte is None and delta_pct is None:
                continue  # tom kryssprodukt-rad (koden ikke gyldig dette året)

            target = kom_mapping.get(code)
            if target is None:
                unmapped += 1
                continue

            for field in _DELTAKELSE_FIELDS:
                val = r.get(field)
                if val is not None:
                    agg[target][field] += val
                    agg_present[target][field] = True

            if avgitte is not None and delta_pct is not None and delta_pct > 0:
                stemmeberettigede_hist = avgitte / (delta_pct / 100)
                agg[target]["stemmeberettigede"] += stemmeberettigede_hist
                agg_present[target]["stemmeberettigede"] = True

        for kom2024, vals in sorted(agg.items()):
            avgitte_sum = vals.get("AvgitteStemmer") if agg_present[kom2024].get("AvgitteStemmer") else None
            stemmeber_sum = vals.get("stemmeberettigede") if agg_present[kom2024].get("stemmeberettigede") else None
            if avgitte_sum and stemmeber_sum:
                delta_pct_kom = round(avgitte_sum / stemmeber_sum * 100, 2)
            else:
                delta_pct_kom = None
            forhand_sum = vals.get("Forhand") if agg_present[kom2024].get("Forhand") else None
            if forhand_sum is not None and avgitte_sum:
                forhand_pct = round(forhand_sum / avgitte_sum * 100, 2)
            else:
                forhand_pct = None

            rows_out.append({
                "kom2024": kom2024,
                "aar": year,
                "stemmeberettigede": round(stemmeber_sum) if stemmeber_sum is not None else "",
                "avgitte_stemmer": round(avgitte_sum) if avgitte_sum is not None else "",
                "godkjente_stemmer": round(vals["Godkjente"]) if agg_present[kom2024].get("Godkjente") else "",
                "forkastede_stemmer": round(vals["Forkastede"]) if agg_present[kom2024].get("Forkastede") else "",
                "blanke_stemmer": round(vals["Blanke"]) if agg_present[kom2024].get("Blanke") else "",
                "rettede_stemmer": round(vals["Rettede"]) if agg_present[kom2024].get("Rettede") else "",
                "forhandsstemmer": round(forhand_sum) if forhand_sum is not None else "",
                "forhandsstemmer_prosent": forhand_pct if forhand_pct is not None else "",
                "valgdeltakelse_prosent": delta_pct_kom if delta_pct_kom is not None else "",
            })

        coverage[year] = len(agg)
        print(f"  {year}: {len(agg)} kommuner (2024-struktur), "
              f"{unmapped} rader uten mapping, {skipped_nonmuni} ikke-kommunerader hoppet over")

    return rows_out


# --- 3. Andre/lokale lister (kv_andre_lister.csv) --------------------------

def build_andre_lister(tool_results_dir: Path, kom_mapping: dict) -> list[dict]:
    rows_out = []
    for year in KOMMUNEVALG_YEARS:
        path = tool_results_dir / FILES_01180[year]
        data = load_json(path)

        # Summer per (kom2024): total (alle partier) og andre (utenfor de ni store)
        totals: dict[str, int] = defaultdict(int)
        andre: dict[str, int] = defaultdict(int)
        unmapped_votes = 0

        for r in data["rows"]:
            v = r.get("Godkjente1")
            if not v:
                continue
            code = extract_code(r.get("Region", ""))
            if not code:
                continue
            target = kom_mapping.get(code)
            if target is None:
                unmapped_votes += v
                continue
            parti_kode = r.get("PolitParti", "").split(None, 1)[0]
            totals[target] += v
            if parti_kode not in NI_PARTIER:
                andre[target] += v

        for kom2024, total in sorted(totals.items()):
            stemmer_andre = andre.get(kom2024, 0)
            rows_out.append({
                "kom2024": kom2024,
                "aar": year,
                "stemmer_andre": stemmer_andre,
                "total_stemmer_alle_partier": total,
                "prosent_andre": round(stemmer_andre / total * 100, 2) if total else None,
            })

        print(f"  {year}: {len(totals)} kommuner, "
              f"{unmapped_votes:,} stemmer uten kommunemapping (hoppet over)")

    return rows_out


# --- CSV output --------------------------------------------------------------

def write_csv(rows: list[dict], path: Path, fieldnames: list[str]):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  Lagret {len(rows):,} rader til {path.name}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool-results-dir", type=Path, default=DEFAULT_TOOL_RESULTS)
    args = parser.parse_args()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("=== hent_kv_supplement.py ===\n")

    print("0. Leser kom_mapping.csv (eksisterende, ikke endret)...")
    kom_mapping = load_kom_mapping()
    print(f"  {len(kom_mapping)} historiske koder lest\n")

    print("1. Bygger nasjonal fasit (01180, alle regioner summert per parti/aar)...")
    fasit_rows = build_fasit(args.tool_results_dir)
    write_csv(fasit_rows, PROCESSED_DIR / "kv_fasit_nasjonal.csv",
              ["aar", "parti_kode", "parti_navn", "stemmer", "prosent"])

    print("\n2. Bygger valgdeltakelse per kommune (09475, mappet til 2024-struktur)...")
    delt_rows = build_deltakelse(args.tool_results_dir, kom_mapping)
    write_csv(delt_rows, PROCESSED_DIR / "kv_deltakelse.csv",
              ["kom2024", "aar", "stemmeberettigede", "avgitte_stemmer",
               "godkjente_stemmer", "forkastede_stemmer", "blanke_stemmer",
               "rettede_stemmer", "forhandsstemmer", "forhandsstemmer_prosent",
               "valgdeltakelse_prosent"])

    print("\n3. Bygger andre/lokale lister per kommune (01180, mappet til 2024-struktur)...")
    andre_rows = build_andre_lister(args.tool_results_dir, kom_mapping)
    write_csv(andre_rows, PROCESSED_DIR / "kv_andre_lister.csv",
              ["kom2024", "aar", "stemmer_andre", "total_stemmer_alle_partier",
               "prosent_andre"])

    print("\n=== Ferdig ===")


if __name__ == "__main__":
    main()
