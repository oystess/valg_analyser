#!/usr/bin/env python3
"""
Analyse: Befolkningsvekst og partioppslutning i norske stortingsvalg
Hypotese: Ap tapte velgere til Sp 2013→2017 i kommuner med lav befolkningsvekst

Datakilder (lokale filer):
  - data_valg_1317.csv:  SSB 08092 (2013/2017, pre-2020 kommunekoder)
  - data_valg_2125.csv:  SSB 08092 (2021/2025, 2024-kommunekoder)
  - distriktstall.xlsx:  Befolkningsdata + sentralitet (B06, B16, befvekst10)
  - sentralitet.csv:     SSBs sentralitetsindeks
"""

import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import plotly.graph_objects as go

warnings.filterwarnings("ignore")

PARTIER = {
    "01": "Ap",
    "02": "FrP",
    "03": "Høyre",
    "04": "KrF",
    "05": "Sp",
    "06": "SV",
    "07": "Venstre",
    "08": "MDG",
    "55": "Rødt",
}

PARTI_FARGER = {
    "Ap": "#e4202c",
    "FrP": "#003f7f",
    "Høyre": "#0065f1",
    "KrF": "#ffd700",
    "Sp": "#009900",
    "SV": "#eb4040",
    "Venstre": "#00b050",
    "MDG": "#3cb371",
    "Rødt": "#aa0000",
}

SENTRALITET_NAVN = {
    "0": "Minst sentrale",
    "1": "Mindre sentrale",
    "2": "Noe sentrale",
    "3": "Sentrale",
}

SENT_FARGER = {
    "0": "#d62728",
    "1": "#ff7f0e",
    "2": "#2ca02c",
    "3": "#1f77b4",
}


# ── DATAHENTING ───────────────────────────────────────────────────────────────

def hent_valgdata_1317(path="data_valg_1317.csv") -> pd.DataFrame:
    """Les 2013/2017 valgdata fra lokal CSV (SSB 08092, pre-2020 koder)."""
    print(f"  Leser {path}...")
    return pd.read_csv(path)


def hent_valgdata_2125(path="data_valg_2125.csv") -> pd.DataFrame:
    """Les 2021/2025 valgdata fra lokal CSV (SSB 08092, 2024-koder)."""
    print(f"  Leser {path}...")
    return pd.read_csv(path)


def hent_befolkning(path="distriktstall.xlsx") -> pd.DataFrame:
    """Les befolkningsdata fra lokalt Excel-ark."""
    print(f"  Leser {path}...")
    df = pd.read_excel(path, sheet_name="Ark1")
    return df


# ── PROSESSERING ──────────────────────────────────────────────────────────────

