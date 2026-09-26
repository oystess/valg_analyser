#!/usr/bin/env python3
"""
bygg_datasett_1945.py – Valg 1945–2025 og befolkning 1951–2026 på 2024-kommuner.

Bygger videre på bygg_datasett.py (1987–2025) og bygg_kodemapping_1945.py (1945–1985).
Hele tidsserien regnes med samme partigrupper, slik at 1945 og 2025 er sammenlignbare:

  01 Ap, 02 FrP (inkl. Anders Langes parti 1973), 03 H, 04 KrF,
  05 Sp (inkl. Bondepartiet), 06 SV (inkl. Sosialistisk Folkeparti 1961–69), 07 V,
  08 MDG, 55 Rødt (inkl. RV og FMS), 09 NKP, 90 Felleslister (90a–90h, og 90 i KV),
  99 Andre

Kodeidentitet før 1986: grunnkoden (fire sifre) + året avgjør hvilken kommune koden var.
Kommunestyrevalg før en strukturendring ble holdt for den nye strukturen (f.eks. KV 1963 for
1964-kommunene). For hvert valgår velges derfor strukturåret (valgåret eller året etter) som
flest av valgets koder finnes i.

Utdata (data/processed/):
  stortingsvalg_1945.csv, kommunestyrevalg_1945.csv
     kom2024, navn, aar, parti, stemmer, total_stemmer, prosent, estimert, sikkerhet
     sikkerhet: 'høy'     = 1986–, eller kommunens befolkning i strukturåret er nøyaktig lik
                            SSBs «Kommuner 2024, sammenslåtte tidsserier» (06913)
                'middels' = 1951–1985 der SSB ikke har tall eller tallet avviker (delinger fordelt
                            etter rapport 99/13, eller SSB fører deler på «Rest»)
                'lav'     = 1945–1950: 1951-struktur uten befolkningstall
  befolkning_1951.csv   kom2024, navn, aar, befolkning (1951–2026)
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bygg_datasett import les_etiketter, dagens_navn  # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
SSB = PROJECT / "data" / "raw" / "ssb"
PROC = PROJECT / "data" / "processed"

ST_AAR = [1945, 1949, 1953, 1957, 1961, 1965, 1969, 1973, 1977, 1981, 1985,
          1989, 1993, 1997, 2001, 2005, 2009, 2013, 2017, 2021, 2025]
KV_AAR = [1945, 1947, 1951, 1955, 1959, 1963, 1967, 1971, 1975, 1979, 1983,
          1987, 1991, 1995, 1999, 2003, 2007, 2011, 2015, 2019, 2023]
GRUPPE = {"01": "01", "02": "02", "75": "02", "03": "03", "04": "04", "05": "05", "71": "05",
          "06": "06", "70": "06", "07": "07", "08": "08", "55": "55", "11": "55", "15": "55",
          "09": "09"}
GRUPPER = ["01", "02", "03", "04", "05", "06", "07", "08", "55", "09", "90", "99"]
ALIAS_06913 = {"0903": "0906", "2001": "2004"}


def gruppe(p):
    if p.startswith("90"):
        return "90"
    return GRUPPE.get(p, "99")


def grunnkode(k):
    return re.sub(r"[^0-9]", "", k)[:4]


def main():
    lab = les_etiketter()
    pop06 = defaultdict(dict)
    for r in csv.DictReader(open(SSB / "bef06913_kommuner.csv", encoding="utf-8")):
        v = int(r["befolkning"])
        if v > 0:
            pop06[int(r["aar"])][r["kode"]] = v
    m45 = defaultdict(dict)
    met45 = {}
    for r in csv.DictReader(open(PROC / "kodemapping_1945.csv", encoding="utf-8")):
        k = (r["kode"], int(r["aar"]))
        m45[k][r["kom2024"]] = float(r["andel"])
        met45[k] = r["metode"]
    m24 = defaultdict(dict)
    met24 = {}
    for r in csv.DictReader(open(PROC / "kodemapping_2024.csv", encoding="utf-8")):
        k = (r["kode"], int(r["aar"]))
        m24[k][r["kom2024"]] = float(r["andel"])
        met24[k] = r["metode"]

    def ident(g, aar):
        if aar < 1951:
            return g if (g, aar) in m45 else None
        kand = [k for k in pop06.get(aar, {}) if grunnkode(k) == g]
        if not kand and g in ALIAS_06913:
            kand = [k for k in pop06.get(aar, {}) if grunnkode(k) == ALIAS_06913[g]]
        return kand[0] if len(kand) == 1 else None

    def oppslag(kode, aar):
        """(andeler, sikkerhet, estimert) for valgkode i strukturår aar."""
        if aar >= 1986:
            key = (kode, aar)
            if key not in m24:
                return None
            est = met24[key].startswith("delt")
            return m24[key], "høy", est
        g = grunnkode(kode)
        i = ident(g, aar)
        if i is None or (i, aar) not in m45:
            return None
        met = met45[(i, aar)]
        sikk = "lav" if aar < 1951 else ("middels" if "rapport" in met else "høy")
        return m45[(i, aar)], sikk, len(m45[(i, aar)]) > 1

    rang = {"høy": 0, "middels": 1, "lav": 2}
    agg06 = {}
    for r in csv.DictReader(open(SSB / "bef06913_agg2024.csv", encoding="utf-8")):
        if len(r["kom2024"]) == 4 and r["kom2024"].isdigit():
            agg06[(r["kom2024"], int(r["aar"]))] = int(r["befolkning"])
    harm = defaultdict(float)
    for (kode, a), andeler in m45.items():
        if a >= 1951:
            for kom, x in andeler.items():
                harm[(kom, a)] += pop06[a].get(kode, 0) * x

    def sikkerhet(kom, s):
        if s >= 1986:
            return "høy"
        if s < 1951:
            return "lav"
        f = agg06.get((kom, s), 0)
        return "høy" if f > 0 and round(harm[(kom, s)]) == f else "middels"
    for prefix, aarliste, ut in (("st08092", ST_AAR, "stortingsvalg_1945.csv"),
                                 ("kv01180", KV_AAR, "kommunestyrevalg_1945.csv")):
        rows, logg = [], []
        for aar in aarliste:
            data = [(r["Region"], r["PolitParti"], int(r[f"Godkjente1 {aar}"]))
                    for r in csv.DictReader(open(SSB / f"{prefix}_{aar}.csv", encoding="utf-8"))]
            koder = {k for k, _, _ in data}
            # strukturår: valgåret eller året etter, det som flest koder passer i
            kandidater = [aar, aar + 1] if prefix == "kv01180" else [aar]
            treff = {s: sum(1 for k in koder if oppslag(k, s)) for s in kandidater}
            struktur = max(kandidater, key=lambda s: (treff[s], -s))
            # Før 1986: numre er gjenbrukt, så treff avgjør ikke. Har ingen av kommunene som ble
            # nedlagt ved årsskiftet stemmer, gjaldt valget den nye strukturen (f.eks. KV 1963).
            if prefix == "kv01180" and 1951 <= aar < 1986:
                nr_y = {grunnkode(c) for c in pop06[aar]}
                nr_y1 = {grunnkode(c) for c in pop06[aar + 1]}
                forsvant = nr_y - nr_y1
                if forsvant and not ({grunnkode(k) for k in koder} & forsvant):
                    struktur = aar + 1
            st = defaultdict(float)
            tot = defaultdict(float)
            sikk = {}
            est = defaultdict(bool)
            uten = defaultdict(int)
            for kode, parti, v in data:
                o = oppslag(kode, struktur) or next((oppslag(kode, s) for s in (aar, aar + 1, aar - 1)
                                                     if oppslag(kode, s)), None)
                if o is None:
                    uten[kode] += v
                    continue
                andeler, sk, e = o
                g = gruppe(parti)
                for kom, a in andeler.items():
                    st[(kom, g)] += v * a
                    tot[kom] += v * a
                    sikk[kom] = max(sikk.get(kom, "høy"), sikkerhet(kom, struktur), key=lambda x: rang[x])
                    est[kom] |= e
            logg.append((aar, struktur, len(koder), dict(uten)))
            for kom in sorted(tot):
                for g in GRUPPER:
                    v = st.get((kom, g), 0.0)
                    rows.append({"kom2024": kom, "navn": dagens_navn(lab, kom), "aar": aar, "parti": g,
                                 "stemmer": round(v, 2), "total_stemmer": round(tot[kom], 2),
                                 "prosent": round(v / tot[kom] * 100, 2) if tot[kom] else "",
                                 "estimert": est[kom], "sikkerhet": sikk[kom]})
        with open(PROC / ut, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["kom2024", "navn", "aar", "parti", "stemmer",
                                              "total_stemmer", "prosent", "estimert", "sikkerhet"])
            w.writeheader()
            w.writerows(rows)
        print(f"{ut}: {len(rows):,} rader")
        for aar, s, n, u in logg:
            if u or s != aar:
                print(f"   {aar}: strukturår {s}, {n} koder" + (f", UTEN OVERSETTING: {u}" if u else ""))

    # Befolkning 1951–1985 (06913) + 1986– (eksisterende)
    b = defaultdict(float)
    for (kode, aar), andeler in m45.items():
        if aar >= 1951:
            for kom, a in andeler.items():
                b[(kom, aar)] += pop06[aar].get(kode, 0) * a
    rows = [{"kom2024": k, "navn": dagens_navn(lab, k), "aar": a, "befolkning": int(round(v))}
            for (k, a), v in sorted(b.items())]
    for r in csv.DictReader(open(PROC / "befolkning_2024.csv", encoding="utf-8")):
        rows.append(r)
    with open(PROC / "befolkning_1951.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kom2024", "navn", "aar", "befolkning"])
        w.writeheader()
        w.writerows(rows)
    print(f"befolkning_1951.csv: {len(rows):,} rader")


if __name__ == "__main__":
    main()
