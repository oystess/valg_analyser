#!/usr/bin/env python3
"""Spredningsdiagram: endring i Ap og Sp 2013→2017 (pp) mot befolkningsvekst 2007–2017 (%), per 2024-kommune."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess

ROT = Path(__file__).resolve().parent.parent
p = pd.read_csv(ROT / "turnering" / "data" / "panel.csv", dtype={"kom2024": str})
d = p[p["periode"] == "2013-2017"]

TEKST, GRÅ, RUTE = "#274247", "#909090", "#C3DCDC"
serier = [("d_sp", "Senterpartiet", "#1A9D49", "o"), ("d_ap", "Arbeiderpartiet", "#1D9DE2", "^")]

plt.rcParams.update({"font.family": ["Open Sans", "Arial", "DejaVu Sans"], "axes.edgecolor": TEKST})
fig, ax = plt.subplots(figsize=(10, 6.5), dpi=150)
X_UT, Y_UT = (-12, 30), (-20, 30)   # utsnitt; kurvene regnes på alle kommuner
x = d["vekst10_pst"]
utenfor = d[(x < X_UT[0]) | (x > X_UT[1]) | (d["d_sp"] > Y_UT[1]) | (d["d_sp"] < Y_UT[0])
            | (d["d_ap"] > Y_UT[1]) | (d["d_ap"] < Y_UT[0])]
for kol, navn, farge, markør in serier:
    ax.scatter(x, d[kol], s=18, color=farge, marker=markør, alpha=0.55, linewidths=0, label=navn)
    kurve = lowess(d[kol], x, frac=0.4, return_sorted=True)
    ax.plot(kurve[:, 0], kurve[:, 1], color=farge, lw=2.6)
    x0 = -11
    y0 = np.interp(x0, kurve[:, 0], kurve[:, 1])
    ax.annotate(navn, xy=(x0, y0), xytext=(0, 16 if kol == "d_sp" else -18), textcoords="offset points",
                ha="left", va="center", color=farge, fontsize=12, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))

ax.axhline(0, color=TEKST, lw=0.8)
ax.axvline(0, color=RUTE, lw=0.8, ls="--")
ax.grid(axis="y", color=RUTE, ls=":", lw=0.8)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.set_xlabel("Befolkningsvekst 1.1.2007–1.1.2017 (prosent)", fontsize=13, color=TEKST)
ax.set_ylabel("Endring i oppslutning, stortingsvalg 2013–2017 (prosentpoeng)", fontsize=13, color=TEKST)
ax.tick_params(colors=TEKST, labelsize=11)
ax.set_xlim(*X_UT)
ax.set_ylim(*Y_UT)
fig.suptitle("Sp vokste og Ap falt mest der folketallet gikk ned (2013–2017)",
             x=0.06, ha="left", fontsize=16, fontweight="bold", color=TEKST, family=["Roboto Condensed", "DejaVu Sans"])
ax.set_title("357 kommuner (2024-inndeling). Kurvene er glattet trend (LOWESS), regnet på alle kommuner.",
             loc="left", fontsize=11, color=GRÅ)
fig.text(0.06, 0.015, "Kilde: SSB, tabell 08092 (stortingsvalg) og 07459 (befolkning). Andel av alle godkjente stemmer. "
         "Harmonisert til 2024-kommuner.\n"
         f"Utenfor utsnittet ({len(utenfor)}): " + ", ".join(utenfor["navn"].str.split(" - ").str[0]) + ".",
         fontsize=10, color=GRÅ)
fig.tight_layout(rect=(0.03, 0.06, 1, 0.95))
ut = ROT / "figurer" / "ap_sp_2013_2017_befolkning.png"
fig.savefig(ut, facecolor="white")
print(ut)
