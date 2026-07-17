#!/usr/bin/env python3
"""
analyse_mekanismer.py — «Proteststemmens livssyklus»: fire valg, tre mekanismer.

Tester hypotesen om at bølgene har ulik karakter:
  1993: sak-mobilisering (EU) gradert etter statisk periferi (distrikt)
  2017: left-behind — faktisk befolkningsforvitring bærer effekten
  2021: nasjonal metning — ingen befolkningsgradient
  2025: kollaps brattest i left-behind-kommunene; FrP-bølgen er IKKE gradert

Metode per bølge: standardisert OLS av ΔSp mot befolkningsvekst, med og uten
sentralitetskontroll. Persistens: korrelasjon mellom bølgegevinst og påfølgende endring.

1989-laget i kildedataene er permanent fikset (se hent_stv_fiks.py); den
tidligere minne-korreksjonen er fjernet. Vang/Hamar-utelatelsen beholdes for
kontinuitet med tidligere kjøringer (kollisjonen er fikset i data).

Del 2 — avterritorialiserings-testen (2025): tester om FrP-bølgen følger
kjøpekraftsklemma (medianinntektsvekst 2021→2024) eller renteeksponering
(andel 25–44 år) i stedet for befolkningsnedgang. Data: data/processed/
kjopekraft_2124.csv (SSB 06944 medianinntekt etter skatt per husholdning,
2021-tall hentet med 2020-kodeliste og mappet til 2024-koder; SSB 07459
antall 25–44 år, 2021; hentet via SSB MCP 2026-07-02).

Injiserer seksjon i index.html mellom egne merker (idempotent):
  <!-- === START MEKANISMER === --> ... <!-- === SLUTT MEKANISMER === -->

Kjør fra prosjektrot:  python scripts/analyse_mekanismer.py
"""

import warnings
import csv as csvmod
import numpy as np
import pandas as pd
import statsmodels.api as sm
import plotly.graph_objects as go

warnings.filterwarnings("ignore")

PROCESSED = "data/processed"
RAW       = "data/raw"

SENTRALITET_NAVN = {0: "Minst sentrale", 1: "Mindre sentrale",
                    2: "Noe sentrale", 3: "Sentrale"}
SENT_FARGER = {0: "#d62728", 1: "#ff7f0e", 2: "#2ca02c", 3: "#1f77b4"}

START_M = "<!-- === START MEKANISMER === -->"
SLUTT_M = "<!-- === SLUTT MEKANISMER === -->"


# ── DATA ──────────────────────────────────────────────────────────────────────

def last_data():
    sv  = pd.read_csv(f"{PROCESSED}/stortingsvalg_2024.csv", dtype={"kom2024": str, "parti": str})
    bef = pd.read_csv(f"{PROCESSED}/befolkning_2024.csv", dtype={"kom2024": str})

    # Utelat mappingkollisjon Vang/Hamar
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

    # 0 = hull i SSB-serien for sammenslåtte kommuner → NaN
    bpiv = (bef.pivot_table(index="kom2024", columns="aar", values="befolkning",
                            aggfunc="first").replace(0, np.nan))
    return sv, bpiv, sent


def parti_pivot(sv, kode):
    return sv[sv["parti"] == kode].pivot_table(
        index="kom2024", columns="aar", values="prosent", aggfunc="first")


def _z(s):
    return (s - s.mean()) / s.std()


# ── BØLGEANALYSE ─────────────────────────────────────────────────────────────

def analyser_bolge(dser: pd.Series, bpiv, sent, p0: int, p1: int) -> dict:
    """Standardisert OLS av Δoppslutning mot befolkningsvekst p0→p1,
    med og uten sentralitetsdummier."""
    d = dser.rename("d").to_frame()
    d["vekst"] = (bpiv[p1] - bpiv[p0]) / bpiv[p0] * 100
    d = d.join(sent).replace([np.inf, -np.inf], np.nan).dropna()

    mA = sm.OLS(_z(d["d"]), sm.add_constant(_z(d["vekst"]))).fit()
    D = pd.get_dummies(d["sent"], prefix="s", drop_first=True).astype(float)
    mB = sm.OLS(_z(d["d"]), sm.add_constant(pd.concat([_z(d["vekst"]), D], axis=1))).fit()
    mC = sm.OLS(_z(d["d"]), sm.add_constant(D)).fit()

    per_sent = d.groupby("sent")["d"].mean()
    kvintil = d.groupby(pd.qcut(d["vekst"], 5, labels=False))["d"].mean()
    return {"n": len(d), "data": d,
            "beta_alene": mA.params["vekst"], "p_alene": mA.pvalues["vekst"],
            "r2_alene": mA.rsquared,
            "beta_kontroll": mB.params["vekst"], "p_kontroll": mB.pvalues["vekst"],
            "r2_sent": mC.rsquared,
            "per_sent": per_sent, "kvintil": kvintil}


