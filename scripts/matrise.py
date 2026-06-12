#!/usr/bin/env python3
"""
matrise.py — 2×2 matrise: sentralitet × befolkningsretning
Beregner nasjonalt bidrag (pp) = ΔSp (stemmevektet) × velger_andel for hvert kvadrant.

Kjør fra prosjektrot:  python scripts/matrise.py
"""

import warnings
import csv as csvmod
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

PROCESSED = "data/processed"
RAW       = "data/raw"

PARTIER = {
    "01": "Ap", "02": "FrP", "03": "Høyre", "04": "KrF",
    "05": "Sp", "06": "SV", "07": "Venstre", "08": "MDG", "55": "Rødt",
}
PARTIER_VIS = ["Sp", "FrP", "Høyre", "Ap"]
PARTI_CSS = {
    "Sp":    ("#009900", "font-weight:700"),
    "FrP":   ("#003f7f", ""),
    "Høyre": ("#0065f1", ""),
    "Ap":    ("#e4202c", ""),
}

TRANSITIONS = [
    {"key": "89→93", "y1": 1989, "y2": 1993, "pop_fra": 1986, "pop_til": 1990,
     "label": "↑ 89→93", "opp": True},
    {"key": "93→97", "y1": 1993, "y2": 1997, "pop_fra": 1987, "pop_til": 1993,
     "label": "↓ 93→97", "opp": False},
    {"key": "17→21", "y1": 2017, "y2": 2021, "pop_fra": 2011, "pop_til": 2021,
     "label": "↑ 17→21", "opp": True},
    {"key": "21→25", "y1": 2021, "y2": 2025, "pop_fra": 2015, "pop_til": 2021,
     "label": "↓ 21→25", "opp": False},
]

KVADRANTER = [
    ("lav_nedgang", "Lav sent + Nedgang"),
    ("lav_vekst",   "Lav sent + Vekst"),
    ("sent_nedgang","Sentral + Nedgang"),
    ("sent_vekst",  "Sentral + Vekst"),
]

KVAL_FARGER = {
    "lav_nedgang": "#d62728",
    "lav_vekst":   "#2ca02c",
    "sent_nedgang":"#ff7f0e",
    "sent_vekst":  "#1f77b4",
}


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


# ── MATRISE-BEREGNING ─────────────────────────────────────────────────────────

def befolk_vekst(bef, y1, y2):
    b1 = bef[bef["aar"] == y1].set_index("kom2024")["befolkning"].rename("b1")
    b2 = bef[bef["aar"] == y2].set_index("kom2024")["befolkning"].rename("b2")
    df = pd.concat([b1, b2], axis=1).dropna()
    df = df[df["b1"] > 0]
    df["vekst"] = (df["b2"] - df["b1"]) / df["b1"] * 100
    return df["vekst"].reset_index()


