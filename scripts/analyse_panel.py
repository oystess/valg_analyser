#!/usr/bin/env python3
"""
analyse_panel.py — Panel-regresjon: befolkningsvekst og partioppslutning
                    i norske kommuner 1987–2025.

Fase 2 i prosjektplanen:
  - Fixed effects (kommunefaste effekter + år-dummies)
  - Key IV: Δpop_10yr (befolkningsendring siste 10 år)
  - Interaksjon: sent_kode × Δpop (H2 × H1)
  - KV vs STV sammenligning (H4)

Fase 3 i prosjektplanen:
  - Timing: KV leder STV? Lagget kommunevalg → stortingsvalg (H5)

Output:
  - Konsolenivå: resultater per modell
  - panel_resultater.csv: koeffisienter, SE, p-verdier
  - panel_plot.html: Plotly-figurer for inkludering i hovedrapporten
"""

import warnings
import csv as csvmod
import numpy as np
import pandas as pd
import statsmodels.api as sm
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from linearmodels.panel import PanelOLS

warnings.filterwarnings("ignore")

PROCESSED = "data/processed"
RAW       = "data/raw"

PARTIER = {
    "01": "Ap", "02": "FrP", "03": "Høyre", "04": "KrF",
    "05": "Sp", "06": "SV", "07": "Venstre", "08": "MDG", "55": "Rødt",
}

SENTRALITET_NAVN = {0: "Minst sentrale", 1: "Mindre sentrale",
                    2: "Noe sentrale", 3: "Sentrale"}
SENT_FARGER = {0: "#d62728", 1: "#ff7f0e", 2: "#2ca02c", 3: "#1f77b4"}


# ── DATAHENTING ──────────────────────────────────────────────────────────────

def last_valg() -> tuple[pd.DataFrame, pd.DataFrame]:
    sv = pd.read_csv(f"{PROCESSED}/stortingsvalg_2024.csv", dtype={"kom2024": str, "parti": str})
    kv = pd.read_csv(f"{PROCESSED}/kommunestyrevalg_2024.csv", dtype={"kom2024": str, "parti": str})
    sv["parti"] = sv["parti"].map(PARTIER).fillna(sv["parti"])
    kv["parti"] = kv["parti"].map(PARTIER).fillna(kv["parti"])
    sv["aar"] = sv["aar"].astype(int)
    kv["aar"] = kv["aar"].astype(int)
    return sv, kv


def last_bef() -> pd.DataFrame:
    bef = pd.read_csv(f"{PROCESSED}/befolkning_2024.csv", dtype={"kom2024": str})
    bef["aar"] = bef["aar"].astype(int)
    return bef


def last_sentralitet() -> pd.DataFrame:
    mapping = {}
    for row in csvmod.DictReader(open(f"{PROCESSED}/kom_mapping.csv")):
        if row["nr_2024"]:
            mapping[row["gammelt_nr"]] = row["nr_2024"]
    sent = pd.read_csv(f"{RAW}/sentralitet.csv", sep=";", quotechar='"', encoding="latin1")
    sent = sent.rename(columns={"sourceCode": "sent_kode", "targetCode": "komm_nr_old"})
    sent["komm_nr_old"] = sent["komm_nr_old"].astype(str).str.zfill(4)
    sent["kom2024"] = sent["komm_nr_old"].map(lambda x: mapping.get(x, x))
    sent["sent_kode"] = pd.to_numeric(sent["sent_kode"], errors="coerce")
    sent = sent.sort_values("sent_kode").drop_duplicates("kom2024", keep="first")
    return sent[["kom2024", "sent_kode"]]


# ── BYGG PANEL-DATASETT ──────────────────────────────────────────────────────

def dpop(bef: pd.DataFrame, lag: int) -> pd.DataFrame:
    """Prosentvis befolkningsendring over `lag` år for alle (kom2024, aar)."""
    rows = []
    bef_idx = bef.set_index(["kom2024", "aar"])["befolkning"]
    for (k, y), pop in bef_idx.items():
        y0 = y - lag
        if (k, y0) in bef_idx.index:
            pop0 = bef_idx[(k, y0)]
            if pop0 > 0:
                rows.append({"kom2024": k, "aar": y, f"dpop{lag}": (pop - pop0) / pop0 * 100})
    return pd.DataFrame(rows)


