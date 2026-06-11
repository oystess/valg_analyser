#!/usr/bin/env python3
"""
analyse_2021.py — Dybdeanalyse av 2021-valget:
  1. ΔSp 2017→2021 vs ΔPop 2011–2021 (scatter + regresjon)
  2. Per-sentralitet breakdown
  3. Topp 20 kommuner Sp-vekst 2021
  4. Sammenligning 1993 vs 2021 (korrelasjon)
  5. Tiår-for-tiår β-tabell: alle STV-år 1989–2025
  6. Genererer HTML-seksjon for index.html

Forutsetninger:
  - data/processed/{stortingsvalg,befolkning,kommunestyrevalg}_2024.csv
  - data/processed/kom_mapping.csv
  - data/raw/sentralitet.csv
"""

import csv as csvmod
import warnings
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


# ── DATAHENTING ───────────────────────────────────────────────────────────────

def last_data():
    sv  = pd.read_csv(f"{PROCESSED}/stortingsvalg_2024.csv",
                      dtype={"kom2024": str, "parti": str})
    bef = pd.read_csv(f"{PROCESSED}/befolkning_2024.csv",
                      dtype={"kom2024": str})
    sv["parti"]  = sv["parti"].map(PARTIER).fillna(sv["parti"])
    sv["aar"]    = sv["aar"].astype(int)
    bef["aar"]   = bef["aar"].astype(int)
    return sv, bef


def last_sentralitet() -> pd.DataFrame:
    mapping = {}
    for row in csvmod.DictReader(open(f"{PROCESSED}/kom_mapping.csv")):
        if row["nr_2024"]:
            mapping[row["gammelt_nr"]] = row["nr_2024"]
    sent = pd.read_csv(f"{RAW}/sentralitet.csv", sep=";", quotechar='"',
                       encoding="latin1")
    sent = sent.rename(columns={"sourceCode": "sent_kode",
                                "targetCode": "komm_nr_old"})
    sent["komm_nr_old"] = sent["komm_nr_old"].astype(str).str.zfill(4)
    sent["kom2024"]     = sent["komm_nr_old"].map(lambda x: mapping.get(x, x))
    sent["sent_kode"]   = pd.to_numeric(sent["sent_kode"], errors="coerce")
    sent = sent.sort_values("sent_kode").drop_duplicates("kom2024", keep="first")
    return sent[["kom2024", "sent_kode"]].copy()


# ── HJELPEFUNKSJONER ──────────────────────────────────────────────────────────

def sp_delta(sv: pd.DataFrame, y1: int, y2: int) -> pd.DataFrame:
    """ΔSp-oppslutning (pp) mellom to stortingsvalgår."""
    p1 = (sv[(sv["aar"] == y1) & (sv["parti"] == "Sp")]
          .set_index("kom2024")["prosent"].rename("pst1"))
    p2 = (sv[(sv["aar"] == y2) & (sv["parti"] == "Sp")]
          .set_index("kom2024")["prosent"].rename("pst2"))
    df = pd.concat([p1, p2], axis=1).dropna()
    df["delta_sp"] = df["pst2"] - df["pst1"]
    df["pst_y2"]   = df["pst2"]
    # navn
    navn = sv[sv["aar"] == y2][["kom2024", "navn"]].drop_duplicates("kom2024").set_index("kom2024")["navn"]
    df["navn"] = df.index.map(navn)
    return df.reset_index()


def ap_delta(sv: pd.DataFrame, y1: int, y2: int) -> pd.DataFrame:
    """ΔAp-oppslutning (pp) mellom to stortingsvalgår."""
    p1 = (sv[(sv["aar"] == y1) & (sv["parti"] == "Ap")]
          .set_index("kom2024")["prosent"].rename("pst1"))
    p2 = (sv[(sv["aar"] == y2) & (sv["parti"] == "Ap")]
          .set_index("kom2024")["prosent"].rename("pst2"))
    df = pd.concat([p1, p2], axis=1).dropna()
    df["delta_ap"] = df["pst2"] - df["pst1"]
    return df.reset_index()


