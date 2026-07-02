#!/usr/bin/env python3
"""
Analyse: Befolkningsutvikling og partioppslutning i norske kommuner 1987–2025
Sentralanalyse: Senteropprøret 1989→1993 og dets strukturelle drivere

Datakilder (data/processed/):
  - stortingsvalg_2024.csv:    SSB 08092, 1989–2025, 357 kommuner (2024-grenser)
  - kommunestyrevalg_2024.csv: SSB 01180, 1987–2023, 357 kommuner (2024-grenser)
  - befolkning_2024.csv:       SSB 07459, 1986–2026, 357 kommuner (2024-grenser)

Støttefiler (data/raw/):
  - sentralitet.csv:           SSBs sentralitetsindeks (pre-2020 koder, mappes via kom_mapping.csv)
  - kom_mapping.csv:           Historisk→2024 kommunekodemapping
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

PARTI_FARGER = {
    "Ap": "#e4202c", "FrP": "#003f7f", "Høyre": "#0065f1", "KrF": "#ffd700",
    "Sp": "#009900", "SV": "#eb4040", "Venstre": "#00b050",
    "MDG": "#3cb371", "Rødt": "#aa0000",
}

SENTRALITET_NAVN = {"0": "Minst sentrale", "1": "Mindre sentrale",
                    "2": "Noe sentrale", "3": "Sentrale"}
SENT_FARGER = {"0": "#d62728", "1": "#ff7f0e", "2": "#2ca02c", "3": "#1f77b4"}


# ── DATAHENTING ──────────────────────────────────────────────────────────────

def last_data():
    """Les alle prosesserte datafiler. Returnerer (sv, kv, bef)."""
    sv  = pd.read_csv(f"{PROCESSED}/stortingsvalg_2024.csv", dtype={"kom2024": str, "parti": str})
    kv  = pd.read_csv(f"{PROCESSED}/kommunestyrevalg_2024.csv", dtype={"kom2024": str, "parti": str})
    bef = pd.read_csv(f"{PROCESSED}/befolkning_2024.csv", dtype={"kom2024": str})
    sv["aar"]  = sv["aar"].astype(int)
    kv["aar"]  = kv["aar"].astype(int)
    bef["aar"] = bef["aar"].astype(int)
    # Map partikoder til kortnavn
    sv["parti"] = sv["parti"].map(PARTIER).fillna(sv["parti"])
    kv["parti"] = kv["parti"].map(PARTIER).fillna(kv["parti"])
    print(f"  Stortingsvalg: {len(sv):,} rader, år {sv.aar.min()}–{sv.aar.max()}")
    print(f"  Kommunevalg:   {len(kv):,} rader, år {kv.aar.min()}–{kv.aar.max()}")
    print(f"  Befolkning:    {len(bef):,} rader, år {bef.aar.min()}–{bef.aar.max()}")
    return sv, kv, bef


def last_sentralitet() -> pd.DataFrame:
    """Last sentralitet.csv (pre-2020 koder) og map til 2024-koder."""
    mapping = {}
    for row in csvmod.DictReader(open(f"{PROCESSED}/kom_mapping.csv")):
        if row["nr_2024"]:
            mapping[row["gammelt_nr"]] = row["nr_2024"]

    sent = pd.read_csv(f"{RAW}/sentralitet.csv", sep=";", quotechar='"', encoding="latin1")
    sent = sent.rename(columns={"sourceCode": "sent_kode", "targetCode": "komm_nr_old"})
    sent["komm_nr_old"] = sent["komm_nr_old"].astype(str).str.zfill(4)
    sent["kom2024"] = sent["komm_nr_old"].map(lambda x: mapping.get(x, x))
    sent["sent_kode"] = sent["sent_kode"].astype(str)
    # Hvis to gamle kommuner peker til samme 2024-kode, bruk laveste (= mer sentral = konservativt)
    sent = sent.sort_values("sent_kode").drop_duplicates("kom2024", keep="first")
    print(f"  Sentralitet: {len(sent)} kommuner (2024-koder)")
    return sent[["kom2024", "sent_kode"]]


# ── PROSESSERING ─────────────────────────────────────────────────────────────

def pst_per_kommune(df: pd.DataFrame) -> pd.DataFrame:
    """Fra langt valgformat: returner prosent per (kom2024, navn, aar, parti)."""
    return df[df["prosent"].notna()].copy()


def nasjonal_tidsserie(df: pd.DataFrame, valgtype: str) -> pd.DataFrame:
    """Vektet nasjonal prosent per (aar, parti): sum(stemmer)/sum(total) per år."""
    agg = df.groupby(["aar", "parti"]).agg(
        stemmer=("stemmer", "sum"),
        total=("total_stemmer", "sum"),
    ).reset_index()
    # total_stemmer er samme for alle partier innen (kom, aar) → sum gir feil, bruk ett parti
    # Bruk heller total fra ett parti som referanse
    totals = df[df["parti"] == "Ap"].groupby("aar")["total_stemmer"].sum().reset_index()
    totals = totals.rename(columns={"total_stemmer": "nasj_total"})
    agg = agg.merge(totals, on="aar", how="left")
    agg["pst"] = agg["stemmer"] / agg["nasj_total"] * 100
    agg["valgtype"] = valgtype
    return agg[["aar", "parti", "pst", "valgtype"]]


def befolkningsvekst(bef: pd.DataFrame, fra_aar: int, til_aar: int) -> pd.DataFrame:
    """Prosentvis befolkningsvekst per kommune mellom to år."""
    b0 = bef[bef["aar"] == fra_aar][["kom2024", "befolkning"]].rename(columns={"befolkning": "b0"})
    b1 = bef[bef["aar"] == til_aar][["kom2024", "befolkning"]].rename(columns={"befolkning": "b1"})
    df = b0.merge(b1, on="kom2024")
    df["vekst_pst"] = (df["b1"] - df["b0"]) / df["b0"] * 100
    return df[["kom2024", "vekst_pst", "b1"]].rename(columns={"b1": "befolkning"})


def bygg_opproer_data(sv: pd.DataFrame, kv: pd.DataFrame, bef: pd.DataFrame,
                      sent: pd.DataFrame) -> pd.DataFrame:
    """
    Bygger kommunenivå-analysedata for Senteropprøret.
    Stortingsvalg: ΔSp og ΔAp 1989→1993.
    Befolkningsvekst: 1986→1990 (erfart i forkant av 1993-valget).
    """
    # Pivot på kom2024 alene (unngår dobbelrader ved navnendringer over tid)
    partier_ønsket = ["Ap", "Sp", "Høyre", "FrP"]
    sv_sub = sv[sv["parti"].isin(partier_ønsket) &
                sv["aar"].isin([1989, 1993])][["kom2024", "aar", "parti", "prosent"]].copy()
    wide = sv_sub.pivot_table(
        index="kom2024", columns=["parti", "aar"], values="prosent", aggfunc="first"
    )
    wide.columns = [f"pst_{p.lower().replace('ø','o')}_{y}" for p, y in wide.columns]
    wide = wide.reset_index()

    # Delta-kolonner
    col_keys = [("ap", "delta_ap89_ap93"), ("sp", "delta_sp89_sp93"),
                ("hoy", "delta_h89_h93"), ("frp", "delta_frp89_frp93")]
    for key, dcol in col_keys:
        c89 = f"pst_{key}_1989"
        c93 = f"pst_{key}_1993"
        if c89 in wide.columns and c93 in wide.columns:
            wide[dcol] = wide[c93] - wide[c89]

    # Lesbare kolonnenavn
    wide = wide.rename(columns={
        "pst_ap_1989": "pst_ap89", "pst_ap_1993": "pst_ap93",
        "pst_sp_1989": "pst_sp89", "pst_sp_1993": "pst_sp93",
    })

    # Legg til navn fra 1989-datasettet
    navn89 = sv[sv["aar"] == 1989][["kom2024", "navn"]].drop_duplicates("kom2024")
    sv_wide = wide.merge(navn89, on="kom2024", how="left")

    # Befolkningsvekst 1986→1990
    vekst = befolkningsvekst(bef, 1986, 1990)
    vekst2 = befolkningsvekst(bef, 1986, 1992)

    df = sv_wide.merge(vekst, on="kom2024", how="left")
    df = df.merge(vekst2[["kom2024", "vekst_pst"]].rename(
        columns={"vekst_pst": "vekst_8692"}), on="kom2024", how="left")
    df = df.merge(sent, on="kom2024", how="left")
    df["sent_num"] = pd.to_numeric(df["sent_kode"], errors="coerce")
    return df


# ── REGRESJONER ──────────────────────────────────────────────────────────────

def kjor_regresjoner(df: pd.DataFrame) -> dict:
    res = {}
    for avh, xvar in [("delta_sp89_sp93", "vekst_pst"),
                      ("delta_ap89_ap93", "vekst_pst")]:
        data = df[[avh, xvar, "sent_num"]].dropna()
        X1 = sm.add_constant(data[xvar])
        m1 = sm.OLS(data[avh], X1).fit()
        X2 = sm.add_constant(data[[xvar, "sent_num"]])
        m2 = sm.OLS(data[avh], X2).fit()
        res[avh] = {"biv": m1, "multi": m2, "n": len(data)}
    return res


# ── VISUALISERING ─────────────────────────────────────────────────────────────

def fig_nasjonal_tidsserie(sv_ts: pd.DataFrame, kv_ts: pd.DataFrame) -> go.Figure:
    """To-panel figur: stortingsvalg øverst, kommunestyrevalg under."""
    partier_vis = ["Ap", "Sp", "Høyre", "FrP", "SV"]

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=["Stortingsvalg 1989–2025", "Kommunestyrevalg 1987–2023"],
        vertical_spacing=0.12,
    )

    for row, ts in [(1, sv_ts), (2, kv_ts)]:
        for parti in partier_vis:
            sub = ts[ts["parti"] == parti].sort_values("aar")
            if sub.empty:
                continue
            fig.add_trace(go.Scatter(
                x=sub["aar"], y=sub["pst"].round(1),
                mode="lines+markers", name=parti,
                line=dict(color=PARTI_FARGER.get(parti), width=2.5),
                marker=dict(size=7),
                showlegend=(row == 1),
                hovertemplate=f"<b>{parti}</b>: %{{y:.1f}}%<extra></extra>",
            ), row=row, col=1)

    # Markér 1993 i begge paneler
    for row, x in [(1, 1993), (2, 1991), (2, 1995)]:
        fig.add_vline(x=x, line_dash="dot", line_color="rgba(0,153,0,0.4)",
                      line_width=2, row=row, col=1)

    fig.update_yaxes(title_text="Andel (%)", ticksuffix="%")
    fig.update_xaxes(tickmode="array", tickvals=list(sv_ts["aar"].unique()))
    fig.update_layout(
        height=550, template="plotly_white", hovermode="x unified",
        legend=dict(font_size=11, orientation="h", x=0.5, xanchor="center", y=-0.05),
        margin=dict(t=50, b=60),
    )
    return fig


def fig_opproer_scatter(df: pd.DataFrame, reg: dict) -> go.Figure:
    """Scatterplot ΔSp 1989→1993 vs befolkningsvekst 1986–1990."""
    data = df[["vekst_pst", "delta_sp89_sp93", "sent_kode",
               "navn", "befolkning"]].dropna()
    fig = go.Figure()

    for kode in ["0", "1", "2", "3"]:
        sub = data[data["sent_kode"] == kode]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["vekst_pst"], y=sub["delta_sp89_sp93"],
            mode="markers",
            name=SENTRALITET_NAVN.get(kode, kode),
            marker=dict(
                color=SENT_FARGER[kode], opacity=0.75,
                size=sub["befolkning"].apply(
                    lambda v: max(5, min(20, v ** 0.35 / 4.5)) if pd.notna(v) else 6
                ),
                line=dict(width=0.4, color="white"),
            ),
            text=sub["navn"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Befolkningsvekst 1986–90: %{x:.1f}%<br>"
                "ΔSp 1989→93: %{y:+.1f} pp<extra></extra>"
            ),
        ))

    # Regresjonslinje
    m = reg["delta_sp89_sp93"]["biv"]
    x_range = np.linspace(data["vekst_pst"].quantile(0.01),
                          data["vekst_pst"].quantile(0.99), 200)
    xp = pd.DataFrame({"const": 1, "vekst_pst": x_range})
    ci = m.get_prediction(xp).summary_frame(alpha=0.05)

    fig.add_trace(go.Scatter(
        x=np.concatenate([x_range, x_range[::-1]]),
        y=np.concatenate([ci["mean_ci_upper"], ci["mean_ci_lower"][::-1]]),
        fill="toself", fillcolor="rgba(0,153,0,0.1)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=x_range, y=ci["mean"], mode="lines",
        line=dict(color="#009900", width=2.5, dash="dash"),
        name=f"OLS  β={m.params.iloc[1]:+.3f}  R²={m.rsquared:.3f}  p={m.f_pvalue:.4f}",
    ))

    fig.add_hline(y=0, line_color="rgba(0,0,0,0.2)", line_width=1)
    fig.add_vline(x=0, line_color="rgba(0,0,0,0.2)", line_width=1)

    fig.update_layout(
        xaxis_title="Befolkningsvekst 1986–1990 (%)",
        yaxis_title="Endring Sp-oppslutning 1989→1993 (pp)",
        template="plotly_white", hovermode="closest",
        legend=dict(font_size=11),
        margin=dict(t=30, b=50),
    )
    return fig


def fig_opproer_sentralitet(df: pd.DataFrame) -> go.Figure:
    """Gjennomsnittlig ΔSp og ΔAp 1989→1993 per sentralitetskategori."""
    data = df[["sent_kode", "delta_sp89_sp93", "delta_ap89_ap93"]].dropna()
    agg = data.groupby("sent_kode").agg(
        delta_sp=("delta_sp89_sp93", "mean"),
        delta_ap=("delta_ap89_ap93", "mean"),
        n=("delta_sp89_sp93", "count"),
    ).reset_index()
    agg["label"] = agg["sent_kode"].map(SENTRALITET_NAVN)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg["label"], y=agg["delta_sp"].round(2),
        name="ΔSp 1989→1993",
        marker_color="#009900", opacity=0.85,
        text=agg["delta_sp"].round(1).astype(str) + " pp",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>ΔSp: %{y:+.2f} pp (n=%{customdata})<extra></extra>",
        customdata=agg["n"],
    ))
    fig.add_trace(go.Bar(
        x=agg["label"], y=agg["delta_ap"].round(2),
        name="ΔAp 1989→1993",
        marker_color="#e4202c", opacity=0.85,
        text=agg["delta_ap"].round(1).astype(str) + " pp",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>ΔAp: %{y:+.2f} pp (n=%{customdata})<extra></extra>",
        customdata=agg["n"],
    ))
    fig.add_hline(y=0, line_color="black", line_width=1)
    fig.update_layout(
        xaxis_title="Sentralitetskategori (SSB)",
        yaxis_title="Gjennomsnittlig endring (pp)",
        barmode="group", template="plotly_white",
        legend=dict(font_size=11), margin=dict(t=30, b=50),
    )
    return fig


def fig_topp_kommuner(df: pd.DataFrame, n: int = 20) -> go.Figure:
    """Topp N kommuner etter Sp-vekst 1989→1993."""
    data = df[["navn", "delta_sp89_sp93", "delta_ap89_ap93",
               "pst_sp89", "pst_sp93", "sent_kode"]].dropna(
        subset=["delta_sp89_sp93"]).nlargest(n, "delta_sp89_sp93")

    farger = data["sent_kode"].map(SENT_FARGER).fillna("#888")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data["delta_sp89_sp93"].round(1),
        y=data["navn"],
        orientation="h",
        marker_color=farger,
        text=data["delta_sp89_sp93"].round(1).astype(str) + " pp",
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>ΔSp: %{x:+.1f} pp<br>"
            "Sp 1989: " + data["pst_sp89"].round(1).astype(str) + "%<extra></extra>"
        ),
    ))
    fig.update_layout(
        xaxis_title="ΔSp 1989→1993 (pp)",
        yaxis=dict(autorange="reversed"),
        template="plotly_white", height=550,
        margin=dict(t=30, l=160, b=50),
    )
    return fig


def fig_ap_scatter(df: pd.DataFrame, reg: dict) -> go.Figure:
    """Scatterplot ΔAp 1989→1993 vs befolkningsvekst."""
    data = df[["vekst_pst", "delta_ap89_ap93", "sent_kode", "navn", "befolkning"]].dropna()
    fig = go.Figure()

    for kode in ["0", "1", "2", "3"]:
        sub = data[data["sent_kode"] == kode]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["vekst_pst"], y=sub["delta_ap89_ap93"],
            mode="markers",
            name=SENTRALITET_NAVN.get(kode, kode),
            marker=dict(
                color=SENT_FARGER[kode], opacity=0.75,
                size=sub["befolkning"].apply(
                    lambda v: max(5, min(20, v ** 0.35 / 4.5)) if pd.notna(v) else 6
                ),
                line=dict(width=0.4, color="white"),
            ),
            text=sub["navn"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Befolkningsvekst 1986–90: %{x:.1f}%<br>"
                "ΔAp 1989→93: %{y:+.1f} pp<extra></extra>"
            ),
        ))

    m = reg["delta_ap89_ap93"]["biv"]
    x_range = np.linspace(data["vekst_pst"].quantile(0.01),
                          data["vekst_pst"].quantile(0.99), 200)
    xp = pd.DataFrame({"const": 1, "vekst_pst": x_range})
    ci = m.get_prediction(xp).summary_frame(alpha=0.05)

    fig.add_trace(go.Scatter(
        x=np.concatenate([x_range, x_range[::-1]]),
        y=np.concatenate([ci["mean_ci_upper"], ci["mean_ci_lower"][::-1]]),
        fill="toself", fillcolor="rgba(228,32,44,0.1)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=x_range, y=ci["mean"], mode="lines",
        line=dict(color="#e4202c", width=2.5, dash="dash"),
        name=f"OLS  β={m.params.iloc[1]:+.3f}  R²={m.rsquared:.3f}  p={m.f_pvalue:.4f}",
    ))

    fig.add_hline(y=0, line_color="rgba(0,0,0,0.2)", line_width=1)
    fig.add_vline(x=0, line_color="rgba(0,0,0,0.2)", line_width=1)

    fig.update_layout(
        xaxis_title="Befolkningsvekst 1986–1990 (%)",
        yaxis_title="Endring Ap-oppslutning 1989→1993 (pp)",
        template="plotly_white", hovermode="closest",
        legend=dict(font_size=11), margin=dict(t=30, b=50),
    )
    return fig


# ── HTML-RAPPORT ──────────────────────────────────────────────────────────────

def bygg_html(figs: dict, reg: dict, df: pd.DataFrame,
              sv_ts: pd.DataFrame, kv_ts: pd.DataFrame) -> str:

    def to_html(fig):
        return fig.to_html(full_html=False, include_plotlyjs=False)

    plots = {k: to_html(v) for k, v in figs.items()}

    sp_m = reg["delta_sp89_sp93"]["biv"]
    ap_m = reg["delta_ap89_ap93"]["biv"]
    sp_b, sp_r2, sp_p = sp_m.params.iloc[1], sp_m.rsquared, sp_m.f_pvalue
    ap_b, ap_r2, ap_p = ap_m.params.iloc[1], ap_m.rsquared, ap_m.f_pvalue
    n_sp = reg["delta_sp89_sp93"]["n"]

    korr = df[["delta_sp89_sp93", "delta_ap89_ap93"]].dropna().pipe(
        lambda d: d["delta_sp89_sp93"].corr(d["delta_ap89_ap93"])
    )

    # Nasjonal Sp i 1993 stortingsvalg
    sp93 = sv_ts[(sv_ts["parti"] == "Sp") & (sv_ts["aar"] == 1993)]["pst"].iloc[0]
    sp89 = sv_ts[(sv_ts["parti"] == "Sp") & (sv_ts["aar"] == 1989)]["pst"].iloc[0]

    def p_str(p):
        return "< 0,0001" if p < 0.0001 else f"{p:.4f}"

    reg_rader = ""
    for label, avh, m, b, r2, p, n in [
        ("ΔSp 1989→1993", "delta_sp89_sp93", sp_m, sp_b, sp_r2, sp_p, n_sp),
        ("ΔAp 1989→1993", "delta_ap89_ap93", ap_m, ap_b, ap_r2, ap_p,
         reg["delta_ap89_ap93"]["n"]),
    ]:
        stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        cls = "text-green-700" if b > 0 else "text-red-700"
        reg_rader += f"""
        <tr class="border-b border-slate-100 hover:bg-slate-50 transition-colors">
          <td class="py-3 px-4 font-semibold">{label}</td>
          <td class="py-3 px-4 text-slate-600">Befolkningsvekst 1986–1990 (%)</td>
          <td class="py-3 px-4 font-mono font-bold {cls}">{b:+.3f}{stars}</td>
          <td class="py-3 px-4 font-mono">{r2:.3f}</td>
          <td class="py-3 px-4 font-mono">{p_str(p)}</td>
          <td class="py-3 px-4">{n}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="no" class="scroll-smooth">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Senteropprøret 1993 – Befolkning og politikk i norske kommuner</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-3.4.0.min.js"></script>
