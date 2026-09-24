#!/usr/bin/env python3
"""
bygg_datasett.py – Bygger valg- og befolkningsdatasettet på 2024-kommunestruktur.

Erstatter hent_data.py (som leste fra en midlertidig sesjonsmappe, koblet koder
på navn og dobbeltlastet 1989). Alt leses nå fra rådata i repoet:

  data/raw/ssb/st08092_<år>.csv   SSB 08092 Stortingsvalg, alle partier, alle historiske koder
  data/raw/ssb/kv01180_<år>.csv   SSB 01180 Kommunestyrevalg, alle partier/lister
  data/raw/ssb/bef07459_*.csv     SSB 07459 Befolkning 1.1., per historisk kode og SSBs 2024-aggregat
  data/raw/ssb/koder_*.csv        Kodelister med navn og gyldighetsperiode
  data/processed/kodemapping_2024.csv  fra scripts/bygg_kodemapping.py

Utdata (data/processed/):
  stortingsvalg_2024.csv, kommunestyrevalg_2024.csv
      kom2024, navn, aar, parti, stemmer, total_stemmer, prosent,
      sum_9parti, prosent_9parti, dekning, estimert
    parti: 01 Ap, 02 FrP, 03 H, 04 KrF, 05 Sp, 06 SV, 07 V, 08 MDG,
           55 Rødt (inkl. RV 1973–2007 og Fylkeslistene for miljø og solidaritet 1989),
           99 Andre (alle øvrige partier og lokale lister)
    total_stemmer = alle godkjente stemmer (SSBs nevner). prosent = stemmer/total_stemmer.
    sum_9parti/prosent_9parti = gammel definisjon (sum av de 9 partiene) for sammenligning.
    dekning = andel av kommunens befolkning (1.1. valgåret) som bor i historiske kommuner
      med registrerte partistemmer. < 1 betyr at deler av 2024-kommunen hadde flertallsvalg
      (personvalg) i kommunevalget, eller manglet data.
    estimert = True hvis stemmer fra en delt kommune er fordelt etter befolkningsandel.
  befolkning_2024.csv   kom2024, navn, aar, befolkning (1.1. hvert år)
  sentralitet_2024.csv  kom2024, sent_kode, sent_navn, n_kilder, konflikt
  kom_mapping.csv       gammelt_nr, navn, start_yr, end_yr, nr_2024 (bakoverkompatibel:
                        for delte koder er største mottaker oppgitt)

Bruk: python scripts/bygg_datasett.py
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
SSB = RAW / "ssb"
OUT = PROJECT / "data" / "processed"

ST_AAR = [1989, 1993, 1997, 2001, 2005, 2009, 2013, 2017, 2021, 2025]
KV_AAR = [1987, 1991, 1995, 1999, 2003, 2007, 2011, 2015, 2019, 2023]

PARTI_GRUPPE = {
    "01": "01", "02": "02", "03": "03", "04": "04", "05": "05",
    "06": "06", "07": "07", "08": "08",
    "55": "55",  # Rødt (2007–)
    "11": "55",  # Rød Valgallianse (1973–2007)
    "15": "55",  # Fylkeslistene for miljø og solidaritet (RVs liste ved stortingsvalget 1989)
}
NI_PARTIER = ["01", "02", "03", "04", "05", "06", "07", "08", "55"]
ANDRE = "99"


def les_etiketter():
    lab = {}
    for f in ("koder_07459", "koder_08092", "koder_01180"):
        for r in csv.DictReader(open(SSB / f"{f}.csv", encoding="utf-8")):
            lab.setdefault(r["kode"], r["etikett"])
    return lab


def dagens_navn(lab, kode):
    return re.sub(r"\s*\((\d{4})?-(\d{4})?\)$", "", lab.get(kode, "")).strip()


def les_mapping():
    """(kode, aar) -> {kom2024: andel}, og (kode, aar) -> estimert?"""
    m = defaultdict(dict)
    est = {}
    for r in csv.DictReader(open(OUT / "kodemapping_2024.csv", encoding="utf-8")):
        key = (r["kode"], int(r["aar"]))
        m[key][r["kom2024"]] = float(r["andel"])
        est[key] = est.get(key, False) or r["metode"].startswith("delt")
    return m, est


def les_befolkning():
    pop = defaultdict(dict)
    for r in csv.DictReader(open(SSB / "bef07459_kommuner.csv", encoding="utf-8")):
        v = int(r["befolkning"])
        if v > 0:
            pop[int(r["aar"])][r["kode"]] = v
    return pop


def bygg_valg(prefix, aarliste, mapping, est, pop, lab):
    rows = []
    for aar in aarliste:
        stemmer = defaultdict(float)       # (kom, gruppe) -> stemmer
        total = defaultdict(float)         # kom -> alle godkjente
        med_stemmer = set()                # historiske koder med stemmer
        estimert = defaultdict(bool)
        neste_aar_koder = set()
        for r in csv.DictReader(open(SSB / f"{prefix}_{aar}.csv", encoding="utf-8")):
            kode, parti = r["Region"], r["PolitParti"]
            v = int(r[f"Godkjente1 {aar}"])
            if v == 0:
                continue
            # Kommunestyrevalg holdes for kommunestrukturen som gjelder fra 1.1. året etter
            # (f.eks. KV 1987 for nye Larvik 1988, KV 2019 for 2020-kommunene).
            key = (kode, aar) if (kode, aar) in mapping else (kode, aar + 1)
            if key not in mapping:
                raise SystemExit(f"FEIL: {prefix} {aar}: kode {kode} mangler i kodemapping")
            if key[1] != aar:
                neste_aar_koder.add(kode)
            med_stemmer.add(kode)
            gruppe = PARTI_GRUPPE.get(parti, ANDRE)
            for kom, andel in mapping[key].items():
                stemmer[(kom, gruppe)] += v * andel
                total[kom] += v * andel
                estimert[kom] |= est[key]
        if neste_aar_koder:
            print(f"  {prefix} {aar}: {len(neste_aar_koder)} koder med struktur fra {aar + 1}: "
                  f"{' '.join(sorted(neste_aar_koder))}")
        # dekning: andel av befolkningen (1.1. valgåret, eller 1.1. året etter når valget
        # gjaldt ny struktur) i koder med stemmer
        bef_tot, bef_med = defaultdict(float), defaultdict(float)
        bef_aar = aar + 1 if neste_aar_koder else aar
        for kode, p in pop[bef_aar].items():
            for kom, andel in mapping.get((kode, bef_aar), {}).items():
                bef_tot[kom] += p * andel
                # En kode som opphører ved årsskiftet, stemte i kommunevalget som del av
                # den nye kommunen (f.eks. Frei i Kristiansund ved KV 2007).
                opphører = prefix == "kv01180" and kode not in pop.get(bef_aar + 1, {})
                if kode in med_stemmer or opphører:
                    bef_med[kom] += p * andel
        for kom in sorted(bef_tot):
            tot = total.get(kom, 0.0)
            s9 = sum(stemmer.get((kom, g), 0.0) for g in NI_PARTIER)
            dekning = bef_med[kom] / bef_tot[kom] if bef_tot[kom] else 0.0
            for g in NI_PARTIER + [ANDRE]:
                v = stemmer.get((kom, g), 0.0)
                rows.append({
                    "kom2024": kom, "navn": dagens_navn(lab, kom), "aar": aar, "parti": g,
                    "stemmer": round(v, 2) if estimert[kom] else int(round(v)),
                    "total_stemmer": round(tot, 2) if estimert[kom] else int(round(tot)),
                    "prosent": round(v / tot * 100, 2) if tot > 0 else "",
                    "sum_9parti": round(s9, 2) if estimert[kom] else int(round(s9)),
                    "prosent_9parti": round(v / s9 * 100, 2) if s9 > 0 and g != ANDRE else "",
                    "dekning": round(dekning, 4),
                    "estimert": estimert[kom],
                })
    return rows


def bygg_befolkning(mapping, pop, lab):
    agg = defaultdict(float)
    for aar, koder in pop.items():
        for kode, p in koder.items():
            for kom, andel in mapping.get((kode, aar), {}).items():
                agg[(kom, aar)] += p * andel
    return [{"kom2024": k, "navn": dagens_navn(lab, k), "aar": a, "befolkning": int(round(v))}
            for (k, a), v in sorted(agg.items())]


def bygg_sentralitet(mapping, pop):
    """sentralitet.csv har pre-2020-koder (428 kommuner). Til 2024-kommune: klassen til den
    delen med flest innbyggere (1.1.2019). Konflikt markeres når delene har ulik klasse."""
    rader = list(csv.reader(open(RAW / "sentralitet.csv", encoding="latin1"), delimiter=";"))[1:]
    navn = {}
    per_kom = defaultdict(list)
    for kode_s, navn_s, kode, _ in rader:
        navn[kode_s] = navn_s
        kode = kode.zfill(4)
        for aar in (2019, 2017, 2016):
            if (kode, aar) in mapping:
                p = pop[aar].get(kode, 0)
                for kom, andel in mapping[(kode, aar)].items():
                    per_kom[kom].append((p * andel, kode_s, kode))
                break
    out = []
    for kom, deler in sorted(per_kom.items()):
        deler.sort(reverse=True)
        klasser = {d[1] for d in deler}
        out.append({"kom2024": kom, "sent_kode": deler[0][1], "sent_navn": navn[deler[0][1]],
                    "n_kilder": len(deler), "konflikt": len(klasser) > 1})
    return out


def bygg_kom_mapping(mapping, lab):
    """Bakoverkompatibel kom_mapping.csv (én rad per kode, største mottaker)."""
    best = {}
    for (kode, aar), mål in mapping.items():
        kom, andel = max(mål.items(), key=lambda x: x[1])
        if kode not in best or aar > best[kode][0]:
            best[kode] = (aar, kom)
    rows = []
    for kode, (_, kom) in sorted(best.items()):
        etikett = lab.get(kode, "")
        m = re.search(r"\((\d{4})?-(\d{4})?\)$", etikett)
        rows.append({"gammelt_nr": kode, "navn": dagens_navn(lab, kode),
                     "start_yr": (m.group(1) or "") if m else "",
                     "end_yr": (m.group(2) or "") if m else "", "nr_2024": kom})
    return rows


def skriv(rows, navn, felt):
    with open(OUT / navn, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=felt)
        w.writeheader()
        w.writerows(rows)
    print(f"  {navn}: {len(rows):,} rader")


def main():
    lab = les_etiketter()
    mapping, est = les_mapping()
    pop = les_befolkning()
    felt = ["kom2024", "navn", "aar", "parti", "stemmer", "total_stemmer", "prosent",
            "sum_9parti", "prosent_9parti", "dekning", "estimert"]
    skriv(bygg_valg("st08092", ST_AAR, mapping, est, pop, lab), "stortingsvalg_2024.csv", felt)
    skriv(bygg_valg("kv01180", KV_AAR, mapping, est, pop, lab), "kommunestyrevalg_2024.csv", felt)
    skriv(bygg_befolkning(mapping, pop, lab), "befolkning_2024.csv",
          ["kom2024", "navn", "aar", "befolkning"])
    skriv(bygg_sentralitet(mapping, pop), "sentralitet_2024.csv",
          ["kom2024", "sent_kode", "sent_navn", "n_kilder", "konflikt"])
    skriv(bygg_kom_mapping(mapping, lab), "kom_mapping.csv",
          ["gammelt_nr", "navn", "start_yr", "end_yr", "nr_2024"])


if __name__ == "__main__":
    main()