def bygg_panel(sv: pd.DataFrame, kv: pd.DataFrame, bef: pd.DataFrame,
               sent: pd.DataFrame) -> pd.DataFrame:
    """
    Lang panel-struktur: én rad per (kom2024, aar, valgtype, parti).
    Inneholder: pst, dpop5, dpop10, sent_kode, befolkning.
    """
    print("  Beregner ΔPop (5- og 10-år)…", end=" ", flush=True)
    dp5  = dpop(bef, 5)
    dp10 = dpop(bef, 10)
    pop_yr = bef[["kom2024", "aar", "befolkning"]]
    print("ferdig")

    frames = []
    for df, vtype in [(sv, "STV"), (kv, "KV")]:
        sub = df[df["parti"].isin(["Sp", "Ap"])][
            ["kom2024", "aar", "parti", "prosent"]
        ].copy()
        sub["valgtype"] = vtype
        sub = sub.rename(columns={"prosent": "pst"})
        frames.append(sub)

    panel = pd.concat(frames, ignore_index=True)

    # Merge befolkningsdata (bruk år for valget)
    panel = panel.merge(pop_yr.rename(columns={"befolkning": "pop"}),
                        on=["kom2024", "aar"], how="left")
    panel = panel.merge(dp5,  on=["kom2024", "aar"], how="left")
    panel = panel.merge(dp10, on=["kom2024", "aar"], how="left")
    panel = panel.merge(sent, on="kom2024", how="left")

    panel["ln_pop"] = np.log(panel["pop"].clip(lower=1))
    panel["sent_kode"] = pd.to_numeric(panel["sent_kode"], errors="coerce")
    # Sentral dummy: 1=sentral, 0=periferi
    panel["periferi"] = (panel["sent_kode"] <= 1).astype(float)

    print(f"  Panel: {len(panel):,} rader, "
          f"{panel.kom2024.nunique()} kommuner, "
          f"år {panel.aar.min()}–{panel.aar.max()}")
    return panel


# ── FIXED EFFECTS PANEL-REGRESJON ─────────────────────────────────────────────

def fe_modell(data: pd.DataFrame, avh: str, uavh: list[str],
              label: str) -> dict:
    """
    PanelOLS med tids-FE (år-dummies) og entitets-FE (kommuner).
    Returnerer dict med koeffisienter, SE, p-verdier og metadata.
    """
    df = data[[avh] + uavh + ["kom2024", "aar"]].dropna()
    n_obs = len(df)
    n_ent = df["kom2024"].nunique()
    n_yr  = df["aar"].nunique()

    # Sett multi-indeks (entity, tid) for linearmodels
    df = df.set_index(["kom2024", "aar"])
    y = df[avh]
    X = df[uavh]

    try:
        mod = PanelOLS(y, X, entity_effects=True, time_effects=True)
        res = mod.fit(cov_type="clustered", cluster_entity=True)
        koeff = {v: {"b": res.params[v], "se": res.std_errors[v],
                     "p": res.pvalues[v], "ci_lo": res.conf_int()["lower"][v],
                     "ci_hi": res.conf_int()["upper"][v]}
                 for v in uavh}
        return {"label": label, "avh": avh, "uavh": uavh,
                "koeff": koeff, "r2_within": res.rsquared,
                "n_obs": n_obs, "n_ent": n_ent, "n_yr": n_yr,
                "success": True}
    except Exception as e:
        print(f"  [FEIL] {label}: {e}")
        return {"label": label, "success": False}


def kjor_fe_regresjoner(panel: pd.DataFrame) -> list[dict]:
    """
    PanelOLS FE-regresjoner.
    NB: Tidsfast sentralitet absorberes av entitets-FE.
    Løsning: kjør separate FE-regresjoner per sentralitetskategori (split-sample).
    """
    resultater = []

    for parti in ["Sp", "Ap"]:
        for vtype in ["STV", "KV", None]:  # None = begge
            sub = panel[panel["parti"] == parti].copy()
            if vtype:
                sub = sub[sub["valgtype"] == vtype]
            vtag = vtype or "Alle"

            # Modell 1: Bare dpop10 (hele utvalget)
            r = fe_modell(sub, "pst", ["dpop10"], f"{parti} {vtag}: dpop10")
            resultater.append(r)

            # Modell 2: dpop10 + ln_pop (størrelse-kontroll)
            r = fe_modell(sub, "pst", ["dpop10", "ln_pop"],
                          f"{parti} {vtag}: dpop10+lnpop")
            resultater.append(r)

            # Modell 3: Split etter sentralitet (løser absorbsjonsproblem)
            # Kjør FE separat for periferi (sent 0-1) og sentrale (sent 2-3)
            for grp_label, koder in [("periferi", [0, 1]), ("sentrale", [2, 3])]:
                sub_g = sub[sub["sent_kode"].isin(koder)].copy()
                r = fe_modell(sub_g, "pst", ["dpop10"],
                              f"{parti} {vtag} [{grp_label}]: dpop10")
                resultater.append(r)

    return resultater


