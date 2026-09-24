#!/usr/bin/env python3
"""
analyse/felles.py – Én kilde til sannhet for analysene.

Bygger turnering/data/panel.csv: én rad per 2024-kommune × valgperiode
(stortingsvalg t-1 → t), med utfall, nivåer og forklaringsvariabler målt ved
periodens start eller over perioden. Alle tellinger harmoniseres til 2024-kommuner
med data/processed/kodemapping_2024.csv (andeler for delte koder).

Kjøring: python analyse/felles.py
"""
import csv
import hashlib
import math
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SSB = PROJECT / "data" / "raw" / "ssb"
PROC = PROJECT / "data" / "processed"
UT = PROJECT / "turnering" / "data"

ST_AAR = [1989, 1993, 1997, 2001, 2005, 2009, 2013, 2017, 2021, 2025]
KV_AAR = [1987, 1991, 1995, 1999, 2003, 2007, 2011, 2015, 2019, 2023]
PARTI = {"01": "ap", "02": "frp", "03": "h", "04": "krf", "05": "sp",
         "06": "sv", "07": "v", "08": "mdg", "55": "rodt", "99": "andre"}
LANDSDEL = {"03": "Oslo/Akershus", "31": "Østlandet", "32": "Oslo/Akershus",
            "33": "Østlandet", "34": "Innlandet", "39": "Østlandet", "40": "Østlandet",
            "42": "Agder", "11": "Vestlandet", "46": "Vestlandet", "15": "Vestlandet",
            "50": "Trøndelag", "18": "Nord-Norge", "55": "Nord-Norge", "56": "Nord-Norge"}
FYLKE = {"03": "Oslo", "11": "Rogaland", "15": "Møre og Romsdal", "18": "Nordland",
         "31": "Østfold", "32": "Akershus", "33": "Buskerud", "34": "Innlandet",
         "39": "Vestfold", "40": "Telemark", "42": "Agder", "46": "Vestland",
         "50": "Trøndelag", "55": "Troms", "56": "Finnmark"}


def les_mapping():
    m = defaultdict(dict)
    for r in csv.DictReader(open(PROC / "kodemapping_2024.csv", encoding="utf-8")):
        m[(r["kode"], int(r["aar"]))][r["kom2024"]] = float(r["andel"])
    return m


def harmoniser(rader, m, stat):
    """rader: iterable av (kode, aar, verdi) -> {(kom, aar): sum}. Logger ukartlagte."""
    ut = defaultdict(float)
    ukartlagt = defaultdict(float)
    for kode, aar, v in rader:
        mål = m.get((kode, aar)) or m.get((kode, aar + 1)) or m.get((kode, aar - 1))
        if not mål:
            ukartlagt[aar] += v
            continue
        for kom, andel in mål.items():
            ut[(kom, aar)] += v * andel
    if ukartlagt:
        stat[f"ukartlagt"] = {a: round(v) for a, v in sorted(ukartlagt.items()) if v}
    return ut


def les_lang(fil, filtre, verdifelt="verdi"):
    for r in csv.DictReader(open(SSB / fil, encoding="utf-8")):
        if all(r[k] in v for k, v in filtre.items()):
            yield r


