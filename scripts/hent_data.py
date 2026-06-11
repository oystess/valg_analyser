#!/usr/bin/env python3
"""
hent_data.py – Prosesserer SSB-data lastet ned via Claude Code MCP-verktøy.

DATAKILDER (lastet ned via SSB MCP i Claude Code-sesjon):
  - SSB 08092: Stortingsvalg 1989–2025, per kommune, Godkjente røyster
    Codelist: vs_KommunValg (alle historiske kommunekoder)
    Parter: 01 Ap, 02 FrP, 03 Høyre, 04 KrF, 05 Sp, 06 SV, 07 V, 08 MDG, 55 Rødt
  - SSB 01180: Kommunestyrevalg 1987–2023, per kommune, Godkjente stemmer
    Codelist: vs_KommunerV (alle historiske kommunekoder)
  - SSB 07459: Befolkning 1986–2026, kommuner 2024 (agg_KommSummer = sammenslåtte tidsserier)

KOMMUNESTRUKTUR:
  Mål: 2024-struktur (357 kommuner)
  Metode: navnematch + grenser_mapping.csv (1987–1998) + regelbasert for 2020-reform

UTDATA:
  data/processed/stortingsvalg_2024.csv
  data/processed/kommunestyrevalg_2024.csv
  data/processed/befolkning_2024.csv
  data/processed/kom_mapping.csv

Bruk:
  python scripts/hent_data.py [--tool-results-dir PATH]
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────

PROJECT = Path(__file__).parent.parent
RAW_DIR = PROJECT / "data" / "raw"
PROCESSED_DIR = PROJECT / "data" / "processed"
GRENSER_CSV = RAW_DIR / "grenser_mapping.csv"
SUPPLEMENT_CSV = RAW_DIR / "kommunereform_mapping.csv"

# Rå nedlastede JSON-filer fra SSB MCP (Claude Code tool-results)
DEFAULT_TOOL_RESULTS = Path(
    "/root/.claude/projects/-home-user-valg-analyser"
    "/b8ff7b50-64c1-5dbc-80eb-7dfe0ec83326/tool-results"
)

PARTIES = {
    "01": "Ap", "02": "FrP", "03": "Høyre", "04": "KrF",
    "05": "Sp", "06": "SV", "07": "Venstre", "08": "MDG", "55": "Rødt",
}

STORTINGSVALG_YEARS  = [1989, 1993, 1997, 2001, 2005, 2009, 2013, 2017, 2021, 2025]
KOMMUNEVALG_YEARS    = [1987, 1991, 1995, 1999, 2003, 2007, 2011, 2015, 2019, 2023]

# ─── Parsing helpers ──────────────────────────────────────────────────────────

_RE_ELEK = re.compile(
    r'^(\d{4})\s+(.+?)(?:\s+\((-?\d{4})?(?:-(\d{4})?)?\))?$'
)
# Matches:
#   "0101 Halden (-2019)"       → code=0101, name=Halden, start=None, end=2019
#   "0105 Sarpsborg (1992-2019)"→ code=0105, name=Sarpsborg, start=1992, end=2019
#   "3101 Halden"               → code=3101, name=Halden, start=None, end=None
#   "3001 Halden (2020-2023)"   → code=3001, name=Halden, start=2020, end=2023

_RE_ELEK2 = re.compile(
    r'^(\d{4})\s+(.+?)(?:\s+\((-?\d{4})?(?:-(\d{4})?)?\))?$'
)


def parse_election_region(label: str):
    """
    Parse 'CODE NAME' or 'CODE NAME (PERIOD)' labels from election data.
    Returns (code4, name, start_year, end_year).
    """
    # Handle the pattern "(YYYY-)" (open-ended start)
    m = re.match(
        r'^(\d{4})\s+(.+?)(?:\s+\((-?\d{4})?-?(\d{4})?\))?$',
        label.strip()
    )
    if not m:
        return None, label, None, None

    code = m.group(1)
    name = m.group(2).strip()

    # Parse period from original label more carefully
    period_match = re.search(r'\((.+?)\)$', label.strip())
    start_year = end_year = None
    if period_match:
        period = period_match.group(1)
        if period.startswith('-'):
            # (-YYYY) format
            try:
                end_year = int(period[1:])
            except ValueError:
                pass
        elif '-' in period:
            parts = period.split('-', 1)
            try:
                start_year = int(parts[0]) if parts[0] else None
            except ValueError:
                start_year = None
            try:
                end_year = int(parts[1]) if parts[1] else None
            except ValueError:
                end_year = None

    return code, name, start_year, end_year


def parse_pop_region(label: str):
    """
    Parse 'K-CODE NAME' labels from population data (agg_KommSummer).
    Returns (code4, name).
    """
    m = re.match(r'^K-(\d{4})\s+(.+)$', label.strip())
    if m:
        return m.group(1), m.group(2).strip()
    return None, label


def extract_year(tid: str) -> int:
    """'1989 1989' → 1989"""
    return int(tid.split()[0])


def extract_party(parti: str) -> str:
    """'01 Arbeiderpartiet' → '01'"""
    return parti.split()[0]


# ─── File identification ───────────────────────────────────────────────────────

def load_tool_result(path: Path) -> dict | None:
    """Load a tool-result JSON file. Returns None if not valid SSB data."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "rows" not in data:
            return None
        meta = data.get("metadata", {})
        if meta.get("tableId") not in ("08092", "01180", "07459"):
            return None
        return data
    except Exception:
        return None


