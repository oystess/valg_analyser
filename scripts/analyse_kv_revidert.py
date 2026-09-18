#!/usr/bin/env python3
"""
analyse_kv_revidert.py — Tiltak 10: reviderte KV-analyser med korrigerte
prosenter, og bygdelistene som egen protestkanal.

Tre deler:
  A. H5 REVIDERT (lagget avhengig variabel + reverstest, korrigerte KV-prosenter):
     KV→STV: sv_t ~ kv_{t-2} + sv_{t-4}  vs  REVERS: kv_{t+4} ~ sv_{t+2} + kv_t.
     Funn: reversen er ~3× sterkere (Sp +0,33 vs +0,11; Ap +0,35 vs +0,08).
     Stortingsvalg leder kommunevalg — ikke omvendt. H5 forkastes/snus.
     (NB: FE med lagget avh. variabel gir Nickell-skjevhet ved kort T; designet
     er symmetrisk i begge retninger, så SAMMENLIGNINGEN er informativ.)
  B. H4 med korrigert nevner: between-effekten av befolkningsvekst er fortsatt
     svakere i KV (Sp −0,46) enn STV (−0,58). H4 fortsatt ikke støttet.
  C. BYGDELISTENE (kv_andre_lister.csv):
     - Left behind-gradert: std-β(vekst → bygdelisteandel) = −0,28*** m/ sentralitet.
     - 1993-bølgen høstet dem: ΔSp 1989→93 høyere der bygdelistene sto sterkt
       i KV 1991 (+0,20***) — lokallistevelgere trenger STV-kanal, Sp tok dem.
     - 2023: der Sp falt mest i KV, vokste bygdelistene mest (r=−0,31; −0,32 i
       periferien). Den lokale protesten fant bygdelista i 2023, den nasjonale
       fant Frp i 2025.

Injiserer seksjon i index.html mellom egne merker (idempotent):
  <!-- === START BYGDELISTER === --> ... <!-- === SLUTT BYGDELISTER === -->

Kjør fra prosjektrot:  python scripts/analyse_kv_revidert.py
Krever: linearmodels (pip install linearmodels)
"""

import warnings
import csv as csvmod
import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS
import plotly.graph_objects as go

warnings.filterwarnings("ignore")

PROCESSED = "data/processed"
RAW       = "data/raw"
KV_AAR = [1987, 1991, 1995, 1999, 2003, 2007, 2011, 2015, 2019]
SENTRALITET_NAVN = {0: "Minst sentrale", 1: "Mindre sentrale",
                    2: "Noe sentrale", 3: "Sentrale"}
SENT_FARGER = {0: "#d62728", 1: "#ff7f0e", 2: "#2ca02c", 3: "#1f77b4"}

START_M = "<!-- === START BYGDELISTER === -->"
SLUTT_M = "<!-- === SLUTT BYGDELISTER === -->"


def last_data():
    kvk = pd.read_csv(f"{PROCESSED}/kv_prosent_korrigert.csv",
                      dtype={"kom2024": str, "parti": str})
    sv = pd.read_csv(f"{PROCESSED}/stortingsvalg_2024.csv",
                     dtype={"kom2024": str, "parti": str})
    andre = pd.read_csv(f"{PROCESSED}/kv_andre_lister.csv", dtype={"kom2024": str})
    bef = pd.read_csv(f"{PROCESSED}/befolkning_2024.csv", dtype={"kom2024": str})
    for d in (kvk, sv, andre):
        d.drop(d[d["kom2024"].isin(["3454", "3403"])].index, inplace=True)

    mapping = {r["gammelt_nr"]: r["nr_2024"]
               for r in csvmod.DictReader(open(f"{PROCESSED}/kom_mapping.csv"))
               if r["nr_2024"]}
    sent = pd.read_csv(f"{RAW}/sentralitet.csv", sep=";", quotechar='"', encoding="latin1")
    sent["kom2024"] = (sent["targetCode"].astype(str).str.zfill(4)
                       .map(lambda x: mapping.get(x, x)))
    sent = sent.rename(columns={"sourceCode": "sent"})[["kom2024", "sent"]]
    sent["sent"] = pd.to_numeric(sent["sent"], errors="coerce")
    sent = sent.sort_values("sent").drop_duplicates("kom2024").set_index("kom2024")
    bpiv = (bef.pivot_table(index="kom2024", columns="aar", values="befolkning",
                            aggfunc="first").replace(0, np.nan))
    return kvk, sv, andre, bpiv, sent