def bygg_kovariater(m, logg):
    kov = defaultdict(dict)   # (kom, aar) -> {var: verdi}

    # Befolkning (total og aldersgrupper). agg_Funksjonell6a:
    # F340 0-15, F341 16-18, F342 19-34, F343 35-66, F344 67-74, F345 75+
    grupper = {"F340": "a0_15", "F341": "a16_18", "F342": "a19_34", "F343": "a35_66",
               "F344": "a67_74", "F345": "a75p"}
    for g, navn in grupper.items():
        st = {}
        h = harmoniser(((r["kode"], int(r["aar"]), float(r["verdi"]))
                        for r in les_lang("bef07459_alder_kommuner.csv", {"alder": {g}})), m, st)
        for k, v in h.items():
            kov[k][navn] = v
        if st:
            logg.append(f"alder {g}: {st}")
    for k, d in kov.items():
        tot = sum(d.get(n, 0) for n in grupper.values())
        d["bef"] = tot
        if tot:
            d["andel_67p"] = (d.get("a67_74", 0) + d.get("a75p", 0)) / tot * 100
            d["andel_19_34"] = d.get("a19_34", 0) / tot * 100

    # Fødselsoverskudd og nettoinnflytting (tellinger per kalenderår)
    for var in ("Fodselsoverskudd", "Nettoinnflytting"):
        st = {}
        h = harmoniser(((r["kode"], int(r["aar"]), float(r["verdi"]))
                        for r in les_lang("flytt06913_kommuner.csv", {"variabel": {var}})), m, st)
        for k, v in h.items():
            kov[k][var.lower()] = v
        logg.append(f"{var}: ukartlagt {st.get('ukartlagt', {})}")

    # Utdanning 16+: andel med universitets-/høgskoleutdanning
    st = {}
    tot = harmoniser(((r["kode"], int(r["aar"]), float(r["verdi"]))
                      for r in les_lang("utd09429_kommuner.csv", {"nivaa": {"00"}, "kjonn": {"0"}})), m, st)
    hoy = harmoniser(((r["kode"], int(r["aar"]), float(r["verdi"]))
                      for r in les_lang("utd09429_kommuner.csv", {"nivaa": {"03a", "04a"}, "kjonn": {"0"}})), m, {})
    logg.append(f"utdanning: ukartlagt {st.get('ukartlagt', {})}")
    for k, t in tot.items():
        if t:
            kov[k]["andel_hoyutd"] = hoy.get(k, 0) / t * 100

    # Inntekt: median inntekt etter skatt, alle husholdninger (2005–). For sammenslåtte
    # kommuner: husholdningsvektet snitt av medianene (tilnærming, merkes i datadictionary).
    med = {}
    ant = {}
    for r in les_lang("innt06944_kommuner.csv", {"husholdtype": {"0000"}}):
        key = (r["kode"], int(r["aar"]))
        (med if r["variabel"] == "InntSkatt" else ant)[key] = float(r["verdi"])
    vekt = defaultdict(float)
    sumv = defaultdict(float)
    for key, v in med.items():
        a = ant.get(key)
        mål = m.get(key) or m.get((key[0], key[1] + 1)) or m.get((key[0], key[1] - 1))
        if not a or not mål:
            continue
        for kom, andel in mål.items():
            vekt[(kom, key[1])] += a * andel
            sumv[(kom, key[1])] += v * a * andel
    for k, w in vekt.items():
        kov[k]["inntekt_median"] = sumv[k] / w

    # Sysselsatte etter bosted (4. kvartal, 2008–): næringsandeler
    naering = {"00-99": "syss", "01-03": "syss_primaer", "10-33": "syss_industri",
               "84": "syss_offadm", "85": "syss_undervisning", "86-88": "syss_helse"}
    for kode_n, navn in naering.items():
        h = harmoniser(((r["kode"], int(r["aar"]), float(r["verdi"]))
                        for r in les_lang("syss07984_kommuner.csv", {"naering": {kode_n}})), m, {})
        for k, v in h.items():
            kov[k][navn] = v
    for k, d in kov.items():
        if d.get("syss"):
            d["andel_primaer"] = d.get("syss_primaer", 0) / d["syss"] * 100
            d["andel_industri"] = d.get("syss_industri", 0) / d["syss"] * 100
            d["andel_offentlig"] = (d.get("syss_offadm", 0) + d.get("syss_undervisning", 0)
                                    + d.get("syss_helse", 0)) / d["syss"] * 100
    return kov


def les_valg(fil):
    v = defaultdict(dict)
    for r in csv.DictReader(open(PROC / fil, encoding="utf-8")):
        key = (r["kom2024"], int(r["aar"]))
        p = PARTI[r["parti"]]
        v[key][p] = float(r["prosent"]) if r["prosent"] else float("nan")
        v[key]["total"] = float(r["total_stemmer"])
        v[key]["estimert"] = r["estimert"] == "True"
        v[key]["navn"] = r["navn"]
    return v


