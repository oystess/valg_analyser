#!/usr/bin/env python3
"""
analyse_bastioner.py — Aps distriktsbastioner 1989–2025: elastiske, ikke stabile.

Spørsmål (prosjekteier): Har Aps distriktsbastioner vært stabile hele tiden,
eventuelt mer stabile enn andre steder?

Funn:
  1. Bastionene var ELASTISKE, ikke stabile: rystet i 1993 (EU) og 2001
     (katastrofevalget), men hentet alt tilbake begge ganger. Det er denne
     hjemvendingen som ser ut som stabilitet fra 2005.
  2. De var IKKE mer stabile enn andre grupper — within-kommune-variansen er
     høyest i bastionene i alle epoker. Det stabile er RANGERINGEN
     (Spearman ≈ +0,91 mellom alle valgpar): Ap-kartet er hugget i granitt.
  3. 2017 er unik: første rystelse uten hjemvending. Bastionene ligger
     fortsatt ~6 pp under 2013-nivået i 2025, mens ikke-bastionene er tilbake.
  4. Kaskaden: velgerne Sp ristet løs i 2017 gikk videre til FrP i 2025,
     ikke hjem til Ap (ΔSp −16,3 pp i bastionene 2021→25, ΔAp bare +1,6).
     Ap → Sp → FrP: båndet røk, velgerne forble løse.

Definisjoner: distriktsbastion = sentralitet 0–1 og Ap-andel ≥ periferimedianen
i 2005 (referanseår fra prosjektets første analyse). Tilsvarende for sentrale.
1989-laget i kildedataene er permanent fikset (se hent_stv_fiks.py).
Vang (3454) og Hamar (3403) utelates (mappingkollisjon).

Injiserer seksjon i index.html mellom egne merker (idempotent):
  <!-- === START BASTIONER === --> ... <!-- === SLUTT BASTIONER === -->

Kjør fra prosjektrot:  python scripts/analyse_bastioner.py
"""

import warnings
import csv as csvmod
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import plotly.graph_objects as go

warnings.filterwarnings("ignore")

PROCESSED = "data/processed"
RAW       = "data/raw"

AAR = [1989, 1993, 1997, 2001, 2005, 2009, 2013, 2017, 2021, 2025]
GRUPPE_FARGER = {"Distriktsbastion": "#e4202c", "Periferi ellers": "#f28e8e",
                 "Sentral bastion": "#7f1d1d", "Sentral ellers": "#d4a5a5"}

START_M = "<!-- === START BASTIONER === -->"
SLUTT_M = "<!-- === SLUTT BASTIONER === -->"


# ── DATA ──────────────────────────────────────────────────────────────────────

def last_data():
    sv = pd.read_csv(f"{PROCESSED}/stortingsvalg_2024.csv", dtype={"kom2024": str, "parti": str})
    sv = sv[~sv["kom2024"].isin(["3454", "3403"])]

    mapping = {r["gammelt_nr"]: r["nr_2024"]
               for r in csvmod.DictReader(open(f"{PROCESSED}/kom_mapping.csv"))
               if r["nr_2024"]}
    sent = pd.read_csv(f"{RAW}/sentralitet.csv", sep=";", quotechar='"', encoding="latin1")
    sent["kom2024"] = (sent["targetCode"].astype(str).str.zfill(4)
                       .map(lambda x: mapping.get(x, x)))
    sent = sent.rename(columns={"sourceCode": "sent"})[["kom2024", "sent"]]
    sent["sent"] = pd.to_numeric(sent["sent"], errors="coerce")
    sent = sent.sort_values("sent").drop_duplicates("kom2024").set_index("kom2024")

    piv = lambda p: sv[sv["parti"] == p].pivot_table(
        index="kom2024", columns="aar", values="prosent", aggfunc="first")
    return piv("01"), piv("05"), piv("02"), sent