def analyser_kanal_2025(sp, frp, bpiv, sent) -> dict:
    """
    Avterritorialiserings-testen: ΔFrP og ΔSp 2021→2025 mot
    (a) medianinntektsvekst 2021→2024, (b) andel 25–44 år, (c) dpop10.
    """
    kk = pd.read_csv(f"{PROCESSED}/kjopekraft_2124.csv", dtype={"kom2024": str}).set_index("kom2024")
    df = pd.DataFrame({
        "dfrp": frp[2025] - frp[2021],
        "dsp":  sp[2025] - sp[2021],
        "dpop10": (bpiv[2025] - bpiv[2015]) / bpiv[2015] * 100,
    }).join(kk).join(sent)
    df["inntvekst"] = (df["medianinntekt_2024"] / df["medianinntekt_2021"] - 1) * 100
    df["andel2544"] = df["antall_25_44_2021"] / bpiv[2021] * 100
    df = df.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["dfrp", "dsp", "dpop10", "inntvekst", "andel2544", "sent"])

    D = pd.get_dummies(df["sent"], prefix="s", drop_first=True).astype(float)
    res = {"n": len(df), "data": df,
           "iqr_innt": (df["inntvekst"].quantile(0.25), df["inntvekst"].quantile(0.75))}
    for y in ["dfrp", "dsp"]:
        res[y] = {}
        for lab, Xv, med_sent in [("biv_innt", ["inntvekst"], False),
                                  ("biv_alder", ["andel2544"], False),
                                  ("biv_dpop", ["dpop10"], False),
                                  ("full", ["inntvekst", "andel2544", "dpop10"], True)]:
            X = pd.concat([_z(df[v]).rename(v) for v in Xv], axis=1)
            if med_sent:
                X = pd.concat([X, D], axis=1)
            m = sm.OLS(_z(df[y]), sm.add_constant(X)).fit()
            res[y][lab] = {v: (m.params[v], m.pvalues[v]) for v in Xv}
        res[y]["kvintil_alder"] = df.groupby(
            pd.qcut(df["andel2544"], 5, labels=False))[y].mean()
    return res


# ── FIGURER ──────────────────────────────────────────────────────────────────

def fig_sp_niva(sp: pd.DataFrame, sent) -> go.Figure:
    """Sp-nivå per sentralitetsgruppe 1989–2025."""
    niva = sp.join(sent).groupby("sent").mean()
    fig = go.Figure()
    for kode in [0, 1, 2, 3]:
        if kode not in niva.index:
            continue
        rad = niva.loc[kode].dropna()
        fig.add_trace(go.Scatter(
            x=rad.index, y=rad.values.round(1), mode="lines+markers",
            name=SENTRALITET_NAVN[kode],
            line=dict(color=SENT_FARGER[kode], width=2.5), marker=dict(size=7),
            hovertemplate=f"<b>{SENTRALITET_NAVN[kode]}</b><br>"
                          "%{x}: %{y:.1f} %<extra></extra>",
        ))
    fig.update_layout(
        xaxis_title="Stortingsvalg", yaxis_title="Gj.sn. Sp-oppslutning (%)",
        template="plotly_white", hovermode="x unified",
        legend=dict(font_size=11, orientation="h", x=0.5, xanchor="center", y=-0.15),
        margin=dict(t=30, b=70),
    )
    return fig