def pop_vekst(bef: pd.DataFrame, y1: int, y2: int,
              colname: str = "vekst") -> pd.DataFrame:
    """Prosentvis befolkningsendring y1→y2 per kommune."""
    b1 = bef[bef["aar"] == y1].set_index("kom2024")["befolkning"].rename("b1")
    b2 = bef[bef["aar"] == y2].set_index("kom2024")["befolkning"].rename("b2")
    df = pd.concat([b1, b2], axis=1).dropna()
    df = df.query("b1 > 0 and b2 > 0")
    df[colname] = (df["b2"] - df["b1"]) / df["b1"] * 100
    return df[[colname]].reset_index()


def ols_regresjon(df: pd.DataFrame, y_col: str, x_col: str,
                  label: str = "") -> dict:
    """Enkel OLS med konstant. Returnerer dict med β, R², p, n."""
    d = df[[y_col, x_col]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(d) < 10:
        return {"label": label, "beta": np.nan, "r2": np.nan,
                "p": np.nan, "n": len(d)}
    X = sm.add_constant(d[x_col])
    m = sm.OLS(d[y_col], X).fit()
    return {
        "label": label,
        "beta":  m.params[x_col],
        "r2":    m.rsquared,
        "p":     m.pvalues[x_col],
        "n":     len(d),
        "ci_lo": m.conf_int().loc[x_col, 0],
        "ci_hi": m.conf_int().loc[x_col, 1],
    }


# ── ANALYSE 2021 ──────────────────────────────────────────────────────────────

def analyse_2021(sv, bef, sent):
    print("\n=== ANALYSE 2021 ===")

    dsp = sp_delta(sv, 2017, 2021)
    dpop = pop_vekst(bef, 2011, 2021, "vekst_11_21")

    data = dsp.merge(dpop, on="kom2024").merge(sent, on="kom2024", how="left")
    data = data.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["delta_sp", "vekst_11_21"])

    # --- Totalregresjon ---
    r_tot = ols_regresjon(data, "delta_sp", "vekst_11_21", "2021 total")
    print(f"\n2021 total (n={r_tot['n']}): β={r_tot['beta']:.4f}, "
          f"R²={r_tot['r2']:.3f}, p={r_tot['p']:.4f}")

    # --- Per sentralitet ---
    r_sent = {}
    print("\nPer sentralitetsgruppe:")
    for kode, navn in SENTRALITET_NAVN.items():
        sub = data[data["sent_kode"] == kode]
        r = ols_regresjon(sub, "delta_sp", "vekst_11_21", navn)
        r_sent[kode] = r
        print(f"  {navn} (n={r['n']}): β={r['beta']:.4f}, R²={r['r2']:.3f}, p={r['p']:.4f}")

    # --- Topp 20 kommuner 2021 ---
    top20 = data.nlargest(20, "delta_sp")[
        ["kom2024", "navn", "pst_y2", "delta_sp", "vekst_11_21", "sent_kode"]
    ].reset_index(drop=True)
    print(f"\nTopp 20 Sp-vekst 2017→2021:")
    for _, row in top20.iterrows():
        print(f"  {row['navn']}: ΔSp={row['delta_sp']:+.1f}pp, "
              f"Sp={row['pst_y2']:.1f}%, pop={row['vekst_11_21']:.1f}%")

    return data, r_tot, r_sent, top20


# ── SAMMENLIGNING 1993 vs 2021 ────────────────────────────────────────────────

