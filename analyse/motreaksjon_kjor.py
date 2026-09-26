#!/usr/bin/env python3
"""
analyse/motreaksjon_kjor.py – Kjører de låste testene i hypoteser/motreaksjon/låst.json.

Gjenbruker modeller.kjør (klyngerobuste SE på kommune) og kjor_laste.holm/med_utvalg.
Skriver hypoteser/motreaksjon/resultater.json og parvis.csv, og skriver ut en sammendragstabell.
Ingen skjønn: spesifikasjonene kjøres slik de er låst. Avbryter hvis panelene er endret.
"""
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).parent))
from kjor_laste import holm, med_utvalg  # noqa: E402
from modeller import kjør, last_panel  # noqa: E402

ROT = Path(__file__).resolve().parent.parent
MAPPE = ROT / "hypoteser" / "motreaksjon"
LÅST = json.load(open(MAPPE / "låst.json", encoding="utf-8"))
PANELER = {"ST": ROT / "turnering" / "data" / "panel.csv", "KV": MAPPE / "data" / "kv_panel.csv"}
SETT = {tuple(p) for p in LÅST["sett_episode"]["par"]}
SPES = LÅST["spesifikasjoner"]


# ---------- regjeringer ----------
def les_regjeringer():
    r = pd.read_csv(MAPPE / "regjeringer.csv", parse_dates=["fra", "til"])
    # kontroll mot kjente årstall
    assert (r["til"].iloc[:-1].values == r["fra"].iloc[1:].values).all(), "hull/overlapp i regjeringstabellen"
    kjent = {"Syse": 1989, "Bondevik I": 1997, "Bondevik II": 2001, "Stoltenberg II": 2005,
             "Solberg (H+FrP)": 2013, "Støre (Ap+Sp)": 2021, "Brundtland III": 1990, "Willoch I": 1981}
    for navn, år in kjent.items():
        assert r.loc[r["regjering"] == navn, "fra"].dt.year.item() == år, navn
    h = set(r.loc[r["partier"].str.split(";").apply(lambda p: "H" in p), "regjering"])
    assert h == {"Willoch I", "Willoch II", "Syse", "Bondevik II", "Solberg (H+FrP)", "Solberg (H+FrP+V)",
                 "Solberg (H+FrP+V+KrF)", "Solberg (H+V+KrF)"}, h
    assert r.loc[r["regjering"] == "Solberg (H+V+KrF)", "til"].dt.year.item() == 2021
    return r


def andel_i_regjering(reg, parti, fra, til):
    fra, til = pd.Timestamp(fra), pd.Timestamp(til)
    tid = 0.0
    for _, g in reg.iterrows():
        if parti in g["partier"].split(";"):
            a, b = max(g["fra"], fra), min(g["til"], til)
            tid += max((b - a).days, 0)
    return tid / (til - fra).days


# ---------- hjelpere ----------
def fyll(spes, **kw):
    s = {k: v for k, v in spes.items() if k in ("formel", "nøkkelledd", "forventet_fortegn", "vekt", "utvalg")}
    if s.get("utvalg"):
        s["utvalg"] = s["utvalg"].format(**kw)
    return s


def batteri(spes, df, uten_par=False):
    res = {"hoved": kjør(spes, df)}
    s = dict(spes); s["vekt"] = None
    res["uvektet"] = kjør(s, df)
    res["uten_estimert"] = kjør(med_utvalg(spes, "estimert == False"), df)
    for f in sorted(df["fylke"].unique()):
        res[f"uten_fylke_{f}"] = kjør(med_utvalg(spes, f"fylke != '{f}'"), df)
    if uten_par:
        d = df.query(spes["utvalg"]) if spes.get("utvalg") else df
        for p in sorted(d["periode"].unique()):
            res[f"uten_par_{p}"] = kjør(med_utvalg(spes, f"periode != '{p}'"), df)
    return res


