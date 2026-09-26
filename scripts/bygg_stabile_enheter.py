#!/usr/bin/env python3
"""
bygg_stabile_enheter.py – Slår sammen 2024-kommuner som har delt områder med hverandre
1945–2025, slik at hver enhet har samme grenser hele perioden og ingen stemmer må fordeles.

To 2024-kommuner havner i samme enhet hvis en historisk kode noen gang er fordelt på begge med
minst TERSKEL (5 %) av kodens befolkning på hver (kodemapping_1945.csv og kodemapping_2024.csv).
Mindre deler (små grenseendringer) kobler ikke kommunene; i den stabile filen følger de da
fordelingen i hovedfilen, så estimatet for disse små områdene gjenstår.

Utdata: data/processed/stabile_enheter.csv (kom2024, enhet, enhet_navn, n_kommuner)
        data/processed/stortingsvalg_1945_stabil.csv, kommunestyrevalg_1945_stabil.csv
        (enhet, enhet_navn, aar, parti, stemmer, total_stemmer, prosent)
"""
import csv
from collections import defaultdict
from pathlib import Path

PROC = Path(__file__).resolve().parent.parent / "data" / "processed"
TERSKEL = 0.05


def main():
    forelder = {}

    def finn(x):
        forelder.setdefault(x, x)
        while forelder[x] != x:
            forelder[x] = forelder[forelder[x]]
            x = forelder[x]
        return x

    def slå_sammen(a, b):
        forelder[finn(a)] = finn(b)

    per_kode = defaultdict(set)
    for fil in ("kodemapping_1945.csv", "kodemapping_2024.csv"):
        for r in csv.DictReader(open(PROC / fil, encoding="utf-8")):
            if float(r["andel"]) >= TERSKEL:
                per_kode[(fil, r["kode"], r["aar"])].add(r["kom2024"])
            finn(r["kom2024"])
    for koms in per_kode.values():
        koms = sorted(koms)
        for k in koms[1:]:
            slå_sammen(koms[0], k)
    navn = {}
    for r in csv.DictReader(open(PROC / "befolkning_2024.csv", encoding="utf-8")):
        navn[r["kom2024"]] = r["navn"]
    grupper = defaultdict(list)
    for k in list(forelder):
        grupper[finn(k)].append(k)
    enhet = {}
    rows = []
    for rot, koms in grupper.items():
        koms = sorted(koms)
        eid = koms[0] if len(koms) == 1 else "E" + koms[0]
        en = " + ".join(navn.get(k, k) for k in koms)
        for k in koms:
            enhet[k] = (eid, en)
            rows.append({"kom2024": k, "enhet": eid, "enhet_navn": en, "n_kommuner": len(koms)})
    with open(PROC / "stabile_enheter.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kom2024", "enhet", "enhet_navn", "n_kommuner"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["enhet"], r["kom2024"])))
    n_enh = len(grupper)
    print(f"{len(rows)} kommuner -> {n_enh} stabile enheter "
          f"({sum(1 for g in grupper.values() if len(g) > 1)} sammenslåtte)")
    for inn, ut in (("stortingsvalg_1945.csv", "stortingsvalg_1945_stabil.csv"),
                    ("kommunestyrevalg_1945.csv", "kommunestyrevalg_1945_stabil.csv")):
        st, tot = defaultdict(float), {}
        tot_k = defaultdict(float)
        for r in csv.DictReader(open(PROC / inn, encoding="utf-8")):
            e = enhet[r["kom2024"]]
            st[(e, r["aar"], r["parti"])] += float(r["stemmer"])
            tot_k[(e, r["aar"], r["kom2024"])] = float(r["total_stemmer"])
        for (e, a, k), v in tot_k.items():
            tot[(e, a)] = tot.get((e, a), 0) + v
        out = [{"enhet": e[0], "enhet_navn": e[1], "aar": a, "parti": p, "stemmer": round(v, 2),
                "total_stemmer": round(tot[(e, a)], 2),
                "prosent": round(v / tot[(e, a)] * 100, 2) if tot[(e, a)] else ""}
               for (e, a, p), v in sorted(st.items())]
        with open(PROC / ut, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["enhet", "enhet_navn", "aar", "parti", "stemmer",
                                              "total_stemmer", "prosent"])
            w.writeheader()
            w.writerows(out)
        print(f"{ut}: {len(out):,} rader")


if __name__ == "__main__":
    main()