def identify_dataset(data: dict) -> tuple[str, int | None]:
    """
    Returns (table_id, year) where year is None for multi-year population data.
    """
    table_id = data["metadata"]["tableId"]
    rows = [r for r in data["rows"] if any(v is not None for k, v in r.items() if k not in ("Tid", "Region", "PolitParti"))]
    if not rows:
        rows = data["rows"]
    if rows:
        year = extract_year(rows[0]["Tid"])
    else:
        year = None
    if table_id == "07459":
        year = None  # multi-year
    return table_id, year


# ─── Data loading ─────────────────────────────────────────────────────────────

def load_all_files(tool_results_dir: Path):
    """
    Load and classify all MCP tool-result files.
    Returns:
      election_rows: list of dicts {table, year, code, name, start_yr, end_yr, party, votes}
      pop_rows: list of dicts {code, name, year, befolkning}
    """
    election_rows = []
    pop_rows = []
    loaded = 0
    skipped = 0

    for f in sorted(tool_results_dir.glob("mcp-7c19f76f*.txt")):
        data = load_tool_result(f)
        if data is None:
            skipped += 1
            continue

        table_id, year = identify_dataset(data)
        loaded += 1

        for row in data["rows"]:
            region_label = row.get("Region", "")

            if table_id == "07459":
                # Population data
                code, name = parse_pop_region(region_label)
                if not code:
                    continue
                yr = extract_year(row["Tid"])
                val = row.get("Personer1")
                if val is not None:
                    pop_rows.append({
                        "code": code, "name": name,
                        "year": yr, "befolkning": int(val),
                    })

            else:
                # Election data
                code, name, start_yr, end_yr = parse_election_region(region_label)
                if not code:
                    continue
                party = extract_party(row.get("PolitParti", ""))
                if party not in PARTIES:
                    continue
                yr = year or extract_year(row["Tid"])
                val = row.get("Godkjente1")
                if val is not None:
                    election_rows.append({
                        "table": table_id,
                        "year": yr,
                        "code": code, "name": name,
                        "start_yr": start_yr, "end_yr": end_yr,
                        "party": party,
                        "votes": int(val),
                    })

    print(f"  Lastet {loaded} filer, hoppet over {skipped}")
    print(f"  Valgdata: {len(election_rows):,} rader (ikke-null)")
    print(f"  Befolkning: {len(pop_rows):,} rader")
    return election_rows, pop_rows


# ─── Municipality code mapping ────────────────────────────────────────────────