# ── TIMING-TEST: KOMMUNEVALG LEDER STORTINGSVALG ───────────────────────────────

def timing_test(sv: pd.DataFrame, kv: pd.DataFrame,
                bef: pd.DataFrame, sent: pd.DataFrame) -> list[dict]:
    """
    H5: Kommunevalg leder stortingsvalg med 2 år.
    Regresjonsstruktur:
      sv_sp_{y} ~ kv_sp_{y-2} + FE  (y = STV-år)
    KV-STV par: (1987→1989), (1991→1993), (1995→1997), ..., (2021→2023 er KV)
    Gyldige par: KV år, STV år = KV+2
    """
    # KV → STV mapping
    par_map = {kv_y: kv_y + 2 for kv_y in [1987, 1991, 1995, 1999, 2003, 2007, 2011, 2015, 2019]}

    # Pivot STV og KV til bredt format per (kom2024, år, parti)
    def pivot_pst(df, vtype):
        sub = df[df["parti"].isin(["Sp", "Ap"])][
            ["kom2024", "aar", "parti", "prosent"]
        ].copy()
        sub["valgtype"] = vtype
        return sub.rename(columns={"prosent": "pst"})

    sv_long = pivot_pst(sv, "STV")
    kv_long = pivot_pst(kv, "KV")

    resultater = []
    for parti in ["Sp", "Ap"]:
        rows = []
        for kv_y, sv_y in par_map.items():
            sv_sub = sv_long[(sv_long["parti"] == parti) & (sv_long["aar"] == sv_y)][
                ["kom2024", "pst"]].rename(columns={"pst": "sv_pst"})
            kv_sub = kv_long[(kv_long["parti"] == parti) & (kv_long["aar"] == kv_y)][
                ["kom2024", "pst"]].rename(columns={"pst": "kv_pst"})
            merged = sv_sub.merge(kv_sub, on="kom2024")
            merged["kv_aar"] = kv_y
            merged["sv_aar"] = sv_y
            rows.append(merged)

        if not rows:
            continue
        data = pd.concat(rows, ignore_index=True)
        data = data.merge(sent, on="kom2024", how="left")
        data["sent_kode"] = pd.to_numeric(data["sent_kode"], errors="coerce")

        # Panel-regresjon: sv_pst ~ kv_pst (entitets-FE + tids-FE)
        data["aar"] = data["sv_aar"]
        df_fe = data[["kom2024", "aar", "sv_pst", "kv_pst"]].dropna()
        df_fe = df_fe.set_index(["kom2024", "aar"])

        try:
            mod = PanelOLS(df_fe["sv_pst"], df_fe[["kv_pst"]],
                           entity_effects=True, time_effects=True)
            res = mod.fit(cov_type="clustered", cluster_entity=True)
            resultater.append({
                "parti": parti,
                "b_kv": res.params["kv_pst"],
                "se_kv": res.std_errors["kv_pst"],
                "p_kv": res.pvalues["kv_pst"],
                "r2_within": res.rsquared,
                "n_obs": len(df_fe),
                "n_kommuner": df_fe.index.get_level_values("kom2024").nunique(),
                "n_perioder": df_fe.index.get_level_values("aar").nunique(),
            })
        except Exception as e:
            print(f"  [FEIL] Timing {parti}: {e}")

    return resultater


# ── VISUALISERING ──────────────────────────────────────────────────────────────