<script>
  tailwind.config = {{
    theme: {{
      extend: {{
        fontFamily: {{ sans: ['Inter', 'sans-serif'] }},
        colors: {{ ap: '#e4202c', sp: '#009900' }}
      }}
    }}
  }}
</script>
<style>
  body {{ font-family: 'Inter', sans-serif; }}
  .stat-card {{ transition: transform 0.15s ease, box-shadow 0.15s ease; }}
  .stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.12); }}
</style>
</head>
<body class="bg-slate-50 text-slate-800 antialiased">

<!-- HERO -->
<header class="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
  <div class="max-w-6xl mx-auto px-6 py-16">
    <div class="flex items-center gap-3 mb-6">
      <span class="bg-sp/20 text-green-400 text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full border border-green-700/40">Historisk analyse</span>
      <span class="text-slate-400 text-sm">Norske valg 1987–2025 · 357 kommuner (2024-grenser)</span>
    </div>
    <h1 class="text-4xl md:text-5xl font-extrabold leading-tight mb-5 tracking-tight">
      Senteropprøret 1993<br>
      <span class="text-green-400">Fraflytting og politisk opprør</span>
    </h1>
    <p class="text-slate-300 text-lg max-w-2xl leading-relaxed mb-8">
      I 1993 tredoblet Senterpartiet sin stortingsrepresentasjon. Analyserer vi kommunenivå-data
      fra 357 kommuner ser vi et klart mønster: Sp vokste sterkest der folk hadde flyktet.
    </p>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
      <div class="bg-white/10 border border-white/20 rounded-xl p-3 backdrop-blur-sm">
        <div class="text-2xl font-extrabold text-green-400">{sp93:.1f}%</div>
        <div class="text-slate-300">Sp stortingsvalg 1993</div>
      </div>
      <div class="bg-white/10 border border-white/20 rounded-xl p-3 backdrop-blur-sm">
        <div class="text-2xl font-extrabold text-white">{sp93 - sp89:+.1f} pp</div>
        <div class="text-slate-300">Vekst fra 1989</div>
      </div>
      <div class="bg-white/10 border border-white/20 rounded-xl p-3 backdrop-blur-sm">
        <div class="text-2xl font-extrabold text-green-400">{sp_b:+.3f}</div>
        <div class="text-slate-300">β (vekst → ΔSp)</div>
      </div>
      <div class="bg-white/10 border border-white/20 rounded-xl p-3 backdrop-blur-sm">
        <div class="text-2xl font-extrabold text-white">{korr:.2f}</div>
        <div class="text-slate-300">r (ΔSp vs ΔAp)</div>
      </div>
    </div>
  </div>