def prosesser_valg(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Gjør CSV-data til tidy format:
      komm_nr, komm_navn, ar, parti, pst
    CSV-kolonnene er: Tid, GodkjenteProsent, PolitParti, Region
    """
    df = df_raw.copy()
    df = df[df["GodkjenteProsent"].notna()]

    # Ekstraher år (første 4 tegn av "2013 2013")
    df["ar"] = df["Tid"].astype(str).str[:4]

    # Ekstraher kommunenummer (første 4 siffer av "0101 Halden (-2019)")
    df["komm_nr"] = df["Region"].astype(str).str.extract(r"^(\d{4})")[0]
    df = df[df["komm_nr"].notna() & (df["komm_nr"] != "0000")]

    # Ekstraher partikode og map til kortnavn
    df["parti_kode"] = df["PolitParti"].astype(str).str.extract(r"^(\d+)")[0]
    df["parti"] = df["parti_kode"].map(PARTIER)
    df = df[df["parti"].notna()]

    # Kommunenavn (fjern parentes og ekstra whitespace)
    df["komm_navn"] = (df["Region"].astype(str)
                       .str.replace(r"\s*\(.*?\)", "", regex=True)
                       .str.replace(r"^\d{4}\s*", "", regex=True)
                       .str.strip())

    df["pst"] = pd.to_numeric(df["GodkjenteProsent"], errors="coerce")

    return df[["komm_nr", "komm_navn", "ar", "parti", "pst"]].copy()


def lag_bred_valgtabell(df: pd.DataFrame) -> pd.DataFrame:
    pivot = df.pivot_table(
        index=["komm_nr", "komm_navn", "ar"], columns="parti", values="pst", aggfunc="first"
    ).reset_index()
    pivot.columns.name = None
    return pivot


def prosesser_befolkning(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Fra distriktstall.xlsx: ekstraher komm_nr, befolkning 2016, vekst.
    Kolonner brukt: Kommunenavn, B06-O, B16-O, befvekst10
    """
    df = df_raw.copy()

    # Kommunenummer fra "0101 Halden"
    df["komm_nr"] = df["Kommunenavn"].astype(str).str.extract(r"^(\d{4})")[0]
    df = df[df["komm_nr"].notna()]

    # befvekst10 er en fraksjon (0.10 = 10 %), gjør om til prosent
    df["vekst_10yr"] = pd.to_numeric(df["befvekst10"], errors="coerce") * 100

    # Beregn vekst fra B06-O og B16-O
    df["pop06"] = pd.to_numeric(df["B06-O"], errors="coerce")
    df["pop16"] = pd.to_numeric(df["B16-O"], errors="coerce")

    # 10-år: 2006→2016 (samme som befvekst10, men i prosent)
    # Bruk befvekst10 direkte (mer presist)

    # Innbyggertall for boble-størrelse
    df["folkemengde_2016"] = df["pop16"]

    return df[["komm_nr", "vekst_10yr", "folkemengde_2016"]].copy()


def last_sentralitet(path="sentralitet.csv") -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", quotechar='"', encoding="latin1")
    # Kolonner: sourceCode, sourceName, targetCode, targetName
    df = df.rename(columns={
        "sourceCode": "sent_kode",
        "targetCode": "komm_nr",
    })
    df["komm_nr"] = df["komm_nr"].astype(str).str.zfill(4)
    df["sent_kode"] = df["sent_kode"].astype(str)
    return df[["komm_nr", "sent_kode"]].copy()


# ── ANALYSE ───────────────────────────────────────────────────────────────────

def bygg_analysedata(valg_1317, pop, sent) -> pd.DataFrame:
    """Merge 2013/2017-valg, befolkningsvekst og sentralitet."""
    v13 = valg_1317[valg_1317["ar"] == "2013"].drop(columns="ar")
    v17 = valg_1317[valg_1317["ar"] == "2017"].drop(columns="ar")

    df = v13.merge(v17, on=["komm_nr", "komm_navn"], suffixes=("_2013", "_2017"))

    for parti in PARTIER.values():
        c13, c17 = f"{parti}_2013", f"{parti}_2017"
        if c13 in df.columns and c17 in df.columns:
            df[f"delta_{parti}"] = (df[c17] - df[c13]).round(2)

    df = df.merge(pop, on="komm_nr", how="left")
    df = df.merge(sent, on="komm_nr", how="left")
    df["sent_num"] = pd.to_numeric(df["sent_kode"], errors="coerce")
    return df


def kjor_regresjoner(df: pd.DataFrame) -> dict:
    resultater = {}
    avh_vars = ["delta_Ap", "delta_Sp"]

    for avh in avh_vars:
        resultater[avh] = {}
        data = df[[avh, "vekst_10yr", "sent_num"]].dropna()
        X1 = sm.add_constant(data["vekst_10yr"])
        m1 = sm.OLS(data[avh], X1).fit()
        X2 = sm.add_constant(data[["vekst_10yr", "sent_num"]])
        m2 = sm.OLS(data[avh], X2).fit()
        resultater[avh]["vekst_10yr"] = {"biv": m1, "multi": m2, "n": len(data)}
    return resultater


# ── PLOTLY VISUALISERING ──────────────────────────────────────────────────────

def scatter_med_reg(df, xvar, yvar, xtittel, ytittel, modell) -> go.Figure:
    data = df[[xvar, yvar, "sent_kode", "komm_navn", "folkemengde_2016"]].dropna()
    fig = go.Figure()

    for kode in sorted(data["sent_kode"].dropna().unique()):
        sub = data[data["sent_kode"] == kode]
        fig.add_trace(go.Scatter(
            x=sub[xvar], y=sub[yvar], mode="markers",
            name=SENTRALITET_NAVN.get(str(kode), kode),
            marker=dict(
                color=SENT_FARGER.get(str(kode), "#888"),
                size=sub["folkemengde_2016"].apply(
                    lambda v: max(4, min(18, v ** 0.35 / 5)) if pd.notna(v) else 6
                ),
                opacity=0.75, line=dict(width=0.4, color="white"),
            ),
            text=sub["komm_navn"],
            hovertemplate=(
                "<b>%{text}</b><br>" + xtittel + ": %{x:.1f}%<br>"
                + ytittel + ": %{y:.1f} pp<extra></extra>"
            ),
        ))

    # Regresjonslinje med KI-bånd
    x_range = np.linspace(data[xvar].quantile(0.01), data[xvar].quantile(0.99), 200)
    xp = pd.DataFrame({"const": 1, xvar: x_range})
    pred = modell.get_prediction(xp)
    ci = pred.summary_frame(alpha=0.05)

    fig.add_trace(go.Scatter(
        x=np.concatenate([x_range, x_range[::-1]]),
        y=np.concatenate([ci["mean_ci_upper"], ci["mean_ci_lower"][::-1]]),
        fill="toself", fillcolor="rgba(0,0,0,0.08)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=x_range, y=ci["mean"],
        mode="lines", line=dict(color="black", width=2, dash="dash"),
        name=f"OLS  R²={modell.rsquared:.3f}  p={modell.f_pvalue:.4f}",
    ))

    fig.update_layout(
        xaxis_title=xtittel, yaxis_title=ytittel,
        hovermode="closest", template="plotly_white",
        legend=dict(font_size=11), margin=dict(t=30, b=40),
    )
    return fig


def tabell_regresjoner(reg: dict) -> str:
    """HTML-tabell med regresjonsresultater."""
    rader = []
    for avh, modeller in reg.items():
        for xvar, res in modeller.items():
            m = res["biv"]
            b = m.params.iloc[1]
            p = m.pvalues.iloc[1]
            stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
            rader.append(f"""
<tr>
  <td>{avh.replace('delta_', '&Delta;')}</td>
  <td>{xvar.replace('vekst_', '').replace('yr', ' år')}</td>
  <td>{b:+.3f}{stars}</td>
  <td>{m.rsquared:.3f}</td>
  <td>{p:.4f}</td>
  <td>{res['n']}</td>
</tr>""")
    return "\n".join(rader)


def lag_tidsserie_nasjonal(raw_1317: pd.DataFrame, raw_2125: pd.DataFrame) -> go.Figure:
    """Nasjonal utvikling alle partier 2013-2025."""
    partier_vis = ["Ap", "Sp", "Høyre", "FrP", "SV", "Rødt", "MDG"]

    df13 = prosesser_valg(raw_1317)
    df21 = prosesser_valg(raw_2125)
    nasjonal = pd.concat([df13, df21], ignore_index=True)
    nasjonal = nasjonal[nasjonal["parti"].isin(partier_vis)]
    nasjonal = nasjonal.groupby(["ar", "parti"])["pst"].mean().reset_index()

    fig = go.Figure()
    for parti in partier_vis:
        sub = nasjonal[nasjonal["parti"] == parti].sort_values("ar")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["ar"], y=sub["pst"], mode="lines+markers",
            name=parti, line=dict(color=PARTI_FARGER.get(parti), width=2.5),
            marker=dict(size=8),
        ))
    fig.update_layout(
        xaxis_title="Valg", yaxis_title="Gjennomsnittlig kommuneoppslutning (%)",
        template="plotly_white", hovermode="x unified",
        legend=dict(font_size=11), margin=dict(t=30),
    )
    return fig


