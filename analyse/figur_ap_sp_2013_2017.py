#!/usr/bin/env python3
"""Spredningsdiagram: endring i Ap og Sp 2013→2017 (pp) mot befolkningsvekst 2007–2017 (%), per 2024-kommune."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROT = Path(__file__).resolve().parent.parent
p = pd.read_csv(ROT / "turnering" / "data" / "panel.csv", dtype={"kom2024": str})
d = p[p["periode"] == "2013-2017"]

TEKST, GRÅ, RUTE = "#274247", "#909090", "#C3DCDC"
serier = [("d_sp", "Senterpartiet", "#1A9D49", "o"), ("d_ap", "Arbeiderpartiet", "#1D9DE2", "^")]

plt.rcParams.update({"font.family": ["Open Sans", "Arial", "DejaVu Sans"], "axes.edgecolor": TEKST})
fig, ax = plt.subplots(figsize=(10, 6.5), dpi=150)
x = d["vekst10_pst"]
xs = np.linspace(x.min(), x.max(), 50)
for kol, navn, farge, markør in serier:
    ax.scatter(x, d[kol], s=18, color=farge, marker=markør, alpha=0.55, linewidths=0, label=navn)
    b, a = np.polyfit(x, d[kol], 1)
    ax.plot(xs, a + b * xs, color=farge, lw=2.2)
    x0 = -14
    ax.annotate(f"{navn}: {b:+.2f} pp per prosent vekst".replace(".", ","), xy=(x0, a + b * x0),
                xytext=(0, 14 if kol == "d_sp" else -18), textcoords="offset points",
                ha="left", va="center", color=farge, fontsize=11, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))

ax.axhline(0, color=TEKST, lw=0.8)
ax.axvline(0, color=RUTE, lw=0.8, ls="--")
ax.grid(axis="y", color=RUTE, ls=":", lw=0.8)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.set_xlabel("Befolkningsvekst 1.1.2007–1.1.2017 (prosent)", fontsize=13, color=TEKST)
ax.set_ylabel("Endring i oppslutning, stortingsvalg 2013–2017 (prosentpoeng)", fontsize=13, color=TEKST)
ax.tick_params(colors=TEKST, labelsize=11)
ax.set_xlim(x.min() - 1, x.max() + 2)
# Ekstremverdi navngis
e = d.loc[d["d_sp"].idxmax()]
ax.annotate(f"{e['navn']}: Sp {e['d_sp']:+.0f} pp".replace(".", ","), xy=(e["vekst10_pst"], e["d_sp"]),
            xytext=(12, -4), textcoords="offset points", fontsize=10, color=GRÅ,
            arrowprops=dict(arrowstyle="-", color=RUTE, lw=0.8))
fig.suptitle("Sp vokste og Ap falt mest der folketallet gikk ned (2013–2017)",
             x=0.06, ha="left", fontsize=16, fontweight="bold", color=TEKST, family=["Roboto Condensed", "DejaVu Sans"])
ax.set_title("357 kommuner (2024-inndeling). Hvert punkt er én kommune per parti; linjene er enkel lineær tilpasning.",
             loc="left", fontsize=11, color=GRÅ)
fig.text(0.06, 0.015, "Kilde: SSB, tabell 08092 (stortingsvalg) og 07459 (befolkning). Andel av alle godkjente stemmer. "
         "Harmonisert til 2024-kommuner.", fontsize=10, color=GRÅ)
fig.tight_layout(rect=(0.03, 0.04, 1, 0.95))
ut = ROT / "figurer" / "ap_sp_2013_2017_befolkning.png"
fig.savefig(ut, facecolor="white")
print(ut)
