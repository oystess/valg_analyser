#!/usr/bin/env python3
"""Steg 1–2: bygg analysepanelet, skriv datadictionary.md, beregn nasjonale Sp-bølger/tilbakefall og lås i låst.json.

Kjøring: python analyse/sp_ventil/steg1_panel_laas.py
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from felles import (ARB, UT, BASTION_GRENSE, DISTRIKT_KLASSER, FAST_BASTION_AAR, FORSTE_TESTAAR,
                    LOKAL_BOLGE_PP, NASJ_BOLGE_PP, bygg_panel)

ARB.mkdir(parents=True, exist_ok=True)
panel, land = bygg_panel()
panel_kv, land_kv = bygg_panel("kommunestyrevalg_1945.csv")
panel_st, _ = bygg_panel("stortingsvalg_1945_stabil.csv", stabil=True)
f = ARB / "panel.csv"
panel.to_csv(f, index=False, float_format="%.4f")
panel_kv.to_csv(ARB / "panel_kv.csv", index=False, float_format="%.4f")
panel_st.to_csv(ARB / "panel_stabil.csv", index=False, float_format="%.4f")
land.to_csv(ARB / "landstall_st.csv", float_format="%.4f")
land_kv.to_csv(ARB / "landstall_kv.csv", float_format="%.4f")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# Nasjonale bølger og tilbakefall
aar = list(land.index)
nasj = []
for i in range(1, len(aar)):
    t0, t1 = aar[i - 1], aar[i]
    nasj.append({"par": f"{t0}-{t1}", "d_sp": round(land.loc[t1, "sp"] - land.loc[t0, "sp"], 2),
                 "d_sp90": round(land.loc[t1, "sp90"] - land.loc[t0, "sp90"], 2),
                 "d_ap": round(land.loc[t1, "ap"] - land.loc[t0, "ap"], 2)})
bolger_sp90 = [r["par"] for r in nasj if r["d_sp90"] >= NASJ_BOLGE_PP and int(r["par"][:4]) >= FORSTE_TESTAAR]
bolger_sp = [r["par"] for r in nasj if r["d_sp"] >= NASJ_BOLGE_PP and int(r["par"][:4]) >= FORSTE_TESTAAR]


def tilbakefall(bolger, kol):
    ut = {}
    for b in bolger:
        i = [r["par"] for r in nasj].index(b)
        for r in nasj[i + 1:]:
            if r[kol] < 0:
                ut[b] = r["par"]
                break
        else:
            ut[b] = None
    return ut


# Første store lokale bølge per kommune (fra 1953) – hovedvariant Sp + felleslister
tb = panel[panel.testbar]
forste = tb[tb.lokal_bolge].groupby("kom")["par"].first()
forste_sp = tb[tb.lokal_bolge_sp].groupby("kom")["par"].first()

låst = {
    "dato": "2026-09-27",
    "beskrivelse": "Definisjoner låst før T1–T8 ble kjørt (PROMPT.md §3, standardsvar §9).",
    "panel_sha256": {"panel.csv": sha(f), "panel_kv.csv": sha(ARB / "panel_kv.csv"),
                     "panel_stabil.csv": sha(ARB / "panel_stabil.csv")},
    "kildefiler_sha256": {n: sha(UT.parents[1] / "data" / "processed" / n) for n in
                          ["stortingsvalg_1945.csv", "kommunestyrevalg_1945.csv", "stortingsvalg_1945_stabil.csv",
                           "befolkning_1951.csv", "sentralitet_2024.csv", "stabile_enheter.csv"]},
    "distrikt_sentralitetsklasser": list(DISTRIKT_KLASSER),
    "bastion": {"hoved": f"rullerende: Ap-snitt ved t0 og valget før >= {BASTION_GRENSE} %",
                "robusthet": [f"fast: Ap-snitt ST {FAST_BASTION_AAR[0]}–{FAST_BASTION_AAR[-1]} >= {BASTION_GRENSE} %",
                              "fast øvre kvartil (snitt 1953–69)", "rullerende grense 45 og 55 %"]},
    "forste_testpar_t0": FORSTE_TESTAAR,
    "lokal_bolge_pp": LOKAL_BOLGE_PP,
    "nasjonal_bolge_pp": NASJ_BOLGE_PP,
    "nasjonale_endringer": nasj,
    "nasjonale_bolger_sp90": bolger_sp90,
    "nasjonale_bolger_sp_alene": bolger_sp,
    "tilbakefall_sp90": tilbakefall(bolger_sp90, "d_sp90"),
    "tilbakefall_sp_alene": tilbakefall(bolger_sp, "d_sp"),
    "antall_kommuner_med_lokal_bolge_sp90": int(forste.size),
    "antall_kommuner_med_lokal_bolge_sp_alene": int(forste_sp.size),
    "forste_lokale_bolge_fordeling_sp90": forste.value_counts().sort_index().to_dict(),
    "gruppestørrelser_per_par": panel[panel.testbar].groupby(["par", "gruppe"]).size().unstack(fill_value=0).to_dict("index"),
    "hovedvariant": "stortingsvalg; kommunestyrevalg parallelt; Sp + felleslister (sp90) og Sp alene begge rapportert",
    "sikkerhet": "valgpar med t0 < 1953 (sikkerhet «lav») brukes ikke i testene; rullerende bastion for par 1953–57 bruker 1949 som bakgrunn",
}
(UT / "låst.json").write_text(json.dumps(låst, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

# Dataordbok
dd = f"""# Dataordbok: analysepanelet (`arbeid/panel.csv`)