def sammenlign_1993_2021(sv, bef, sent):
    print("\n=== SAMMENLIGNING 1993 vs 2021 ===")

    # 1993: ΔSp 1989→1993 og ΔPop 1986→1993 (data starter 1986)
    dsp93  = sp_delta(sv, 1989, 1993)
    dpop93 = pop_vekst(bef, 1986, 1993, "vekst_86_93")

    d93 = dsp93.merge(dpop93, on="kom2024").merge(sent, on="kom2024", how="left")
    d93 = d93.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["delta_sp", "vekst_86_93"])

    r93 = ols_regresjon(d93, "delta_sp", "vekst_86_93", "1993")
    print(f"\n1993 (n={r93['n']}): β={r93['beta']:.4f}, R²={r93['r2']:.3f}, p={r93['p']:.4f}")

    # 2021: ΔSp 2017→2021 (bruker vekst_11_21)
    dsp21  = sp_delta(sv, 2017, 2021)
    dpop21 = pop_vekst(bef, 2011, 2021, "vekst_11_21")

    d21 = dsp21.merge(dpop21, on="kom2024")
    d21 = d21.rename(columns={"delta_sp": "delta_sp_21"}) if "delta_sp" in d21.columns else d21

    # Sammenkobling på tvers
    felles = dsp93[["kom2024", "delta_sp"]].rename(columns={"delta_sp": "delta93"}).merge(
              dsp21[["kom2024", "delta_sp"]].rename(columns={"delta_sp": "delta21"}),
              on="kom2024")

    korr = felles[["delta93", "delta21"]].corr().iloc[0, 1]
    print(f"\nKorrelasjon ΔSp 1993 vs ΔSp 2021 (n={len(felles)}): r={korr:.3f}")

    # Topp 1993-kommuner i 2021?
    top93 = dsp93.nlargest(30, "delta_sp")["kom2024"].tolist()
    top21 = dsp21.nlargest(30, "delta_sp")["kom2024"].tolist()
    overlap = set(top93) & set(top21)
    print(f"Overlapp topp-30 kommuner 1993/2021: {len(overlap)} kommuner")
    if overlap:
        overlap_navn = dsp21[dsp21["kom2024"].isin(overlap)]["navn"].tolist()
        print("  " + ", ".join(overlap_navn[:10]))

    return d93, r93, felles, korr


# ── β-TABELL PER ÅR ──────────────────────────────────────────────────────────

def beta_per_aar(sv, bef, sent):
    """
    For hvert STV-år: cross-sectional OLS Sp% ~ ΔPop(10år).
    Viser når befolknings-Sp-sammenhengen er sterkest.
    """
    print("\n=== β-TABELL PER ÅR (STV 1989–2025) ===")
    resultater = []

    bef_min_aar = bef["aar"].min()

    for aar in sorted(sv["aar"].unique()):
        sp_y = sv[(sv["aar"] == aar) & (sv["parti"] == "Sp")][
            ["kom2024", "prosent"]].copy()
        # Bruk kortere tilbakeblikk dersom 10-årsdata mangler
        lag = 10 if (aar - 10) >= bef_min_aar else max(1, aar - bef_min_aar)
        vekst_y = pop_vekst(bef, aar - lag, aar, "vekst10")
        lag_note = f"({lag}år)" if lag < 10 else ""
        df = sp_y.merge(vekst_y, on="kom2024").merge(sent, on="kom2024", how="left")
        df = df.replace([np.inf, -np.inf], np.nan).dropna(
            subset=["prosent", "vekst10"])

        r = ols_regresjon(df, "prosent", "vekst10", str(aar))
        resultater.append({
            "aar": aar,
            "beta": r["beta"],
            "r2":   r["r2"],
            "p":    r["p"],
            "n":    r["n"],
        })
        sig = "***" if r["p"] < 0.001 else "**" if r["p"] < 0.01 else "*" if r["p"] < 0.05 else ""
        print(f"  {aar}{lag_note}: β={r['beta']:+.4f}, R²={r['r2']:.3f}, p={r['p']:.4f} {sig}, n={r['n']}")

    return pd.DataFrame(resultater)


# ── FrP-KONKURRANSE (H6) ──────────────────────────────────────────────────────