def fig_dpop_tidsserie(bef: pd.DataFrame, sent: pd.DataFrame) -> go.Figure:
    """
    Gjennomsnittlig 10-årig befolkningsvekst per sentralitetskategori over tid.
    Viser om nedgangstrendene er vedvarende.
    """
    dp10 = dpop(bef, 10)
    dp10 = dp10.merge(sent, on="kom2024", how="left")
    dp10["sent_kode"] = pd.to_numeric(dp10["sent_kode"], errors="coerce")
    dp10 = dp10.dropna(subset=["sent_kode", "dpop10"])
    dp10["sent_kode"] = dp10["sent_kode"].astype(int)

    agg = dp10.groupby(["aar", "sent_kode"])["dpop10"].median().reset_index()

    fig = go.Figure()
    for kode in [0, 1, 2, 3]:
        sub = agg[agg["sent_kode"] == kode].sort_values("aar")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["aar"], y=sub["dpop10"].round(1),
            mode="lines+markers",
            name=SENTRALITET_NAVN.get(kode, str(kode)),
            line=dict(color=SENT_FARGER[kode], width=2.5),
            marker=dict(size=6),
            hovertemplate=f"<b>{SENTRALITET_NAVN.get(kode, kode)}</b><br>"
                          "År: %{x}<br>ΔPop 10 år: %{y:.1f}%<extra></extra>",
        ))
    fig.add_hline(y=0, line_color="rgba(0,0,0,0.3)", line_width=1)
    fig.update_layout(
        xaxis_title="År",
        yaxis_title="Median 10-årig befolkningsvekst (%)",
        template="plotly_white", hovermode="x unified",
        legend=dict(font_size=11, orientation="h", x=0.5, xanchor="center", y=-0.12),
        margin=dict(t=30, b=60),
    )
    return fig


def fig_fe_koeff(resultater: list[dict]) -> go.Figure:
    """
    Forest plot: FE-koeffisienter for dpop10 per modell.
    Viser β med 95 % KI, separat for Sp og Ap, STV og KV.
    """
    rader = []
    for r in resultater:
        if not r.get("success"):
            continue
        if "dpop10" not in r["koeff"]:
            continue
        k = r["koeff"]["dpop10"]
        rader.append({
            "label": r["label"],
            "b": k["b"], "ci_lo": k["ci_lo"], "ci_hi": k["ci_hi"],
            "p": k["p"],
        })
    if not rader:
        return go.Figure()

    rader.sort(key=lambda x: x["b"])
    labels = [r["label"] for r in rader]
    bs     = [r["b"]     for r in rader]
    lo     = [r["ci_lo"] for r in rader]
    hi     = [r["ci_hi"] for r in rader]
    ps     = [r["p"]     for r in rader]

    farger = []
    for r in rader:
        if "Sp" in r["label"]:
            farger.append("#009900" if r["b"] < 0 else "rgba(0,153,0,0.4)")
        else:
            farger.append("#e4202c" if r["b"] > 0 else "rgba(228,32,44,0.4)")

    fig = go.Figure()
    # KI-linjer
    for i, (b, l, h, c) in enumerate(zip(bs, lo, hi, farger)):
        fig.add_shape(type="line",
                      x0=l, x1=h, y0=i, y1=i,
                      line=dict(color=c, width=2))
    # Punkter
    fig.add_trace(go.Scatter(
        x=bs, y=list(range(len(bs))),
        mode="markers",
        marker=dict(color=farger, size=10, symbol="diamond"),
        text=[f"β={b:+.3f}, p={p:.3f}" for b, p in zip(bs, ps)],
        hovertemplate="%{text}<extra></extra>",
        showlegend=False,
    ))
    fig.add_vline(x=0, line_color="rgba(0,0,0,0.3)", line_dash="dot")
    fig.update_layout(
        yaxis=dict(tickvals=list(range(len(labels))), ticktext=labels,
                   tickfont_size=11),
        xaxis_title="β (pp per 1 % befolkningsvekst) med 95% KI",
        template="plotly_white", height=max(300, len(rader) * 40),
        margin=dict(t=20, l=280, b=50),
    )
    return fig