def bygg_kvadrant_data(sv, bef, sent, tr):
    """
    For en overgang (y1→y2), bygg per-kommune datasett med:
      - delta_parti for Sp, FrP, Høyre, Ap (voter-weighted innen gruppe)
      - total_stemmer_y2 (til velger_andel-beregning)
      - kvadrant (lav_nedgang / lav_vekst / sent_nedgang / sent_vekst)
    """
    y1, y2 = tr["y1"], tr["y2"]

    # Bredt format: prosent per (kom2024, parti, aar)
    sv_sub = sv[sv["parti"].isin(PARTIER_VIS) & sv["aar"].isin([y1, y2])][
        ["kom2024", "aar", "parti", "prosent", "total_stemmer"]].copy()

    # Hent total_stemmer per kommune for hvert år (identisk for alle partier)
    ts_y2 = (sv_sub[sv_sub["aar"] == y2][["kom2024", "total_stemmer"]]
             .drop_duplicates("kom2024").rename(columns={"total_stemmer": "ts_y2"}))

    # Pivot til wide
    wide = sv_sub.pivot_table(
        index="kom2024", columns=["parti", "aar"], values="prosent", aggfunc="first"
    )
    wide.columns = [f"pst_{p}_{y}" for p, y in wide.columns]
    wide = wide.reset_index()

    # Delta-kolonner
    for p in PARTIER_VIS:
        c1 = f"pst_{p}_{y1}"
        c2 = f"pst_{p}_{y2}"
        if c1 in wide.columns and c2 in wide.columns:
            wide[f"delta_{p}"] = wide[c2] - wide[c1]

    # Legg til total_stemmer y2 og befolkningsvekst
    wide = wide.merge(ts_y2, on="kom2024", how="left")
    vekst = befolk_vekst(bef, tr["pop_fra"], tr["pop_til"])
    wide = wide.merge(vekst, on="kom2024", how="left")
    wide = wide.merge(sent, on="kom2024", how="left")

    # Dropp manglende verdier
    wide = wide.dropna(subset=["delta_Sp", "vekst", "sent_kode", "ts_y2"])

    # Klassifiser i kvadranter
    lav = wide["sent_kode"] <= 1
    opp = wide["vekst"] < 0
    wide["kvadrant"] = "ukjent"
    wide.loc[lav  &  opp, "kvadrant"] = "lav_nedgang"
    wide.loc[lav  & ~opp, "kvadrant"] = "lav_vekst"
    wide.loc[~lav &  opp, "kvadrant"] = "sent_nedgang"
    wide.loc[~lav & ~opp, "kvadrant"] = "sent_vekst"

    return wide


def aggreger_kvadrant(df):
    """
    Per kvadrant:
      - n: antall kommuner
      - ts_sum: totale stemmer i gruppen
      - velger_andel: andel av nasjonale stemmer
      - delta_X_w: stemmevektet snitt ΔX
      - bidrag_X: stemmevektet ΔX × velger_andel (pp)
    """
    total_ts = df["ts_y2"].sum()
    rows = []
    for kv, _ in KVADRANTER:
        g = df[df["kvadrant"] == kv]
        if len(g) == 0:
            continue
        ts_sum = g["ts_y2"].sum()
        va = ts_sum / total_ts if total_ts > 0 else np.nan
        row = {"kvadrant": kv, "n": len(g), "velger_andel": va}
        for p in PARTIER_VIS:
            dcol = f"delta_{p}"
            if dcol in g.columns:
                dw = (g[dcol] * g["ts_y2"]).sum() / ts_sum
                row[f"delta_{p}_w"] = dw
                row[f"bidrag_{p}"] = dw * va
        rows.append(row)
    return pd.DataFrame(rows)


def bygg_alle_matriser(sv, bef, sent):
    resultat = {}
    for tr in TRANSITIONS:
        print(f"  Beregner {tr['key']}…")
        df = bygg_kvadrant_data(sv, bef, sent, tr)
        agg = aggreger_kvadrant(df)
        # Legg til Sp-nivå (ikke bare delta) for scatter-referanse
        y2 = tr["y2"]
        sp_y2 = sv[(sv["aar"] == y2) & (sv["parti"] == "Sp")][
            ["kom2024", "prosent"]].rename(columns={"prosent": "pst_sp_y2"})
        df = df.merge(sp_y2, on="kom2024", how="left")
        resultat[tr["key"]] = {"raw": df, "agg": agg}
    return resultat


# ── PLOTLY FIGURER ────────────────────────────────────────────────────────────

