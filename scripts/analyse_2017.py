#!/usr/bin/env python3
"""
analyse_2017.py — Dybdeanalyse av Sps gjennombrudd 2013→2017.

Inkluderer:
  1. Scatter: ΔSp 2013→2017 vs ΔPop 2007–2017 (per sentralitet)
  2. Sammenligning av tre bølger: 1993, 2017, 2021
  3. Regressionstabell for alle tre bølger
  4. Sentralitetsbar: ΔSp per gruppe i alle tre bølger

Injiserer ny seksjon "2017-analyse" i index.html.
"""

import warnings
import csv as csvmod
import numpy as np
import pandas as pd
import statsmodels.api as sm
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

PROCESSED = "data/processed"
RAW       = "data/raw"

PARTIER = {
    "01": "Ap", "02": "FrP", "03": "Høyre", "04": "KrF",
    "05": "Sp", "06": "SV", "07": "Venstre", "08": "MDG", "55": "Rødt",
}
SENTRALITET_NAVN = {0: "Minst sentrale", 1: "Mindre sentrale",
                    2: "Noe sentrale",   3: "Sentrale"}
SENT_FARGER = {0: "#d62728", 1: "#ff7f0e", 2: "#2ca02c", 3: "#1f77b4"}


# ── DATA ──────────────────────────────────────────────────────────────────────

def last_data():
    sv  = pd.read_csv(f"{PROCESSED}/stortingsvalg_2024.csv",
                      dtype={"kom2024": str, "parti": str})
    bef = pd.read_csv(f"{PROCESSED}/befolkning_2024.csv",
                      dtype={"kom2024": str})
    sv["parti"] = sv["parti"].map(PARTIER).fillna(sv["parti"])
    sv["aar"]   = sv["aar"].astype(int)
    bef["aar"]  = bef["aar"].astype(int)
    return sv, bef


def last_sentralitet():
    mapping = {}
    for row in csvmod.DictReader(open(f"{PROCESSED}/kom_mapping.csv")):
        if row["nr_2024"]:
            mapping[row["gammelt_nr"]] = row["nr_2024"]
    sent = pd.read_csv(f"{RAW}/sentralitet.csv", sep=";", quotechar='"',
                       encoding="latin1")
    sent = sent.rename(columns={"sourceCode": "sent_kode", "targetCode": "komm_nr_old"})
    sent["komm_nr_old"] = sent["komm_nr_old"].astype(str).str.zfill(4)
    sent["kom2024"]     = sent["komm_nr_old"].map(lambda x: mapping.get(x, x))
    sent["sent_kode"]   = pd.to_numeric(sent["sent_kode"], errors="coerce")
    sent = sent.sort_values("sent_kode").drop_duplicates("kom2024", keep="first")
    return sent[["kom2024", "sent_kode"]].copy()


def sp_delta(sv, y1, y2):
    p1 = sv[(sv["aar"] == y1) & (sv["parti"] == "Sp")].set_index("kom2024")["prosent"].rename("pst1")
    p2 = sv[(sv["aar"] == y2) & (sv["parti"] == "Sp")].set_index("kom2024")["prosent"].rename("pst2")
    df = pd.concat([p1, p2], axis=1).dropna()
    df["delta_sp"] = df["pst2"] - df["pst1"]
    navn = sv[sv["aar"] == y2][["kom2024", "navn"]].drop_duplicates("kom2024").set_index("kom2024")["navn"]
    df["navn"] = df.index.map(navn)
    return df.reset_index()


def pop_vekst(bef, y1, y2, colname="vekst"):
    b1 = bef[bef["aar"] == y1].set_index("kom2024")["befolkning"].rename("b1")
    b2 = bef[bef["aar"] == y2].set_index("kom2024")["befolkning"].rename("b2")
    df = pd.concat([b1, b2], axis=1).dropna()
    df = df[df["b1"] > 0]
    df[colname] = (df["b2"] - df["b1"]) / df["b1"] * 100
    return df[[colname]].reset_index()