def fig_beta_bolger(bolger: dict) -> go.Figure:
    """Std-β(vekst) per bølge, alene og med sentralitetskontroll."""
    navn = list(bolger.keys())
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=navn, y=[round(bolger[b]["beta_alene"], 3) for b in navn],
        name="Vekst alene", marker_color="#334155",
        hovertemplate="std-β=%{y:.3f}<extra>alene</extra>",
    ))
    fig.add_trace(go.Bar(
        x=navn, y=[round(bolger[b]["beta_kontroll"], 3) for b in navn],
        name="Vekst m/ sentralitetskontroll", marker_color="#94a3b8",
        hovertemplate="std-β=%{y:.3f}<extra>m/ kontroll</extra>",
    ))
    fig.add_hline(y=0, line_color="rgba(0,0,0,0.4)", line_width=1)
    fig.update_layout(
        barmode="group", yaxis_title="Standardisert β (befolkningsvekst)",
        template="plotly_white",
        legend=dict(font_size=11, orientation="h", x=0.5, xanchor="center", y=-0.2),
        margin=dict(t=30, b=80),
    )
    return fig


def fig_2025(b_sp: dict, b_frp: dict) -> go.Figure:
    """2025: ΔSp og ΔFrP per befolkningsvekst-kvintil."""
    labels = ["Størst<br>nedgang", "2", "3", "4", "Størst<br>vekst"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=b_sp["kvintil"].round(1).tolist(),
                         name="ΔSp 2021→2025", marker_color="#009900",
                         hovertemplate="ΔSp: %{y:.1f} pp<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=b_frp["kvintil"].round(1).tolist(),
                         name="ΔFrP 2021→2025", marker_color="#003f7f",
                         hovertemplate="ΔFrP: %{y:.1f} pp<extra></extra>"))
    fig.add_hline(y=0, line_color="rgba(0,0,0,0.4)", line_width=1)
    fig.update_layout(
        barmode="group", xaxis_title="Befolkningsvekst-kvintil (2015–2025)",
        yaxis_title="Endring 2021→2025 (pp)", template="plotly_white",
        legend=dict(font_size=11, orientation="h", x=0.5, xanchor="center", y=-0.25),
        margin=dict(t=30, b=90),
    )
    return fig


def fig_kanal(kanal: dict) -> go.Figure:
    """ΔFrP og ΔSp 2021→2025 per kvintil av andel 25–44 år."""
    labels = ["Færrest<br>25–44", "2", "3", "4", "Flest<br>25–44"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=kanal["dfrp"]["kvintil_alder"].round(1).tolist(),
                         name="ΔFrP 2021→2025", marker_color="#003f7f",
                         hovertemplate="ΔFrP: %{y:.1f} pp<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=kanal["dsp"]["kvintil_alder"].round(1).tolist(),
                         name="ΔSp 2021→2025", marker_color="#009900",
                         hovertemplate="ΔSp: %{y:.1f} pp<extra></extra>"))
    fig.add_hline(y=0, line_color="rgba(0,0,0,0.4)", line_width=1)
    fig.update_layout(
        barmode="group",
        xaxis_title="Kommuner etter andel 25–44-åringer (2021), kvintiler",
        yaxis_title="Endring 2021→2025 (pp)", template="plotly_white",
        legend=dict(font_size=11, orientation="h", x=0.5, xanchor="center", y=-0.25),
        margin=dict(t=30, b=90),
    )
    return fig


# ── HTML-SEKSJON ─────────────────────────────────────────────────────────────

