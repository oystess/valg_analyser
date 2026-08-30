#!/usr/bin/env python3
"""
qa_kommunevalg.py — Kvalitetssikring av kommunevalgdataene (plan_kommunevalg.md del 2).

Seks kontroller mot data/processed/:
  1. Nasjonal fasit-sjekk:  kommunestyrevalg_2024.csv summert per parti×år
     mot kv_fasit_nasjonal.csv (hentet uavhengig). Flagg ratio utenfor
     [0,97, 1,03]; ratio ≈ 2,0 / ≈ 0,5 flagges som dublett-/hull-mistanke.
  2. Nevner-konsistens:     total_stemmer vs partisum innen kommune-år, og
     mot kv_andre_lister.total_stemmer_alle_partier (andre-andel ≥ 0).
  3. Deltakelse-sanity:     godkjente/stemmeberettigede i [35 %, 90 %] per
     kommune-år; nasjonal beregnet deltakelse vs SSBs egne prosenter.
  4. Navnebror-audit:       totalstemmer-hopp > 50 % mot begge nabovalg
     (fanger mappingkollisjoner à la Vang/Hamar i STV 1989).
  5. Befolknings-kontinuitet: stemmeberettigede/befolkning i [0,62, 0,88]
     og uten brå hopp (> 8 pp mellom valg).
  6. KV↔STV-kryssvalidering: kommunekorrelasjon for Ap- og Sp-andel mellom
     hvert KV og STV to år senere; år med r < 0,6 flagges, uteliggere > 3σ listes.

Output: data/processed/qa_kv_rapport.csv (kontroll, alvor, objekt, detalj)
        + konsollsammendrag. Designet for gjenbruk på STV-dataene.

Kjør fra prosjektrot:  python scripts/qa_kommunevalg.py
"""

import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

PROCESSED = "data/processed"
PARTIER = ["01", "02", "03", "04", "05", "06", "07", "08", "55"]
KV_AAR = [1987, 1991, 1995, 1999, 2003, 2007, 2011, 2015, 2019, 2023]

funn = []  # (kontroll, alvor, objekt, detalj)


def flagg(kontroll, alvor, objekt, detalj):
    funn.append({"kontroll": kontroll, "alvor": alvor,
                 "objekt": objekt, "detalj": detalj})


def last():
    kv = pd.read_csv(f"{PROCESSED}/kommunestyrevalg_2024.csv",
                     dtype={"kom2024": str, "parti": str})
    sv = pd.read_csv(f"{PROCESSED}/stortingsvalg_2024.csv",
                     dtype={"kom2024": str, "parti": str})
    fasit = pd.read_csv(f"{PROCESSED}/kv_fasit_nasjonal.csv",
                        dtype={"parti_kode": str})
    delt = pd.read_csv(f"{PROCESSED}/kv_deltakelse.csv", dtype={"kom2024": str})
    andre = pd.read_csv(f"{PROCESSED}/kv_andre_lister.csv", dtype={"kom2024": str})
    bef = pd.read_csv(f"{PROCESSED}/befolkning_2024.csv", dtype={"kom2024": str})
    return kv, sv, fasit, delt, andre, bef


# ── 1. NASJONAL FASIT-SJEKK ──────────────────────────────────────────────────

def sjekk_fasit(kv, fasit):
    print("\n═══ 1. Nasjonal fasit-sjekk (parti × år) ═══")
    ds = kv.groupby(["aar", "parti"])["stemmer"].sum().reset_index()
    fa = fasit[fasit["parti_kode"].isin(PARTIER)][["aar", "parti_kode", "stemmer"]]
    m = ds.merge(fa, left_on=["aar", "parti"], right_on=["aar", "parti_kode"],
                 suffixes=("_data", "_fasit"))
    m["ratio"] = m["stemmer_data"] / m["stemmer_fasit"]
    n_ok = ((m["ratio"] >= 0.97) & (m["ratio"] <= 1.03)).sum()
    print(f"  {n_ok} av {len(m)} parti×år innenfor [0,97, 1,03]")
    for _, r in m[(m["ratio"] < 0.97) | (m["ratio"] > 1.03)].iterrows():
        alvor = "KRITISK" if (1.8 < r["ratio"] < 2.2 or 0.45 < r["ratio"] < 0.55) else "AVVIK"
        flagg("fasit", alvor, f"parti {r['parti']} år {int(r['aar'])}",
              f"ratio {r['ratio']:.3f} (data {r['stemmer_data']:,.0f} / "
              f"fasit {r['stemmer_fasit']:,.0f})")
        print(f"  [{alvor}] parti {r['parti']} {int(r['aar'])}: ratio {r['ratio']:.3f}")


