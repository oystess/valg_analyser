#!/usr/bin/env python3
"""
analyse_havbruk.py — Velstående periferi: demper havbruksinntekter left behind-effekten?

Hypotese (prosjekteier): Havbruksfondet/oppdrettsaktivitet er en velstandsindikator
langs kysten — kommuner med mye havbrukspenger bør ha hatt MINDRE Sp-byks i 2017
enn like perifere kommuner uten, fordi opplevd forvitring dempes av lokal velstand.

FASE 1 (denne versjonen): proxy = andel sysselsatte i akvakultur (SN2007 03.2)
per arbeidsstedskommune, 4. kv 2017. Kilde: SSB 13470 via SSB MCP (2026-07-02),
committet som data/processed/akvakultur_syss_2017.csv.

FASE 2 (venter på data): Havbruksfondets utbetalinger per kommune
(fiskeridir.no/akvakultur/havbruksfondet — blokkert av sesjonens nettverkspolicy;
lastes opp manuelt). Da testes kr per innbygger direkte mot ΔSp 2017, 2021 og 2025.

Funn fase 1 (n=350): Ukontrollert er effekten maskert (havbrukskommuner ER
periferi). Med kontroll for befolkningsvekst 2007–17 og sentralitet:
std-β(log akvakultur) = −0,12 (p=0,013). Innad i periferien (sent 0–1, n=173):
−0,14 (p=0,061). Deskriptivt: periferikommuner uten akvakultur +14,0 pp Sp,
med mye akvakultur (>2 % av sysselsettingen) +11,5 pp — ved identisk
befolkningsnedgang. Velstående periferi ≠ left behind.

Kjør fra prosjektrot:  python scripts/analyse_havbruk.py
"""

import warnings
import csv as csvmod
import numpy as np
import pandas as pd
import statsmodels.api as sm

warnings.filterwarnings("ignore")

PROCESSED = "data/processed"
RAW       = "data/raw"


def last_grunnlag():
    mapping = {r["gammelt_nr"]: r["nr_2024"]
               for r in csvmod.DictReader(open(f"{PROCESSED}/kom_mapping.csv"))
               if r["nr_2024"]}
    sv  = pd.read_csv(f"{PROCESSED}/stortingsvalg_2024.csv", dtype={"kom2024": str, "parti": str})
    bef = pd.read_csv(f"{PROCESSED}/befolkning_2024.csv", dtype={"kom2024": str})
    sv = sv[~sv["kom2024"].isin(["3454", "3403"])]  # Vang/Hamar-kollisjon

    sent = pd.read_csv(f"{RAW}/sentralitet.csv", sep=";", quotechar='"', encoding="latin1")
    sent["kom2024"] = (sent["targetCode"].astype(str).str.zfill(4)
                       .map(lambda x: mapping.get(x, x)))
    sent = sent.rename(columns={"sourceCode": "sent"})[["kom2024", "sent"]]
    sent["sent"] = pd.to_numeric(sent["sent"], errors="coerce")
    sent = sent.sort_values("sent").drop_duplicates("kom2024").set_index("kom2024")

    bpiv = (bef.pivot_table(index="kom2024", columns="aar", values="befolkning",
                            aggfunc="first").replace(0, np.nan))
    sp = sv[sv["parti"] == "05"].pivot_table(
        index="kom2024", columns="aar", values="prosent", aggfunc="first")
    return sp, bpiv, sent


def last_akvakultur() -> pd.Series:
    ak = pd.read_csv(f"{PROCESSED}/akvakultur_syss_2017.csv",
                     dtype={"kom2024": str}).set_index("kom2024")
    return (ak["syss_akvakultur_2017"] / ak["syss_total_2017"] * 100).rename("akva_pst")


def _z(s):
    return (s - s.mean()) / s.std()


def kjor_modeller(df: pd.DataFrame, label: str):
    D = pd.get_dummies(df["sent"], prefix="s", drop_first=True).astype(float)
    print(f"── {label} (n={len(df)}) ──")
    for lab, Xv, med_sent in [("akvakultur alene",       ["log_akva"], False),
                              ("akvakultur + vekst + sentralitet",
                                                          ["log_akva", "vekst"], True)]:
        X = pd.concat([_z(df[v]).rename(v) for v in Xv], axis=1)
        if med_sent and len(D.columns):
            X = pd.concat([X, D], axis=1)
        m = sm.OLS(_z(df["dsp17"]), sm.add_constant(X)).fit()
        koef = "  ".join(f"{v}={m.params[v]:+.3f}(p={m.pvalues[v]:.3f})" for v in Xv)
        print(f"  {lab:<36} {koef}  R²={m.rsquared:.3f}")


def main():
    print("=== Laster data ===")
    sp, bpiv, sent = last_grunnlag()
    akva = last_akvakultur()

    df = pd.DataFrame({
        "dsp17": sp[2017] - sp[2013],
        "vekst": (bpiv[2017] - bpiv[2007]) / bpiv[2007] * 100,
    }).join(akva).join(sent).replace([np.inf, -np.inf], np.nan).dropna(
        subset=["dsp17", "vekst", "akva_pst", "sent"])
    df["log_akva"] = np.log1p(df["akva_pst"])
    print(f"  Kommuner med akvakultur-sysselsatte: {(df.akva_pst > 0).sum()} av {len(df)}")

    print("\n=== ΔSp 2013→2017 ===")
    kjor_modeller(df, "Alle kommuner")
    kjor_modeller(df[df["sent"] <= 1].copy(), "Bare periferien (sentralitet 0–1)")

    per = df[df["sent"] <= 1].copy()
    per["akva_grp"] = pd.cut(per["akva_pst"], [-0.01, 0.001, 2, 100],
                             labels=["ingen akva", "litt (0-2 %)", "mye (>2 %)"])
    print("\nPeriferien etter akvakultur-intensitet:")
    print(per.groupby("akva_grp", observed=True).agg(
        dSp=("dsp17", "mean"), vekst=("vekst", "mean"), n=("dsp17", "size")
    ).round(1).to_string())

    print("\nFASE 2 venter på Havbruksfondets utbetalingsdata (se docstring).")


if __name__ == "__main__":
    main()
