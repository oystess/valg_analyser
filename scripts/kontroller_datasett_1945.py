#!/usr/bin/env python3
"""
kontroller_datasett_1945.py – Kontroller av valgdatasettet 1945–2025 og befolkning 1951–.

  C1 Bevaring: rådata = ferdigtabell per år og partigruppe
  C2 Landstall mot SSB (08092 region 0 og 01180 uten regionfilter, hentet 2026-09-26)
  C3 Overlapp: 1987/1989– er identisk med stortingsvalg_2024.csv / kommunestyrevalg_2024.csv
  C4 Befolkning mot SSB 06913 «Kommuner 2024, sammenslåtte tidsserier» der SSB har tall
  C5 Kontinuitet: befolkning i hver 2024-kommune år til år (hopp > 8 % listes)
  C6 Struktur: antall kommuner og sikkerhetsnivå per år
Skriver utvidelse_1945/kontroll/automatiske_kontroller.md. Avslutter med 1 ved harde feil.
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bygg_datasett_1945 import gruppe, ST_AAR, KV_AAR  # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
SSB = PROJECT / "data" / "raw" / "ssb"
PROC = PROJECT / "data" / "processed"
RAPPORT = PROJECT / "utvidelse_1945" / "kontroll" / "automatiske_kontroller.md"

# SSB landstall (godkjente stemmer). ST: Sp = 05 + 71 (Bondepartiet), SV = 06 + 70 (SF).
LAND_ST = {
    "01": dict(zip(ST_AAR[:11], [609348, 803471, 830448, 865675, 860526, 883320, 1004348, 759499, 972434, 925087, 1061712])),
    "03": dict(zip(ST_AAR[:11], [252608, 279790, 327971, 301395, 354369, 415612, 406209, 370370, 563783, 792573, 791537])),
    "05": dict(zip(ST_AAR[:11], [119362, 85418, 157018, 154761, 125643, 191702, 194128, 146312, 184087, 105921, 171770])),
    "09": dict(zip(ST_AAR[:11], [176535, 102722, 90422, 60060, 53678, 27996, 21517, 0, 8448, 7154, 4245])),
}
LAND_KV = {
    "01": dict(zip(KV_AAR[:11], [510244, 550222, 657177, 696411, 729503, 870425, 820582, 794594, 732311, 768423, 866053])),
    "03": dict(zip(KV_AAR[:11], [124536, 199667, 236531, 268172, 310632, 376792, 361876, 341968, 420073, 625974, 577356])),
    "05": dict(zip(KV_AAR[:11], [49605, 76733, 92600, 110904, 129777, 156169, 174284, 219592, 207254, 182248, 166168])),
}
ut, feil = [], []


def logg(t):
    ut.append(t)
    print(t)


def hard(ok, t):
    logg(("  OK   " if ok else "  FEIL ") + t)
    if not ok:
        feil.append(t)


def les(fil):
    return list(csv.DictReader(open(PROC / fil, encoding="utf-8")))


def main():
    for fil, prefix, aarliste, land, gammel in (
            ("stortingsvalg_1945.csv", "st08092", ST_AAR, LAND_ST, "stortingsvalg_2024.csv"),
            ("kommunestyrevalg_1945.csv", "kv01180", KV_AAR, LAND_KV, "kommunestyrevalg_2024.csv")):
        rows = les(fil)
        logg(f"\n## {fil}\n")
        per = defaultdict(float)
        for r in rows:
            per[(int(r["aar"]), r["parti"])] += float(r["stemmer"])
        logg("C1 Bevaring:")
        for aar in aarliste:
            raw = defaultdict(int)
            for r in csv.DictReader(open(SSB / f"{prefix}_{aar}.csv", encoding="utf-8")):
                raw[gruppe(r["PolitParti"])] += int(r[f"Godkjente1 {aar}"])
            avv = max(abs(raw[g] - per[(aar, g)]) for g in set(raw) | {g for a, g in per if a == aar})
            hard(avv < 1, f"{aar}: {sum(raw.values()):,} stemmer, største avvik per gruppe {avv:.2f}")
        logg("C2 Landstall mot SSB:")
        for g, serie in land.items():
            avv = {a: round(per[(a, g)]) - v for a, v in serie.items() if round(per[(a, g)]) != v}
            hard(not avv, f"gruppe {g}: {'alle år like' if not avv else avv}")
        # C3 overlapp
        gml = defaultdict(float)
        gtot = {}
        for r in les(gammel):
            p = r["parti"]
            gml[(r["kom2024"], int(r["aar"]), p)] += float(r["stemmer"])
            gtot[(r["kom2024"], int(r["aar"]))] = float(r["total_stemmer"])
        ny = defaultdict(float)
        ntot = {}
        for r in rows:
            a = int(r["aar"])
            if a >= 1987:
                p = r["parti"] if r["parti"] in ("01", "02", "03", "04", "05", "06", "07", "08", "55") else "99"
                ny[(r["kom2024"], a, p)] += float(r["stemmer"])
                ntot[(r["kom2024"], a)] = float(r["total_stemmer"])
        d = [k for k in set(gml) | set(ny) if abs(gml.get(k, 0) - ny.get(k, 0)) > 0.5]
        dt = [k for k in set(gtot) | set(ntot) if abs(gtot.get(k, 0) - ntot.get(k, 0)) > 0.5]
        hard(not d and not dt, f"C3 Overlapp med {gammel} (1987–): {len(d)} celleavvik, {len(dt)} totalavvik {d[:5]}")
        # C6 struktur
        per_aar = defaultdict(set)
        sikk = defaultdict(Counter)
        for r in rows:
            if r["parti"] == "01":
                per_aar[int(r["aar"])].add(r["kom2024"])
                sikk[int(r["aar"])][r["sikkerhet"]] += 1
        logg("C6 Kommuner og sikkerhet per år (høy/middels/lav):")
        for a in aarliste:
            logg(f"    {a}: {len(per_aar[a])} kommuner, {dict(sikk[a])}")

    # C4 befolkning mot SSB 06913-aggregat
    logg("\n## befolkning_1951.csv\n")
    bef = {(r["kom2024"], int(r["aar"])): int(r["befolkning"]) for r in les("befolkning_1951.csv")}
    fas = {}
    for r in csv.DictReader(open(SSB / "bef06913_agg2024.csv", encoding="utf-8")):
        k, a = r["kom2024"], int(r["aar"])
        if len(k) == 4 and k.isdigit() and a <= 1985 and int(r["befolkning"]) > 0:
            fas[(k, a)] = int(r["befolkning"])
    like = sum(1 for k, v in fas.items() if bef.get(k) == v)
    nær = sum(1 for k, v in fas.items() if bef.get(k) and abs(bef[k] / v - 1) <= 0.02)
    logg(f"C4 {len(fas):,} kommune/år 1951–85 der SSB har tall: {like:,} eksakt like, {nær:,} innen ±2 %. "
         "Avvik skyldes at SSB fører delte områder på «Rest» og hele koder på én kommune, mens vi fordeler "
         "etter rapport 99/13.")
    store = sorted(((k, a, v, bef.get((k, a))) for (k, a), v in fas.items()
                    if bef.get((k, a)) and abs(bef[(k, a)] / v - 1) > 0.10), key=lambda x: x[1])
    logg(f"    Avvik > 10 %: {len(store)} kommune/år, i {len({s[0] for s in store})} kommuner: "
         + ", ".join(sorted({s[0] for s in store})))
    # C5 kontinuitet
    ks = sorted({k for k, _ in bef})
    hopp = []
    for k in ks:
        for a in range(1951, 1986):
            x, y = bef.get((k, a), 0), bef.get((k, a + 1), 0)
            if x > 0 and y > 0 and abs(y / x - 1) > 0.08:
                hopp.append((k, a, x, y, round(y / x - 1, 2)))
            elif (x > 0) != (y > 0):
                hopp.append((k, a, x, y, "null"))
    hard(not any(h[4] == "null" for h in hopp), f"C5 Ingen kommune forsvinner eller dukker opp 1951–1986")
    logg(f"C5 Hopp > 8 % år til år 1951–1986: {len(hopp)} (små kommuner med kraftutbygging/industri m.m.):")
    for h in sorted(hopp, key=lambda h: -abs(h[4]) if h[4] != "null" else -9):
        logg(f"    {h}")
    hard(len(ks) == 357, f"C6 357 kommuner i befolkningen ({len(ks)})")

    RAPPORT.parent.mkdir(parents=True, exist_ok=True)
    RAPPORT.write_text("# Automatiske kontroller 1945–2025\n\nGenerert av `scripts/kontroller_datasett_1945.py`.\n\n"
                       + "\n".join(ut) + f"\n\n**Harde feil: {len(feil)}**\n", encoding="utf-8")
    print(f"\nHarde feil: {len(feil)}")
    return 1 if feil else 0


if __name__ == "__main__":
    sys.exit(main())