def fig_bidrag_stacked(alle):
    """
    Staplede søylediagrammer: Sp nasjonalt bidrag (pp) per kvadrant,
    for alle fire overganger.
    """
    tr_keys  = [tr["key"]   for tr in TRANSITIONS]
    tr_labels = [tr["label"] for tr in TRANSITIONS]

    fig = go.Figure()
    for kv, kv_navn in KVADRANTER:
        y_vals = []
        hover  = []
        for tr in TRANSITIONS:
            agg = alle[tr["key"]]["agg"]
            row = agg[agg["kvadrant"] == kv]
            if row.empty:
                y_vals.append(0)
                hover.append("")
            else:
                b = row["bidrag_Sp"].iloc[0]
                va = row["velger_andel"].iloc[0] * 100
                dw = row["delta_Sp_w"].iloc[0]
                y_vals.append(b)
                hover.append(
                    f"<b>{kv_navn}</b><br>"
                    f"Bidrag: {b:+.2f} pp<br>"
                    f"ΔSp (vektet): {dw:+.1f} pp<br>"
                    f"Velger-andel: {va:.1f}%<extra></extra>"
                )
        fig.add_trace(go.Bar(
            name=kv_navn,
            x=tr_labels,
            y=y_vals,
            marker_color=KVAL_FARGER[kv],
            hovertemplate=hover,
        ))

    fig.update_layout(
        barmode="relative",
        title="Sp nasjonalt bidrag (pp) per kvadrant — stemmevektet ΔSp × velger-andel",
        yaxis_title="Bidrag til nasjonal Sp-endring (pp)",
        xaxis_title="Overgang",
        template="plotly_white",
        height=460,
        legend=dict(orientation="h", y=-0.18, font_size=11),
        annotations=[
            dict(
                text="Positiv søyle = Sp vokser i gruppen og den bidrar positivt til nasjonal Sp-vekst.",
                xref="paper", yref="paper", x=0, y=1.06,
                showarrow=False, font=dict(size=10, color="#64748b"),
                align="left",
            )
        ],
    )
    return fig


def fig_bidrag_vs_rate(alle):
    """
    Scatter per overgang: x = velger_andel, y = ΔSp_w (rate),
    boble = bidrag. Viser at Sentral+Vekst dominerer.
    """
    fig = make_subplots(rows=1, cols=4,
                        subplot_titles=[tr["label"] for tr in TRANSITIONS],
                        shared_yaxes=True)
    for col, tr in enumerate(TRANSITIONS, 1):
        agg = alle[tr["key"]]["agg"]
        for _, row in agg.iterrows():
            kv    = row["kvadrant"]
            va    = row["velger_andel"] * 100
            dw    = row.get("delta_Sp_w", 0)
            bidr  = abs(row.get("bidrag_Sp", 0))
            n     = row["n"]
            kv_n  = dict(KVADRANTER).get(kv, kv)
            fig.add_trace(go.Scatter(
                x=[va], y=[dw],
                mode="markers+text",
                text=[f"<b>{kv_n.replace(' + ', '<br>')}</b>"],
                textposition="top center",
                marker=dict(
                    size=max(10, min(60, bidr * 15)),
                    color=KVAL_FARGER[kv],
                    opacity=0.75,
                    line=dict(width=1, color="white"),
                ),
                name=kv_n,
                showlegend=(col == 1),
                hovertemplate=(
                    f"<b>{kv_n}</b><br>"
                    f"Velger-andel: {va:.1f}%<br>"
                    f"ΔSp (vektet): {dw:+.1f} pp<br>"
                    f"Nasjonalt bidrag: {row.get('bidrag_Sp', 0):+.2f} pp<br>"
                    f"n={n}<extra></extra>"
                ),
            ), row=1, col=col)
        fig.add_hline(y=0, line_dash="dot", line_color="gray", row=1, col=col)

    fig.update_xaxes(title_text="Velger-andel (%)", ticksuffix="%")
    fig.update_yaxes(title_text="ΔSp vektet (pp)", row=1, col=1)
    fig.update_layout(
        height=420,
        template="plotly_white",
        title="Velger-andel vs ΔSp-rate per kvadrant (boble = nasjonalt bidrag)",
        legend=dict(orientation="h", y=-0.2, font_size=10),
    )
    return fig


# ── HTML-GENERERING ───────────────────────────────────────────────────────────