def snur(res):
    return [k for k, v in res.items() if k != "hoved" and not v["fortegn_som_forventet"]]


def h_residualer(df, t):
    """Residual fra P1-modellen (vektet, hovedspesifikasjon) i periode t."""
    d = df[df["periode"] == t]
    d = d[d["vekt_stemmer_t0"] > 0]
    fit = smf.wls(SPES["P1"]["formel"], data=d, weights=d["vekt_stemmer_t0"]).fit()
    return pd.Series(fit.resid, name="h_resid_forrige").set_axis(d.loc[fit.resid.index, "kom2024"])


def parfil(df, t, t1):
    a = df[df["periode"] == t].set_index("kom2024")
    b = df[df["periode"] == t1].set_index("kom2024").copy()
    for v in ("d_ap", "d_sp", "d_h"):
        b[f"{v}_forrige"] = a[v]
    b["h_resid_forrige"] = h_residualer(df, t)
    b["estimert"] = b["estimert"] | a["estimert"]
    b["par"] = f"{t}→{t1}"
    return b.reset_index()


def vsnitt(d, kol):
    return float(np.average(d[kol], weights=d["vekt_stemmer_t0"]))


def gradient(df, periode, parti, vekst="vekst10_pst"):
    return kjør({"formel": f"d_{parti} ~ {vekst} + {parti}_t0 + sent_indeks", "nøkkelledd": vekst,
                 "forventet_fortegn": "+", "vekt": "vekt_stemmer_t0", "utvalg": f"periode == '{periode}'"}, df)


def valgdag(år):
    return f"{år}-09-10"