def build_region_index(election_rows: list) -> dict:
    """
    Build index of all known region codes and their metadata.
    Returns dict: code → {name, start_yr, end_yr}
    (If a code appears with conflicting names/periods, last seen wins.)
    """
    index = {}
    for r in election_rows:
        code = r["code"]
        if code not in index:
            index[code] = {
                "name": r["name"],
                "start_yr": r["start_yr"],
                "end_yr": r["end_yr"],
            }
    return index


def normalize_name(name: str) -> str:
    """
    Normalize municipality name for fuzzy matching.
    Strips Sami dual names ('Name - SamiName' → 'Name') and
    county qualifiers ('Nes (Akershus)' → 'nes').
    Returns lowercase for case-insensitive comparison.
    """
    # Strip Sami/secondary name after ' - '
    if ' - ' in name:
        name = name.split(' - ')[0].strip()
    # Strip county qualifiers like '(Akershus)', '(Vestfold)', '(Innlandet)'
    name = re.sub(r'\s*\([A-ZÆØÅ][^)]+\)\s*$', '', name).strip()
    return name.lower()


def load_grenser_mapping() -> tuple[dict, dict]:
    """
    Load municipality boundary change files.
    Returns:
      supplement: kommunereform_mapping.csv entries (explicit mergers/reforms, HIGH priority)
      boundary:   grenser_mapping.csv entries (minor boundary transfers, LOW priority)
    """
    supplement = {}
    boundary = {}

    for csv_path, dest, label in [
        (SUPPLEMENT_CSV, supplement, "1999–2024 reformer"),
        (GRENSER_CSV, boundary, "1987–1998 grenseendringer"),
    ]:
        if not csv_path.exists():
            print(f"  ADVARSEL: {csv_path} ikke funnet")
            continue
        n = 0
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                old = row["gammelt_nr"].strip('"').strip()
                new = row["nytt_nr"].strip('"').strip()
                if old and new and old != new:
                    dest[old] = new
                    n += 1
        print(f"  {csv_path.name}: {n} koder ({label})")

    print(f"  Supplement: {len(supplement)}, Grenser: {len(boundary)} koder")
    return supplement, boundary


def build_municipality_mapping(
    region_index: dict,
    supplement: dict,
    boundary: dict,
) -> dict:
    """
    Build historical code → 2024 code mapping.

    Priority order in resolve():
    1. Exact name match (highest confidence)
    2. Supplement chain: kommunereform_mapping.csv (explicit mergers/renames, e.g. 0616→3322)
    3. Normalized name match (strips Sami names and county qualifiers)
    4. Boundary chain: grenser_mapping.csv (minor land transfers, lowest priority)

    Returns dict: code → code2024 (None if unmapped)
    """
    # Step 1: Identify current codes (no end_year = still valid today)
    current = {
        code: data["name"]
        for code, data in region_index.items()
        if data["end_yr"] is None
    }

    # Build normalized name → current code lookup.
    # When multiple codes share the same normalized name (e.g. code reuse after reform),
    # prefer the higher code (more recent renumbering takes precedence).
    norm_to_current: dict[str, str] = {}  # normalized_name → code
    for code, name in current.items():
        key = normalize_name(name)
        if key not in norm_to_current:
            norm_to_current[key] = code
        else:
            existing = norm_to_current[key]
            if code > existing:
                norm_to_current[key] = code

    # Also keep exact-name lookup for cases where normalization creates collisions
    name_to_current: dict[str, str] = {}
    for code, name in current.items():
        if name not in name_to_current:
            name_to_current[name] = code
        else:
            existing = name_to_current[name]
            if code > existing:
                name_to_current[name] = code

    def resolve(code: str, depth: int = 0) -> str | None:
        """Follow chain to find the 2024 code for a historical code."""
        if depth > 10:
            return None  # prevent infinite loops

        # Already a definitive current code?
        if code in current:
            name = current[code]
            if name_to_current.get(name) == code:
                return code
            # Superseded code with same name as a newer current code → name match
            if name in name_to_current:
                return name_to_current[name]
            nk = normalize_name(name)
            if nk in norm_to_current:
                return norm_to_current[nk]

        if code in region_index:
            name = region_index[code]["name"]

            # 1. Exact name match (highest confidence)
            if name in name_to_current:
                return name_to_current[name]

            # 2. Supplement/reform chain (explicit mergers — e.g. Nes→Nesbyen, old→new codes)
            if code in supplement:
                result = resolve(supplement[code], depth + 1)
                if result is not None:
                    return result

            # 3. Normalized name match (strips Sami names and county qualifiers)
            nk = normalize_name(name)
            if nk in norm_to_current:
                return norm_to_current[nk]

            # 4. Boundary transfer chain (minor land transfers — lowest priority)
            if code in boundary:
                result = resolve(boundary[code], depth + 1)
                if result is not None:
                    return result

        elif code in supplement:
            return resolve(supplement[code], depth + 1)
        elif code in boundary:
            return resolve(boundary[code], depth + 1)

        return None

    mapping = {}
    for code in region_index:
        mapping[code] = resolve(code)

    mapped = sum(1 for v in mapping.values() if v is not None)
    total = len(mapping)
    print(f"  Kommunemapping: {mapped}/{total} koder kartlagt "
          f"({mapped/total*100:.0f}%)")

    unmapped = [
        (code, region_index[code]["name"],
         region_index[code]["start_yr"], region_index[code]["end_yr"])
        for code, target in mapping.items()
        if target is None and region_index[code]["end_yr"] is not None
    ]
    if unmapped:
        print(f"  Ikke kartlagte historiske koder: {len(unmapped)}")

    return mapping