def pp_span(v, bold_thresh=5):
    """Fargekodet pp-verdi som HTML span."""
    if pd.isna(v):
        return '<span style="color:#94a3b8">—</span>'
    col   = "#166534" if v > 0 else "#991b1b" if v < 0 else "#6b7280"
    fw    = "font-weight:700;" if abs(v) >= bold_thresh else ""
    sign  = "+" if v > 0 else ""
    return f'<span style="color:{col};{fw}">{sign}{v:.1f}</span>'


def bidrag_badge(b):
    """Lite merke med nasjonal bidrag-verdi."""
    if pd.isna(b):
        return ""
    col  = "#166534" if b > 0 else "#991b1b" if b < 0 else "#6b7280"
    sign = "+" if b > 0 else ""
    return (
        f'<span title="Nasjonalt bidrag til Sp-endring (stemmevektet ΔSp × velger-andel)" '
        f'style="font-size:0.7rem;background:#f0fdf4;border:1px solid #86efac;'
        f'border-radius:4px;padding:1px 6px;color:{col};font-weight:600;'
        f'font-family:monospace;cursor:help">'
        f'{sign}{b:.2f} pp</span>'
    )


def lag_kort(kv_key, kv_tittel, icon, bg, border, alle):
    """
    Lager HTML for ett av de fire kortene i 2×2-matrisen.
    Inkluderer nå nasjonalt bidrag (pp) per overgang.
    """
    rader = ""
    for tr in TRANSITIONS:
        agg = alle[tr["key"]]["agg"]
        row = agg[agg["kvadrant"] == kv_key]
        if row.empty:
            continue
        r       = row.iloc[0]
        n       = int(r["n"])
        va_pst  = r["velger_andel"] * 100
        label   = tr["label"]
        opp     = tr["opp"]
        bkg     = "#f0fdf4" if opp else "#fef2f2"
        lbl_col = "#166534" if opp else "#991b1b"
        arrow   = "▲" if opp else "▼"

        # Partiendringer
        parts_html = ""
        for p in PARTIER_VIS:
            dw = r.get(f"delta_{p}_w", np.nan)
            pss = PARTI_CSS[p]
            style = f"color:{pss[0]};{pss[1]}"
            parts_html += (
                f'<span style="font-size:0.82rem;font-family:monospace">'
                f'<span style="{style}">{p}</span> '
                f'{pp_span(dw, bold_thresh=10)}</span>  '
            )

        # Bidrag-badge for Sp
        b_sp = r.get("bidrag_Sp", np.nan)
        badge = bidrag_badge(b_sp)

        rader += f"""
        <tr style="background:{bkg}">
          <td style="padding:6px 8px;white-space:nowrap;vertical-align:top">
            <span style="color:{lbl_col};font-weight:700;font-size:0.9rem">{arrow} {label}</span><br>
            <span style="font-size:0.7rem;color:#6b7280">
              <span style="font-size:0.72rem;background:#e2e8f0;border-radius:4px;padding:1px 5px;color:#475569">{va_pst:.1f}% av velgerne</span>
              <span style="font-size:0.72rem;color:#94a3b8">n={n}</span>
            </span>
          </td>
          <td style="padding:6px 8px;line-height:2">{parts_html}</td>
          <td style="padding:6px 8px;text-align:right;white-space:nowrap;vertical-align:middle">{badge}</td>
        </tr>"""

    return f"""
    <div style="background:{bg};border:1.5px solid {border};border-radius:12px;overflow:hidden">
      <div style="padding:10px 14px 6px;border-bottom:1px solid {border}">
        <div style="font-size:0.75rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.05em">{kv_tittel.split()[0]} {kv_tittel.split()[1]}</div>
        <div style="font-size:1.05rem;font-weight:700;color:{'#991b1b' if 'Nedgang' in kv_tittel else '#166534'}">{icon}</div>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:0.85rem">
        <thead>
          <tr style="background:rgba(0,0,0,0.03)">
            <th style="padding:5px 8px;text-align:left;font-size:0.72rem;color:#94a3b8;font-weight:500">Valg</th>
            <th style="padding:5px 8px;text-align:left;font-size:0.72rem;color:#94a3b8;font-weight:500">Netto endring (pp)</th>
            <th style="padding:5px 8px;text-align:right;font-size:0.72rem;color:#94a3b8;font-weight:500"
                title="Stemmevektet ΔSp × velger-andel = bidrag til nasjonal Sp-endring">Sp bidrag ℹ</th>
          </tr>
        </thead>
        <tbody>{rader}</tbody>
      </table>
    </div>"""