def _z(s):
    return (s - s.mean()) / s.std()


# ── A. H5 REVIDERT ───────────────────────────────────────────────────────────

def h5_revidert(kvk, sv) -> dict:
    piv = lambda df, p, v: df[df["parti"] == p].pivot_table(
        index="kom2024", columns="aar", values=v, aggfunc="first")
    res = {}
    for parti, kode in [("Sp", "05"), ("Ap", "01")]:
        y_kv = piv(kvk, kode, "prosent_alle")
        y_sv = piv(sv, kode, "prosent")

        def kjor(y_piv, x_piv, y_off, x_off, lag_piv):
            rows = []
            for kva in KV_AAR:
                ya, xa, la = kva + y_off, kva + x_off, kva + y_off - 4
                if (ya not in y_piv.columns or xa not in x_piv.columns
                        or la not in lag_piv.columns):
                    continue
                d = pd.concat([y_piv[ya].rename("y"), x_piv[xa].rename("x"),
                               lag_piv[la].rename("ylag")], axis=1).dropna()
                d["aar"] = ya
                rows.append(d.reset_index())
            d = pd.concat(rows).set_index(["kom2024", "aar"])
            m = PanelOLS(d["y"], d[["x", "ylag"]], entity_effects=True,
                         time_effects=True).fit(cov_type="clustered",
                                                cluster_entity=True)
            return m.params["x"], m.pvalues["x"], int(m.nobs)

        frem = kjor(y_sv, y_kv, 2, 0, y_sv)     # KV → STV
        rev  = kjor(y_kv, y_sv, 4, 2, y_kv)     # STV → KV
        res[parti] = {"frem": frem, "rev": rev}
        print(f"  {parti}: KV→STV β={frem[0]:+.3f} (p={frem[1]:.4f}, n={frem[2]}) "
              f"| STV→KV β={rev[0]:+.3f} (p={rev[1]:.4f}, n={rev[2]})")
    return res


# ── B. H4 MED KORRIGERT NEVNER ───────────────────────────────────────────────

def h4_revidert(kvk, sv, bpiv) -> dict:
    def dpop10(aar):
        if aar - 10 in bpiv.columns and aar in bpiv.columns:
            return (bpiv[aar] - bpiv[aar - 10]) / bpiv[aar - 10] * 100
        return pd.Series(np.nan, index=bpiv.index)

    res = {}
    for lab, df, kode, vcol, aars in [
            ("KV", kvk, "05", "prosent_alle", KV_AAR + [2023]),
            ("STV", sv, "05", "prosent",
             [1989, 1993, 1997, 2001, 2005, 2009, 2013, 2017, 2021, 2025])]:
        p = df[df["parti"] == kode].pivot_table(
            index="kom2024", columns="aar", values=vcol, aggfunc="first")
        ps, ds = [], []
        for a in aars:
            if a in p.columns:
                ps.append(p[a])
                ds.append(dpop10(a))
        d = pd.concat([pd.concat(ps, axis=1).mean(axis=1).rename("pst"),
                       pd.concat(ds, axis=1).mean(axis=1).rename("dp")],
                      axis=1).dropna()
        m = sm.OLS(d["pst"], sm.add_constant(d["dp"])).fit()
        res[lab] = (m.params["dp"], m.pvalues["dp"], len(d))
        print(f"  Sp {lab}: between β(dpop10)={m.params['dp']:+.3f} "
              f"(p={m.pvalues['dp']:.5f}, n={len(d)})")
    return res


