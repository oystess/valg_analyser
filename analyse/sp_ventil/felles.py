#!/usr/bin/env python3
"""
analyse/sp_ventil/felles.py – felles innlesing, panelbygging og SSB-stil for Sp-ventil-undersøkelsen.

Panelet har én rad per 2024-kommune (eller stabil enhet) × valgpar (t-1 → t), med nivåer i t-1 og t,
endringer i prosentpoeng, endringer relativt til landet, Pedersen-indeks, befolkningsendring,
sentralitet og bastionsflagg. Se hypoteser/sp_ventil/arbeid/datadictionary.md.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROT = Path(__file__).resolve().parents[2]
PROC = ROT / "data" / "processed"
UT = ROT / "hypoteser" / "sp_ventil"
ARB = UT / "arbeid"
FIG = UT / "figurer"

PARTI = {"01": "ap", "02": "frp", "03": "h", "04": "krf", "05": "sp", "06": "sv", "07": "v",
         "08": "mdg", "09": "nkp", "55": "rodt", "90": "fl", "99": "andre"}
PARTIER = list(PARTI.values())
FYLKE = {"03": "Oslo", "11": "Rogaland", "15": "Møre og Romsdal", "18": "Nordland", "31": "Østfold",
         "32": "Akershus", "33": "Buskerud", "34": "Innlandet", "39": "Vestfold", "40": "Telemark",
         "42": "Agder", "46": "Vestland", "50": "Trøndelag", "55": "Troms", "56": "Finnmark"}

# Faste parametre (låses i låst.json)
DISTRIKT_KLASSER = (5, 6)
BASTION_GRENSE = 50.0
LOKAL_BOLGE_PP = 10.0
NASJ_BOLGE_PP = 3.0
FAST_BASTION_AAR = (1953, 1957, 1961, 1965, 1969)
FORSTE_TESTAAR = 1953   # t-1 >= 1953: sikkerhet «lav» (1945–49) brukes bare som bakgrunn


def les_valg(fil="stortingsvalg_1945.csv", stabil=False):
    """Returnerer bred tabell (enhet, aar) med prosent per parti + total_stemmer, sikkerhet, estimert."""
    nøkkel = "enhet" if stabil else "kom2024"
    d = pd.read_csv(PROC / fil, dtype={nøkkel: str, "parti": str})
    d = d.rename(columns={nøkkel: "kom"})
    if "enhet_navn" in d:
        d = d.rename(columns={"enhet_navn": "navn"})
    d["p"] = d["parti"].map(PARTI)
    bred = d.pivot_table(index=["kom", "aar"], columns="p", values="stemmer", aggfunc="sum").fillna(0.0)
    tot = bred.sum(axis=1)
    pst = bred.div(tot, axis=0) * 100
    for p in PARTIER:
        if p not in pst:
            pst[p] = 0.0
    pst = pst[PARTIER]
    pst["stemmer"] = tot
    meta = d.groupby(["kom", "aar"]).agg(navn=("navn", "first"))
    if "sikkerhet" in d:
        rang = {"høy": 2, "middels": 1, "lav": 0}
        meta["sikkerhet"] = d.groupby(["kom", "aar"])["sikkerhet"].agg(lambda s: min(s, key=rang.get))
        meta["estimert"] = d.groupby(["kom", "aar"])["estimert"].agg(lambda s: bool(np.any(s.astype(str) == "True")))
    else:
        meta["sikkerhet"] = np.where(meta.index.get_level_values("aar") <= 1949, "lav", "høy")
        meta["estimert"] = False
    ut = pst.join(meta).reset_index()
    ut["sp90"] = ut["sp"] + ut["fl"]
    ut["hvk"] = ut["h"] + ut["v"] + ut["krf"]
    return ut


def landstall(valg):
    """Nasjonale andeler per år (stemmevektet), samme kolonner som valg."""
    kol = PARTIER
    st = valg[kol].mul(valg["stemmer"], axis=0).groupby(valg["aar"]).sum()
    l = st.div(valg.groupby("aar")["stemmer"].sum(), axis=0)
    l["sp90"] = l["sp"] + l["fl"]
    l["hvk"] = l["h"] + l["v"] + l["krf"]
    return l


def sentralitet(stabil=False):
    s = pd.read_csv(PROC / "sentralitet_2024.csv", dtype={"kom2024": str})[["kom2024", "sent_klasse"]]
    if not stabil:
        return s.rename(columns={"kom2024": "kom"}).set_index("kom")["sent_klasse"]
    e = pd.read_csv(PROC / "stabile_enheter.csv", dtype={"kom2024": str, "enhet": str})
    b = pd.read_csv(PROC / "befolkning_1951.csv", dtype={"kom2024": str})
    b = b[b.aar == b.aar.max()][["kom2024", "befolkning"]]
    e = e.merge(s, on="kom2024").merge(b, on="kom2024", how="left")
    # enhetens sentralitet = sentraliteten til den folkerikeste kommunen i enheten
    e = e.sort_values("befolkning", ascending=False).drop_duplicates("enhet")
    return e.rename(columns={"enhet": "kom"}).set_index("kom")["sent_klasse"]


def befolkning(stabil=False):
    b = pd.read_csv(PROC / "befolkning_1951.csv", dtype={"kom2024": str})
    if stabil:
        e = pd.read_csv(PROC / "stabile_enheter.csv", dtype={"kom2024": str, "enhet": str})
        b = b.merge(e[["kom2024", "enhet"]], on="kom2024").groupby(["enhet", "aar"], as_index=False)["befolkning"].sum()
        b = b.rename(columns={"enhet": "kom"})
    else:
        b = b.rename(columns={"kom2024": "kom"})
    return b.pivot(index="kom", columns="aar", values="befolkning")


def bef_ved(bef, aar):
    """Folketall ved valgåret (nærmeste tilgjengelige år >= 1951)."""
    a = min(max(aar, bef.columns.min()), bef.columns.max())
    return bef[a]


def pedersen(a, b, kol):
    return (b[kol].values - a[kol].values).__abs__().sum(axis=1) / 2


def bygg_panel(fil="stortingsvalg_1945.csv", stabil=False, bastion_grense=BASTION_GRENSE):
    v = landstall_input = les_valg(fil, stabil)
    land = landstall(landstall_input)
    sent = sentralitet(stabil)
    bef = befolkning(stabil)
    aar = sorted(v.aar.unique())
    ap_bred = v.pivot(index="kom", columns="aar", values="ap")
    fast = ap_bred[[a for a in FAST_BASTION_AAR if a in ap_bred]].mean(axis=1)
    fast_q75 = fast.quantile(0.75)
    rader = []
    vi = v.set_index(["kom", "aar"])
    for i in range(1, len(aar)):
        t0, t1 = aar[i - 1], aar[i]
        a = vi.xs(t0, level="aar")
        b = vi.xs(t1, level="aar")
        felles = a.index.intersection(b.index)
        a, b = a.loc[felles], b.loc[felles]
        r = pd.DataFrame(index=felles)
        r["navn"] = b["navn"]
        r["t0"], r["t1"], r["par"] = t0, t1, f"{t0}-{t1}"
        for p in PARTIER + ["sp90", "hvk"]:
            r[f"{p}0"] = a[p]
            r[f"{p}1"] = b[p]
            r[f"d_{p}"] = b[p] - a[p]
            r[f"dl_{p}"] = r[f"d_{p}"] - (land.loc[t1, p] - land.loc[t0, p])   # relativt til landet
        r["ped"] = pedersen(a, b, PARTIER)
        # Pedersen med felleslister slått sammen med Sp (fjerner kunstig flyktighet når Sp bytter listeform)
        a2, b2 = a.copy(), b.copy()
        k2 = [p for p in PARTIER if p not in ("sp", "fl")] + ["sp90"]
        r["ped90"] = pedersen(a2, b2, k2)
        # Utslag hos andre partier enn Sp (og felleslister): ½·Σ|Δp| for p ∉ {Sp, fl}
        k3 = [p for p in PARTIER if p not in ("sp", "fl")]
        r["ped_uten_sp"] = pedersen(a, b, k3)
        r["sikker0"], r["sikker1"] = a["sikkerhet"], b["sikkerhet"]
        r["est"] = a["estimert"].astype(bool) | b["estimert"].astype(bool)
        r["sent"] = sent.reindex(felles).values
        r["distrikt"] = r["sent"].isin(DISTRIKT_KLASSER)
        # Rullerende bastion: Ap-snitt ved de to valgene før t1 (dvs. t0 og valget før)
        if i >= 2:
            tm = aar[i - 2]
            r["ap_rull"] = (ap_bred.loc[felles, t0] + ap_bred.loc[felles, tm]) / 2
        else:
            r["ap_rull"] = ap_bred.loc[felles, t0]
        r["bastion"] = r["ap_rull"] >= bastion_grense
        r["ap_fast"] = fast.reindex(felles).values
        r["bastion_fast"] = r["ap_fast"] >= bastion_grense
        r["bastion_q75"] = r["ap_fast"] >= fast_q75
        b0, b1 = bef_ved(bef, t0).reindex(felles), bef_ved(bef, t1).reindex(felles)
        r["bef0"], r["bef1"] = b0.values, b1.values
        r["dlog_bef"] = np.log(r["bef1"] / r["bef0"]) * 100
        r["fylke"] = [k[:2] for k in felles]
        r["nasj_d_sp90"] = land.loc[t1, "sp90"] - land.loc[t0, "sp90"]
        r["nasj_d_sp"] = land.loc[t1, "sp"] - land.loc[t0, "sp"]
        rader.append(r)
    p = pd.concat(rader).rename_axis("kom").reset_index()
    p["testbar"] = p["t0"] >= FORSTE_TESTAAR
    p["lokal_bolge"] = p["d_sp90"] >= LOKAL_BOLGE_PP
    p["lokal_bolge_sp"] = p["d_sp"] >= LOKAL_BOLGE_PP
    p["gruppe"] = np.select(
        [p.distrikt & p.bastion, p.distrikt & ~p.bastion, ~p.distrikt],
        ["distrikt_bastion", "distrikt_ikke_bastion", "sentral"], default="ukjent")
    return p.sort_values(["kom", "t1"]).reset_index(drop=True), land


# ---------- SSB-stil (samme som analyse/figur_parti_vs_befolkning.py) ----------
TEKST, GRÅ, RUTE = "#274247", "#909090", "#C3DCDC"
FARGE = {"ap": "#1D9DE2", "sp": "#1A9D49", "frp": "#0F2080", "h": "#C78800", "krf": "#C775A7",
         "sv": "#A3136C", "v": "#075745", "andre": "#909090", "hvk": "#C78800"}
NAVN = {"ap": "Arbeiderpartiet", "sp": "Senterpartiet", "frp": "Fremskrittspartiet", "h": "Høyre",
        "krf": "KrF", "v": "Venstre", "sv": "SV", "rodt": "Rødt", "mdg": "MDG", "nkp": "NKP",
        "fl": "Felleslister", "andre": "Andre", "sp90": "Sp + felleslister", "hvk": "H + V + KrF"}


def ssb_stil():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": ["Open Sans", "Arial", "DejaVu Sans"], "axes.edgecolor": TEKST,
                         "axes.labelcolor": TEKST, "xtick.color": TEKST, "ytick.color": TEKST})
    return plt


def pynt(ax, ygrid=True):
    if ygrid:
        ax.grid(axis="y", color=RUTE, ls=":", lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=10)


def overskrift(fig, tittel, undertittel=None, kilde=None, x=0.06, bredde=None):
    """Tittel og undertittel øverst (med linjebryting), kilde nederst. Returnerer y for toppen av plottområdet."""
    import textwrap
    h = fig.get_size_inches()[1]
    bredde = bredde or int(fig.get_size_inches()[0] * 11.5)
    linje = 0.26 / h          # ca. én tekstlinje i figurbrøk
    y = 1 - 0.18 / h
    fig.text(x, y, tittel, ha="left", va="top", fontsize=15, fontweight="bold", color=TEKST,
             family=["Roboto Condensed", "DejaVu Sans"])
    y -= 1.35 * linje
    if undertittel:
        linjer = [l for avsnitt in undertittel.split("\n") for l in textwrap.wrap(avsnitt, bredde)]
        fig.text(x, y, "\n".join(linjer), ha="left", va="top", fontsize=10.5, color=GRÅ, linespacing=1.35)
        y -= len(linjer) * 0.95 * linje
    if kilde:
        fig.text(x, 0.012, kilde, fontsize=9, color=GRÅ)
    return y - 0.3 * linje