def lag_matrise_html(alle, fig_stacked, fig_scatter):
    """Komplett HTML-seksjon for 2×2-matrisen."""
    import plotly

    stacked_html = fig_stacked.to_html(full_html=False, include_plotlyjs=False)
    scatter_html = fig_scatter.to_html(full_html=False, include_plotlyjs=False)

    # Finn nasjonal ΔSp per overgang (sum av bidrag over alle kvadranter)
    nasj_linje = ""
    for tr in TRANSITIONS:
        agg = alle[tr["key"]]["agg"]
        total_b = agg["bidrag_Sp"].sum() if "bidrag_Sp" in agg.columns else np.nan
        nasj_linje += (
            f'<span style="font-size:0.78rem;background:#f8fafc;border:1px solid #e2e8f0;'
            f'border-radius:6px;padding:2px 8px;margin-right:6px">'
            f'<b>{tr["label"]}</b>: '
            f'<span style="color:{"#166534" if total_b > 0 else "#991b1b"};font-family:monospace">'
            f'{"+" if total_b > 0 else ""}{total_b:.2f} pp</span></span>'
        )

    kort_lav_ned  = lag_kort("lav_nedgang",  "Lav sentralitet Nedgang", "🏔️ Nedgang",
                              "#fff1f2", "#fca5a5", alle)
    kort_sent_ned = lag_kort("sent_nedgang", "Sentral Nedgang",          "🏙️ Nedgang",
                              "#fff1f2", "#fca5a5", alle)
    kort_lav_vek  = lag_kort("lav_vekst",   "Lav sentralitet Vekst",    "🌿 Vekst",
                              "#f0fdf4", "#86efac", alle)
    kort_sent_vek = lag_kort("sent_vekst",  "Sentral Vekst",             "🌆 Vekst",
                              "#f0fdf4", "#86efac", alle)

    return f"""<!-- === MATRISE-SEKSJON (generert) === -->
<section id="matrise" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
  <div class="mb-4">
    <h2 class="text-xl font-bold text-slate-900 mb-2">2×2 matrise: Sentralitet × Befolkningsretning</h2>
    <p class="text-slate-500 text-sm leading-relaxed">
      Netto endring i stemmeandel (pp) for Sp, FrP, Høyre og Ap i fire kommunegrupper —
      ved Senterpartiets to store opp­ganger (1993, 2021) og nedganger (1997, 2025).
      Velger-andel viser hvor stor del av stemmene som befinner seg i gruppen.
      <strong>Sp bidrag</strong> = stemmevektet ΔSp × velger-andel = gruppens bidrag til nasjonal Sp-endring.
    </p>
    <div style="margin-top:8px;line-height:2.2">
      <span style="font-size:0.72rem;color:#94a3b8;margin-right:4px">Nasjonal Sp-endring (rekonstruert fra kvadranter):</span>
      {nasj_linje}
    </div>
  </div>

  <!-- Akselabels -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;margin-bottom:4px;padding:0 4px">
    <div style="text-align:center;font-size:0.78rem;font-weight:600;color:#64748b;padding:4px;background:#f1f5f9;border-radius:6px">⬅ Lav sentralitet</div>
    <div style="text-align:center;font-size:0.78rem;font-weight:600;color:#64748b;padding:4px;background:#f1f5f9;border-radius:6px">Sentral ➡</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
    {kort_lav_ned}
    {kort_sent_ned}
    {kort_lav_vek}
    {kort_sent_vek}
  </div>

  <div style="margin-top:16px">
    <h3 style="font-size:0.95rem;font-weight:600;color:#334155;margin-bottom:4px">
      Nasjonalt bidrag per kvadrant (stablede søyler)
    </h3>
    <p style="font-size:0.8rem;color:#64748b;margin-bottom:8px">
      Bidrag = stemmevektet ΔSp i gruppen × gruppens andel av nasjonale stemmer.
      Sentral + Vekst (blå) dominerer det nasjonale utslaget — ikke fordi ΔSp er høyest der,
      men fordi gruppen har 70–80 % av velgerne.
    </p>
    {stacked_html}
  </div>

  <div style="margin-top:16px">
    <h3 style="font-size:0.95rem;font-weight:600;color:#334155;margin-bottom:4px">
      Velger-andel vs ΔSp-rate (boble = nasjonalt bidrag)
    </h3>
    <p style="font-size:0.8rem;color:#64748b;margin-bottom:8px">
      Kommunene med høyest ΔSp (y-akse) er de perifere nedgangskommunene — men de sitter
      med for liten andel av velgerne (x-akse) til å flytte det nasjonale resultatet alene.
    </p>
    {scatter_html}
  </div>
</section>
<!-- === SLUTT MATRISE === -->"""