# ── C. BYGDELISTENE ──────────────────────────────────────────────────────────

def bygdelister(andre, kvk, sv, bpiv, sent) -> dict:
    a = andre.merge(sent.reset_index(), on="kom2024")
    trend = (a.groupby(["aar", "sent"])
             .apply(lambda g: g["stemmer_andre"].sum()
                    / g["total_stemmer_alle_partier"].sum() * 100)
             .unstack())

    # Left behind-gradient (2019+2023-snitt)
    sn = a[a["aar"].isin([2019, 2023])].groupby("kom2024").agg(
        andre_pst=("prosent_andre", "mean"), sent=("sent", "first"))
    sn["dpop"] = (bpiv[2023] - bpiv[2013]) / bpiv[2013] * 100
    sn = sn.replace([np.inf, -np.inf], np.nan).dropna()
    D = pd.get_dummies(sn["sent"], prefix="s", drop_first=True).astype(float)
    m_lb = sm.OLS(_z(sn["andre_pst"]), sm.add_constant(
        pd.concat([_z(sn["dpop"]).rename("dpop"), D], axis=1))).fit()

    # 1993-høsting: ΔSp STV 1989→93 vs bygdelisteandel KV 1991
    sp_sv = sv[sv["parti"] == "05"].pivot_table(
        index="kom2024", columns="aar", values="prosent", aggfunc="first")
    ab91 = andre[andre["aar"] == 1991].set_index("kom2024")["prosent_andre"]
    d93 = pd.DataFrame({
        "dsp": sp_sv[1993] - sp_sv[1989],
        "vekst": (bpiv[1993] - bpiv[1986]) / bpiv[1986] * 100,
        "andre": ab91}).join(sent).replace([np.inf, -np.inf], np.nan).dropna()
    D93 = pd.get_dummies(d93["sent"], prefix="s", drop_first=True).astype(float)
    m_93 = sm.OLS(_z(d93["dsp"]), sm.add_constant(pd.concat(
        [_z(d93["andre"]).rename("andre"), _z(d93["vekst"]).rename("vekst"),
         D93], axis=1))).fit()

    # 2023: kanalbytte i lokalvalget
    sp_kv = kvk[kvk["parti"] == "05"].pivot_table(
        index="kom2024", columns="aar", values="prosent_alle", aggfunc="first")
    da = andre.pivot_table(index="kom2024", columns="aar",
                           values="prosent_andre", aggfunc="first")
    d23 = pd.DataFrame({"dspkv": sp_kv[2023] - sp_kv[2019],
                        "dandre": da[2023] - da[2019]}).join(sent).dropna()
    korr = d23["dspkv"].corr(d23["dandre"])
    korr_per = d23[d23["sent"] <= 1]["dspkv"].corr(d23[d23["sent"] <= 1]["dandre"])

    print(f"  Left behind-gradient: std-β={m_lb.params['dpop']:+.3f} "
          f"(p={m_lb.pvalues['dpop']:.4f})")
    print(f"  1993-høsting: std-β(bygdeliste KV91 → ΔSp 89-93)="
          f"{m_93.params['andre']:+.3f} (p={m_93.pvalues['andre']:.4f})")
    print(f"  2023: korr(ΔSp KV, Δbygdeliste)={korr:+.2f} (periferi {korr_per:+.2f})")
    return {"trend": trend, "m_lb": m_lb, "m_93": m_93, "d23": d23,
            "korr": korr, "korr_per": korr_per,
            "dsp_snitt": d23["dspkv"].mean(), "dandre_snitt": d23["dandre"].mean()}


# ── FIGURER ──────────────────────────────────────────────────────────────────

