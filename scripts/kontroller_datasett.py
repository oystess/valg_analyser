#!/usr/bin/env python3
"""
kontroller_datasett.py – Automatiske kvalitetskontroller av datasettet (QA K4–K7).

Kjøres etter bygg_kodemapping.py og bygg_datasett.py. Avslutter med kode 1 hvis
en harde kontroll feiler. Skriver en oversikt til qa/kontroll/automatiske_kontroller.md.

  C1 Bevaring: sum stemmer i rådata = sum i ferdigtabellen, per år og partigruppe
  C2 Landstall: Ap, FrP, H og Sp mot SSBs publiserte landstall (tabell 08092 region 0,
     og 01180 uten regionfilter), hentet 2026-09-24
  C3 Uendrede kommuner: ferdigtabellen = SSBs egen 2024-aggregering der SSB har tall
  C4 Befolkning: = SSBs «Kommuner 2024, sammenslåtte tidsserier» der SSB har tall
  C5 Struktur: 357 kommuner per år, én rad per kommune/år/parti, andeler summerer til 1
  C6 Kontinuitet: stemmer per innbygger per kommune – avvik listes (myk kontroll)
"""
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SSB = PROJECT / "data" / "raw" / "ssb"
PROC = PROJECT / "data" / "processed"
RAPPORT = PROJECT / "qa" / "kontroll" / "automatiske_kontroller.md"

sys.path.insert(0, str(Path(__file__).parent))
from bygg_datasett import PARTI_GRUPPE, ANDRE, ST_AAR, KV_AAR  # noqa: E402

# SSB landstall, Godkjente stemmer (hentet via SSB-API 2026-09-24)
LANDSTALL = {
    "st": {
        "01": [907393, 908724, 904362, 612632, 862456, 949049, 874769, 800947, 783394, 902296],
        "02": [345185, 154497, 395376, 369236, 581896, 614717, 463560, 444681, 346474, 767903],
        "03": [588682, 419373, 370441, 534852, 371948, 462458, 760232, 732895, 607316, 471602],
        "05": [171269, 412187, 204824, 140287, 171063, 165006, 155357, 302017, 402961, 179994],
    },
    "kv": {
        "01": [795876, 655716, 644573, 592281, 563583, 655096, 767641, 789170, 664695, 576082],
        "02": [231609, 141524, 221493, 249753, 337595, 387487, 275559, 226640, 220713, 302722],
        "03": [516601, 467483, 427242, 442284, 372427, 425700, 678732, 554399, 538765, 689952],
        "05": [157317, 250367, 244326, 171080, 162557, 175145, 163382, 203188, 386349, 217608],
    },
}

ut, feil = [], []


def logg(tekst):
    ut.append(tekst)
    print(tekst)


def hard(ok, tekst):
    logg(("  OK   " if ok else "  FEIL ") + tekst)
    if not ok:
        feil.append(tekst)


def les(navn):
    return list(csv.DictReader(open(PROC / navn, encoding="utf-8")))