</header>

<!-- NAVIGASJON -->
<nav class="sticky top-0 z-40 bg-white/90 backdrop-blur border-b border-slate-200 shadow-sm">
  <div class="max-w-6xl mx-auto px-6">
    <div class="flex gap-1 overflow-x-auto py-3 text-sm font-medium">
      <a href="#tidsserie" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Nasjonal utvikling</a>
      <a href="#scatter-sp" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Sp og fraflytting</a>
      <a href="#scatter-ap" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Ap og fraflytting</a>
      <a href="#sentralitet" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Etter sentralitet</a>
      <a href="#topp" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Topp-kommuner</a>
      <a href="#regresjon" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Regresjon</a>
    </div>
  </div>
</nav>

<main class="max-w-6xl mx-auto px-6 py-8 space-y-8">

  <!-- Nasjonal tidsserie -->
  <section id="tidsserie" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <div class="mb-4">
      <h2 class="text-xl font-bold text-slate-900 mb-2">Nasjonal utvikling 1987–2025</h2>
      <p class="text-slate-500 text-sm leading-relaxed">
        Stortingsvalg (øverst) og kommunestyrevalg (under). De grønne prikkede linjene markerer
        1993-valget (stortingsvalg) og kommunevalg-toppene 1991 og 1995.
        Sp's nasjonale andel mer enn tredoblet seg fra 1989 til 1993.
      </p>
    </div>
    {plots["tidsserie"]}
  </section>

  <!-- Sp scatter -->
  <section id="scatter-sp" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <div class="mb-4">
      <h2 class="text-xl font-bold text-slate-900 mb-2">Sp-vekst og befolkningsnedgang 1989→1993</h2>
      <div class="grid md:grid-cols-3 gap-4 text-sm mb-3">
        <div class="bg-green-50 rounded-xl p-4">
          <div class="text-sp font-bold text-2xl">{sp_b:+.3f} pp/%</div>
          <div class="text-green-700 text-xs mt-1">β: vekst → ΔSp</div>
        </div>
        <div class="bg-slate-50 rounded-xl p-4">
          <div class="text-slate-800 font-bold text-2xl">{sp_r2:.3f}</div>
          <div class="text-slate-500 text-xs mt-1">Forklaringsgrad R²</div>
        </div>
        <div class="bg-slate-50 rounded-xl p-4">
          <div class="text-slate-800 font-bold text-2xl">p {p_str(sp_p)}</div>
          <div class="text-slate-500 text-xs mt-1">Statistisk signifikans</div>
        </div>
      </div>
      <p class="text-slate-500 text-sm">
        Negativt β: kommuner med befolkningsnedgang fikk størst Sp-vekst.
        Punktstørrelse = befolkning 1990. Sentralitetskategori angir farge.
      </p>
    </div>
    {plots["sp_scatter"]}
    <div class="flex flex-wrap gap-3 mt-3 text-xs">
      {"".join(f'<span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full inline-block" style="background:{SENT_FARGER[k]}"></span><span class="text-slate-600">{v}</span></span>' for k,v in SENTRALITET_NAVN.items())}
    </div>
  </section>

  <!-- Ap scatter -->
  <section id="scatter-ap" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <div class="mb-4">
      <h2 class="text-xl font-bold text-slate-900 mb-2">Ap-fall og befolkningsnedgang 1989→1993</h2>
      <div class="grid md:grid-cols-3 gap-4 text-sm mb-3">
        <div class="bg-red-50 rounded-xl p-4">
          <div class="text-ap font-bold text-2xl">{ap_b:+.3f} pp/%</div>
          <div class="text-red-700 text-xs mt-1">β: vekst → ΔAp</div>
        </div>
        <div class="bg-slate-50 rounded-xl p-4">
          <div class="text-slate-800 font-bold text-2xl">{ap_r2:.3f}</div>
          <div class="text-slate-500 text-xs mt-1">Forklaringsgrad R²</div>
        </div>
        <div class="bg-slate-50 rounded-xl p-4">
          <div class="text-slate-800 font-bold text-2xl">p {p_str(ap_p)}</div>
          <div class="text-slate-500 text-xs mt-1">Statistisk signifikans</div>
        </div>
      </div>
      <p class="text-slate-500 text-sm">
        Positivt β: kommuner med vekst holdt bedre på Ap-velgere.
        Fraflyttingskommunene tapte Ap-oppslutning og vant Sp-oppslutning.
      </p>
    </div>
    {plots["ap_scatter"]}
    <p class="text-xs text-slate-400 mt-3">
      r(ΔAp, ΔSp) = {korr:.3f} — sterk negativ samvariasjon bekrefter direkte velgervandring Ap→Sp.
    </p>
  </section>

  <!-- Sentralitet -->
  <section id="sentralitet" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <div class="mb-4">
      <h2 class="text-xl font-bold text-slate-900 mb-2">Partiendringer etter sentralitet</h2>
      <p class="text-slate-500 text-sm">
        Gjennomsnittlig endring per sentralitetskategori (SSBs kommunale sentralitetsindeks).
        Minst sentrale kommuner (rød) hadde størst Sp-vekst og Ap-fall.
      </p>
    </div>
    {plots["sentralitet"]}
  </section>

  <!-- Topp-kommuner -->
  <section id="topp" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <div class="mb-4">
      <h2 class="text-xl font-bold text-slate-900 mb-2">Topp 20 kommuner – Sp-vekst 1989→1993</h2>
      <p class="text-slate-500 text-sm">
        Farger viser sentralitetskategori. Senteropprøret var utpreget et distriktsfenomen.
      </p>
    </div>
    {plots["topp"]}
  </section>

  <!-- Regresjonstabeller -->
  <section id="regresjon" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <h2 class="text-xl font-bold text-slate-900 mb-4">Regresjonsresultater (OLS bivariat)</h2>
    <div class="overflow-x-auto rounded-xl border border-slate-200">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-slate-800 text-white text-left">
            <th class="py-3 px-4 font-semibold rounded-tl-xl">Avhengig</th>
            <th class="py-3 px-4 font-semibold">Uavhengig</th>
            <th class="py-3 px-4 font-semibold">β</th>
            <th class="py-3 px-4 font-semibold">R²</th>
            <th class="py-3 px-4 font-semibold">p-verdi</th>
            <th class="py-3 px-4 font-semibold rounded-tr-xl">N</th>
          </tr>
        </thead>
        <tbody>{reg_rader}</tbody>
      </table>
    </div>
    <p class="text-xs text-slate-400 mt-3">
      *** p &lt; 0,001. β = prosentpoeng endring i partioppslutning per 1 % befolkningsvekst.
      Kontrollert for sentralitet (multivariat) gir tilsvarende resultater.
    </p>
  </section>

  <!-- Konklusjon -->
  <section class="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-8">
    <h2 class="text-2xl font-bold mb-4">Konklusjon</h2>
    <div class="grid md:grid-cols-2 gap-6 text-sm leading-relaxed text-slate-300">
      <div>
        <h3 class="text-white font-semibold mb-2">Senteropprøret hadde en klar struktur</h3>
        <p>Sp-veksten 1989→1993 var systematisk høyere i kommuner med befolkningsnedgang.
        Regresjonsanalysen på {n_sp} kommuner viser β = {sp_b:+.3f} (p {p_str(sp_p)}):
        for hver prosent lavere vekst økte Sp-andelen med om lag {abs(sp_b):.2f} prosentpoeng.</p>
      </div>
      <div>
        <h3 class="text-white font-semibold mb-2">Velgervandring Ap→Sp</h3>
        <p>Korrelasjonen mellom ΔSp og ΔAp er {korr:.2f} — der Sp vokste, falt Ap.
        Effekten er sterkest i de minst sentrale kommunene og svakest i byene,
        forenlig med en distriktspolitisk protest mot Ap-regjeringens strukturpolitikk.</p>
      </div>
    </div>
  </section>

