#!/usr/bin/env python3
"""Spredningsdiagram: endring i Sp og ett annet parti 2013→2017 (pp) mot befolkningsvekst 2007–2017 (%),
per 2024-kommune, med glattet trend (LOWESS).

Bruk: python analyse/figur_parti_vs_befolkning.py ap|h|frp|krf|sv|v|mdg|rodt [periode, f.eks. 2009-2013]
"""
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess

ROT = Path(__file__).resolve().parent.parent
p = pd.read_csv(ROT / "turnering" / "data" / "panel.csv", dtype={"kom2024": str})
PERIODE = sys.argv[2] if len(sys.argv) > 2 else "2013-2017"
T0, T1 = (int(a) for a in PERIODE.split("-"))
d = p[p["periode"] == PERIODE]

TEKST, GRÅ, RUTE = "#274247", "#909090", "#C3DCDC"
# Fast farge per parti på tvers av figurene (SSB-palett); Sp er alltid grønn
PARTI = {"ap": ("Arbeiderpartiet", "#1D9DE2"), "h": ("Høyre", "#C78800"), "frp": ("Fremskrittspartiet", "#0F2080"),
         "krf": ("Kristelig Folkeparti", "#C775A7"), "sv": ("SV", "#A3136C"), "v": ("Venstre", "#075745"),
         "mdg": ("MDG", "#471F00"), "rodt": ("Rødt", "#909090")}
TITTEL = {("ap", "2013-2017"): "Sp vokste og Ap falt mest der folketallet gikk ned (2013–2017)",
          ("h", "2013-2017"): "Sp vokste der folketallet falt – Høyre sto nesten stille (2013–2017)",
          ("ap", "2009-2013"): "Ingen tydelig sammenheng med folketallet for Sp og Ap (2009–2013)",
          ("h", "2009-2013"): "Høyre vokste mest der folketallet vokste – Sp sto stille (2009–2013)"}
annet = sys.argv[1] if len(sys.argv) > 1 else "ap"
navn2, farge2 = PARTI[annet]
serier = [("d_sp", "Senterpartiet", "#1A9D49", "o"), (f"d_{annet}", navn2, farge2, "^")]

plt.rcParams.update({"font.family": ["Open Sans", "Arial", "DejaVu Sans"], "axes.edgecolor": TEKST})
fig, ax = plt.subplots(figsize=(10, 6.5), dpi=150)
X_UT, Y_UT = (-12, 30), (-20, 30)   # utsnitt; kurvene regnes på alle kommuner
x = d["vekst10_pst"]
k2 = f"d_{annet}"
utenfor = d[(x < X_UT[0]) | (x > X_UT[1]) | (d["d_sp"] > Y_UT[1]) | (d["d_sp"] < Y_UT[0])
            | (d[k2] > Y_UT[1]) | (d[k2] < Y_UT[0])]
kurver = {}
for kol, navn, farge, markør in serier:
    ax.scatter(x, d[kol], s=18, color=farge, marker=markør, alpha=0.55, linewidths=0, label=navn)
    kurve = lowess(d[kol], x, frac=0.4, return_sorted=True)
    ax.plot(kurve[:, 0], kurve[:, 1], color=farge, lw=2.6)
    kurver[kol] = kurve
# Etiketter ved venstre kant: øverste kurve merkes over, nederste under
x0 = -11
y0 = {k: np.interp(x0, c[:, 0], c[:, 1]) for k, c in kurver.items()}
øverst = max(y0, key=y0.get)
for kol, navn, farge, _ in serier:
    ax.annotate(navn, xy=(x0, y0[kol]), xytext=(0, 16 if kol == øverst else -18), textcoords="offset points",
                ha="left", va="center", color=farge, fontsize=12, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))

ax.axhline(0, color=TEKST, lw=0.8)
ax.axvline(0, color=RUTE, lw=0.8, ls="--")
ax.grid(axis="y", color=RUTE, ls=":", lw=0.8)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.set_xlabel(f"Befolkningsvekst 1.1.{T1 - 10}–1.1.{T1} (prosent)", fontsize=13, color=TEKST)
ax.set_ylabel(f"Endring i oppslutning, stortingsvalg {T0}–{T1} (prosentpoeng)", fontsize=13, color=TEKST)
ax.tick_params(colors=TEKST, labelsize=11)
ax.set_xlim(*X_UT)
ax.set_ylim(*Y_UT)
fig.suptitle(TITTEL.get((annet, PERIODE), f"Endring for Sp og {navn2} etter befolkningsutvikling ({T0}–{T1})"),
             x=0.06, ha="left", fontsize=16, fontweight="bold", color=TEKST, family=["Roboto Condensed", "DejaVu Sans"])
ax.set_title("357 kommuner (2024-inndeling). Kurvene er glattet trend (LOWESS), regnet på alle kommuner.",
             loc="left", fontsize=11, color=GRÅ)
fig.text(0.11, 0.012, "Kilde: SSB, tabell 08092 (stortingsvalg) og 07459 (befolkning). Andel av alle godkjente stemmer, "
         "harmonisert til 2024-kommuner.\n"
         + textwrap.fill(f"Utenfor utsnittet ({len(utenfor)}): " + ", ".join(utenfor["navn"].str.split(" - ").str[0]) + ".", 115),
         fontsize=9.5, color=GRÅ)
fig.tight_layout(rect=(0.03, 0.10, 1, 0.95))
ut = ROT / "figurer" / f"{annet}_sp_{T0}_{T1}_befolkning.png"
fig.savefig(ut, facecolor="white")
print(ut)