def fig_trend(trend: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for kode in [0, 1, 2, 3]:
        if kode not in trend.columns:
            continue
        s = trend[kode].dropna()
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values.round(1), mode="lines+markers",
            name=SENTRALITET_NAVN[kode],
            line=dict(color=SENT_FARGER[kode], width=2.5), marker=dict(size=7),
            hovertemplate=f"<b>{SENTRALITET_NAVN[kode]}</b><br>"
                          "%{x}: %{y:.1f} %<extra></extra>"))
    fig.update_layout(
        xaxis_title="Kommunestyrevalg",
        yaxis_title="Lokale lister / Andre, andel av godkjente stemmer (%)",
        template="plotly_white", hovermode="x unified",
        legend=dict(font_size=11, orientation="h", x=0.5, xanchor="center", y=-0.15),
        margin=dict(t=30, b=70))
    return fig


def fig_kanalbytte(d23: pd.DataFrame) -> go.Figure:
    d = d23.copy()
    d["kv"] = pd.qcut(d["dspkv"], 5, labels=False)
    agg = d.groupby("kv").agg(dsp=("dspkv", "mean"), dandre=("dandre", "mean"))
    labels = ["Størst<br>Sp-fall", "2", "3", "4", "Minst<br>Sp-fall"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=agg["dsp"].round(1).tolist(),
                         name="ΔSp KV 2019→2023", marker_color="#009900",
                         hovertemplate="ΔSp: %{y:.1f} pp<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=agg["dandre"].round(1).tolist(),
                         name="ΔBygdelister 2019→2023", marker_color="#8B5A2B",
                         hovertemplate="ΔAndre: %{y:.1f} pp<extra></extra>"))
    fig.add_hline(y=0, line_color="rgba(0,0,0,0.4)", line_width=1)
    fig.update_layout(
        barmode="group", xaxis_title="Kommuner etter Sp-fall i KV 2019→2023, kvintiler",
        yaxis_title="Endring (pp)", template="plotly_white",
        legend=dict(font_size=11, orientation="h", x=0.5, xanchor="center", y=-0.25),
        margin=dict(t=30, b=90))
    return fig


# ── HTML ─────────────────────────────────────────────────────────────────────

