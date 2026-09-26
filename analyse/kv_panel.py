#!/usr/bin/env python3
"""
analyse/kv_panel.py – KV-panel for alle partier, bygget som panel.csv (felles.py), men for kommunestyrevalg.

Én rad per 2024-kommune × kommunestyrevalgperiode t0 → t1 (1987–1991 … 2019–2023, 9 perioder).
Kolonner: {parti}_t0, {parti}_t1, d_{parti} (andel av alle godkjente stemmer, pp), vekt_stemmer_t0,
bef_t0, vekst4_pst (1.1.t0 → 1.1.t1), vekst10_pst (1.1.(t1−10) → 1.1.t1, mangler når t1−10 < 1986),
sent_indeks/sent_klasse, fylke, landsdel, estimert og reform_2017_20 (kommunen er slått sammen av
flere koder som fantes i 2016, altså kommunereformen 2017–2020).

Kilder: data/processed/kommunestyrevalg_2024.csv, befolkning_2024.csv, sentralitet_2024.csv,
kodemapping_2024.csv. Samme definisjoner som panel.csv der de finnes.

Kjøring: python analyse/kv_panel.py  → hypoteser/motreaksjon/data/kv_panel.csv
"""
import csv
import hashlib
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from felles import FYLKE, KV_AAR, LANDSDEL, PARTI, PROC, PROJECT, les_valg  # noqa: E402

UT = PROJECT / "hypoteser" / "motreaksjon" / "data" / "kv_panel.csv"


def reformkommuner():
    """2024-kommuner som fikk bidrag fra mer enn én kommunekode som fantes i 2016."""
    koder = defaultdict(set)
    for r in csv.DictReader(open(PROC / "kodemapping_2024.csv", encoding="utf-8")):
        if r["aar"] == "2016" and float(r["andel"]) > 0:
            koder[r["kom2024"]].add(r["kode"])
    return {k for k, v in koder.items() if len(v) > 1}


def bygg():
    kv = les_valg("kommunestyrevalg_2024.csv")
    bef = {(r["kom2024"], int(r["aar"])): float(r["befolkning"])
           for r in csv.DictReader(open(PROC / "befolkning_2024.csv", encoding="utf-8"))}
    sent = {r["kom2024"]: r for r in csv.DictReader(open(PROC / "sentralitet_2024.csv", encoding="utf-8"))}
    reform = reformkommuner()
    kommuner = sorted({k for k, _ in kv})
    rader = []
    for i in range(1, len(KV_AAR)):
        t0, t1 = KV_AAR[i - 1], KV_AAR[i]
        for kom in kommuner:
            a, b = kv[(kom, t0)], kv[(kom, t1)]
            b0, b1, b10 = bef.get((kom, t0)), bef.get((kom, t1)), bef.get((kom, t1 - 10))
            r = {
                "kom2024": kom, "navn": a["navn"], "periode": f"{t0}-{t1}", "t0": t0, "t1": t1,
                "fylke": FYLKE[kom[:2]], "landsdel": LANDSDEL[kom[:2]],
                "sent_klasse": int(sent[kom]["sent_klasse"]), "sent_indeks": int(sent[kom]["sent_indeks"]),
                "estimert": a["estimert"] or b["estimert"],
                "reform_2017_20": kom in reform,
                "vekt_stemmer_t0": a["total"],
            }
            for p in PARTI.values():
                r[f"{p}_t0"] = a[p]
                r[f"{p}_t1"] = b[p]
                r[f"d_{p}"] = b[p] - a[p]
            r["bef_t0"] = b0
            r["ln_bef_t0"] = math.log(b0) if b0 else float("nan")
            r["vekst4_pst"] = (b1 / b0 - 1) * 100 if b0 else float("nan")
            r["vekst10_pst"] = (b1 / b10 - 1) * 100 if b10 else float("nan")
            rader.append(r)
    UT.parent.mkdir(parents=True, exist_ok=True)
    felt = list(rader[0].keys())
    with open(UT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=felt)
        w.writeheader()
        for r in rader:
            w.writerow({k: ("" if isinstance(v, float) and v != v else
                            (round(v, 4) if isinstance(v, float) else v)) for k, v in r.items()})
    h = hashlib.sha256(UT.read_bytes()).hexdigest()
    print(f"kv_panel.csv: {len(rader)} rader, {len(felt)} kolonner, {len(reform)} reformkommuner, sha256 {h[:16]}")
    return h


if __name__ == "__main__":
    bygg()