# ── 2. NEVNER-KONSISTENS ─────────────────────────────────────────────────────

def sjekk_nevner(kv, andre):
    print("\n═══ 2. Nevner-konsistens ═══")
    g = kv.groupby(["kom2024", "aar"]).agg(
        partisum=("stemmer", "sum"), total=("total_stemmer", "first"),
        n_tot=("total_stemmer", "nunique")).reset_index()
    inkons = g[g["n_tot"] > 1]
    for _, r in inkons.iterrows():
        flagg("nevner", "AVVIK", f"{r['kom2024']} {int(r['aar'])}",
              "total_stemmer varierer mellom partirader")
    avvik = g[(g["total"] > 0) & ((g["partisum"] / g["total"]).sub(1).abs() > 0.001)]
    print(f"  total_stemmer = 9-partisum i {len(g)-len(avvik)} av {len(g)} kommune-år"
          f" ({len(inkons)} med intern inkonsistens)")
    for _, r in avvik.head(20).iterrows():
        flagg("nevner", "AVVIK", f"{r['kom2024']} {int(r['aar'])}",
              f"partisum {r['partisum']:,.0f} ≠ total {r['total']:,.0f}")

    m = g.merge(andre, on=["kom2024", "aar"], how="left")
    neg = m[(m["total_stemmer_alle_partier"].notna()) &
            (m["total_stemmer_alle_partier"] - m["partisum"] < -1)]
    print(f"  negative Andre-andeler (alle-partier-total < 9-partisum): {len(neg)}")
    for _, r in neg.head(20).iterrows():
        flagg("nevner", "AVVIK", f"{r['kom2024']} {int(r['aar'])}",
              f"alle-partier {r['total_stemmer_alle_partier']:,.0f} < "
              f"9-partisum {r['partisum']:,.0f}")


# ── 3. DELTAKELSE-SANITY ─────────────────────────────────────────────────────

def sjekk_deltakelse(delt):
    print("\n═══ 3. Deltakelse-sanity ═══")
    d = delt.dropna(subset=["stemmeberettigede", "godkjente_stemmer"]).copy()
    d = d[d["stemmeberettigede"] > 0]
    d["andel"] = d["godkjente_stemmer"] / d["stemmeberettigede"] * 100
    ute = d[(d["andel"] < 35) | (d["andel"] > 90)]
    print(f"  {len(d) - len(ute)} av {len(d)} kommune-år innenfor [35 %, 90 %]")
    for _, r in ute.iterrows():
        flagg("deltakelse", "AVVIK", f"{r['kom2024']} {int(r['aar'])}",
              f"deltakelse-proxy {r['andel']:.1f} %")
    nasj = (d.groupby("aar").apply(
        lambda g: g["avgitte_stemmer"].sum() / g["stemmeberettigede"].sum() * 100)
        .round(1))
    print("  nasjonal beregnet deltakelse (avgitte/berettigede):")
    print("   " + "  ".join(f"{int(a)}: {v}" for a, v in nasj.items()))


# ── 4. NAVNEBROR-AUDIT ───────────────────────────────────────────────────────

def sjekk_navnebror(kv):
    print("\n═══ 4. Navnebror-audit (totalstemmer-hopp > 50 % mot begge naboer) ═══")
    tot = kv.groupby(["kom2024", "aar"])["total_stemmer"].first().unstack()
    navn = kv.groupby("kom2024")["navn"].last()
    n_flagg = 0
    for kom, rad in tot.iterrows():
        r = rad.dropna()
        aar = list(r.index)
        for i in range(1, len(aar) - 1):
            v, f, e = r[aar[i]], r[aar[i - 1]], r[aar[i + 1]]
            if f > 0 and e > 0 and v > 0:
                opp = v / f > 1.5 and v / e > 1.5
                ned = v / f < 0.67 and v / e < 0.67
                if opp or ned:
                    n_flagg += 1
                    flagg("navnebror", "KRITISK", f"{kom} ({navn.get(kom, '?')}) {aar[i]}",
                          f"total {v:,.0f} mot {f:,.0f} ({aar[i-1]}) og {e:,.0f} ({aar[i+1]})")
                    print(f"  [KRITISK] {kom} {navn.get(kom, '?')} {aar[i]}: "
                          f"{f:,.0f} → {v:,.0f} → {e:,.0f}")
    if n_flagg == 0:
        print("  ingen spike-mønstre funnet")


