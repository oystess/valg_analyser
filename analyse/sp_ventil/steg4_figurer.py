#!/usr/bin/env python3
"""Steg 4: figurer i SSB-stil til hypoteser/sp_ventil/figurer/. Leser bare filer fra steg 1 og 3.

Kjøring: python analyse/sp_ventil/steg4_figurer.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from felles import ARB, FARGE, FIG, GRÅ, NAVN, RUTE, TEKST, overskrift, pynt, ssb_stil

plt = ssb_stil()
FIG.mkdir(parents=True, exist_ok=True)
RES = json.loads((ARB / "resultater.json").read_text(encoding="utf-8"))
land = pd.read_csv(ARB / "landstall_st.csv", index_col=0)
KILDE = "Kilde: SSB, stortingsvalg 1945–2025 harmonisert til 2024-kommuner (data/processed/stortingsvalg_1945.csv). Egne beregninger."
SP = "sp90"
NAVN_SP = "Sp (inkl. felleslister)"


def spre(y, gap):
    """Flytt etikett-y-verdier fra hverandre slik at avstanden er minst gap (i dataenheter)."""
    rek = np.argsort(y)
    ut = np.array(y, dtype=float)
    for i in range(1, len(rek)):
        if ut[rek[i]] - ut[rek[i - 1]] < gap:
            ut[rek[i]] = ut[rek[i - 1]] + gap
    return ut


def sluttetiketter(ax, x, rader, gap, dx=6, **kw):
    """rader: liste av (y, tekst, farge). Tegner etiketter ved x, spredt vertikalt."""
    ys = spre([r[0] for r in rader], gap)
    for (y0, tekst, farge), y in zip(rader, ys):
        ax.annotate(tekst, xy=(x, y0), xytext=(x, y), textcoords="data", va="center", color=farge,
                    fontsize=kw.get("fontsize", 9), fontweight=kw.get("fontweight", "normal"),
                    xycoords="data", annotation_clip=False, ha="left")


def lagre(fig, navn):
    ut = FIG / navn
    fig.savefig(ut, facecolor="white")
    plt.close(fig)
    print(ut)


# ---------- Figur 1: Sømna 1945–2025
def fig1():
    s = pd.read_csv(ARB / "t7_serier.csv", dtype={"kom": str})
    s = s[s.kom == "1812"].pivot(index="aar", columns="parti", values="prosent")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    etik = []
    ax.axvspan(1944, 1951, color=RUTE, alpha=0.35, lw=0)
    ax.text(1947.5, 63, "Usikre tall\n(1945–49)", ha="center", va="top", fontsize=9, color=GRÅ)
    for x0, x1 in [(1989, 1993), (2013, 2021)]:
        ax.axvspan(x0, x1, color="#1A9D49", alpha=0.07, lw=0)
    for kol, navn in [("ap", "Arbeiderpartiet"), ("sp90", NAVN_SP), ("frp", "Fremskrittspartiet"), ("h", "Høyre")]:
        farge = FARGE["sp" if kol == "sp90" else kol]
        ax.plot(s.index, s[kol], color=farge, lw=2.6 if kol in ("ap", "sp90") else 1.8, marker="o", ms=3.5)
        etik.append((s.loc[2025, kol], navn, farge))
    sluttetiketter(ax, 2026.2, etik, 3.2, fontsize=10.5, fontweight="bold")
    ax.plot(land.index, land["ap"], color=FARGE["ap"], lw=1, ls="--", alpha=0.7)
    ax.plot(land.index, land["sp90"], color=FARGE["sp"], lw=1, ls="--", alpha=0.7)
    ax.set_xlim(1944, 2033)
    ax.set_ylim(0, 65)
    ax.set_ylabel("Prosent av godkjente stemmer", fontsize=11)
    pynt(ax)
    topp = overskrift(fig, "Sømna: Sp vokste langsomt, og tok så over i bølgene 1993 og 2017–21",
               "Stortingsvalg 1945–2025, Sømna (2024-inndeling). Grønne felt: nasjonale Sp-bølger 1989–93 og 2013–21. Stiplet: hele landet.", KILDE)
    fig.tight_layout(rect=(0.02, 0.04, 1, topp))
    lagre(fig, "fig1_somna.png")


# ---------- Figur 2: hendelsesstudie
def fig2():
    t = pd.read_csv(ARB / "t4_hendelse.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8), dpi=150, sharey=True)
    oppsett = [("1993", "bastion", 1989, "Bølgen 1993 – rullerende bastioner (Ap ≥ 50 % i 1985–89)"),
               ("2021", "bastion_fast", 2013, "Bølgen 2017–21 – faste bastioner (Ap ≥ 50 % i 1953–69)")]
    for ax, (h, bk, basis, tittel) in zip(axes, oppsett):
        etik = []
        for dose, stil, navn in [("høy_dose", "-", "høy Sp-dose"), ("lav_dose", "--", "lav Sp-dose")]:
            for parti in ("ap", "sp90"):
                d = t[(t.hendelse == int(h)) & (t.bastion == bk) & (t.dose == dose) & (t.parti == parti)].sort_values("aar")
                farge = FARGE["sp" if parti == "sp90" else "ap"]
                ax.plot(d.aar, d.snitt, ls=stil, color=farge, lw=2.4 if dose == "høy_dose" else 1.6, marker="o", ms=3.5)
                ax.fill_between(d.aar, d.snitt - 1.96 * d.se, d.snitt + 1.96 * d.se, color=farge,
                                alpha=0.12 if dose == "høy_dose" else 0.06, lw=0)
                etik.append((d.snitt.iloc[-1], f"{'Ap' if parti == 'ap' else 'Sp'}, {navn}", farge))
        sluttetiketter(ax, d.aar.iloc[-1] + 0.8, etik, 1.4, fontsize=8.5)
        n = t[(t.hendelse == int(h)) & (t.bastion == bk)].groupby("dose").n.max()
        ax.axhline(0, color=TEKST, lw=0.8)
        ax.axvline(basis, color=GRÅ, lw=0.8, ls=":")
        ax.set_title(tittel + f"\n{n.get('høy_dose', 0)} + {n.get('lav_dose', 0)} distriktskommuner, delt på median dose",
                     loc="left", fontsize=10, color=TEKST)
        ax.set_xlim(d.aar.min() - 1, d.aar.max() + 9)
        pynt(ax)
    axes[0].set_ylabel(f"Endring fra {oppsett[0][2]}/{oppsett[1][2]} relativt til landet (prosentpoeng)", fontsize=10.5)
    topp = overskrift(fig, "Der Sp-bølgen var størst, falt Ap mest – og tok bare delvis igjen tapet",
               "Oppslutning relativt til landsresultatet, endring fra valget før bølgen. Skygge: 95 % konfidensintervall for snittet.", KILDE)
    fig.tight_layout(rect=(0.02, 0.04, 1, topp))
    lagre(fig, "fig2_hendelsesstudie.png")


# ---------- Figur 3: asymmetrikoeffisienter
def fig3():
    rader = []
    t2 = RES["T2"]["sp90"]
    etiketter = {"distrikt_bastion": "Distrikt, Ap-bastion", "distrikt_ikke_bastion": "Distrikt, ikke bastion",
                 "sentral": "Sentrale kommuner", "placebo_ap_svake_distrikt": "Placebo: Ap-svake distriktskommuner"}
    for g, et in etiketter.items():
        a = t2["periode_FE"][g]
        rader.append(("1953–2025, rullerende bastion", et, a))
    for g in ("distrikt_bastion", "distrikt_ikke_bastion", "sentral"):
        rader.append(("1989–2025, fast bastion (1953–69)", etiketter[g], RES["T2"]["bastion_fast_sp90"]["delperioder"]["1989-2025"][g]))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), dpi=150, sharex=True)
    for ax, blokk in zip(axes, ["1953–2025, rullerende bastion", "1989–2025, fast bastion (1953–69)"]):
        rr = [r for r in rader if r[0] == blokk]
        for i, (_, et, a) in enumerate(rr):
            y = len(rr) - i
            for k, farge, dy, navn in [("b_pos", FARGE["sp"], 0.14, "b⁺: Sp går fram"), ("b_neg", FARGE["frp"], -0.14, "b⁻: Sp går tilbake")]:
                b, (lo, hi) = a[k]["b"], a[k]["ki95"]
                ax.plot([lo, hi], [y + dy] * 2, color=farge, lw=2)
                ax.plot(b, y + dy, "o", color=farge, ms=6, label=navn if i == 0 else None)
            ax.text(0.02, y, f"n = {a['n']}", fontsize=8.5, color=GRÅ, va="center")
        ax.set_yticks([len(rr) - i for i in range(len(rr))])
        ax.set_yticklabels([r[1] for r in rr], fontsize=10)
        ax.axvline(0, color=TEKST, lw=0.8)
        ax.axvline(-1, color=RUTE, lw=0.8, ls="--")
        ax.set_title(blokk, loc="left", fontsize=11, color=TEKST)
        ax.grid(axis="x", color=RUTE, ls=":", lw=0.8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_xlabel("Endring i Ap per pp endring i Sp", fontsize=9.5)
    axes[0].legend(loc="lower left", fontsize=9, frameon=False)
    axes[1].set_xlim(-1.15, 0.2)
    topp = overskrift(fig, "Ap taper mer når Sp går fram enn Ap vinner når Sp faller – men ikke bare i bastionene",
               "Paneldata, endring mellom stortingsvalg: ΔAp = b⁺·max(ΔSp,0) + b⁻·min(ΔSp,0) + periodeeffekter. 95 % KI, klynget på kommune. Stiplet linje ved −1: alt går mellom Ap og Sp.",
               KILDE)
    fig.tight_layout(rect=(0.02, 0.04, 1, topp))
    lagre(fig, "fig3_asymmetri.png")


# ---------- Figur 4: volatilitet før og etter
def fig4():
    t = pd.read_csv(ARB / "t5_volatilitet_median.csv")
    grp = {"rammet_bastion": ("Bastion, høy Sp-dose 1993", FARGE["sp"], "-", 2.6),
           "a_bastion_lav_dose": ("Bastion, lav Sp-dose 1993", FARGE["sp"], "--", 1.6),
           "b_distrikt_ikke_bastion": ("Distrikt, ikke bastion", GRÅ, "-", 1.6),
           "c_sentral": ("Sentrale kommuner", FARGE["frp"], "-", 1.6)}
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=150)
    ax.axvspan(1976, 1990, color=RUTE, alpha=0.3, lw=0)
    ax.axvspan(2000, 2014, color=RUTE, alpha=0.3, lw=0)
    ax.text(1983, 34, "Før\n(1973–89)", ha="center", fontsize=9, color=GRÅ)
    ax.text(2007, 34, "Etter\n(1997–2013)", ha="center", fontsize=9, color=GRÅ)
    etik = []
    for g, (navn, farge, ls, lw) in grp.items():
        d = t[t.grp == g].sort_values("t1")
        ax.plot(d.t1, d.ped90, color=farge, ls=ls, lw=lw, marker="o", ms=3)
        etik.append((d.ped90.iloc[-1], navn, farge))
    sluttetiketter(ax, 2026.5, etik, 1.3)
    did = RES["T5"]["median_deling"]["did_ped90"]
    ax.set_ylim(0, 37)
    ax.set_xlim(1955, 2040)
    ax.set_ylabel("Pedersen-indeks (prosentpoeng)", fontsize=11)
    ax.set_xlabel("Valgpar, år for det siste valget", fontsize=10)
    pynt(ax)
    tekst = (f"Diff-in-diff, høy dose mot lav dose: {did['mot_a_bastion_lav_dose']['b']:+.1f} pp "
             f"(95 % KI {did['mot_a_bastion_lav_dose']['ki95'][0]:.1f} til {did['mot_a_bastion_lav_dose']['ki95'][1]:.1f}). "
             f"Mot sentrale: {did['mot_c_sentral']['b']:+.1f} pp.")
    topp = overskrift(fig, "Velgerne ble noe mer flyktige i bastionene med størst Sp-bølge i 1993",
               "Snitt Pedersen-indeks per valgpar (Sp og felleslister slått sammen). Distrikts-bastioner (Ap ≥ 50 % i 1985–89) delt på median Sp-økning 1989–93.\n" + tekst,
               KILDE)
    fig.tight_layout(rect=(0.02, 0.04, 1, topp))
    lagre(fig, "fig4_volatilitet.png")


# ---------- Figur 5: hvor kom Sp-velgerne fra, og hvor gikk de?
def fig5():
    t1 = RES["T1"]["sp90"]
    t8 = RES["T8"]["uten_felleslister"]
    t6 = RES["T6"]
    rader = [
        ("Sp fram 1953–89 (uten felleslister)", -t8["alle_distrikt"]["ap"]["b"], -t8["alle_distrikt"]["hvk"]["b"], None),
        ("Sp fram 1989–93", -t1["1989-1993"]["dekomponering_distrikt"]["ap"],
         -sum(t1["1989-1993"]["dekomponering_distrikt"][q] for q in ("h", "v", "krf")), -t1["1989-1993"]["dekomponering_distrikt"]["frp"]),
        ("Sp tilbake 1993–97", t6["1993-1997"]["alle_distrikt"]["andel_av_tap_til"]["ap"],
         sum(t6["1993-1997"]["alle_distrikt"]["andel_av_tap_til"][q] for q in ("h", "v", "krf")), t6["1993-1997"]["alle_distrikt"]["andel_av_tap_til"]["frp"]),
        ("Sp fram 2013–17", -t1["2013-2017"]["dekomponering_distrikt"]["ap"],
         -sum(t1["2013-2017"]["dekomponering_distrikt"][q] for q in ("h", "v", "krf")), -t1["2013-2017"]["dekomponering_distrikt"]["frp"]),
        ("Sp fram 2017–21", -t1["2017-2021"]["dekomponering_distrikt"]["ap"],
         -sum(t1["2017-2021"]["dekomponering_distrikt"][q] for q in ("h", "v", "krf")), -t1["2017-2021"]["dekomponering_distrikt"]["frp"]),
        ("Sp tilbake 2021–25", t6["2021-2025"]["alle_distrikt"]["andel_av_tap_til"]["ap"],
         sum(t6["2021-2025"]["alle_distrikt"]["andel_av_tap_til"][q] for q in ("h", "v", "krf")), t6["2021-2025"]["alle_distrikt"]["andel_av_tap_til"]["frp"]),
    ]
    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=150)
    y = np.arange(len(rader))[::-1]
    venstre = np.zeros(len(rader))
    for j, (navn, farge) in enumerate([("Ap", FARGE["ap"]), ("H + V + KrF", FARGE["h"]), ("FrP", FARGE["frp"])]):
        v = np.array([0 if rr[j + 1] is None else rr[j + 1] for rr in rader]) * 100
        ax.barh(y, v, left=venstre, color=farge, height=0.6, label=navn)
        for yi, vi, li in zip(y, v, venstre):
            if abs(vi) >= 6:
                ax.text(li + vi / 2, yi, f"{vi:.0f} %", ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        venstre = venstre + v
    ax.set_yticks(y)
    ax.set_yticklabels([rr[0] for rr in rader], fontsize=10)
    ax.axvline(0, color=TEKST, lw=0.8)
    ax.set_xlim(-10, 110)
    ax.set_xlabel("Andel av Sps endring som svarer til endring hos partiet (helning, prosent)", fontsize=10)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=9.5, frameon=False, ncol=3)
    ax.grid(axis="x", color=RUTE, ls=":", lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    topp = overskrift(fig, "I 1993 tok Sp mest fra Ap i distriktet – da Sp falt i 1997, gikk lite tilbake til Ap",
               "Distriktskommuner (sentralitet 5–6). Tverrsnittshelning: endring for partiet per prosentpoeng endring for Sp (inkl. felleslister).\n"
               "1953–89: kommune- og periodeeffekter, bare kommune-par uten felleslister. Resten (SV, Rødt, andre lister m.m.) er ikke vist; i 1997 gikk mye til «andre».", KILDE)
    fig.tight_layout(rect=(0.02, 0.04, 1, topp))
    lagre(fig, "fig5_hvor_fra_hvor_til.png")


# ---------- Figur 6: Sømna og tilsvarende kommuner (T7)
def fig6():
    s = pd.read_csv(ARB / "t7_serier.csv", dtype={"kom": str})
    kom = list(dict.fromkeys(s.kom))
    fig, axes = plt.subplots(3, 3, figsize=(12, 9), dpi=150, sharex=True, sharey=True)
    for ax, k in zip(axes.flat, kom):
        d = s[s.kom == k].pivot(index="aar", columns="parti", values="prosent")
        for kol in ("ap", "sp90", "frp", "h"):
            ax.plot(d.index, d[kol], color=FARGE["sp" if kol == "sp90" else kol], lw=2 if kol in ("ap", "sp90") else 1.2)
        ax.set_title(s[s.kom == k].navn.iloc[0], loc="left", fontsize=10.5, color=TEKST, fontweight="bold")
        ax.axvspan(1944, 1951, color=RUTE, alpha=0.35, lw=0)
        pynt(ax)
    axes[0, 0].legend(["Ap", NAVN_SP, "FrP", "H"], fontsize=8, frameon=False, loc="upper right")
    regel = RES["T7"]["regel"]
    topp = overskrift(fig, "Sømna har slektninger: Ap-kommuner med store Sp-bølger både i 1993 og i 2017–21",
               f"Regel i kode: sentralitet 5–6, Ap-snitt 1953–69 ≥ {regel['ap_fast_min']} %, Sp-økning 1989–93 ≥ {regel['dose93_min']} pp, "
               f"Ap relativt til landet ned ≥ 5 pp (1997–2013 mot 1981–89), Sp ≥ {regel['sp90_2021_min']} % i 2021. De 8 med størst samlet Sp-økning.",
               KILDE)
    fig.tight_layout(rect=(0.02, 0.04, 1, topp))
    lagre(fig, "fig6_somna_og_tilsvarende.png")


for f in (fig1, fig2, fig3, fig4, fig5, fig6):
    f()