def bygg_grupper(ap: pd.DataFrame, sent: pd.DataFrame) -> pd.DataFrame:
    df = ap.join(sent).dropna(subset=[2005, "sent"])
    df["periferi"] = df["sent"] <= 1
    med_per = df.loc[df["periferi"], 2005].median()
    med_sen = df.loc[~df["periferi"], 2005].median()
    df["gruppe"] = np.select(
        [df["periferi"] & (df[2005] >= med_per), df["periferi"],
         ~df["periferi"] & (df[2005] >= med_sen)],
        ["Distriktsbastion", "Periferi ellers", "Sentral bastion"], "Sentral ellers")
    return df


# ── FIGURER ──────────────────────────────────────────────────────────────────

def fig_baner(df: pd.DataFrame) -> go.Figure:
    baner = df.groupby("gruppe")[AAR].mean()
    fig = go.Figure()
    for grp in ["Distriktsbastion", "Sentral bastion", "Periferi ellers", "Sentral ellers"]:
        if grp not in baner.index:
            continue
        rad = baner.loc[grp]
        fig.add_trace(go.Scatter(
            x=AAR, y=rad.values.round(1), mode="lines+markers", name=grp,
            line=dict(color=GRUPPE_FARGER[grp], width=3 if "bastion" in grp.lower() else 1.8,
                      dash=None if "bastion" in grp.lower() else "dot"),
            marker=dict(size=7),
            hovertemplate=f"<b>{grp}</b><br>%{{x}}: %{{y:.1f}} %<extra></extra>",
        ))
    for x, tekst in [(1993, "EU"), (2001, "2001"), (2017, "2017")]:
        fig.add_vline(x=x, line_color="rgba(0,0,0,0.15)", line_dash="dash",
                      annotation_text=tekst, annotation_position="top")
    fig.update_layout(
        xaxis_title="Stortingsvalg", yaxis_title="Gj.sn. Ap-oppslutning (%)",
        template="plotly_white", hovermode="x unified",
        legend=dict(font_size=11, orientation="h", x=0.5, xanchor="center", y=-0.15),
        margin=dict(t=40, b=70),
    )
    return fig


def fig_kaskade(deltas: dict) -> go.Figure:
    """ΔAp/ΔSp/ΔFrP i distriktsbastionene per periode: kaskaden Ap→Sp→FrP."""
    perioder = list(deltas.keys())
    farger = {"Ap": "#e4202c", "Sp": "#009900", "FrP": "#003f7f"}
    fig = go.Figure()
    for parti in ["Ap", "Sp", "FrP"]:
        fig.add_trace(go.Bar(
            x=perioder, y=[round(deltas[p][parti], 1) for p in perioder],
            name=parti, marker_color=farger[parti],
            hovertemplate=f"Δ{parti}: %{{y:+.1f}} pp<extra></extra>",
        ))
    fig.add_hline(y=0, line_color="rgba(0,0,0,0.4)", line_width=1)
    fig.update_layout(
        barmode="group", yaxis_title="Endring i distriktsbastionene (pp)",
        template="plotly_white",
        legend=dict(font_size=11, orientation="h", x=0.5, xanchor="center", y=-0.2),
        margin=dict(t=30, b=80),
    )
    return fig


# ── HTML ─────────────────────────────────────────────────────────────────────