def save_mapping_csv(mapping: dict, region_index: dict):
    """Save the full mapping to data/processed/kom_mapping.csv"""
    out = PROCESSED_DIR / "kom_mapping.csv"
    rows = []
    for code, target in sorted(mapping.items()):
        d = region_index.get(code, {})
        rows.append({
            "gammelt_nr": code,
            "navn": d.get("name", ""),
            "start_yr": d.get("start_yr", ""),
            "end_yr": d.get("end_yr", ""),
            "nr_2024": target or "",
        })
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["gammelt_nr", "navn", "start_yr", "end_yr", "nr_2024"])
        w.writeheader()
        w.writerows(rows)
    print(f"  Lagret {len(rows)} koder til {out.name}")


# ─── Aggregation ──────────────────────────────────────────────────────────────

def aggregate_election(
    election_rows: list,
    mapping: dict,
    region_index: dict,
    table_id: str,
) -> list:
    """
    Aggregate vote counts to 2024 municipality boundaries.
    Returns list of dicts: {kom2024, navn, aar, parti, stemmer}
    """
    # Build 2024 code → canonical name (prefer exact 2024 code entries)
    code2024_names = {}
    for code, data in region_index.items():
        target = mapping.get(code)
        if target is not None and target not in code2024_names:
            # Use the name from the target code's own entry if available
            if target in region_index:
                code2024_names[target] = region_index[target]["name"]
            else:
                code2024_names[target] = data["name"]

    # Aggregate: (kom2024, year, party) → sum of votes
    agg: dict[tuple, int] = defaultdict(int)
    skipped = 0

    for r in election_rows:
        if r["table"] != table_id:
            continue
        target = mapping.get(r["code"])
        if target is None:
            skipped += 1
            continue
        key = (target, r["year"], r["party"])
        agg[key] += r["votes"]

    if skipped:
        print(f"  {table_id}: {skipped:,} rader hoppet over (ukjent mapping)")

    # Build output
    rows = []
    for (kom2024, aar, parti), stemmer in sorted(agg.items()):
        rows.append({
            "kom2024": kom2024,
            "navn": code2024_names.get(kom2024, ""),
            "aar": aar,
            "parti": parti,
            "stemmer": stemmer,
        })

    return rows