def ols(df, y_col, x_col):
    d = df[[y_col, x_col]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(d) < 10:
        return {"beta": np.nan, "r2": np.nan, "p": np.nan, "n": len(d)}
    X = sm.add_constant(d[x_col])
    m = sm.OLS(d[y_col], X).fit()
    return {"beta": m.params[x_col], "r2": m.rsquared, "p": m.pvalues[x_col], "n": len(d)}


# ── BØLGE-DATASETT ────────────────────────────────────────────────────────────

BOLGER = [
    {"key": "1993", "label": "1993-bølgen",  "y1": 1989, "y2": 1993, "pop_fra": 1986, "pop_til": 1990, "farge": "#8B0000"},
    {"key": "2017", "label": "2017-bølgen",  "y1": 2013, "y2": 2017, "pop_fra": 2007, "pop_til": 2017, "farge": "#009900"},
    {"key": "2021", "label": "2021-bølgen",  "y1": 2017, "y2": 2021, "pop_fra": 2011, "pop_til": 2021, "farge": "#1f77b4"},
]


def bygg_bolge(sv, bef, sent, b):
    dsp   = sp_delta(sv, b["y1"], b["y2"])
    dpop  = pop_vekst(bef, b["pop_fra"], b["pop_til"], "vekst")
    df = dsp.merge(dpop, on="kom2024").merge(sent, on="kom2024", how="left")
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["delta_sp", "vekst", "sent_kode"])
    # Nivå-regresjon (Sp% ~ vekst) for y2
    sp_lev = sv[(sv["aar"] == b["y2"]) & (sv["parti"] == "Sp")][["kom2024","prosent"]].copy()
    sp_lev2 = pop_vekst(bef, b["pop_fra"], b["pop_til"], "vekst")
    lev = sp_lev.merge(sp_lev2, on="kom2024").merge(sent, on="kom2024", how="left")
    lev = lev.dropna(subset=["prosent","vekst","sent_kode"])
    return df, lev


# ── FIGURER ───────────────────────────────────────────────────────────────────

def fig_scatter_2017(df17, r_tot, r_sent):
    """Scatter ΔSp 2013→2017 vs ΔPop 2007→2017 per sentralitet."""
    fig = go.Figure()
    for kode in sorted(SENTRALITET_NAVN.keys()):
        sub = df17[df17["sent_kode"] == kode]
        r   = r_sent.get(kode, {})
        n   = r.get("n", len(sub))
        beta = r.get("beta", np.nan)
        p    = r.get("p", np.nan)
        sig  = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        fig.add_trace(go.Scatter(
            x=sub["vekst"], y=sub["delta_sp"],
            mode="markers",
            marker=dict(color=SENT_FARGER[kode], size=5, opacity=0.7),
            name=f"{SENTRALITET_NAVN[kode]} (β={beta:.3f}{sig}, n={n})" if not np.isnan(beta) else f"{SENTRALITET_NAVN[kode]} (n={n})",
            text=sub["navn"],
            hovertemplate="<b>%{text}</b><br>ΔPop: %{x:.1f}%<br>ΔSp: %{y:+.1f}pp<extra></extra>",
        ))
    x_lin = np.linspace(df17["vekst"].quantile(0.01), df17["vekst"].quantile(0.99), 100)
    b_tot = r_tot["beta"]
    int_  = (df17["delta_sp"] - b_tot * df17["vekst"]).mean()
    fig.add_trace(go.Scatter(
        x=x_lin, y=b_tot * x_lin + int_,
        mode="lines", line=dict(color="black", width=2, dash="dash"),
        name=f"Total β={b_tot:.3f}  R²={r_tot['r2']:.3f}",
    ))
    fig.update_layout(
        title="Sp-vekst 2013→2017 vs befolkningsendring 2007–2017",
        xaxis_title="Befolkningsendring 2007–2017 (%)",
        yaxis_title="ΔSp 2013→2017 (prosentpoeng)",
        template="plotly_white", height=500,
        legend=dict(x=0.01, y=0.99, font_size=11),
    )
    return fig