# ── INJECT I INDEX.HTML ───────────────────────────────────────────────────────

def inject_html(ny_html: str, start_m: str, end_m: str, idx: str = "index.html"):
    try:
        with open(idx, encoding="utf-8") as f:
            page = f.read()
        s = page.find(start_m)
        e = page.find(end_m)
        if s == -1 or e == -1:
            print(f"  Advarsel: merker ikke funnet i {idx}")
            return
        e += len(end_m)
        page = page[:s] + ny_html.strip() + "\n" + page[e:]
        with open(idx, "w", encoding="utf-8") as f:
            f.write(page)
        print(f"  {idx} oppdatert")
    except FileNotFoundError:
        print(f"  Advarsel: {idx} ikke funnet")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("Laster data…")
    sv, bef = last_data()
    sent     = last_sentralitet()

    print("Beregner 2×2-matriser…")
    alle = bygg_alle_matriser(sv, bef, sent)

    # Skriv ut sammendrag
    print("\nSammendrag nasjonalt bidrag Sp:")
    for tr in TRANSITIONS:
        agg = alle[tr["key"]]["agg"]
        total_b = agg["bidrag_Sp"].sum()
        print(f"  {tr['label']}  nasjonal Sp Δ (rekonstruert): {total_b:+.2f} pp")
        for _, row in agg.iterrows():
            kv  = row["kvadrant"]
            dw  = row.get("delta_Sp_w", np.nan)
            va  = row["velger_andel"] * 100
            b   = row.get("bidrag_Sp", np.nan)
            n   = int(row["n"])
            print(f"    {kv:20s}  n={n:3d}  velgere={va:5.1f}%  ΔSp={dw:+5.1f}  bidrag={b:+5.2f} pp")

    print("\nLager figurer…")
    fig_stacked = fig_bidrag_stacked(alle)
    fig_scatter = fig_bidrag_vs_rate(alle)

    print("Lagrer HTML-filer…")
    # Lagre standalone-figurer
    fig_stacked.to_html(f"{PROCESSED}/bidrag_stacked.html",
                        full_html=True, include_plotlyjs="cdn")
    print(f"  {PROCESSED}/bidrag_stacked.html")

    # Bygg og lagre matrise-seksjon
    matrise_html = lag_matrise_html(alle, fig_stacked, fig_scatter)
    with open(f"{PROCESSED}/matrise.html", "w", encoding="utf-8") as f:
        f.write(matrise_html)
    print(f"  {PROCESSED}/matrise.html")

    # Inject i index.html
    print("Injiserer i index.html…")
    inject_html(
        matrise_html,
        "<!-- === MATRISE-SEKSJON (generert) === -->",
        "<!-- === SLUTT MATRISE === -->",
    )
    print("Ferdig.")


if __name__ == "__main__":
    main()