def main():
    tabeller = {"st": ("stortingsvalg_2024.csv", "st08092", ST_AAR),
                "kv": ("kommunestyrevalg_2024.csv", "kv01180", KV_AAR)}
    bef = {(r["kom2024"], int(r["aar"])): int(r["befolkning"]) for r in les("befolkning_2024.csv")}

    for tag, (fil, prefix, aarliste) in tabeller.items():
        rows = les(fil)
        logg(f"\n## {fil}\n")
        per = defaultdict(float)
        tot = {}
        est = set()
        for r in rows:
            per[(int(r["aar"]), r["parti"])] += float(r["stemmer"])
            tot[(r["kom2024"], int(r["aar"]))] = float(r["total_stemmer"])
            if r["estimert"] == "True":
                est.add((r["kom2024"], int(r["aar"])))

        # C1 bevaring
        logg("C1 Bevaring (rådata = ferdigtabell):")
        for aar in aarliste:
            raw = defaultdict(int)
            for r in csv.DictReader(open(SSB / f"{prefix}_{aar}.csv", encoding="utf-8")):
                raw[PARTI_GRUPPE.get(r["PolitParti"], ANDRE)] += int(r[f"Godkjente1 {aar}"])
            avvik = max(abs(raw[g] - per[(aar, g)]) for g in set(raw) | {g for (a, g) in per if a == aar})
            sum_tot = sum(v for (k, a), v in tot.items() if a == aar)
            hard(avvik < 0.5 and abs(sum_tot - sum(raw.values())) < 0.5,
                 f"{aar}: {sum(raw.values()):,} stemmer, største avvik per parti {avvik:.2f}")

        # C2 landstall
        logg("C2 Landstall mot SSB:")
        for parti, serie in LANDSTALL[tag].items():
            avv = [(a, round(per[(a, parti)]) - v) for a, v in zip(aarliste, serie)
                   if round(per[(a, parti)]) != v]
            hard(not avv, f"parti {parti}: {'alle år like' if not avv else avv}")

        # C3 uendrede kommuner mot SSBs aggregering
        fasit = defaultdict(int)
        for r in csv.DictReader(open(SSB / f"{prefix}_agg2024.csv", encoding="utf-8")):
            fasit[(r["kom2024"], int(r["aar"]), PARTI_GRUPPE.get(r["parti"], ANDRE))] += int(r["stemmer"])
        vaar = {(r["kom2024"], int(r["aar"]), r["parti"]): float(r["stemmer"]) for r in rows}
        # SSBs valgaggregat har bare tall for samme kode (f.eks. gamle Stavanger uten Finnøy
        # og Rennesøy). Sammenlign derfor bare der 2024-kommunen besto av én og samme kode.
        bidrag = defaultdict(set)
        for r in csv.DictReader(open(PROC / "kodemapping_2024.csv", encoding="utf-8")):
            bidrag[(r["kom2024"], int(r["aar"]))].add(r["kode"])
        n, avvik = 0, []
        for key, v in fasit.items():
            kom, aar, _ = key
            koder = bidrag.get((kom, aar), set()) | bidrag.get((kom, aar + 1), set()) if tag == "kv" else bidrag.get((kom, aar), set())
            if koder != {kom}:
                continue
            n += 1
            if abs(vaar.get(key, 0) - v) > 0.5:
                avvik.append((key, v, vaar.get(key)))
        hard(not avvik, f"C3 {n:,} celler for uendrede kommuner der SSB har 2024-aggregat: "
                        f"{len(avvik)} avvik {avvik[:5]}")

        # C5 struktur
        per_aar = defaultdict(set)
        dupl = set()
        seen = set()
        for r in rows:
            k = (r["kom2024"], r["aar"], r["parti"])
            if k in seen:
                dupl.add(k)
            seen.add(k)
            per_aar[int(r["aar"])].add(r["kom2024"])
        hard(all(len(v) == 357 for v in per_aar.values()) and not dupl,
             f"C5 357 kommuner alle år ({sorted({len(v) for v in per_aar.values()})}), duplikater: {len(dupl)}")
        dekn = [(r["kom2024"], r["navn"], r["aar"], r["dekning"]) for r in rows
                if r["parti"] == "01" and float(r["dekning"]) < 0.999]
        logg(f"  INFO {len(dekn)} kommune/år med dekning < 1 (flertallsvalg/manglende data): "
             + "; ".join(f"{k} {n} {a} ({float(d):.0%})" for k, n, a, d in dekn[:40]))
        logg(f"  INFO {len(est)} kommune/år med estimert fordeling (delte kommuner): "
             + ", ".join(f"{k} {a}" for k, a in sorted(est)))

        # C6 kontinuitet: stemmer per innbygger
        ratio = {}
        for (k, a), t in tot.items():
            b = bef.get((k, a))
            if b and t > 0:
                ratio[(k, a)] = t / b
        avvik6 = []
        for aar in aarliste:
            vals = [v for (k, a), v in ratio.items() if a == aar]
            med = statistics.median(vals)
            mad = statistics.median(abs(v - med) for v in vals)
            for (k, a), v in ratio.items():
                if a == aar and abs(v - med) > 6 * mad:
                    avvik6.append((k, a, round(v, 3), round(med, 3)))
        logg(f"C6 Stemmer per innbygger, avvik > 6 MAD fra årsmedianen: {len(avvik6)}")
        for x in sorted(avvik6):
            logg(f"    {x}")

    # C4 befolkning
    logg("\n## befolkning_2024.csv\n")
    fasit = {}
    for r in csv.DictReader(open(SSB / "bef07459_agg2024.csv", encoding="utf-8")):
        k = r["kom2024"].replace("K-", "")
        # Ålesund 2020–2023 fører SSB i sin helhet på nye Ålesund; vi deler på Ålesund/Haram
        if len(k) == 4 and k.isdigit() and int(r["befolkning"]) > 0 \
                and not (k == "1508" and 2020 <= int(r["aar"]) <= 2023):
            fasit[(k, int(r["aar"]))] = int(r["befolkning"])
    avv = [(k, a, v, bef.get((k, a))) for (k, a), v in fasit.items() if bef.get((k, a)) != v]
    hard(not avv, f"C4 {len(fasit):,} kommune/år mot SSB-aggregat: {len(avv)} avvik {avv[:5]}")
    uten = sorted({k for (k, a) in bef} - {k for (k, a) in fasit if a == 2000})
    logg(f"  INFO kommuner uten SSB-tidsserie før 2020 (egen oversetting): {uten}")
    hard(len({k for k, a in bef}) == 357 and len(bef) == 357 * 41, f"C5 befolkning 357 × 41 år ({len(bef)})")

    # C5 andeler i mapping
    s = defaultdict(float)
    for r in csv.DictReader(open(PROC / "kodemapping_2024.csv", encoding="utf-8")):
        s[(r["kode"], r["aar"])] += float(r["andel"])
    hard(all(abs(v - 1) < 1e-4 for v in s.values()), f"C5 andeler summerer til 1 for {len(s):,} kode/år")

    RAPPORT.parent.mkdir(parents=True, exist_ok=True)
    RAPPORT.write_text("# Automatiske kontroller\n\nGenerert av `scripts/kontroller_datasett.py`.\n\n"
                       + "\n".join(ut) + f"\n\n**Harde feil: {len(feil)}**\n", encoding="utf-8")
    print(f"\nHarde feil: {len(feil)}")
    return 1 if feil else 0


if __name__ == "__main__":
    sys.exit(main())
