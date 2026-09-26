#!/usr/bin/env python3
"""Figurer til hypoteser/motreaksjon/RAPPORT.md (SSB-stil).

1) figurer/motreaksjon_gradienter.png: Høyre-gradient i t mot Sp-gradient i t+1, ett punkt per periodepar,
   ST og KV med ulik markør, 95 % KI som streker. Bygger på hypoteser/motreaksjon/parvis.csv.
2) figurer/h_sp_1997_2005_for_etter.png: før–etter for testepisoden ST 1997–2001 → 2001–2005, satt sammen av
   figurene fra figur_parti_vs_befolkning.py (kjøres først: `... h 1997-2001` og `... h 2001-2005`).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd

ROT = Path(__file__).resolve().parent.parent
TEKST, GRÅ, RUTE = "#274247", "#909090", "#C3DCDC"
FARGE = {"ST": "#1A9D49", "KV": "#1D9DE2"}
MARKØR = {"ST": "o", "KV": "^"}
plt.rcParams.update({"font.family": ["Open Sans", "Arial", "DejaVu Sans"], "axes.edgecolor": TEKST})


# etikettplassering (punkter) for å unngå overlapp i klyngen nær origo
FORSKYV = {("ST", "2013-2017"): (-190, 30), ("ST", "2001-2005"): (-190, 12), ("KV", "1999-2003"): (-190, -14),
           ("ST", "1993-1997"): (-190, -40), ("ST", "2005-2009"): (25, -42), ("KV", "2003-2007"): (18, -20),
           ("KV", "2015-2019"): (-60, 32), ("KV", "1995-1999"): (14, 16), ("ST", "1997-2001"): (8, -20),
           ("ST", "2017-2021"): (-150, 26), ("KV", "2007-2011"): (8, -16), ("KV", "2011-2015"): (8, 8)}


def komma(x, _):
    return f"{x:.2f}".replace(".", ",").replace("-", "−")


def kort(p):
    return f"{p[2:4]}–{p[7:9]}"


def gradienter():
    p = pd.read_csv(ROT / "hypoteser" / "motreaksjon" / "parvis.csv")
    p = p[p["rolle"] != "bare_vekst4"]
    fig, ax = plt.subplots(figsize=(10, 7), dpi=150)
    ax.axhline(0, color=TEKST, lw=0.8)
    ax.axvline(0, color=TEKST, lw=0.8)
    ax.grid(color=RUTE, ls=":", lw=0.8)
    for vs, navn in (("ST", "Stortingsvalg"), ("KV", "Kommunestyrevalg")):
        d = p[(p["valgslag"] == vs) & (p["rolle"] == "test")]
        ax.errorbar(d["b_P1"], d["b_P2"], xerr=[d["b_P1"] - d["lo_P1"], d["hi_P1"] - d["b_P1"]],
                    yerr=[d["b_P2"] - d["lo_P2"], d["hi_P2"] - d["b_P2"]], fmt="none", ecolor=FARGE[vs],
                    alpha=0.35, lw=1.2)
        ax.scatter(d["b_P1"], d["b_P2"], s=80, color=FARGE[vs], marker=MARKØR[vs], zorder=3,
                   label=f"{navn}, testpar ({len(d)})", edgecolors="white", linewidths=0.8)
        for r in d.itertuples():
            ax.annotate(f"{vs} {kort(r.t)} → {kort(r.t1)}" + (" (H i reg.)" if r.h_i_regjering else ""),
                        (r.b_P1, r.b_P2), xytext=FORSKYV[(vs, r.t)], textcoords="offset points", fontsize=9,
                        color=FARGE[vs], arrowprops=dict(arrowstyle="-", color=FARGE[vs], lw=0.6, alpha=0.6))
    s = p[p["rolle"] == "sett"]
    ax.errorbar(s["b_P1"], s["b_P2"], xerr=[s["b_P1"] - s["lo_P1"], s["hi_P1"] - s["b_P1"]],
                yerr=[s["b_P2"] - s["lo_P2"], s["hi_P2"] - s["b_P2"]], fmt="none", ecolor=GRÅ, alpha=0.6, lw=1.2)
    ax.scatter(s["b_P1"], s["b_P2"], s=110, facecolors="white", edgecolors=GRÅ, linewidths=2, marker="o", zorder=3,
               label="Stortingsvalg, sett episode (bare illustrasjon)")
    for r in s.itertuples():
        ax.annotate(f"ST {kort(r.t)} → {kort(r.t1)}: episoden\nhypotesen ble laget fra", (r.b_P1, r.b_P2),
                    xytext=(8, -4), textcoords="offset points", fontsize=9, color=GRÅ, va="top")
    ax.text(0.99, 0.02, "Hypotesen forutsier punkter\nnede til høyre", transform=ax.transAxes, ha="right",
            va="bottom", fontsize=10, color=GRÅ, style="italic")
    for sp_ in ("top", "right"):
        ax.spines[sp_].set_visible(False)
    ax.set_xlabel("Høyre-gradient i periode t (pp endring per prosent befolkningsvekst)", fontsize=13, color=TEKST)
    ax.set_ylabel("Sp-gradient i periode t+1\n(pp endring per prosent befolkningsvekst)", fontsize=13, color=TEKST)
    ax.tick_params(colors=TEKST, labelsize=11)
    from matplotlib.ticker import FuncFormatter
    ax.xaxis.set_major_formatter(FuncFormatter(komma))
    ax.yaxis.set_major_formatter(FuncFormatter(komma))
    ax.legend(loc="upper left", frameon=False, fontsize=10, labelcolor=TEKST)
    fig.suptitle("Sterkere Høyre-gradient ga ikke sterkere Sp-motreaksjon i testparene",
                 x=0.06, ha="left", fontsize=16, fontweight="bold", color=TEKST, family=["Roboto Condensed", "DejaVu Sans"])
    ax.set_title("Koeffisienter fra vektede regresjoner med kontroll for partiets nivå i t0 og sentralitet. "
                 "Strekene er 95 % KI.", loc="left", fontsize=10.5, color=GRÅ)
    fig.text(0.07, 0.012, "Kilde: SSB, tabell 08092 (stortingsvalg), 01180 (kommunestyrevalg) og 07459 (befolkning). "
             "357 kommuner i 2024-inndeling.\nBefolkningsvekst = vekst over ti år fram til periodens slutt. "
             "«H i reg.» = Høyre i regjering minst halve tiden i t+1.", fontsize=9.5, color=GRÅ)
    fig.tight_layout(rect=(0.02, 0.06, 1, 0.95))
    ut = ROT / "figurer" / "motreaksjon_gradienter.png"
    fig.savefig(ut, facecolor="white")
    print(ut)


def for_etter():
    filer = [ROT / "figurer" / f"h_sp_{a}_befolkning.png" for a in ("1997_2001", "2001_2005")]
    bilder = [mpimg.imread(f) for f in filer]
    h, w = bilder[0].shape[:2]
    fig = plt.figure(figsize=(w / 150, 2 * h / 150 + 0.9), dpi=150)
    fig.text(0.02, 1 - 0.35 / (2 * h / 150 + 0.9), "Før og etter: Høyre-året 2001 og valget etter (testepisode)",
             fontsize=18, fontweight="bold", color=TEKST, va="top", family=["Roboto Condensed", "DejaVu Sans"])
    for i, b in enumerate(bilder):
        ax = fig.add_axes([0, (1 - i) * h / (2 * h + 135), 1, h / (2 * h + 135)])
        ax.imshow(b)
        ax.axis("off")
    ut = ROT / "figurer" / "h_sp_1997_2005_for_etter.png"
    fig.savefig(ut, facecolor="white")
    print(ut)


if __name__ == "__main__":
    gradienter()
    for_etter()
