#!/usr/bin/env python3
"""
analyse/modeller.py – Kjører en testspesifikasjon på panelet uten skjønn.

En spesifikasjon er et dict:
  {
    "formel": "d_sp ~ vekst4_pst + sp_t0 + C(periode)",   # patsy/statsmodels-formel
    "nøkkelledd": "vekst4_pst",          # koeffisientnavn slik statsmodels skriver det
    "forventet_fortegn": "-",            # "+" eller "-"
    "utvalg": "t0 >= 2005" | null,       # pandas query-streng på panelet
    "vekt": "vekt_stemmer_t0" | null     # WLS-vekt; null = OLS
  }
Standardfeil er alltid klyngerobuste på kommune (kom2024).
Brukes av generatorene (eksplorativt), kjør_låste.py (låst kjøring) og kontrollen.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

PANEL = Path(__file__).resolve().parent.parent / "turnering" / "data" / "panel.csv"


def last_panel(sti=PANEL):
    df = pd.read_csv(sti, dtype={"kom2024": str})
    df["estimert"] = df["estimert"].astype(str) == "True"
    return df


def kjør(spes, df=None):
    df = last_panel() if df is None else df
    d = df.query(spes["utvalg"]) if spes.get("utvalg") else df
    vekt = spes.get("vekt")
    if vekt:
        d = d[d[vekt] > 0]
        mod = smf.wls(spes["formel"], data=d, weights=d[vekt])
    else:
        mod = smf.ols(spes["formel"], data=d)
    # patsy dropper rader med manglende verdier; klynger må følge de samme radene
    rader = mod.data.row_labels
    fit = mod.fit(cov_type="cluster", cov_kwds={"groups": d.loc[rader, "kom2024"].astype("category").cat.codes})
    k = spes["nøkkelledd"]
    if k not in fit.params:
        raise KeyError(f"Nøkkelledd {k!r} finnes ikke. Tilgjengelige: {list(fit.params.index)}")
    b, se, p = fit.params[k], fit.bse[k], fit.pvalues[k]
    lo, hi = fit.conf_int().loc[k]
    return {
        "b": float(b), "se": float(se), "p": float(p), "ki_lav": float(lo), "ki_høy": float(hi),
        "n": int(fit.nobs), "n_kommuner": int(d.loc[rader, "kom2024"].nunique()),
        "r2": float(fit.rsquared),
        "fortegn_som_forventet": bool(np.sign(b) == (1 if spes["forventet_fortegn"] == "+" else -1)),
    }


if __name__ == "__main__":
    # python analyse/modeller.py '<json-spesifikasjon>'
    print(json.dumps(kjør(json.loads(sys.argv[1])), ensure_ascii=False, indent=2))