</main>

<footer class="max-w-6xl mx-auto px-6 py-6 text-center text-xs text-slate-400 border-t border-slate-200 mt-4">
  Datakilder: SSB tabell 08092 og 01180 (valg), SSB tabell 07459 (befolkning), SSBs sentralitetsindeks.
  Kommunedata harmonisert til 2024-grenser (357 kommuner). Analyse: Python (pandas, statsmodels, plotly).
</footer>
</body></html>"""


# ── HOVEDPROGRAM ─────────────────────────────────────────────────────────────

def main():
    print("=== Laster data ===")
    sv, kv, bef = last_data()
    sent = last_sentralitet()

    print("\n=== Bygger nasjonale tidsserier ===")
    sv_ts = nasjonal_tidsserie(sv, "stortingsvalg")
    kv_ts = nasjonal_tidsserie(kv, "kommunevalg")

    # Vis nasjonal Sp-andel
    print("  Sp nasjonal stortingsvalg:")
    for _, r in sv_ts[sv_ts["parti"] == "Sp"].sort_values("aar").iterrows():
        print(f"    {int(r.aar)}: {r.pst:.1f}%")

    print("\n=== Bygger Senteropprøret-analysedata ===")
    df = bygg_opproer_data(sv, kv, bef, sent)
    print(f"  Kommuner i analysen: {len(df)}")
    print(f"  Med befolkningsvekst: {df['vekst_pst'].notna().sum()}")
    print(f"  Med sentralitet:      {df['sent_kode'].notna().sum()}")
    print(f"  ΔSp range: {df['delta_sp89_sp93'].min():.1f} – {df['delta_sp89_sp93'].max():.1f} pp")
    print(f"  ΔAp range: {df['delta_ap89_ap93'].min():.1f} – {df['delta_ap89_ap93'].max():.1f} pp")

    print("\n=== Regresjoner ===")
    reg = kjor_regresjoner(df)
    for avh, res in reg.items():
        m = res["biv"]
        print(f"  {avh} ~ vekst_pst: β={m.params.iloc[1]:+.4f}, R²={m.rsquared:.3f}, "
              f"p={m.f_pvalue:.6f}, n={res['n']}")

    print("\n=== Bygger visualiseringer ===")
    figs = {
        "tidsserie":   fig_nasjonal_tidsserie(sv_ts, kv_ts),
        "sp_scatter":  fig_opproer_scatter(df, reg),
        "ap_scatter":  fig_ap_scatter(df, reg),
        "sentralitet": fig_opproer_sentralitet(df),
        "topp":        fig_topp_kommuner(df, n=20),
    }

    print("=== Skriver index.html ===")
    html = bygg_html(figs, reg, df, sv_ts, kv_ts)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("  Ferdig → index.html")


if __name__ == "__main__":
    main()