def bygg_panel():
    m = les_mapping()
    logg = []
    kov = bygg_kovariater(m, logg)
    st = les_valg("stortingsvalg_2024.csv")
    kv = les_valg("kommunestyrevalg_2024.csv")
    sent = {r["kom2024"]: r for r in csv.DictReader(open(PROC / "sentralitet_2024.csv", encoding="utf-8"))}
    kommuner = sorted({k for k, _ in st})

    def g(kom, aar, var):
        return kov.get((kom, aar), {}).get(var, float("nan"))

    rader = []
    for i in range(1, len(ST_AAR)):
        t0, t1 = ST_AAR[i - 1], ST_AAR[i]
        k0, k1 = KV_AAR[i - 1], KV_AAR[i]      # kommunevalgperioden som slutter 2 år før t1
        for kom in kommuner:
            a, b = st[(kom, t0)], st[(kom, t1)]
            bef0, bef1 = g(kom, t0, "bef"), g(kom, t1, "bef")
            bef10 = g(kom, t1 - 10, "bef")
            # flytting og fødselsoverskudd summert over årene t0 … t1-1, per 1000 innb. ved start
            netto = sum(g(kom, y, "nettoinnflytting") for y in range(t0, t1))
            fodsel = sum(g(kom, y, "fodselsoverskudd") for y in range(t0, t1))
            r = {
                "kom2024": kom, "navn": a["navn"], "periode": f"{t0}-{t1}", "t0": t0, "t1": t1,
                "fylke": FYLKE[kom[:2]], "landsdel": LANDSDEL[kom[:2]],
                "sent_klasse": int(sent[kom]["sent_klasse"]), "sent_indeks": int(sent[kom]["sent_indeks"]),
                "estimert": a["estimert"] or b["estimert"],
                "vekt_stemmer_t0": a["total"],
            }
            for p in PARTI.values():
                r[f"{p}_t0"] = a[p]
                r[f"{p}_t1"] = b[p]
                r[f"d_{p}"] = b[p] - a[p]
            r["d_sp_frp"] = r["d_sp"] + r["d_frp"]
            # kommunevalg (robusthet): KV i samme fireårsvindu (k0 → k1)
            r["kv_sp_t0"] = kv[(kom, k0)]["sp"]
            r["kv_d_sp"] = kv[(kom, k1)]["sp"] - kv[(kom, k0)]["sp"]
            r["bef_t0"] = bef0
            r["ln_bef_t0"] = math.log(bef0) if bef0 and bef0 > 0 else float("nan")
            r["vekst4_pst"] = (bef1 / bef0 - 1) * 100 if bef0 else float("nan")
            r["vekst10_pst"] = (bef1 / bef10 - 1) * 100 if bef10 == bef10 and bef10 else float("nan")
            r["nettoinnfl_per1000"] = netto / bef0 * 1000 if bef0 else float("nan")
            r["fodselsovsk_per1000"] = fodsel / bef0 * 1000 if bef0 else float("nan")
            r["andel_67p_t0"] = g(kom, t0, "andel_67p")
            r["andel_19_34_t0"] = g(kom, t0, "andel_19_34")
            r["d_andel_67p"] = g(kom, t1, "andel_67p") - g(kom, t0, "andel_67p")
            r["andel_hoyutd_t0"] = g(kom, t0 - 1, "andel_hoyutd")
            r["inntekt_median_t0"] = g(kom, max(t0 - 1, 2005), "inntekt_median") if t0 >= 2005 else float("nan")
            r["andel_primaer_t0"] = g(kom, max(t0 - 1, 2008), "andel_primaer") if t0 >= 2009 else float("nan")
            r["andel_industri_t0"] = g(kom, max(t0 - 1, 2008), "andel_industri") if t0 >= 2009 else float("nan")
            r["andel_offentlig_t0"] = g(kom, max(t0 - 1, 2008), "andel_offentlig") if t0 >= 2009 else float("nan")
            rader.append(r)

    UT.mkdir(parents=True, exist_ok=True)
    felt = list(rader[0].keys())
    with open(UT / "panel.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=felt)
        w.writeheader()
        for r in rader:
            w.writerow({k: ("" if isinstance(v, float) and v != v else
                            (round(v, 4) if isinstance(v, float) else v)) for k, v in r.items()})
    h = hashlib.sha256((UT / "panel.csv").read_bytes()).hexdigest()
    print(f"panel.csv: {len(rader)} rader, {len(felt)} kolonner, sha256 {h[:16]}")
    for l in logg:
        print("  ", l)
    return rader, h


if __name__ == "__main__":
    bygg_panel()