def fig_scatter_dpop_pst(panel: pd.DataFrame, parti: str, vtype: str) -> go.Figure:
    """Binned scatter: dpop10 vs pst per sentralitetskategori."""
    sub = panel[(panel["parti"] == parti) & (panel["valgtype"] == vtype)].dropna(
        subset=["dpop10", "pst", "sent_kode"]
    ).copy()
    sub["sent_kode"] = sub["sent_kode"].astype(int)

    # Bin dpop10 i 20 kvantiler
    sub["dpop_bin"] = pd.qcut(sub["dpop10"], q=20, labels=False, duplicates="drop")

    fig = go.Figure()
    for kode in [0, 1, 2, 3]:
        s = sub[sub["sent_kode"] == kode]
        if s.empty:
            continue
        agg = s.groupby("dpop_bin").agg(
            x=("dpop10", "median"), y=("pst", "median"), n=("pst", "count")
        ).reset_index()
        fig.add_trace(go.Scatter(
            x=agg["x"], y=agg["y"],
            mode="markers+lines",
            name=SENTRALITET_NAVN.get(kode, str(kode)),
            marker=dict(color=SENT_FARGER[kode], size=8, opacity=0.8),
            line=dict(color=SENT_FARGER[kode], width=1.5),
            hovertemplate=f"<b>{SENTRALITET_NAVN.get(kode, kode)}</b><br>"
                          "ΔPop 10 år: %{x:.1f}%<br>Median %{text}: %{y:.1f}%<extra></extra>",
            text=[parti] * len(agg),
        ))

    fig.add_vline(x=0, line_color="rgba(0,0,0,0.2)", line_dash="dot")
    farge = "#009900" if parti == "Sp" else "#e4202c"
    fig.update_layout(
        xaxis_title="10-årig befolkningsvekst (%)",
        yaxis_title=f"{parti}-oppslutning (%)",
        title=f"{parti} {vtype}: Befolkningsvekst vs partioppslutning (binnede medianverdier)",
        template="plotly_white", hovermode="closest",
        legend=dict(font_size=11),
        margin=dict(t=50, b=50),
    )
    return fig


# ── RAPPORTGENERERING ──────────────────────────────────────────────────────────

def skriv_resultater(resultater: list[dict], timing: list[dict]):
    print("\n=== FE-REGRESJONSRESULTATER ===")
    print(f"{'Modell':<45} {'β(dpop10)':>10} {'SE':>8} {'p':>8} {'R²within':>9} {'N obs':>7}")
    print("-" * 90)
    for r in resultater:
        if not r.get("success"):
            print(f"  [FEIL] {r['label']}")
            continue
        if "dpop10" not in r["koeff"]:
            continue
        k = r["koeff"]["dpop10"]
        stars = "***" if k["p"] < 0.001 else "**" if k["p"] < 0.01 else "*" if k["p"] < 0.05 else ""
        print(f"  {r['label']:<43} {k['b']:>+10.4f} {k['se']:>8.4f} "
              f"{k['p']:>8.4f}{stars:<3} {r['r2_within']:>9.3f} {r['n_obs']:>7,}")

    if timing:
        print("\n=== TIMING-TEST: KV LEDER STV ===")
        print(f"{'Parti':<6} {'β(kv_pst)':>10} {'SE':>8} {'p':>8} {'R²within':>9} {'N obs':>7}")
        print("-" * 60)
        for t in timing:
            stars = "***" if t["p_kv"] < 0.001 else "**" if t["p_kv"] < 0.01 else "*" if t["p_kv"] < 0.05 else ""
            print(f"  {t['parti']:<4} {t['b_kv']:>+10.4f} {t['se_kv']:>8.4f} "
                  f"{t['p_kv']:>8.4f}{stars:<3} {t['r2_within']:>9.3f} {t['n_obs']:>7,}")


def between_estimator(panel: pd.DataFrame) -> list[dict]:
    """
    Between-estimator: kommunegjennomsnitts-OLS.
    Fanger den strukturelle (tverrsnitts-)sammenhengen mellom
    langsiktig gjennomsnittlig befolkningsvekst og partioppslutning.
    Komplementerer FE som bare fanger within-variasjon.
    """
    resultater = []
    for parti in ["Sp", "Ap"]:
        for vtype in ["STV", "KV", None]:
            sub = panel[panel["parti"] == parti].copy()
            if vtype:
                sub = sub[sub["valgtype"] == vtype]
            vtag = vtype or "Alle"

            means = sub.groupby("kom2024").agg(
                pst_mean=("pst", "mean"),
                dpop10_mean=("dpop10", "mean"),
                lnpop_mean=("ln_pop", "mean"),
                sent_kode=("sent_kode", "first"),
            ).dropna()

            if len(means) < 50:
                continue

            X = sm.add_constant(means[["dpop10_mean", "lnpop_mean"]])
            m = sm.OLS(means["pst_mean"], X).fit()

            b = m.params.get("dpop10_mean", np.nan)
            se = m.bse.get("dpop10_mean", np.nan)
            p = m.pvalues.get("dpop10_mean", np.nan)
            resultater.append({
                "label": f"{parti} {vtag} [BETWEEN]",
                "avh": "pst",
                "uavh": ["dpop10_mean", "lnpop_mean"],
                "koeff": {"dpop10": {"b": b, "se": se, "p": p,
                                     "ci_lo": b - 1.96*se, "ci_hi": b + 1.96*se}},
                "r2_within": m.rsquared,
                "n_obs": len(means),
                "n_ent": len(means),
                "n_yr": 1,
                "success": True,
            })
    return resultater