def fig_tre_bolger_scatter(bolge_data):
    """Tre-panel scatter: 1993, 2017, 2021 side om side."""
    titler = [f"ΔSp {b['y1']}→{b['y2']}" for b in BOLGER]
    fig = make_subplots(rows=1, cols=3, subplot_titles=titler, shared_yaxes=False)
    for col, (b, (df, _)) in enumerate(zip(BOLGER, bolge_data), 1):
        for kode in sorted(SENTRALITET_NAVN.keys()):
            sub = df[df["sent_kode"] == kode]
            fig.add_trace(go.Scatter(
                x=sub["vekst"], y=sub["delta_sp"],
                mode="markers",
                marker=dict(color=SENT_FARGER[kode], size=4, opacity=0.55),
                name=SENTRALITET_NAVN[kode],
                showlegend=(col == 1),
                text=sub["navn"],
                hovertemplate="<b>%{text}</b><br>ΔPop: %{x:.1f}%<br>ΔSp: %{y:+.1f}pp<extra></extra>",
            ), row=1, col=col)
        # Regresjonslinje
        r  = ols(df, "delta_sp", "vekst")
        if not np.isnan(r["beta"]):
            x_lin = np.linspace(df["vekst"].quantile(0.02), df["vekst"].quantile(0.98), 80)
            int_  = (df["delta_sp"] - r["beta"] * df["vekst"]).mean()
            sig   = "***" if r["p"] < 0.001 else "**" if r["p"] < 0.01 else "*" if r["p"] < 0.05 else "(n.s.)"
            fig.add_trace(go.Scatter(
                x=x_lin, y=r["beta"] * x_lin + int_,
                mode="lines", line=dict(color=b["farge"], width=2.5, dash="dash"),
                name=f"β={r['beta']:.3f}{sig}", showlegend=False,
            ), row=1, col=col)
        fig.add_hline(y=0, line_dash="dot", line_color="gray", row=1, col=col)

    fig.update_xaxes(title_text="ΔPop (%)")
    fig.update_yaxes(title_text="ΔSp (pp)", row=1, col=1)
    fig.update_layout(
        height=420, template="plotly_white",
        title="Tre Sp-bølger: endrings-mønster sammenligning",
        legend=dict(orientation="h", y=-0.2, font_size=10),
    )
    return fig


def fig_sentralitet_sammenlign(bolge_data):
    """
    Gruppert søylediagram: ΔSp per sentralitetskategori for 1993, 2017, 2021.
    Viser om mønsteret er mer/mindre periferi-konsentrert per bølge.
    """
    fig = go.Figure()
    for b, (df, _) in zip(BOLGER, bolge_data):
        agg = df.groupby("sent_kode")["delta_sp"].mean().reset_index()
        agg["label"] = agg["sent_kode"].map(SENTRALITET_NAVN)
        fig.add_trace(go.Bar(
            x=agg["label"], y=agg["delta_sp"].round(1),
            name=b["label"],
            marker_color=b["farge"],
            opacity=0.80,
            text=agg["delta_sp"].round(1).astype(str) + " pp",
            textposition="outside",
            hovertemplate=f"<b>{b['label']}</b> — %{{x}}: %{{y:+.1f}} pp<extra></extra>",
        ))
    fig.add_hline(y=0, line_color="black", line_width=1)
    fig.update_layout(
        barmode="group",
        title="Gjennomsnittlig ΔSp per sentralitetskategori: 1993, 2017, 2021",
        yaxis_title="Gjennomsnittlig ΔSp (prosentpoeng)",
        xaxis_title="Sentralitetskategori (SSB)",
        template="plotly_white",
        height=420,
        legend=dict(font_size=11),
    )
    return fig