def lag_korrscatter(df) -> go.Figure:
    """Korrelasjon mellom ΔAp og ΔSp 2013→2017."""
    data = df[["delta_Ap", "delta_Sp", "sent_kode", "komm_navn"]].dropna()
    fig = go.Figure()
    for kode in sorted(data["sent_kode"].dropna().unique()):
        sub = data[data["sent_kode"] == kode]
        fig.add_trace(go.Scatter(
            x=sub["delta_Ap"], y=sub["delta_Sp"], mode="markers",
            name=SENTRALITET_NAVN.get(str(kode), kode),
            marker=dict(color=SENT_FARGER.get(str(kode), "#888"), size=6, opacity=0.7),
            text=sub["komm_navn"],
            hovertemplate="<b>%{text}</b><br>ΔAp: %{x:.1f} pp<br>ΔSp: %{y:.1f} pp<extra></extra>",
        ))
    r = data["delta_Ap"].corr(data["delta_Sp"])
    fig.add_annotation(
        x=0.05, y=0.95, xref="paper", yref="paper",
        text=f"Pearson r = {r:.3f}", showarrow=False,
        font=dict(size=13), bgcolor="white", bordercolor="gray",
    )
    fig.update_layout(
        xaxis_title="Endring Ap 2013→2017 (pp)",
        yaxis_title="Endring Sp 2013→2017 (pp)",
        template="plotly_white", hovermode="closest",
        legend=dict(font_size=11), margin=dict(t=30),
    )
    return fig