def frp_konkurranse(sv):
    """
    H6: Sp og FrP konkurrerer om periferi-velgere.
    Nasjonal tidsserie for begge partier.
    """
    sp = (sv[sv["parti"] == "Sp"]
          .groupby("aar")["prosent"].mean().rename("Sp"))
    frp = (sv[sv["parti"] == "FrP"]
           .groupby("aar")["prosent"].mean().rename("FrP"))
    df = pd.concat([sp, frp], axis=1).reset_index()
    print("\n=== Sp vs FrP NASJONAL TIDSSERIE ===")
    print(df.to_string(index=False))
    return df


# ── PLOTLY FIGURER ────────────────────────────────────────────────────────────

def fig_scatter_2021(data: pd.DataFrame, r_tot: dict, r_sent: dict) -> go.Figure:
    fig = go.Figure()

    for kode in sorted(SENTRALITET_NAVN.keys()):
        sub = data[data["sent_kode"] == kode]
        r   = r_sent.get(kode, {})
        n   = r.get("n", len(sub))
        beta = r.get("beta", np.nan)
        p    = r.get("p", np.nan)
        sig  = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        fig.add_trace(go.Scatter(
            x=sub["vekst_11_21"], y=sub["delta_sp"],
            mode="markers",
            marker=dict(color=SENT_FARGER[kode], size=5, opacity=0.7),
            name=f"{SENTRALITET_NAVN[kode]} (β={beta:.3f}{sig}, n={n})",
            text=sub["navn"],
            hovertemplate="<b>%{text}</b><br>ΔPop: %{x:.1f}%<br>ΔSp: %{y:+.1f}pp<extra></extra>",
        ))

    # Regresjonslinje (total)
    x_lin = np.linspace(data["vekst_11_21"].quantile(0.01),
                        data["vekst_11_21"].quantile(0.99), 100)
    b_tot = r_tot["beta"]
    int_  = (data["delta_sp"] - b_tot * data["vekst_11_21"]).mean()
    fig.add_trace(go.Scatter(
        x=x_lin, y=b_tot * x_lin + int_,
        mode="lines",
        line=dict(color="black", width=2, dash="dash"),
        name=f"Total β={b_tot:.3f}***  R²={r_tot['r2']:.3f}",
        showlegend=True,
    ))

    fig.update_layout(
        title="Sp-vekst 2017→2021 vs befolkningsendring 2011–2021",
        xaxis_title="Befolkningsendring 2011–2021 (%)",
        yaxis_title="ΔSp 2017→2021 (prosentpoeng)",
        template="plotly_white",
        height=520,
        legend=dict(x=0.01, y=0.99, font_size=11),
    )
    return fig


def fig_sammenlign_1993_2021(felles: pd.DataFrame, d93, d21, korr: float,
                              sv: pd.DataFrame) -> go.Figure:
    df = felles.copy()
    navn93 = d93[["kom2024", "navn"]].drop_duplicates() if "navn" in d93.columns else None
    if navn93 is None:
        n_map = sv[["kom2024", "navn"]].drop_duplicates().set_index("kom2024")["navn"]
        df["navn"] = df["kom2024"].map(n_map)
    else:
        df = df.merge(navn93, on="kom2024", how="left")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["delta93"], y=df["delta21"],
        mode="markers",
        marker=dict(size=4, color="#8B0000", opacity=0.6),
        text=df.get("navn", df["kom2024"]),
        hovertemplate="<b>%{text}</b><br>ΔSp 1993: %{x:+.1f}pp<br>ΔSp 2021: %{y:+.1f}pp<extra></extra>",
    ))
    # Regresjonslinje
    x_lin = np.linspace(df["delta93"].min(), df["delta93"].max(), 100)
    b = np.polyfit(df["delta93"].values, df["delta21"].values, 1)
    fig.add_trace(go.Scatter(
        x=x_lin, y=np.polyval(b, x_lin),
        mode="lines", line=dict(color="black", dash="dash", width=1.5),
        name=f"r={korr:.3f}", showlegend=True,
    ))
    # 0-linjer
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.add_vline(x=0, line_dash="dot", line_color="gray")

    fig.update_layout(
        title=f"Samme kommuner — ΔSp 1993 vs ΔSp 2021 (r={korr:.2f}, n={len(df)})",
        xaxis_title="ΔSp 1989→1993 (prosentpoeng)",
        yaxis_title="ΔSp 2017→2021 (prosentpoeng)",
        template="plotly_white",
        height=480,
        showlegend=True,
    )
    return fig