def fig_korrelasjon_tre(bolge_data):
    """
    Krysskorrelasjon ΔSp 1993 vs 2017 vs 2021 på kommunenivå.
    To scatter: 1993 vs 2017, og 2017 vs 2021.
    """
    d93  = bolge_data[0][0][["kom2024","delta_sp"]].rename(columns={"delta_sp":"d93"})
    d17  = bolge_data[1][0][["kom2024","delta_sp"]].rename(columns={"delta_sp":"d17"})
    d21  = bolge_data[2][0][["kom2024","delta_sp"]].rename(columns={"delta_sp":"d21"})
    navn = bolge_data[1][0][["kom2024","navn"]]
    f93_17 = d93.merge(d17, on="kom2024").merge(navn, on="kom2024", how="left")
    f17_21 = d17.merge(d21, on="kom2024").merge(navn, on="kom2024", how="left")
    r1 = f93_17[["d93","d17"]].corr().iloc[0,1]
    r2 = f17_21[["d17","d21"]].corr().iloc[0,1]

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=[
                            f"ΔSp 1993 vs 2017 (r={r1:.2f})",
                            f"ΔSp 2017 vs 2021 (r={r2:.2f})",
                        ])
    for col, (felles, xc, yc, farge) in enumerate([
        (f93_17, "d93", "d17", "#8B0000"),
        (f17_21, "d17", "d21", "#009900"),
    ], 1):
        fig.add_trace(go.Scatter(
            x=felles[xc], y=felles[yc],
            mode="markers",
            marker=dict(size=4, color=farge, opacity=0.55),
            text=felles["navn"],
            hovertemplate="<b>%{text}</b><br>x: %{x:+.1f}pp<br>y: %{y:+.1f}pp<extra></extra>",
            showlegend=False,
        ), row=1, col=col)
        b = np.polyfit(felles[xc].values, felles[yc].values, 1)
        x_lin = np.linspace(felles[xc].min(), felles[xc].max(), 80)
        fig.add_trace(go.Scatter(
            x=x_lin, y=np.polyval(b, x_lin),
            mode="lines", line=dict(color="black", dash="dash", width=1.5),
            showlegend=False,
        ), row=1, col=col)
        fig.add_hline(y=0, line_dash="dot", line_color="gray", row=1, col=col)
        fig.add_vline(x=0, line_dash="dot", line_color="gray", row=1, col=col)

    fig.update_layout(
        height=420, template="plotly_white",
        title="Er det de samme kommunene som svinger med Sp i alle tre bølger?",
    )
    return fig, r1, r2