# ── HTML-RAPPORT ──────────────────────────────────────────────────────────────

def bygg_html(figs: dict, reg: dict, n_kommuner: int) -> str:
    plots = {k: f.to_html(full_html=False, include_plotlyjs=False) for k, f in figs.items()}
    reg_html = tabell_regresjoner(reg)

    return f"""<!DOCTYPE html>
<html lang="no">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Befolkningsvekst og partioppslutning – Norge</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f9f9f9; color: #222; }}
  h1 {{ color: #1a1a2e; border-bottom: 3px solid #e4202c; padding-bottom: 10px; }}
  h2 {{ color: #333; margin-top: 40px; }}
  .kort {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 6px rgba(0,0,0,.08); }}
  .tabs {{ display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }}
  .tab {{ padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; background: #eee; font-size: 14px; }}
  .tab.aktiv {{ background: #e4202c; color: white; }}
  .panel {{ display: none; }}
  .panel.aktiv {{ display: block; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  th {{ background: #1a1a2e; color: white; padding: 10px; text-align: left; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #eee; }}
  tr:hover td {{ background: #f5f5f5; }}
  .info {{ background: #e8f4fd; border-left: 4px solid #2196F3; padding: 12px; border-radius: 4px; margin: 10px 0; font-size: 14px; }}
  .merknad {{ font-size: 12px; color: #666; margin-top: 8px; }}
</style>
</head>
<body>

<h1>Befolkningsvekst og politisk oppslutning i norske kommuner</h1>

<div class="info">
  <strong>Analysegrunnlag:</strong> {n_kommuner} kommuner (stabilt grensesett, stortingsvalg 2013–2025).
  Valgdata: SSB tabell 08092. Befolkningsdata: Distriktsindikatorene (B06/B16, 10-år vekst 2006–2016). Sentralitet: SSBs indeks.
  <br><strong>Hypotese:</strong> Ap tapte velgere til Sp i perioden 2013→2017 i kommuner med lavest befolkningsvekst.
</div>

<!-- Nasjonal tidsserie -->
<div class="kort">
  <h2>Nasjonal utvikling 2013–2025</h2>
  <p>Gjennomsnittlig kommuneoppslutning per valg. Sp når topp i 2021; Ap på jevnt lavere nivå.</p>
  {plots["tidsserie"]}
</div>

<!-- Korrelasjon ΔAp vs ΔSp -->
<div class="kort">
  <h2>Sammenheng mellom Aps tap og Sps vekst 2013→2017</h2>
  <p>Hvert punkt er én kommune. Negativt samband indikerer at der Ap falt, vokste Sp.</p>
  {plots["korrelasjon"]}
  <p class="merknad">Farger = SSBs sentralitetsindeks (4 grupper). Kommuner med stort Ap-fall hadde ofte stor Sp-vekst.</p>
</div>

<!-- Scatter befolkningsvekst vs ΔAp -->
<div class="kort">
  <h2>Befolkningsvekst (2006–2016) vs. endring i Ap-oppslutning 2013→2017</h2>
  {plots["ap_10yr"]}
  <p class="merknad">Negativt stigningstall: kommuner med høyere befolkningsvekst hadde mindre Ap-fall.
     Boble-størrelse = antall innbyggere (2016). Farger = sentralitetsklasse.</p>
</div>

<!-- Scatter befolkningsvekst vs ΔSp -->
<div class="kort">
  <h2>Befolkningsvekst (2006–2016) vs. endring i Sp-oppslutning 2013→2017</h2>
  {plots["sp_10yr"]}
  <p class="merknad">Negativt stigningstall: Sp vokste mest der befolkningsveksten var lavest.</p>
</div>

<!-- Regresjonstabeller -->
<div class="kort">
  <h2>Regresjonsresultater (OLS bivariat)</h2>
  <table>
    <tr><th>Avhengig var.</th><th>Vekstmål</th><th>Koeffisient</th><th>R²</th><th>p-verdi</th><th>N</th></tr>
    {reg_html}
  </table>
  <p class="merknad">*** p&lt;0.001 &nbsp; ** p&lt;0.01 &nbsp; * p&lt;0.05.
     Koeffisient = prosentpoeng endring i partioppslutning per % befolkningsvekst.</p>
</div>

<script>
function byttPanel(el, prefix, id) {{
  document.querySelectorAll('#' + prefix + '-p5yr, #' + prefix + '-p10yr, #' + prefix + '-p15yr')
    .forEach(p => p.classList.remove('aktiv'));
  el.closest('.kort').querySelectorAll('.tab').forEach(t => t.classList.remove('aktiv'));
  document.getElementById(prefix + '-' + id).classList.add('aktiv');
  el.classList.add('aktiv');
}}
</script>
</body>
</html>"""