def add_totals_and_pct(rows: list) -> list:
    """
    Add total_stemmer and prosent columns.
    total_stemmer = sum of all 9 parties for that municipality-year.
    """
    totals: dict[tuple, int] = defaultdict(int)
    for r in rows:
        totals[(r["kom2024"], r["aar"])] += r["stemmer"]

    out = []
    for r in rows:
        total = totals[(r["kom2024"], r["aar"])]
        pct = round(r["stemmer"] / total * 100, 2) if total > 0 else None
        out.append({**r, "total_stemmer": total, "prosent": pct})
    return out


# ─── Population ───────────────────────────────────────────────────────────────

def process_population(pop_rows: list) -> list:
    """Population data is already aggregated to 2024 codes by agg_KommSummer."""
    rows = []
    for r in pop_rows:
        rows.append({
            "kom2024": r["code"],
            "navn": r["name"],
            "aar": r["year"],
            "befolkning": r["befolkning"],
        })
    return sorted(rows, key=lambda r: (r["kom2024"], r["aar"]))


# ─── CSV output ───────────────────────────────────────────────────────────────

def write_csv(rows: list, path: Path, fieldnames: list):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  Lagret {len(rows):,} rader til {path.name}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool-results-dir", type=Path, default=DEFAULT_TOOL_RESULTS)
    args = parser.parse_args()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("=== hent_data.py: Prosesserer SSB-data ===\n")

    # 1. Last inn alle nedlastede filer
    print("1. Leser nedlastede SSB-filer...")
    election_rows, pop_rows = load_all_files(args.tool_results_dir)

    # 2. Bygg kommunekodeindeks
    print("\n2. Bygger kommunekodeindeks...")
    region_index = build_region_index(election_rows)
    print(f"  Unike kommunekoder i valgdata: {len(region_index)}")

    # 3. Last inn grensemapping (1987–1998 + kommunereform 1999–2024)
    print("\n3. Laster grenser_mapping.csv + kommunereform_mapping.csv...")
    supplement, boundary = load_grenser_mapping()

    # 4. Bygg mapping til 2024-koder
    print("\n4. Bygger historisk → 2024 kommunemapping...")
    mapping = build_municipality_mapping(region_index, supplement, boundary)

    # 5. Lagre mapping
    save_mapping_csv(mapping, region_index)

    # 6. Aggreger stortingsvalg
    print("\n5. Aggregerer stortingsvalg til 2024-grenser...")
    sv_rows = aggregate_election(election_rows, mapping, region_index, "08092")
    sv_rows = add_totals_and_pct(sv_rows)
    write_csv(sv_rows, PROCESSED_DIR / "stortingsvalg_2024.csv",
              ["kom2024", "navn", "aar", "parti", "stemmer", "total_stemmer", "prosent"])

    # 7. Aggreger kommunestyrevalg
    print("\n6. Aggregerer kommunestyrevalg til 2024-grenser...")
    kv_rows = aggregate_election(election_rows, mapping, region_index, "01180")
    kv_rows = add_totals_and_pct(kv_rows)
    write_csv(kv_rows, PROCESSED_DIR / "kommunestyrevalg_2024.csv",
              ["kom2024", "navn", "aar", "parti", "stemmer", "total_stemmer", "prosent"])

    # 8. Befolkning (allerede aggregert)
    print("\n7. Prosesserer befolkningsdata...")
    pop = process_population(pop_rows)
    write_csv(pop, PROCESSED_DIR / "befolkning_2024.csv",
              ["kom2024", "navn", "aar", "befolkning"])

    # 9. Sammendrag
    print("\n=== Ferdig ===")
    sv_years = sorted({r["aar"] for r in sv_rows})
    kv_years = sorted({r["aar"] for r in kv_rows})
    pop_years = sorted({r["aar"] for r in pop})
    komm = sorted({r["kom2024"] for r in sv_rows})
    print(f"  Stortingsvalg: {sv_years}")
    print(f"  Kommunevalg:   {kv_years}")
    print(f"  Befolkning:    {pop_years[0]}–{pop_years[-1]}")
    print(f"  Kommuner (2024): {len(komm)}")


if __name__ == "__main__":
    main()