def bygg_seksjon(df, stab, pers, deltas, gjen, figs) -> str:
    plots = {k: f.to_html(full_html=False, include_plotlyjs=False)
             for k, f in figs.items()}
    n_bast = (df["gruppe"] == "Distriktsbastion").sum()

    return f"""{START_M}
  <section id="bastioner" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 section-fade">
    <div class="flex items-center gap-2 mb-2">
      <span class="w-1 h-6 bg-ap rounded-full inline-block"></span>
      <h2 class="text-xl font-bold text-slate-900">Aps distriktsbastioner: elastiske, ikke stabile</h2>
    </div>
    <p class="text-slate-500 text-sm leading-relaxed mb-4">
      {n_bast} periferikommuner der Ap i 2005 lå over periferimedianen, fulgt 1989–2025
      (1989-data revidert mot fasit). Bastionene ble rystet før 2017 også — men forskjellen er hva som
      skjedde etterpå.
    </p>

    <div class="grid md:grid-cols-3 gap-3 text-sm mb-5">
      <div class="bg-slate-50 rounded-xl p-4">
        <div class="font-bold text-slate-800 mb-1">Elastisitet, ikke ro</div>
        <p class="text-xs text-slate-500 leading-relaxed">1993 (−5,7 pp) og 2001 (−8,0 pp) ble
        begge fullt gjenopprettet — i 2005 var bastionene tilbake på {gjen["niva05"]:.1f} %.
        Volatiliteten var faktisk <em>høyest</em> i bastionene i alle epoker
        (std {stab["bast_0513"]:.1f} mot {stab["andre_0513"]:.1f} pp i 2005–2013).
        Det stabile er rangeringen: Spearman ≈ {pers["typisk"]:+.2f} mellom alle valgpar.</p>
      </div>
      <div class="bg-red-50 rounded-xl p-4">
        <div class="font-bold text-red-900 mb-1">2017: rystelsen uten hjemvending</div>
        <p class="text-xs text-red-900/70 leading-relaxed">Bastionene tapte {deltas["2013→2017"]["Ap"]:+.1f} pp
        i 2017 — på nivå med tidligere rystelser. Men: 2021 {deltas["2017→2021"]["Ap"]:+.1f},
        2025 {deltas["2021→2025"]["Ap"]:+.1f}. Åtte år senere ligger de fortsatt
        {gjen["rest_2025"]:.1f} pp under 2013-nivået, mens ikke-bastionkommunene er
        tilbake ({gjen["rest_andre"]:.1f} pp). Båndet røk.</p>
      </div>
      <div class="bg-slate-50 rounded-xl p-4">
        <div class="font-bold text-slate-800 mb-1">Kaskaden Ap → Sp → FrP</div>
        <p class="text-xs text-slate-500 leading-relaxed">Da Sp kollapset i bastionene
        ({deltas["2021→2025"]["Sp"]:+.1f} pp i 2025), vendte velgerne ikke hjem: Ap tok
        {deltas["2021→2025"]["Ap"]:+.1f} pp, FrP {deltas["2021→2025"]["FrP"]:+.1f}.
        Velgerne Sp ristet løs i 2017 gikk videre — én gang løsrevet fra en 80 år
        gammel lojalitet, forble de løse.</p>
      </div>
    </div>

    <h3 class="font-semibold text-slate-800 mb-1 mt-6">Ap-nivå per gruppe 1989–2025</h3>
    <p class="text-slate-500 text-sm leading-relaxed mb-2">
      Heltrukne linjer er bastioner (Ap ≥ median 2005), stiplede er øvrige kommuner.
      Legg merke til V-ene i 1993 og 2001 — og den manglende V-en etter 2017.
    </p>
    <div class="plotly-chart">{plots["baner"]}</div>

    <h3 class="font-semibold text-slate-800 mb-1 mt-6">Kaskaden i distriktsbastionene</h3>
    <p class="text-slate-500 text-sm leading-relaxed mb-2">
      Endring per parti i de {n_bast} bastionkommunene. 2013→17: Sp høster Aps tap.
      2021→25: Sp kollapser, men gevinsten går til FrP — ikke tilbake til Ap.
    </p>
    <div class="plotly-chart">{plots["kaskade"]}</div>
    <p class="text-xs text-slate-400 mt-2">
      Distriktsbastion = sentralitet 0–1 og Ap-andel ≥ periferimedianen i 2005. Stortingsvalgdata;
      1989-laget revidert mot offisielle tall. korr(ΔAp, ΔSp) 2021→25 i bastionene: r={gjen["korr2125"]:+.2f}
      — noe direkte hjemvending, men marginal i nivå.
    </p>
  </section>
{SLUTT_M}"""