# ---------- hovedkjøring ----------
def main():
    for k, p in PANELER.items():
        if hashlib.sha256(p.read_bytes()).hexdigest() != LÅST["panel_sha256"][k]:
            raise SystemExit(f"{k}-panelet er endret etter låsing – avbryter.")
    reg = les_regjeringer()
    paneler = {k: last_panel(p) for k, p in PANELER.items()}
    for df in paneler.values():
        if df["estimert"].dtype != bool:
            df["estimert"] = df["estimert"].astype(str) == "True"
        if "reform_2017_20" in df:
            df["reform_2017_20"] = (df["reform_2017_20"].astype(str) == "True").astype(int)
    # reform-dummy også i ST-panelet (fast per kommune)
    reform = paneler["KV"].groupby("kom2024")["reform_2017_20"].first()
    paneler["ST"]["reform_2017_20"] = paneler["ST"]["kom2024"].map(reform)

    par_rader, tester, sens, konk = [], [], [], []
    parpanel = {}
    for vs, df in paneler.items():
        filer = []
        for t, t1 in LÅST["periodepar"][vs]:
            har_v10 = df.loc[df["periode"] == t, "vekst10_pst"].notna().any()
            sett = (vs, t, t1) in SETT
            rolle = "sett" if sett else ("test" if har_v10 else "bare_vekst4")
            d_t, d_t1 = df[df["periode"] == t], df[df["periode"] == t1]
            rad = {"valgslag": vs, "t": t, "t1": t1, "rolle": rolle,
                   "h_nasj_t": vsnitt(d_t, "d_h"), "sp_nasj_t1": vsnitt(d_t1, "d_sp"),
                   "ap_nasj_t": vsnitt(d_t, "d_ap"),
                   "h_i_regjering_andel": andel_i_regjering(reg, "H", valgdag(int(t[-4:])), valgdag(int(t1[-4:]))),
                   "sp_i_regjering_andel": andel_i_regjering(reg, "Sp", valgdag(int(t[-4:])), valgdag(int(t1[-4:])))}
            rad["h_i_regjering"] = rad["h_i_regjering_andel"] >= 0.5
            # beskrivende, ikke låst: bivariat r som i figurene (uvektet, vekst10)
            rad["r_biv_h_t"] = float(d_t["d_h"].corr(d_t["vekst10_pst"]))
            rad["r_biv_sp_t1"] = float(d_t1["d_sp"].corr(d_t1["vekst10_pst"]))
            # sensitivitet med vekst4 for alle par
            for navn, parti, per in (("P1_v4", "h", t), ("P2_v4", "sp", t1)):
                g = gradient(df, per, parti, "vekst4_pst")
                rad[f"b_{navn}"], rad[f"lo_{navn}"], rad[f"hi_{navn}"] = g["b"], g["ki_lav"], g["ki_høy"]
            if rolle != "bare_vekst4":
                pf = parfil(df, t, t1)
                if rolle == "test":
                    filer.append(pf)
                for navn, spes, data in (("P1", fyll(SPES["P1"], t=t), df), ("P2", fyll(SPES["P2"], t1=t1), df)):
                    res = batteri(spes, data)
                    tester.append({"id": f"{navn} {vs} {t}→{t1}", "valgslag": vs, "test": navn, "t": t, "t1": t1,
                                   "rolle": rolle, "spes": spes, "res": res})
                    h = res["hoved"]
                    rad.update({f"b_{navn}": h["b"], f"lo_{navn}": h["ki_lav"], f"hi_{navn}": h["ki_høy"],
                                f"p_{navn}": h["p"], f"snur_{navn}": len(snur(res))})
                # konkurrent (b): Ap-kontroll i P2, og Ap-gradient i t
                s = fyll(SPES["P2"], t1=t1); s["formel"] = SPES["P2_ap"]["formel"]
                h = kjør(s, pf)
                rad.update({"b_P2_ap": h["b"], "lo_P2_ap": h["ki_lav"], "hi_P2_ap": h["ki_høy"]})
                g = gradient(df, t, "ap")
                rad.update({"b_ap_t": g["b"], "lo_ap_t": g["ki_lav"], "hi_ap_t": g["ki_høy"]})
                # P4 per par (beskrivende)
                s = {"formel": SPES["P4"]["formel"].replace(" + C(periode)", ""), "nøkkelledd": "h_resid_forrige",
                     "forventet_fortegn": "-", "vekt": "vekt_stemmer_t0"}
                h = kjør(s, pf)
                rad.update({"b_P4": h["b"], "lo_P4": h["ki_lav"], "hi_P4": h["ki_høy"]})
                # konkurrent (c): reform
                if (vs, t1) in {("ST", "2017-2021"), ("KV", "2015-2019"), ("KV", "2019-2023")}:
                    s = fyll(SPES["P2"], t1=t1); s["formel"] += " + reform_2017_20"
                    h = kjør(s, df)
                    rad.update({"b_P2_reform": h["b"], "lo_P2_reform": h["ki_lav"], "hi_P2_reform": h["ki_høy"]})
                    s = dict(s); s["nøkkelledd"] = "reform_2017_20"; s["forventet_fortegn"] = "+"
                    h = kjør(s, df)
                    rad.update({"b_reform": h["b"], "lo_reform": h["ki_lav"], "hi_reform": h["ki_høy"]})
            par_rader.append(rad)
        pp = pd.concat(filer, ignore_index=True)
        parpanel[vs] = pp
        pp.to_csv(MAPPE / "data" / f"par_{vs.lower()}.csv", index=False)
        # samlet P4 (Holm) + konkurrentvarianter
        base = {"formel": SPES["P4"]["formel"], "nøkkelledd": "h_resid_forrige", "forventet_fortegn": "-",
                "vekt": "vekt_stemmer_t0"}
        res = batteri(base, pp, uten_par=True)
        tester.append({"id": f"P4 {vs} samlet", "valgslag": vs, "test": "P4", "rolle": "test", "spes": base, "res": res})
        for navn in ("P4_ap", "P4_rtm"):
            s = dict(base); s["formel"] = SPES[navn]["formel"]
            konk.append({"id": f"{navn} {vs}", "res": {"hoved": kjør(s, pp), "uvektet": kjør({**s, "vekt": None}, pp)}})
        s = dict(base); s["formel"] += " + reform_2017_20"
        konk.append({"id": f"P4_reform {vs}", "res": {"hoved": kjør(s, pp)}})

    # Holm over testfamilien (sett episode utenfor)
    fam = [x for x in tester if x["rolle"] == "test"]
    assert len(fam) == 26, len(fam)
    for x, p in zip(fam, holm([x["res"]["hoved"]["p"] for x in fam])):
        x["p_holm"] = p
    for x in tester:
        h = x["res"]["hoved"]
        if x["test"] == "P4":
            # P4A (−) og P4B (+): status for den versjonen som har fortegnet i hoved
            x["versjon"] = "P4A" if h["b"] < 0 else "P4B"
            fortegn = np.sign(h["b"])
            x["snur"] = [k for k, v in x["res"].items() if k != "hoved" and np.sign(v["b"]) != fortegn]
            x["robust"] = bool(x["p_holm"] < 0.05 and not x["snur"])
        else:
            x["snur"] = snur(x["res"])
            x["robust"] = bool("p_holm" in x and h["fortegn_som_forventet"] and x["p_holm"] < 0.05 and not x["snur"])
            if x["rolle"] == "sett":  # illustrasjon: samme regel uten Holm
                x["robust_ujustert"] = bool(h["fortegn_som_forventet"] and h["p"] < 0.05 and not x["snur"])

    par = pd.DataFrame(par_rader)
    for navn in ("P1", "P2"):
        m = {(x["valgslag"], x["t"], x["t1"]): x for x in tester if x["test"] == navn}
        par[f"p_holm_{navn}"] = [m.get((r.valgslag, r.t, r.t1), {}).get("p_holm", np.nan) for r in par.itertuples()]
        # sett episode: samme regel uten Holm (robust_ujustert); testpar: Holm-regelen
        par[f"robust_{navn}"] = [m[k].get("robust_ujustert", m[k]["robust"]) if (k := (r.valgslag, r.t, r.t1)) in m
                                 else np.nan for r in par.itertuples()]
    par["par_støtter"] = par["robust_P1"].eq(True) & par["robust_P2"].eq(True)
    par.to_csv(MAPPE / "parvis.csv", index=False)

    # ---------- statusvurderinger ----------
    test = par[par["rolle"] == "test"]
    st_ = {}
    ant = {vs: int(test.loc[test.valgslag == vs, "par_støtter"].sum()) for vs in ("ST", "KV")}
    n = {vs: int((test.valgslag == vs).sum()) for vs in ("ST", "KV")}
    if all(ant[v] >= 4 for v in ant):
        st_["P1_P2"] = "støttet"
    elif any(ant[v] >= 4 for v in ant) or sum(ant.values()) >= 7:
        st_["P1_P2"] = "delvis"
    else:
        st_["P1_P2"] = "ikke støttet"
    st_["P1_P2_antall"] = {v: f"{ant[v]} av {n[v]}" for v in ant}
    spes_ = {}
    for vs in ("ST", "KV", "samlet"):
        d = test if vs == "samlet" else test[test.valgslag == vs]
        a, b = d[d.robust_P1 == True], d[d.robust_P1 != True]  # noqa: E712
        spes_[vs] = {"P2_robust_når_P1_robust": f"{int((a.robust_P2 == True).sum())} av {len(a)}",  # noqa: E712
                     "P2_robust_når_P1_ikke": f"{int((b.robust_P2 == True).sum())} av {len(b)}"}  # noqa: E712
    st_["spesifisitet"] = spes_
    p3 = {}
    for vs in ("ST", "KV", "samlet"):
        d = test if vs == "samlet" else test[test.valgslag == vs]
        p3[vs] = {"n_par": len(d), "pearson": float(d.b_P1.corr(d.b_P2)),
                  "spearman": float(d.b_P1.corr(d.b_P2, method="spearman")),
                  "pearson_med_sett": float(par[(par.rolle != "bare_vekst4") & ((par.valgslag == vs) | (vs == "samlet"))]
                                            [["b_P1", "b_P2"]].corr().iloc[0, 1])}
    st_["P3"] = p3
    neg = [p3[v]["pearson"] < 0 and p3[v]["spearman"] < 0 for v in ("ST", "KV")]
    st_["P3_status"] = ("støttet (beskrivende)" if all(neg) else
                        "delvis (beskrivende)" if any(neg) or p3["samlet"]["pearson"] < 0 else "ikke støttet")
    p4 = {x["valgslag"]: x for x in tester if x["test"] == "P4"}
    v = {k: (x["versjon"], x["robust"]) for k, x in p4.items()}
    if v["ST"][0] == v["KV"][0] and v["ST"][1] and v["KV"][1]:
        st_["P4"] = f"støttet ({v['ST'][0]})"
    elif any(r for _, r in v.values()) or v["ST"][0] == v["KV"][0]:
        st_["P4"] = f"delvis (ST: {v['ST'][0]}{' robust' if v['ST'][1] else ''}, KV: {v['KV'][0]}{' robust' if v['KV'][1] else ''})"
    else:
        st_["P4"] = "ikke støttet"
    p5 = {}
    for vs in ("ST", "KV"):
        d = test[test.valgslag == vs]
        g = {str(k): {"n_par": len(x), "snitt_b_P2": float(x.b_P2.mean()),
                      "par": [f"{a}→{b}" for a, b in zip(x.t, x.t1)],
                      "pearson_P3": float(x.b_P1.corr(x.b_P2)) if len(x) > 2 else None}
             for k, x in d.groupby("h_i_regjering")}
        p5[vs] = g
    st_["P5"] = p5
    mer_neg = [p5[vs].get("True", {}).get("snitt_b_P2", np.inf) < p5[vs].get("False", {}).get("snitt_b_P2", -np.inf)
               for vs in ("ST", "KV")]
    st_["P5_status"] = ("støttet (beskrivende)" if all(mer_neg) else "delvis (beskrivende)" if any(mer_neg)
                        else "ikke støttet")
    # konkurrenter på parnivå (beskrivende)
    kpar = {}
    for vs in ("ST", "KV", "samlet"):
        d = test if vs == "samlet" else test[test.valgslag == vs]
        kpar[vs] = {"r_bP2_mot_sp_nasj_t1": float(d.b_P2.corr(d.sp_nasj_t1)),
                    "r_bP2_mot_ap_gradient_t": float(d.b_P2.corr(d.b_ap_t)),
                    "r_bP1_mot_h_nasj_t": float(d.b_P1.corr(d.h_nasj_t))}
    st_["konkurrenter_parnivå"] = kpar

    ut = {"kjørt": date.today().isoformat(), "panel_sha256": LÅST["panel_sha256"], "status": st_,
          "tester": [{k: v for k, v in x.items()} for x in tester], "konkurrenter": konk}
    json.dump(ut, open(MAPPE / "resultater.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)

    vis = par[["valgslag", "t", "t1", "rolle", "h_i_regjering_andel", "b_P1", "p_holm_P1", "robust_P1",
               "b_P2", "p_holm_P2", "robust_P2", "par_støtter", "b_P4", "b_P2_ap"]]
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(vis.round(3).to_string(index=False))
    for x in tester:
        if x["test"] == "P4":
            h = x["res"]["hoved"]
            print(x["id"], x["versjon"], round(h["b"], 4), round(x["p_holm"], 4), "robust" if x["robust"] else "ikke robust",
                  "snur:", x["snur"])
    for x in konk:
        h = x["res"]["hoved"]
        print(x["id"], round(h["b"], 4), f"[{h['ki_lav']:.4f}, {h['ki_høy']:.4f}]", round(h["p"], 4))
    print(json.dumps({k: v for k, v in st_.items()}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