def lagre_koeffisienter(resultater: list[dict], timing: list[dict]):
    rader = []
    for r in resultater:
        if not r.get("success"):
            continue
        for var, k in r["koeff"].items():
            rader.append({
                "modell": r["label"], "avh": r["avh"], "variabel": var,
                "b": round(k["b"], 5), "se": round(k["se"], 5),
                "p": round(k["p"], 5), "ci_lo": round(k["ci_lo"], 5),
                "ci_hi": round(k["ci_hi"], 5),
                "r2_within": round(r["r2_within"], 4),
                "n_obs": r["n_obs"], "n_ent": r["n_ent"],
            })
    for t in timing:
        rader.append({
            "modell": f"Timing {t['parti']}: KV→STV",
            "avh": "sv_pst", "variabel": "kv_pst",
            "b": round(t["b_kv"], 5), "se": round(t["se_kv"], 5),
            "p": round(t["p_kv"], 5),
            "ci_lo": None, "ci_hi": None,
            "r2_within": round(t["r2_within"], 4),
            "n_obs": t["n_obs"], "n_ent": t["n_kommuner"],
        })
    df = pd.DataFrame(rader)
    df.to_csv(f"{PROCESSED}/panel_resultater.csv", index=False)
    print(f"\n  Resultater lagret til {PROCESSED}/panel_resultater.csv")


# ── HOVEDPROGRAM ──────────────────────────────────────────────────────────────

def main():
    print("=== Laster data ===")
    sv, kv = last_valg()
    bef = last_bef()
    sent = last_sentralitet()
    print(f"  Befolkning: {bef.aar.min()}–{bef.aar.max()}, "
          f"{bef.kom2024.nunique()} kommuner")

    print("\n=== Bygger panel-datasett ===")
    panel = bygg_panel(sv, kv, bef, sent)

    # Sjekk dekningsgrad
    for parti in ["Sp", "Ap"]:
        sub = panel[panel["parti"] == parti]
        print(f"  {parti}: {sub.dropna(subset=['dpop10']).shape[0]:,} obs med dpop10 "
              f"({sub.dropna(subset=['dpop10']).kom2024.nunique()} kommuner)")

    print("\n=== FE-regresjoner ===")
    resultater = kjor_fe_regresjoner(panel)

    print("\n=== Between-estimator (strukturell effekt) ===")
    between = between_estimator(panel)
    resultater.extend(between)

    print("\n=== Timing-test ===")
    timing = timing_test(sv, kv, bef, sent)

    skriv_resultater(resultater, timing)
    lagre_koeffisienter(resultater, timing)

    print("\n=== Bygger visualiseringer ===")
    figs = {
        "dpop_ts":  fig_dpop_tidsserie(bef, sent),
        "fe_koeff": fig_fe_koeff(resultater),
        "sp_stv_scatter": fig_scatter_dpop_pst(panel, "Sp", "STV"),
        "sp_kv_scatter":  fig_scatter_dpop_pst(panel, "Sp", "KV"),
        "ap_stv_scatter": fig_scatter_dpop_pst(panel, "Ap", "STV"),
    }

    # Skriv standalone HTML med alle panelfigurer
    html_deler = []
    for navn, fig in figs.items():
        html_deler.append(f'<h3>{navn}</h3>' + fig.to_html(full_html=False,
                                                             include_plotlyjs=False))

    html = f"""<!DOCTYPE html>
<html lang="no">
<head><meta charset="UTF-8">
<title>Panel-regresjon: befolkning og partioppslutning</title>
<script src="https://cdn.plot.ly/plotly-3.4.0.min.js"></script>
<style>body{{font-family:sans-serif;max-width:1100px;margin:2rem auto;padding:1rem}}</style>
</head>
<body>
<h1>Panel-regresjon: befolkningsvekst og partioppslutning 1987–2025</h1>
{''.join(html_deler)}
</body></html>"""

    with open("panel_plot.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("  Ferdig → panel_plot.html")


if __name__ == "__main__":
    main()