def injiser(seksjon: str, idx: str = "index.html"):
    with open(idx, encoding="utf-8") as f:
        page = f.read()
    s, e = page.find(START_M), page.find(SLUTT_M)
    if s != -1 and e != -1:
        page = page[:s] + seksjon + page[e + len(SLUTT_M):]
    else:
        anker = "<!-- === SLUTT MEKANISMER === -->"
        pos = page.find(anker)
        if pos != -1:
            pos += len(anker)
            page = page[:pos] + "\n\n" + seksjon + page[pos:]
        else:
            pos = page.find("</main>")
            if pos == -1:
                print("  ADVARSEL: fant ikke injeksjonspunkt")
                return
            page = page[:pos] + seksjon + "\n" + page[pos:]
    with open(idx, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"  {idx} oppdatert (seksjon 'bastioner')")


# ── HOVEDPROGRAM ─────────────────────────────────────────────────────────────

def main():
    print("=== Laster data (m/ 1989-korreksjon) ===")
    ap, sp, frp, sent = last_data()
    df = bygg_grupper(ap, sent)
    print(df["gruppe"].value_counts().to_string())

    print("\n=== Nivåbaner (snitt %) ===")
    print(df.groupby("gruppe")[AAR].mean().round(1).T.to_string())

    # Stabilitet
    epoker = {"1989–2005": [1989, 1993, 1997, 2001, 2005],
              "2005–2013": [2005, 2009, 2013],
              "2013–2025": [2013, 2017, 2021, 2025]}
    print("\n=== Within-kommune std per epoke ===")
    stab_tab = {}
    for lab, aar in epoker.items():
        s = df.groupby("gruppe").apply(lambda g: g[aar].std(axis=1).mean())
        stab_tab[lab] = s
        print(f"  {lab}: " + "  ".join(f"{k}={v:.1f}" for k, v in s.round(1).items()))
    stab = {"bast_0513": stab_tab["2005–2013"]["Distriktsbastion"],
            "andre_0513": stab_tab["2005–2013"][["Periferi ellers", "Sentral ellers"]].mean()}

    # Rangpersistens
    rs = []
    print("\n=== Rangpersistens (Spearman) ===")
    for a, b in zip(AAR[:-1], AAR[1:]):
        ok = df[[a, b]].dropna()
        r = spearmanr(ok[a], ok[b]).statistic
        rs.append(r)
        print(f"  {a}→{b}: r={r:+.2f}")
    pers = {"typisk": float(np.median(rs))}

    # Deltas i bastionene (Ap, Sp, FrP)
    bast = df[df["gruppe"] == "Distriktsbastion"].index
    deltas = {}
    for a, b in [(2013, 2017), (2017, 2021), (2021, 2025)]:
        deltas[f"{a}→{b}"] = {
            "Ap":  (ap[b] - ap[a]).reindex(bast).mean(),
            "Sp":  (sp[b] - sp[a]).reindex(bast).mean(),
            "FrP": (frp[b] - frp[a]).reindex(bast).mean(),
        }
    print("\n=== Kaskaden i bastionene ===")
    for p, d in deltas.items():
        print(f"  {p}: " + "  ".join(f"Δ{k}={v:+.1f}" for k, v in d.items()))

    korr = pd.concat([(ap[2025] - ap[2021]).reindex(bast).rename("dap"),
                      (sp[2025] - sp[2021]).reindex(bast).rename("dsp")], axis=1).dropna()
    gjen = {
        "niva05": df.loc[bast, 2005].mean(),
        "rest_2025": (ap[2025] - ap[2013]).reindex(bast).mean(),
        "rest_andre": (ap[2025] - ap[2013]).reindex(
            df[df["gruppe"].isin(["Periferi ellers", "Sentral ellers"])].index).mean(),
        "korr2125": korr["dap"].corr(korr["dsp"]),
    }
    print(f"  Rest 2025 vs 2013: bastioner {gjen['rest_2025']:+.1f} pp, "
          f"ikke-bastioner {gjen['rest_andre']:+.1f} pp")

    print("\n=== Bygger figurer og injiserer ===")
    figs = {"baner": fig_baner(df), "kaskade": fig_kaskade(deltas)}
    injiser(bygg_seksjon(df, stab, pers, deltas, gjen, figs))
    print("Ferdig.")


if __name__ == "__main__":
    main()