def bygg_seksjon(bolger, pers_93, snitt_93_97, pers_17, snitt_17_21,
                 korr_opp_ned, korr_sp_frp, niva21_periferi, kanal, figs) -> str:
    b93, b17, b21, b25sp, b25frp = (bolger[k] for k in
        ["1993", "2017", "2021", "2025 (Sp-fall)", "2025 (FrP)"])
    andel93 = abs(b93["beta_kontroll"] / b93["beta_alene"]) * 100
    andel17 = abs(b17["beta_kontroll"] / b17["beta_alene"]) * 100
    plots = {k: f.to_html(full_html=False, include_plotlyjs=False)
             for k, f in figs.items()}

    return f"""{START_M}
  <section id="mekanismer" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 section-fade">
    <div class="flex items-center gap-2 mb-2">
      <span class="w-1 h-6 bg-slate-800 rounded-full inline-block"></span>
      <h2 class="text-xl font-bold text-slate-900">Proteststemmens livssyklus: fire valg, tre mekanismer</h2>
    </div>
    <p class="text-slate-500 text-sm leading-relaxed mb-4">
      Sps fire store bevegelser (1993, 2017, 2021, 2025) har ulik geografisk signatur.
      Sammenligningen under bruker standardiserte koeffisienter slik at bølgene kan måles mot hverandre,
      og skiller mellom <em>statisk periferi</em> (sentralitet) og <em>faktisk forvitring</em> (befolkningsnedgang).
      1989-dataene er revidert mot offisielle valgresultater (se metodenotat).
    </p>

    <div class="grid md:grid-cols-4 gap-3 text-sm mb-5">
      <div class="bg-slate-50 rounded-xl p-4">
        <div class="font-bold text-slate-800 mb-1">1993 · Sak-bølgen</div>
        <p class="text-xs text-slate-500 leading-relaxed">EU-mobilisering gradert etter <em>statisk</em> periferi.
        Sentralitet alene forklarer mer (R²={b93["r2_sent"]:.2f}) enn befolkningsvekst (R²={b93["r2_alene"]:.2f});
        vekst-effekten beholder bare {andel93:.0f}&nbsp;% etter kontroll. Selv de mest sentrale kommunene fikk
        +{b93["per_sent"][3]:.0f}&nbsp;pp. Og gevinsten kollapset: −{abs(snitt_93_97):.0f}&nbsp;pp i snitt innen 1997
        (r&nbsp;=&nbsp;{pers_93:+.2f} mellom oppgang og tilbakefall).</p>
      </div>
      <div class="bg-green-50 rounded-xl p-4">
        <div class="font-bold text-green-900 mb-1">2017 · Left behind-bølgen</div>
        <p class="text-xs text-green-900/70 leading-relaxed">Faktisk forvitring bærer effekten:
        std-β={b17["beta_alene"]:.2f} (R²={b17["r2_alene"]:.2f}), og {andel17:.0f}&nbsp;% består etter
        sentralitetskontroll. Toppene kom i kommuner med konkrete tap (forsvarskommunene, samiske kommuner).
        Gevinsten <em>varte</em>: +{snitt_17_21:.1f}&nbsp;pp videre inn i 2021.</p>
      </div>
      <div class="bg-slate-50 rounded-xl p-4">
        <div class="font-bold text-slate-800 mb-1">2021 · Metningen</div>
        <p class="text-xs text-slate-500 leading-relaxed">Ingen befolkningsgradient
        (std-β={b21["beta_alene"]:+.2f}, p={b21["p_alene"]:.2f}). Fremgangen var lik overalt
        (+{b21["per_sent"][0]:.0f} til +{b21["per_sent"][1]:.0f}&nbsp;pp) — distriktskommunene var
        allerede nær metning ({niva21_periferi:.1f}&nbsp;% snittnivå i minst sentrale), og protesten var blitt nasjonal.</p>
      </div>
      <div class="bg-red-50 rounded-xl p-4">
        <div class="font-bold text-red-900 mb-1">2025 · Kollapsen</div>
        <p class="text-xs text-red-900/70 leading-relaxed">Fallet er brattest der oppturen var størst
        (r&nbsp;=&nbsp;{korr_opp_ned:+.2f}): −{abs(b25sp["per_sent"][0]):.0f}&nbsp;pp i de minst sentrale mot
        −{abs(b25sp["per_sent"][3]):.0f}&nbsp;pp i de mest sentrale. FrPs samtidige bølge er
        <em>ikke</em> geografisk gradert (std-β={b25frp["beta_kontroll"]:+.2f} etter kontroll, n.s.) —
        protesten flyttet ikke kanal kommune for kommune (r&nbsp;=&nbsp;{korr_sp_frp:+.2f}).</p>
      </div>
    </div>

    <h3 class="font-semibold text-slate-800 mb-1 mt-6">Sp-nivå per sentralitetsgruppe 1989–2025</h3>
    <p class="text-slate-500 text-sm leading-relaxed mb-2">
      Det strukturelle distriktsforspranget (Rokkan) ligger fast under alle bølgene: avstanden mellom
      minst og mest sentrale kommuner er om lag like stor i 2025 som i 2013 — bølgene kommer og går
      <em>oppå</em> en stabil kløft.
    </p>
    <div class="plotly-chart">{plots["niva"]}</div>

    <h3 class="font-semibold text-slate-800 mb-1 mt-6">Hva bar bølgene: statisk periferi eller faktisk forvitring?</h3>
    <p class="text-slate-500 text-sm leading-relaxed mb-2">
      Standardisert effekt av befolkningsvekst på endringen i oppslutning, med og uten kontroll for sentralitet.
      2017 skiller seg ut: left behind-signaturen (mørk søyle som består etter kontroll) er sterkest der.
      I 2025 snur Sp-søylen fortegn — fallet er størst i forvitringskommunene — mens FrP-søylen er nær null.
    </p>
    <div class="plotly-chart">{plots["beta"]}</div>

    <h3 class="font-semibold text-slate-800 mb-1 mt-6">2025: Sp-fallet er gradert, FrP-bølgen er flat</h3>
    <p class="text-slate-500 text-sm leading-relaxed mb-2">
      Endring 2021→2025 per befolkningsvekst-kvintil. Sp trekker seg mest tilbake i nedgangskommunene;
      FrP vokser omtrent like mye overalt — om noe <em>mest</em> i vekstkommunene.
    </p>
    <div class="plotly-chart">{plots["b2025"]}</div>

    <h3 class="font-semibold text-slate-800 mb-1 mt-6">2025: Protesten flyttet fra kartet til husholdningsregnskapet</h3>
    <p class="text-slate-500 text-sm leading-relaxed mb-2">
      Hvorfor er FrP-bølgen geografisk flat, hvis samme protestmekanisme virker? Fordi tapet i 2022–2025
      (renter, priser) ikke fulgte kommunegrenser: nominell medianinntektsvekst 2021→2024 varierer knapt
      mellom kommuner (IQR {kanal["iqr_innt"][0]:.1f}–{kanal["iqr_innt"][1]:.1f} %) og predikerer ikke
      ΔFrP (std-β={kanal["dfrp"]["biv_innt"]["inntvekst"][0]:+.2f}, n.s.). Den sterkeste prediktoren er i
      stedet <strong>andelen 25–44-åringer</strong> — den renteeksponerte generasjonen —
      (std-β={kanal["dfrp"]["biv_alder"]["andel2544"][0]:+.2f}, p&lt;0,001), som også absorberer hele den
      svake vekstkommune-dreiningen (dpop10 → {kanal["dfrp"]["full"]["dpop10"][0]:+.2f} n.s. i full modell).
      Sp-fallet er speilbildet: størst der det er få unge og befolkningsnedgang.
    </p>
    <div class="plotly-chart">{plots["kanal"]}</div>
    <p class="text-xs text-slate-400 mt-2">
      Data: SSB 06944 (medianinntekt etter skatt) og 07459 (alder), n={kanal["n"]} kommuner.
      Merk: «inntekt etter skatt» fanger ikke renteutgifter — den reelle klemma er mer husholdningsspesifikk
      enn inntektstallene viser. Økologisk slutning; bør valideres mot Valgundersøkelsen 2025.
    </p>

    <div class="bg-blue-50 border border-blue-200 rounded-xl px-5 py-4 text-sm text-blue-900 leading-relaxed mt-5">
      <span class="font-semibold">Tolkning:</span>
      Left behind-<em>følelsen</em> forsvant neppe i 2025 — men både kanalen og tapets geografi endret seg.
      Sp gikk i regjering i 2021 og kunne ikke lenger bære protesten; velgerne som ble mobilisert i 2017/2021
      trakk seg tilbake, brattest der mobiliseringen var sterkest. Samtidig ble deprivasjonen
      <em>avterritorialisert</em>: i 2017 var «de som fikk det verre» definert av sted (fraflytting,
      tjenestetap → Sp, som kanaliserer stedstap); i 2022–25 av livsfase og gjeld (unge huseiere → FrP,
      som kanaliserer husholdningsøkonomi). Grunnkløften består (nivåfiguren) — potensialet for en ny
      distriktsmobilisering ligger der, uten tydelig kanal per 2025. Jf. Auerbach (2024) om Sp som «trygg»
      periferikanal og Sánchez-García et al. (2025) om anti-etablissement-logikken: et parti i regjering
      kan per definisjon ikke være protestkanal.
    </div>
  </section>
{SLUTT_M}"""