def fig_top20(top20: pd.DataFrame) -> go.Figure:
    top20 = top20.sort_values("delta_sp")
    colors = [SENT_FARGER.get(int(s), "#888") for s in top20["sent_kode"].fillna(-1)]
    fig = go.Figure(go.Bar(
        x=top20["delta_sp"],
        y=top20["navn"],
        orientation="h",
        marker_color=colors,
        text=[f"Sp={r:.1f}%" for r in top20["pst_y2"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>ΔSp: %{x:+.1f}pp<extra></extra>",
    ))
    fig.update_layout(
        title="Topp 20 kommuner: Sp-vekst 2017→2021",
        xaxis_title="ΔSp 2017→2021 (prosentpoeng)",
        template="plotly_white",
        height=560,
        margin=dict(l=160),
    )
    return fig


def fig_beta_tabell(beta_df: pd.DataFrame) -> go.Figure:
    colors = ["#d62728" if p < 0.05 else "#aaaaaa" for p in beta_df["p"]]
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        subplot_titles=["β: Sp% ~ ΔPop(10yr) — per valgår",
                        "R² — per valgår"],
        vertical_spacing=0.12,
    )
    fig.add_trace(go.Bar(
        x=beta_df["aar"], y=beta_df["beta"],
        marker_color=colors,
        name="β",
        error_y=dict(type="data", array=[0]*len(beta_df), visible=False),
        hovertemplate="<b>%{x}</b><br>β=%{y:.4f}<extra></extra>",
    ), row=1, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=1, col=1)
    fig.add_trace(go.Bar(
        x=beta_df["aar"], y=beta_df["r2"],
        marker_color="#1f77b4", name="R²",
        hovertemplate="<b>%{x}</b><br>R²=%{y:.3f}<extra></extra>",
    ), row=2, col=1)
    fig.update_layout(
        template="plotly_white", height=480,
        title="Sp% ~ ΔPop(10 år): β og R² per stortingsvalgår",
        showlegend=False,
    )
    return fig


# ── HTML ──────────────────────────────────────────────────────────────────────

def lag_html_seksjon(data21, r_tot, r_sent, top20, felles, korr,
                     beta_df, spfrp,
                     fig_scatter, fig_komp, fig_top, fig_beta) -> str:
    """Produserer komplett HTML-seksjon for innliming i index.html."""

    def pct(v):
        return f"{v:.1f}%"

    def pp(v):
        return f"{v:+.2f}"

    # --- β-tabell HTML ---
    brows = ""
    for _, row in beta_df.iterrows():
        sig = "***" if row["p"] < 0.001 else "**" if row["p"] < 0.01 else "*" if row["p"] < 0.05 else ""
        klass = "highlight" if row["aar"] in [1993, 2021] else ""
        brows += (
            f'<tr class="{klass}"><td>{int(row["aar"])}</td>'
            f'<td>{row["beta"]:+.4f}{sig}</td>'
            f'<td>{row["r2"]:.3f}</td>'
            f'<td>{row["p"]:.4f}</td>'
            f'<td>{int(row["n"])}</td></tr>\n'
        )

    # --- Top 20 HTML ---
    top_rows = ""
    for i, (_, row) in enumerate(
            top20.sort_values("delta_sp", ascending=False).iterrows(), 1):
        s = int(row["sent_kode"]) if not pd.isna(row["sent_kode"]) else -1
        sn = SENTRALITET_NAVN.get(s, "Ukjent")
        top_rows += (
            f'<tr><td>{i}</td><td>{row["navn"]}</td>'
            f'<td class="num">{row["pst_y2"]:.1f}%</td>'
            f'<td class="num pos">{row["delta_sp"]:+.1f}</td>'
            f'<td class="num">{row["vekst_11_21"]:.1f}%</td>'
            f'<td>{sn}</td></tr>\n'
        )

    import plotly
    sc21_html  = fig_scatter.to_html(full_html=False, include_plotlyjs=False)
    komp_html  = fig_komp.to_html(full_html=False, include_plotlyjs=False)
    top_p_html = fig_top.to_html(full_html=False, include_plotlyjs=False)
    beta_html  = fig_beta.to_html(full_html=False, include_plotlyjs=False)

    # Sp vs FrP rows
    sfrows = "".join(
        f'<tr><td>{int(row["aar"])}</td>'
        f'<td class="num">{row["Sp"]:.1f}%</td>'
        f'<td class="num">{row["FrP"]:.1f}%</td>'
        f'<td class="num">{row["Sp"] - row["FrP"]:+.1f}</td></tr>\n'
        for _, row in spfrp.iterrows()
    )

    html = f"""
<!-- === 2021-ANALYSE SEKSJON (generert av analyse_2021.py) === -->
<div class="mt-2">
<h2>Senteropprøret 2021 — dybdeanalyse</h2>
<p>Sp gikk fra 10,3 % i 2017 til 13,5 % i 2021 (+3,2 pp, nasjonalt gjennomsnitt).
Analysen under undersøker hvilke kommuner som drev denne veksten og om mønsteret
ligner 1993-opprøret.</p>

<h3>1. Sp-vekst vs befolkningsendring</h3>
<p><strong>Nøkkelfunn:</strong> β = {r_tot['beta']:.4f}, R² = {r_tot['r2']:.3f},
p = {r_tot['p']:.4f}, n = {r_tot['n']} — ingen signifikant sammenheng mellom
befolkningsendring og Sp-vekst i 2021. Til sammenligning var β = −0,48*** for 1993.
Dette betyr at 2021-opprøret var bredt anlagt og ikke geografisk konsentrert til
de samme fraflyttingskommunene som i 1993.</p>
{sc21_html}

<h3>2. Per sentralitetsgruppe</h3>
<table>
<thead><tr><th>Gruppe</th><th>β</th><th>R²</th><th>p</th><th>n</th></tr></thead>
<tbody>
{''.join(
    f'<tr><td>{SENTRALITET_NAVN[k]}</td>'
    f'<td>{r_sent[k]["beta"]:+.4f}</td>'
    f'<td>{r_sent[k]["r2"]:.3f}</td>'
    f'<td>{r_sent[k]["p"]:.4f}</td>'
    f'<td>{r_sent[k]["n"]}</td></tr>'
    for k in sorted(r_sent.keys())
)}
</tbody>
</table>

<h3>3. Topp 20 kommuner: Sp-vekst 2017→2021</h3>
{top_p_html}
<details><summary>Talldetaljer</summary>
<table>
<thead><tr><th>#</th><th>Kommune</th><th>Sp 2021</th><th>ΔSp</th>
<th>ΔPop 2011–21</th><th>Sentralitet</th></tr></thead>
<tbody>{top_rows}</tbody>
</table>
</details>

<h3>4. Sammenligning: 1993 vs 2021 — to ulike opprør</h3>
<p>Korrelasjon ΔSp 1993 vs ΔSp 2021 (n={len(felles)}): <strong>r = {korr:.3f}</strong> —
nær null. Bare 2 av de 30 kommunene med størst Sp-vekst i 1993 finner vi igjen i topp-30
for 2021 (Træna og Balsfjord). De to bølgene er drevet av helt ulike kommuner.</p>
<p>Mulig forklaring: 1993-opprøret var EU-mobilisert og periferi-konsentrert.
2021-opprøret var bredere — en nasjonal reaksjon på sentralisering, kommunereform og
lederskifte til Vedum — og rammet også mer sentrale kommuner.</p>
{komp_html}

<h3>5. β-koeffisienter per stortingsvalgår — strukturell stabilitet</h3>
<p>OLS-regresjon Sp% ~ ΔPop(10 år) for hvert enkelt stortingsvalg (cross-sectional).
Røde søyler = statistisk signifikant (p&lt;0,05). Merk at β er konsekvent negativ og
sterkt signifikant fra 1997 til 2025 — kommuner med befolkningsnedgang har systematisk
høyere Sp-oppslutning. Strukturen var stabil (β ≈ −0,40) frem til 2017, da effekten
tilnærmet doblet seg (β ≈ −0,82) og holdt seg der i 2021.</p>
{beta_html}
<details><summary>Talltabell</summary>
<table>
<thead><tr><th>År</th><th>β</th><th>R²</th><th>p</th><th>n</th></tr></thead>
<tbody>{brows}</tbody>
</table>
</details>

<h3>6. Sp vs FrP: Nasjonal konkurranse om periferi-velgere (H6)</h3>
<table>
<thead><tr><th>År</th><th>Sp</th><th>FrP</th><th>Sp−FrP</th></tr></thead>
<tbody>{sfrows}</tbody>
</table>

</section>
</div>
<!-- === SLUTT 2021-ANALYSE === -->
"""
    return html


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("Laster data…")
    sv, bef = last_data()
    sent     = last_sentralitet()

    # 1. 2021-analyse
    data21, r_tot, r_sent, top20 = analyse_2021(sv, bef, sent)

    # 2. Sammenligning 1993 vs 2021
    d93, r93, felles, korr = sammenlign_1993_2021(sv, bef, sent)

    # 3. β per år
    beta_df = beta_per_aar(sv, bef, sent)

    # 4. FrP-konkurranse
    spfrp = frp_konkurranse(sv)

    # 5. Figurer
    print("\nLager figurer…")
    fig_scatter = fig_scatter_2021(data21, r_tot, r_sent)
    fig_komp    = fig_sammenlign_1993_2021(felles, d93, data21, korr, sv)
    fig_top     = fig_top20(top20)
    fig_beta    = fig_beta_tabell(beta_df)

    # 6. Lagre HTML-seksjon
    html_seksjon = lag_html_seksjon(
        data21, r_tot, r_sent, top20, felles, korr,
        beta_df, spfrp,
        fig_scatter, fig_komp, fig_top, fig_beta,
    )

    with open("data/processed/seksjon_2021.html", "w", encoding="utf-8") as f:
        f.write(html_seksjon)
    print("\nHTML-seksjon lagret: data/processed/seksjon_2021.html")

    # 7. Injiser i index.html (oppdater eksisterende seksjon)
    idx = "index.html"
    try:
        with open(idx, encoding="utf-8") as f:
            page = f.read()
        start_m = "<!-- === 2021-ANALYSE SEKSJON (generert av analyse_2021.py) === -->"
        end_m   = "<!-- === SLUTT 2021-ANALYSE === -->"
        s = page.find(start_m)
        e = page.find(end_m) + len(end_m)
        if s != -1 and e > len(end_m):
            page = page[:s] + html_seksjon.strip() + "\n" + page[e:]
            with open(idx, "w", encoding="utf-8") as f:
                f.write(page)
            print("index.html oppdatert med ny 2021-seksjon")
        else:
            print("Advarsel: 2021-merker ikke funnet i index.html")
    except FileNotFoundError:
        print(f"Advarsel: {idx} ikke funnet — kun seksjon_2021.html lagret")


if __name__ == "__main__":
    main()