def bygg_seksjon(h5, h4, byg, figs) -> str:
    plots = {k: f.to_html(full_html=False, include_plotlyjs=False)
             for k, f in figs.items()}
    return f"""{START_M}
  <section id="bygdelister" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 section-fade">
    <div class="flex items-center gap-2 mb-2">
      <span class="w-1 h-6 bg-slate-800 rounded-full inline-block"></span>
      <h2 class="text-xl font-bold text-slate-900">Kommunevalgene revidert: rikspolitikkens ekko — og bygdelistenes comeback</h2>
    </div>
    <p class="text-slate-500 text-sm leading-relaxed mb-4">
      Kommunevalgdataene er kvalitetssikret mot offisielle tall og prosentene korrigert for
      bygdeliste-skjevheten (lokallister utgjør opptil 89 % av stemmene i enkelte kommuner).
      Det endrer to konklusjoner og åpner en ny protestkanal for analyse.
    </p>

    <div class="grid md:grid-cols-3 gap-3 text-sm mb-5">
      <div class="bg-red-50 rounded-xl p-4">
        <div class="font-bold text-red-900 mb-1">H5 snus: riksvalg leder lokalvalg</div>
        <p class="text-xs text-red-900/70 leading-relaxed">Med lagget avhengig variabel og
        reverstest: KV→STV β={h5["Sp"]["frem"][0]:+.2f}, men STV→KV
        β={h5["Sp"]["rev"][0]:+.2f} (Sp; Ap {h5["Ap"]["frem"][0]:+.2f} mot
        {h5["Ap"]["rev"][0]:+.2f}). Panel-seksjonens «kommunevalg forutser stortingsvalg»
        var persistens forkledd som ledelse — informasjonen flyter fra riks til lokal,
        i tråd med rikspolitiseringen av lokalvalgene.</p>
      </div>
      <div class="bg-slate-50 rounded-xl p-4">
        <div class="font-bold text-slate-800 mb-1">H4 fortsatt ikke støttet</div>
        <p class="text-xs text-slate-500 leading-relaxed">Også med korrigert nevner er
        befolknings­gradienten svakere i kommunevalg (Sp between β={h4["KV"][0]:+.2f})
        enn i stortingsvalg ({h4["STV"][0]:+.2f}). Periferi­protesten er en <em>riksvalg</em>-
        atferd — lokalt stemmer man på person og bygdeliste.</p>
      </div>
      <div class="bg-amber-50 rounded-xl p-4">
        <div class="font-bold text-amber-900 mb-1">Bygdelista: den tredje kanalen</div>
        <p class="text-xs text-amber-900/70 leading-relaxed">Lokallistene er left behind-
        graderte (std-β={byg["m_lb"].params["dpop"]:+.2f}***), og i 1993 høstet Sp mest
        nettopp der bygdelistene sto sterkt (+{byg["m_93"].params["andre"]:.2f}***) —
        lokallistevelgere trenger en rikskanal. I 2023 vokste bygdelistene bredt
        (+{byg["dandre_snitt"]:.1f} pp) mens Sp kollapset — men kommune-koblingen til
        Sp-fallet spesifikt (r={byg["korr"]:+.2f}) er ikke sterkere enn for andre
        partier (Ap −0,40, Høyre −0,35): andels-regnskapet skviser alle når lista
        vokser. Kanalbytte-tolkningen krever individdata.</p>
      </div>
    </div>

    <h3 class="font-semibold text-slate-800 mb-1 mt-6">Lokale lister 1987–2023 per sentralitet</h3>
    <p class="text-slate-500 text-sm leading-relaxed mb-2">
      Andel av alle godkjente stemmer. Merk fallet gjennom Sp-bølgeårene (2011–2019, da
      Sp okkuperte protestrommet) og comebacket i 2023 (+{byg["dandre_snitt"]:.1f} pp i snitt)
      da Sp satt i regjering.
    </p>
    <div class="plotly-chart">{plots["trend"]}</div>

    <h3 class="font-semibold text-slate-800 mb-1 mt-6">2023: bygdelistenes comeback — men hvem de tok fra, er åpent</h3>
    <p class="text-slate-500 text-sm leading-relaxed mb-2">
      Sp falt {byg["dsp_snitt"]:+.1f} pp i kommunevalget 2023 mens bygdelistene vokste
      {byg["dandre_snitt"]:+.1f} pp. Den negative samvariasjonen per kommune er imidlertid
      i stor grad mekanisk (andeler summerer til hundre) og ikke sterkere for Sp enn for
      Ap og Høyre — figuren viser mønsteret, men hvilke velgere bygdelistene faktisk tok,
      kan bare individdata avgjøre.
    </p>
    <div class="plotly-chart">{plots["kanal"]}</div>
    <p class="text-xs text-slate-400 mt-2">
      Kilder: SSB 01180/09475 (QA: qa_kommunevalg.py — fasit-sjekk 83/83 rene parti-år).
      KV-prosenter med alle godkjente stemmer som nevner (kv_prosent_korrigert.csv).
      Lagget-DV-modellene har Nickell-skjevhet ved kort T; sammenligningen mellom retningene
      er symmetrisk og derfor informativ.
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
        anker = "<!-- === SLUTT BASTIONER === -->"
        pos = page.find(anker)
        if pos == -1:
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
    print(f"  {idx} oppdatert (seksjon 'bygdelister')")


def main():
    print("=== Laster data ===")
    kvk, sv, andre, bpiv, sent = last_data()

    print("\n=== A. H5 revidert (lagget DV + reverstest) ===")
    h5 = h5_revidert(kvk, sv)

    print("\n=== B. H4 med korrigert nevner ===")
    h4 = h4_revidert(kvk, sv, bpiv)

    print("\n=== C. Bygdelistene ===")
    byg = bygdelister(andre, kvk, sv, bpiv, sent)

    print("\n=== Figurer og injeksjon ===")
    figs = {"trend": fig_trend(byg["trend"]), "kanal": fig_kanalbytte(byg["d23"])}
    injiser(bygg_seksjon(h5, h4, byg, figs))
    print("Ferdig.")


if __name__ == "__main__":
    main()