# ── INJEKSJON ────────────────────────────────────────────────────────────────

def injiser(seksjon: str, idx: str = "index.html"):
    with open(idx, encoding="utf-8") as f:
        page = f.read()

    s, e = page.find(START_M), page.find(SLUTT_M)
    if s != -1 and e != -1:
        # Idempotent: erstatt eksisterende seksjon
        page = page[:s] + seksjon + page[e + len(SLUTT_M):]
    else:
        anker = "<!-- === SLUTT PROTESTSTEMMEN === -->"
        pos = page.find(anker)
        if pos != -1:
            pos += len(anker)
            page = page[:pos] + "\n\n" + seksjon + page[pos:]
        else:
            pos = page.find("</main>")
            if pos == -1:
                print("  ADVARSEL: fant ikke injeksjonspunkt — hopper over")
                return
            page = page[:pos] + seksjon + "\n" + page[pos:]

    with open(idx, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"  {idx} oppdatert (seksjon 'mekanismer')")


# ── HOVEDPROGRAM ─────────────────────────────────────────────────────────────

def main():
    print("=== Laster data (m/ 1989-korreksjon) ===")
    sv, bpiv, sent = last_data()
    sp  = parti_pivot(sv, "05")
    frp = parti_pivot(sv, "02")

    print("=== Analyserer bølgene ===")
    bolger = {
        "1993":           analyser_bolge(sp[1993] - sp[1989], bpiv, sent, 1986, 1993),
        "2017":           analyser_bolge(sp[2017] - sp[2013], bpiv, sent, 2007, 2017),
        "2021":           analyser_bolge(sp[2021] - sp[2017], bpiv, sent, 2011, 2021),
        "2025 (Sp-fall)": analyser_bolge(sp[2025] - sp[2021], bpiv, sent, 2015, 2025),
        "2025 (FrP)":     analyser_bolge(frp[2025] - frp[2021], bpiv, sent, 2015, 2025),
    }
    for navn, b in bolger.items():
        print(f"  {navn:<16} std-β={b['beta_alene']:+.3f} (p={b['p_alene']:.1e}) "
              f"| m/kontroll {b['beta_kontroll']:+.3f} | R²_sent={b['r2_sent']:.2f} | n={b['n']}")

    # Persistens
    p93 = pd.concat([(sp[1993]-sp[1989]).rename("opp"),
                     (sp[1997]-sp[1993]).rename("etter")], axis=1).dropna()
    p17 = pd.concat([(sp[2017]-sp[2013]).rename("opp"),
                     (sp[2021]-sp[2017]).rename("etter")], axis=1).dropna()
    pers_93, snitt_93_97 = p93["opp"].corr(p93["etter"]), p93["etter"].mean()
    pers_17, snitt_17_21 = p17["opp"].corr(p17["etter"]), p17["etter"].mean()
    print(f"  Persistens 1993→97: r={pers_93:+.2f}, snitt {snitt_93_97:+.1f} pp")
    print(f"  Persistens 2017→21: r={pers_17:+.2f}, snitt {snitt_17_21:+.1f} pp")

    on = pd.concat([(sp[2021]-sp[2013]).rename("opp"),
                    (sp[2025]-sp[2021]).rename("ned")], axis=1).dropna()
    korr_opp_ned = on["opp"].corr(on["ned"])
    sf = pd.concat([(sp[2025]-sp[2021]).rename("dsp"),
                    (frp[2025]-frp[2021]).rename("dfrp")], axis=1).dropna()
    korr_sp_frp = sf["dsp"].corr(sf["dfrp"])
    print(f"  Opptur 13→21 vs fall 21→25: r={korr_opp_ned:+.2f} | ΔSp vs ΔFrP 21→25: r={korr_sp_frp:+.2f}")

    print("=== Kanal-analyse 2025 (avterritorialisering) ===")
    kanal = analyser_kanal_2025(sp, frp, bpiv, sent)
    for y, navn in [("dfrp", "ΔFrP"), ("dsp", "ΔSp")]:
        f = kanal[y]["full"]
        print(f"  {navn} full modell: " + "  ".join(
            f"{v}={b:+.3f}(p={p:.3f})" for v, (b, p) in f.items()))

    print("=== Bygger figurer og injiserer ===")
    figs = {
        "niva":  fig_sp_niva(sp, sent),
        "beta":  fig_beta_bolger(bolger),
        "b2025": fig_2025(bolger["2025 (Sp-fall)"], bolger["2025 (FrP)"]),
        "kanal": fig_kanal(kanal),
    }
    niva21_periferi = sp[2021].to_frame().join(sent).groupby("sent")[2021].mean().get(0, float("nan"))
    seksjon = bygg_seksjon(bolger, pers_93, snitt_93_97, pers_17, snitt_17_21,
                           korr_opp_ned, korr_sp_frp, niva21_periferi, kanal, figs)
    injiser(seksjon)
    print("Ferdig.")


if __name__ == "__main__":
    main()