# ── HOVEDPROGRAM ──────────────────────────────────────────────────────────────

def main():
    print("=== Laster data ===")
    raw_1317 = hent_valgdata_1317()
    raw_2125 = hent_valgdata_2125()
    raw_bef  = hent_befolkning()

    print("=== Prosesserer ===")
    valg_1317 = prosesser_valg(raw_1317)
    bred_1317 = lag_bred_valgtabell(valg_1317)
    pop       = prosesser_befolkning(raw_bef)
    sent      = last_sentralitet("sentralitet.csv")

    df = bygg_analysedata(bred_1317, pop, sent)
    print(f"  Analysedata: {len(df)} kommuner")

    # Diagnostikk
    print(f"  Kommuner med vekst_10yr: {df['vekst_10yr'].notna().sum()}")
    print(f"  Kommuner med sentralitet: {df['sent_kode'].notna().sum()}")
    print(f"  delta_Ap range: {df['delta_Ap'].min():.1f} til {df['delta_Ap'].max():.1f}")
    print(f"  delta_Sp range: {df['delta_Sp'].min():.1f} til {df['delta_Sp'].max():.1f}")

    print("=== Kjører regresjoner ===")
    reg = kjor_regresjoner(df)
    for avh, modeller in reg.items():
        for xvar, res in modeller.items():
            m = res["biv"]
            print(f"  {avh} ~ {xvar}: β={m.params.iloc[1]:+.3f}, R²={m.rsquared:.3f}, "
                  f"p={m.pvalues.iloc[1]:.4f}, n={res['n']}")

    print("=== Bygger visualiseringer ===")
    figs = {
        "tidsserie":  lag_tidsserie_nasjonal(raw_1317, raw_2125),
        "korrelasjon": lag_korrscatter(df),
        "ap_10yr": scatter_med_reg(
            df, "vekst_10yr", "delta_Ap",
            "Befolkningsvekst 2006–2016 (%)", "Endring Ap (pp)",
            reg["delta_Ap"]["vekst_10yr"]["biv"]
        ),
        "sp_10yr": scatter_med_reg(
            df, "vekst_10yr", "delta_Sp",
            "Befolkningsvekst 2006–2016 (%)", "Endring Sp (pp)",
            reg["delta_Sp"]["vekst_10yr"]["biv"]
        ),
    }

    print("=== Skriver index.html ===")
    html = bygg_html(figs, reg, len(df))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("  Ferdig → index.html")


if __name__ == "__main__":
    main()