def fig_topp20_2017(df17):
    top20 = df17.nlargest(20, "delta_sp").sort_values("delta_sp")
    colors = [SENT_FARGER.get(int(s) if not pd.isna(s) else -1, "#888")
              for s in top20["sent_kode"]]
    fig = go.Figure(go.Bar(
        x=top20["delta_sp"],
        y=top20["navn"],
        orientation="h",
        marker_color=colors,
        text=[f"Sp={r:.1f}%" for r in top20["pst2"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>ΔSp: %{x:+.1f}pp<extra></extra>",
    ))
    fig.update_layout(
        title="Topp 20 kommuner: Sp-vekst 2013→2017",
        xaxis_title="ΔSp 2013→2017 (pp)",
        template="plotly_white", height=560,
        margin=dict(l=160),
    )
    return fig


# ── HTML ──────────────────────────────────────────────────────────────────────

def lag_html(df17, r_tot, r_sent, bolge_data, r1, r2,
             fig_sc, fig_3, fig_sent, fig_korr, fig_top):
    import plotly
    sc_html   = fig_sc.to_html(full_html=False, include_plotlyjs=False)
    tre_html  = fig_3.to_html(full_html=False, include_plotlyjs=False)
    sent_html = fig_sent.to_html(full_html=False, include_plotlyjs=False)
    korr_html = fig_korr.to_html(full_html=False, include_plotlyjs=False)
    top_html  = fig_top.to_html(full_html=False, include_plotlyjs=False)

    # Reg-tabell
    reg_rader = ""
    for b, (df, _) in zip(BOLGER, bolge_data):
        r = ols(df, "delta_sp", "vekst")
        sig = "***" if r["p"] < 0.001 else "**" if r["p"] < 0.01 else "*" if r["p"] < 0.05 else "(n.s.)"
        reg_rader += (
            f'<tr><td>{b["label"]}</td>'
            f'<td class="num">{r["beta"]:+.4f}{sig}</td>'
            f'<td class="num">{r["r2"]:.3f}</td>'
            f'<td class="num">{r["p"]:.4f}</td>'
            f'<td class="num">{r["n"]}</td></tr>\n'
        )

    # Sentralitet per bølge-tabell
    sent_rader = ""
    for kode in sorted(SENTRALITET_NAVN.keys()):
        sent_rader += f'<tr><td>{SENTRALITET_NAVN[kode]}</td>'
        for _, (df, _) in zip(BOLGER, bolge_data):
            sub = df[df["sent_kode"] == kode]["delta_sp"]
            mn  = sub.mean() if len(sub) else np.nan
            col = "#166534" if mn > 0 else "#991b1b" if mn < 0 else "#6b7280"
            sent_rader += f'<td class="num" style="color:{col};font-weight:{"700" if abs(mn)>10 else "400"}">{mn:+.1f}</td>'
        sent_rader += "</tr>\n"

    sp_nat = {b["key"]: ols(df, "delta_sp", "vekst") for b, (df, _) in zip(BOLGER, bolge_data)}

    return f"""<!-- === 2017-ANALYSE SEKSJON === -->
<section id="analyse2017" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
<div class="mb-4">
  <h2 class="text-xl font-bold text-slate-900 mb-2">Sp-gjennombrudd 2013→2017 — dybdeanalyse</h2>
  <p class="text-slate-500 text-sm leading-relaxed">
    Sp doblet sin oppslutning fra 5,6&nbsp;% i 2013 til 10,5&nbsp;% i 2017 (+4,9&nbsp;pp).
    Analysen undersøker om dette gjennombruddets geografi likner 1993-bølgen
    eller snarere var en forsmak på den enda bredere 2021-bølgen.
  </p>
</div>

<h3 class="text-base font-semibold text-slate-800 mt-4 mb-1">1. Sp-vekst vs befolkningsendring 2013→2017</h3>
<p class="text-slate-500 text-sm mb-2">
  β&nbsp;= {r_tot["beta"]:+.4f}, R²&nbsp;= {r_tot["r2"]:.3f}, p&nbsp;= {r_tot["p"]:.4f},
  n&nbsp;= {r_tot["n"]}.
  Sterk negativ sammenheng: kommuner med befolkningsnedgang fikk høyest Sp-vekst.
  Til sammenligning var β&nbsp;≈&nbsp;0 for 2021 (bred bølge),
  mens 1993 hadde β&nbsp;≈&nbsp;−0,48.
  2017-gjennombruddets β ({r_tot["beta"]:+.3f}) er altså <em>mer</em> periferkonsentrert enn 1993.
</p>
{sc_html}

<h3 class="text-base font-semibold text-slate-800 mt-5 mb-1">2. Topp 20 kommuner: Sp-vekst 2013→2017</h3>
{top_html}

<h3 class="text-base font-semibold text-slate-800 mt-5 mb-1">3. Tre bølger sammenligning</h3>
<p class="text-slate-500 text-sm mb-2">
  Scatter-panelene viser samme mønster: β-stigningstallet er negativt i alle tre,
  men skråningen er langt brattest i 2017 og 1993 — og nær flat i 2021.
</p>
{tre_html}

<h4 class="text-sm font-semibold text-slate-700 mt-4 mb-1">Regresjonsresultater (ΔSp ~ ΔPop)</h4>
<table>
  <thead><tr><th>Bølge</th><th>β</th><th>R²</th><th>p</th><th>n</th></tr></thead>
  <tbody>{reg_rader}</tbody>
</table>
<p class="text-xs text-slate-400 mt-1">*** p &lt; 0,001. Endringer-regresjon: ΔSp som funksjon av befolkningsvekst.</p>

<h3 class="text-base font-semibold text-slate-800 mt-5 mb-1">4. ΔSp per sentralitetskategori</h3>
<p class="text-slate-500 text-sm mb-2">
  I 2017 og 1993 var Sp-veksten kraftig konsentrert til de minst sentrale kommunene.
  I 2021 var forskjellen mellom kategoriene mye mindre — alle kommunetyper vokste Sp omtrent likt.
</p>
{sent_html}
<details><summary class="text-sm text-slate-500 cursor-pointer">Talltabell</summary>
<table>
  <thead>
    <tr><th>Sentralitet</th><th>1993-bølgen</th><th>2017-bølgen</th><th>2021-bølgen</th></tr>
  </thead>
  <tbody>{sent_rader}</tbody>
</table>
</details>

<h3 class="text-base font-semibold text-slate-800 mt-5 mb-1">5. Er det de samme kommunene som svinger med Sp?</h3>
<p class="text-slate-500 text-sm mb-2">
  Korrelasjonen ΔSp 1993 vs ΔSp 2017 er r&nbsp;=&nbsp;<strong>{r1:.2f}</strong> —
  tydelig positiv: kommunene som ledet 1993-opprøret ledet også 2017-gjennombrudddet.
  Derimot er korrelasjonen ΔSp 2017 vs ΔSp 2021 bare r&nbsp;=&nbsp;<strong>{r2:.2f}</strong> —
  svakere, fordi 2021-bølgen rammet bredere og geografisk annerledes.
</p>
{korr_html}

</section>
<!-- === SLUTT 2017-ANALYSE === -->"""


# ── INJECT ────────────────────────────────────────────────────────────────────

def inject_html(ny_html, start_m, end_m, idx="index.html"):
    try:
        with open(idx, encoding="utf-8") as f:
            page = f.read()
        s = page.find(start_m)
        e = page.find(end_m)
        if s != -1 and e != -1:
            e += len(end_m)
            page = page[:s] + ny_html.strip() + "\n" + page[e:]
        else:
            # Append etter slutt sp_matrise
            slutt = "<!-- === SLUTT SP MATRISE === -->"
            pos = page.find(slutt)
            if pos != -1:
                pos += len(slutt)
                page = page[:pos] + "\n\n" + ny_html.strip() + "\n" + page[pos:]
            else:
                print("  Advarsel: fant ingen passende injeksjonspunkt")
                return
        with open(idx, "w", encoding="utf-8") as f:
            f.write(page)
        print(f"  {idx} oppdatert")
    except FileNotFoundError:
        print(f"  Advarsel: {idx} ikke funnet")


def legg_til_nav_link(idx="index.html"):
    with open(idx, encoding="utf-8") as f:
        page = f.read()
    marker = '<a href="#analyse2021"'
    link   = '<a href="#analyse2017" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">2017-analyse</a>\n      '
    if "#analyse2017" not in page:
        page = page.replace(marker, link + marker, 1)
        with open(idx, "w", encoding="utf-8") as f:
            f.write(page)
        print("  Nav-link for 2017-analyse lagt til")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("Laster data…")
    sv, bef = last_data()
    sent     = last_sentralitet()

    print("Beregner 2013→2017 analyse…")
    # 2017-analyse
    dsp17 = sp_delta(sv, 2013, 2017)
    dpop17 = pop_vekst(bef, 2007, 2017)
    df17 = dsp17.merge(dpop17, on="kom2024").merge(sent, on="kom2024", how="left")
    df17 = df17.dropna(subset=["delta_sp", "vekst", "sent_kode"])
    print(f"  Kommuner med data: {len(df17)}")

    r_tot = ols(df17, "delta_sp", "vekst")
    r_sent = {}
    print(f"\n2017-bølgen (total): β={r_tot['beta']:+.4f}, R²={r_tot['r2']:.3f}, p={r_tot['p']:.4f}")
    for kode, navn in SENTRALITET_NAVN.items():
        sub = df17[df17["sent_kode"] == kode]
        r   = ols(sub, "delta_sp", "vekst")
        r_sent[kode] = r
        print(f"  {navn}: β={r['beta']:+.4f}, R²={r['r2']:.3f}, p={r['p']:.4f}, n={r['n']}")

    print("\nBeregner alle tre bølger…")
    bolge_data = [bygg_bolge(sv, bef, sent, b) for b in BOLGER]

    print("Lager figurer…")
    fig_sc   = fig_scatter_2017(df17, r_tot, r_sent)
    fig_top  = fig_topp20_2017(df17)
    fig_3    = fig_tre_bolger_scatter(bolge_data)
    fig_sent = fig_sentralitet_sammenlign(bolge_data)
    fig_korr, r1, r2 = fig_korrelasjon_tre(bolge_data)

    print(f"\nKorrelasjon ΔSp 1993 vs ΔSp 2017: r={r1:.3f}")
    print(f"Korrelasjon ΔSp 2017 vs ΔSp 2021: r={r2:.3f}")

    html = lag_html(df17, r_tot, r_sent, bolge_data, r1, r2,
                    fig_sc, fig_3, fig_sent, fig_korr, fig_top)

    print("Injiserer i index.html…")
    inject_html(
        html,
        "<!-- === 2017-ANALYSE SEKSJON === -->",
        "<!-- === SLUTT 2017-ANALYSE === -->",
    )
    legg_til_nav_link()
    print("Ferdig.")


if __name__ == "__main__":
    main()