Bygget av `analyse/sp_ventil/steg1_panel_laas.py` fra `data/processed/`. Én rad per 2024-kommune × valgpar
(stortingsvalg t0 → t1), {len(panel)} rader, {panel.kom.nunique()} kommuner, {panel.par.nunique()} valgpar (1945–49 til 2021–25).
`panel_kv.csv` er det samme for kommunestyrevalg, og `panel_stabil.csv` for 279 stabile enheter.

| Kolonne | Innhold |
|---|---|
| kom, navn | 2024-kommunenummer (eller stabil enhet) og navn |
| t0, t1, par | Valgår før og etter, og «t0-t1» |
| `<p>0`, `<p>1` | Oppslutning i prosent ved t0 og t1. p ∈ ap, frp, h, krf, sp, sv, v, mdg, nkp, rodt, fl (felleslister, gruppe 90), andre |
| sp90 | Sp + felleslister (gruppe 90). Hele gruppe 90 regnes til Sp. Det overvurderer Sp noe, fordi felleslistene også rommet KrF/V |
| hvk | H + V + KrF (uten felleslister) |
| `d_<p>` | Endring t0 → t1 i prosentpoeng |
| `dl_<p>` | Endring relativt til landet: d_p minus landsendringen (stemmevektet landstall) |
| ped | Pedersen-indeks, ½·Σ\\|Δp\\| over de 12 gruppene |
| ped90 | Pedersen med Sp og felleslister slått sammen (fjerner kunstig flyktighet når Sp bytter mellom egen liste og felleslister) |
| ped_uten_sp | ½·Σ\\|Δp\\| over alle partier unntatt Sp og felleslister («utslag hos andre partier») |
| sikker0, sikker1 | Laveste `sikkerhet` blant radene for kommunen i t0 og t1 |
| est | Minst én partirad ved t0 eller t1 er `estimert` (fordelt etter nøkkel) |
| sent, distrikt | SSB sentralitetsklasse 2024. distrikt = klasse {DISTRIKT_KLASSER} |
| ap_rull, bastion | Ap-snitt ved t0 og valget før t0. bastion = ap_rull ≥ {BASTION_GRENSE} % |
| ap_fast, bastion_fast, bastion_q75 | Ap-snitt ST 1953–69. Bastion ved ≥ {BASTION_GRENSE} % eller øvre kvartil |
| bef0, bef1, dlog_bef | Folketall (nærmeste år ≥ 1951) og 100·ln(bef1/bef0) |
| fylke | To første sifre i 2024-nummeret |
| nasj_d_sp90, nasj_d_sp | Landsendring for Sp + felleslister og Sp alene |
| testbar | t0 ≥ {FORSTE_TESTAAR}. Par med t0 = 1945 eller 1949 (sikkerhet «lav») er bare bakgrunn |
| lokal_bolge, lokal_bolge_sp | d_sp90 (d_sp) ≥ {LOKAL_BOLGE_PP} pp |
| gruppe | distrikt_bastion / distrikt_ikke_bastion / sentral (rullerende bastion) |

Landstall per år: `landstall_st.csv` og `landstall_kv.csv`.
"""
(ARB / "datadictionary.md").write_text(dd, encoding="utf-8")
print("panel", panel.shape, "kv", panel_kv.shape, "stabil", panel_st.shape)
print("bølger sp90", bolger_sp90, "sp", bolger_sp, "tilbakefall", låst["tilbakefall_sp90"], låst["tilbakefall_sp_alene"])
print("første lokale bølge", låst["forste_lokale_bolge_fordeling_sp90"])