# ── 5. BEFOLKNINGS-KONTINUITET ───────────────────────────────────────────────

def sjekk_befolkning(delt, bef):
    print("\n═══ 5. Stemmeberettigede vs befolkning ═══")
    bpiv = (bef.pivot_table(index="kom2024", columns="aar", values="befolkning",
                            aggfunc="first").replace(0, np.nan))
    d = delt.dropna(subset=["stemmeberettigede"]).copy()
    d["befolkning"] = d.apply(
        lambda r: bpiv.at[r["kom2024"], r["aar"]]
        if r["kom2024"] in bpiv.index and r["aar"] in bpiv.columns else np.nan, axis=1)
    d = d[d["befolkning"] > 0]
    d["ratio"] = d["stemmeberettigede"] / d["befolkning"]
    ute = d[(d["ratio"] < 0.62) | (d["ratio"] > 0.88)]
    print(f"  {len(d) - len(ute)} av {len(d)} kommune-år innenfor [0,62, 0,88]")
    for _, r in ute.iterrows():
        flagg("befolkning", "AVVIK", f"{r['kom2024']} {int(r['aar'])}",
              f"berettigede/befolkning = {r['ratio']:.2f}")
    piv = d.pivot_table(index="kom2024", columns="aar", values="ratio")
    hopp = (piv.diff(axis=1).abs() > 0.08)
    n_hopp = int(hopp.sum().sum())
    print(f"  brå ratio-hopp (> 0,08 mellom valg): {n_hopp}")
    for kom in piv.index[hopp.any(axis=1)][:15]:
        aar = list(piv.columns[hopp.loc[kom]])
        flagg("befolkning", "AVVIK", str(kom), f"ratio-hopp i {aar}")


# ── 6. KV ↔ STV KRYSSVALIDERING ─────────────────────────────────────────────

def sjekk_kryss(kv, sv):
    print("\n═══ 6. KV↔STV-kryssvalidering (Ap og Sp, KV-år → STV+2) ═══")
    for parti, navn in [("01", "Ap"), ("05", "Sp")]:
        kvp = kv[kv["parti"] == parti].pivot_table(
            index="kom2024", columns="aar", values="prosent", aggfunc="first")
        svp = sv[sv["parti"] == parti].pivot_table(
            index="kom2024", columns="aar", values="prosent", aggfunc="first")
        rs = []
        for kv_a in KV_AAR:
            sv_a = kv_a + 2
            if kv_a not in kvp.columns or sv_a not in svp.columns:
                continue
            par = pd.concat([kvp[kv_a].rename("kv"), svp[sv_a].rename("sv")],
                            axis=1).dropna()
            r = par["kv"].corr(par["sv"])
            rs.append(f"{kv_a}→{sv_a}: {r:+.2f}")
            if r < 0.6:
                flagg("kryss", "AVVIK", f"{navn} {kv_a}→{sv_a}", f"r = {r:.2f}")
            resid = par["sv"] - (par["sv"].mean()
                                 + (par["kv"] - par["kv"].mean())
                                 * par["sv"].std() / par["kv"].std())
            for kom in par.index[np.abs(resid) > 3 * resid.std()][:5]:
                flagg("kryss", "OBS", f"{navn} {kom} {kv_a}→{sv_a}",
                      f"uteligger (residual {resid[kom]:+.1f} pp)")
        print(f"  {navn}: " + "  ".join(rs))


def main():
    kv, sv, fasit, delt, andre, bef = last()
    print(f"KV-data: {len(kv):,} rader, {kv['kom2024'].nunique()} kommuner, "
          f"{sorted(kv['aar'].unique())[0]}–{sorted(kv['aar'].unique())[-1]}")

    sjekk_fasit(kv, fasit)
    sjekk_nevner(kv, andre)
    sjekk_deltakelse(delt)
    sjekk_navnebror(kv)
    sjekk_befolkning(delt, bef)
    sjekk_kryss(kv, sv)

    rap = pd.DataFrame(funn)
    rap.to_csv(f"{PROCESSED}/qa_kv_rapport.csv", index=False)
    print(f"\n═══ SAMMENDRAG ═══")
    if len(rap):
        print(rap.groupby(["kontroll", "alvor"]).size().to_string())
    else:
        print("  Ingen funn — alle kontroller rene.")
    print(f"  Rapport: {PROCESSED}/qa_kv_rapport.csv ({len(rap)} funn)")


if __name__ == "__main__":
    main()
