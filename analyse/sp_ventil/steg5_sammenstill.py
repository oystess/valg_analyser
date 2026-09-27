#!/usr/bin/env python3
"""Steg 5: sammenstill individdata fra agent L (SSB-tabell 11666/11659, Valgundersøkelsen) med aggregatresultatene.

Overgangsandelene (andel av avgiverpartiets velgere) gjøres om til prosentpoeng av velgerne ved å gange med partiets
landsoppslutning ved forrige valg. Dette er en tilnærming: ikke-stemmere, erindringsfeil og utvalgsusikkerhet er ikke tatt med.

Kjøring: python analyse/sp_ventil/steg5_sammenstill.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from felles import ARB

L = json.loads((ARB / "L_litteratur.json").read_text(encoding="utf-8"))
RES = json.loads((ARB / "resultater.json").read_text(encoding="utf-8"))
land = pd.read_csv(ARB / "landstall_st.csv", index_col=0)


def finn(id_):
    f = next(x for x in L["funn"] if x["id"] == id_)
    return float(str(f["tall"]).replace("%", "").replace(",", ".").strip()) / 100, f


ut = {"metode": __doc__.strip().splitlines()[2:4], "valg": {}}
for (t0, t1), (ap_sp, sp_ap, sp_frp) in {(2017, 2021): ("L02", "L08", "L14"), (2021, 2025): ("L18", "L24", "L30")}.items():
    a, fa = finn(ap_sp)
    b, fb = finn(sp_ap)
    c, fc = finn(sp_frp)
    ap0, sp0 = land.loc[t0, "ap"], land.loc[t0, "sp90"]
    brutto_ap_til_sp = a * ap0
    brutto_sp_til_ap = b * sp0
    netto_ap_til_sp = brutto_ap_til_sp - brutto_sp_til_ap
    d_sp = land.loc[t1, "sp90"] - land.loc[t0, "sp90"]
    ut["valg"][f"{t0}-{t1}"] = {
        "kilder": [fa["id"], fb["id"], fc["id"]],
        "ap_til_sp_andel_av_ap": a, "sp_til_ap_andel_av_sp": b, "sp_til_frp_andel_av_sp": c,
        "brutto_ap_til_sp_pp": round(brutto_ap_til_sp, 2), "brutto_sp_til_ap_pp": round(brutto_sp_til_ap, 2),
        "brutto_sp_til_frp_pp": round(c * sp0, 2),
        "netto_ap_til_sp_pp": round(netto_ap_til_sp, 2), "landsendring_sp_pp": round(d_sp, 2),
        "individ_netto_andel_av_sp_endring_fra_eller_til_ap": round(abs(netto_ap_til_sp / d_sp), 3),
    }
# Aggregatet: helning i distriktet og i sentrale kommuner (T1 for bølgen, T6 for tilbakefallet)
ut["valg"]["2017-2021"]["aggregat_andel_fra_ap_distrikt"] = -RES["T1"]["sp90"]["2017-2021"]["dekomponering_distrikt"]["ap"]
ut["valg"]["2017-2021"]["aggregat_andel_fra_ap_alle"] = -RES["T1"]["sp90"]["2017-2021"]["alle|bastion"]["b"]
for g in ("alle_distrikt", "distrikt_bastion_fast", "sentral"):
    ut["valg"]["2021-2025"][f"aggregat_andel_til_ap_{g}"] = RES["T6"]["2021-2025"][g]["andel_av_tap_til"]["ap"]
    ut["valg"]["2021-2025"][f"aggregat_andel_til_frp_{g}"] = RES["T6"]["2021-2025"][g]["andel_av_tap_til"]["frp"]
ut["partibyttere_nasjonalt_11665"] = [f["tall"] + " " + f["valg"] for f in L["funn"] if "11665" in json.dumps(f["kilde"])][:14]
(ARB / "individ_vs_aggregat.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(ut, ensure_ascii=False, indent=1))
