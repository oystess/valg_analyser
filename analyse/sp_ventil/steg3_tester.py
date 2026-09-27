#!/usr/bin/env python3
"""Steg 3: T1–T8 og robusthet. Leser panelet fra steg 1, skriver hypoteser/sp_ventil/arbeid/resultater.json
og tabeller til figurene (arbeid/t4_*.csv, t5_*.csv, t7_*.csv).

Kjøring: python analyse/sp_ventil/steg3_tester.py
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).parent))
from felles import ARB, UT, FYLKE, bygg_panel, landstall, les_valg

warnings.filterwarnings("ignore")
LÅST = json.loads((UT / "låst.json").read_text(encoding="utf-8"))
ANDRE = ["ap", "frp", "h", "krf", "sv", "v", "rodt", "mdg", "nkp", "andre"]   # alle unntatt sp og fl
NASJ_BOLGER = LÅST["nasjonale_bolger_sp90"]          # 1989-1993, 2013-2017, 2017-2021
TILBAKEFALL = sorted(set(LÅST["tilbakefall_sp90"].values()))   # 1993-1997, 2021-2025


def les_panel(navn="panel.csv"):
    return pd.read_csv(ARB / navn, dtype={"kom": str, "fylke": str})


def r(x, n=3):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)


def ols(df, formel, klynge="kom", robust=True):
    d = df.dropna(subset=[c for c in df.columns if c in formel])
    m = smf.ols(formel, data=d)
    if klynge and d[klynge].nunique() > 1 and robust:
        return m.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d[klynge])[0]})
    return m.fit(cov_type="HC1")


def koef(fit, navn):
    b, se = fit.params[navn], fit.bse[navn]
    return {"b": r(b), "se": r(se), "ki95": [r(b - 1.96 * se), r(b + 1.96 * se)], "p": r(fit.pvalues[navn], 4)}


def helning(df, y, x, fe=None):
    """Helning y på x (HC1 for tverrsnitt, klynget på kommune når fe er gitt)."""
    if len(df) < 8:
        return {"b": None, "n": int(len(df))}
    f = f"{y} ~ {x}" + ("".join(f" + C({e})" for e in fe) if fe else "")
    fit = ols(df, f, klynge="kom" if fe else None)
    ut = koef(fit, x)
    ut["n"] = int(fit.nobs)
    return ut


def testbar(p):
    return p[p.testbar].copy()


def grupper(p, bastkol="bastion"):
    """Kommunegrupper som masker (bastkol angir bastionsdefinisjon)."""
    return {
        "distrikt_bastion": p.distrikt & p[bastkol],
        "distrikt_ikke_bastion": p.distrikt & ~p[bastkol],
        "sentral": ~p.distrikt,
        "alle_distrikt": p.distrikt,
        "alle": pd.Series(True, index=p.index),
    }


# ---------------------------------------------------------------- T1 Erosjon
def t1(p, spk="sp90"):
    ut = {}
    x = f"d_{spk}"
    for par in NASJ_BOLGER:
        d = p[p.par == par]
        rad = {}
        for bk in ("bastion", "bastion_fast"):
            for g, m in grupper(d, bk).items():
                if bk == "bastion_fast" and g in ("sentral", "alle", "alle_distrikt"):
                    continue
                rad[f"{g}|{bk}"] = helning(d[m], "d_ap", x)
            # interaksjon: brattere i distrikts-bastioner?
            dd = d.assign(db=(d.distrikt & d[bk]).astype(int))
            if dd.db.sum() >= 10:
                fit = ols(dd, f"d_ap ~ {x} * db", klynge=None)
                rad[f"interaksjon|{bk}"] = koef(fit, f"{x}:db")
            else:
                rad[f"interaksjon|{bk}"] = {"b": None, "merknad": f"bare {int(dd.db.sum())} distrikts-bastioner"}
        # dekomponering i distriktet: hvor kom Sp-gevinsten fra (helning per parti; summerer til −1)
        dist = d[d.distrikt]
        rad["dekomponering_distrikt"] = {q: r(ols(dist, f"d_{q} ~ {x}", klynge=None).params[x])
                                         for q in ANDRE + (["fl"] if spk == "sp" else [])}
        db = d[d.distrikt & d.bastion_fast]
        rad["dekomponering_distrikt_bastion_fast"] = {q: r(ols(db, f"d_{q} ~ {x}", klynge=None).params[x])
                                                      for q in ANDRE + (["fl"] if spk == "sp" else [])}
        rad["snitt_distrikt_bastion_fast"] = {"d_sp90": r(db.d_sp90.mean(), 2), "d_ap": r(db.d_ap.mean(), 2),
                                             "dl_ap": r(db.dl_ap.mean(), 2), "n": int(len(db))}
        ut[par] = rad
    # Lokale bølger 1953–2025 samlet: dekomponering relativt til landet, med periode-FE
    lb = p[p[f"d_{spk}"] >= 10]
    lok = {}
    for navn, m in {"distrikt_bastion": lb.distrikt & lb.bastion, "distrikt_ikke_bastion": lb.distrikt & ~lb.bastion,
                    "sentral": ~lb.distrikt}.items():
        s = lb[m]
        lok[navn] = {"n": int(len(s)), "snitt_dl_sp": r(s[f"dl_{spk}"].mean(), 2),
                     **{f"snitt_dl_{q}": r(s[f"dl_{q}"].mean(), 2) for q in ["ap", "h", "v", "krf", "frp", "sv", "nkp", "hvk"]},
                     "andel_fra_ap": r(-s.dl_ap.mean() / s[f"dl_{spk}"].mean())}
    ut["lokale_bolger_1953_2025"] = lok
    # Helning i alle testbare par, periode-FE, per gruppe og periode
    per = {}
    for navn, sub in {"1953-1989": p[p.t1 <= 1989], "1989-2025": p[p.t0 >= 1989], "alle": p}.items():
        per[navn] = {g: helning(sub[m], "d_ap", x, fe=["par"]) for g, m in grupper(sub).items() if g != "alle"}
    ut["helning_panel_periode_FE"] = per
    return ut


# ---------------------------------------------------------------- T2 Asymmetri
def asym(d, spk="sp90", kom_fe=False, kontroll=""):
    d = d.assign(pos=d[f"d_{spk}"].clip(lower=0), neg=d[f"d_{spk}"].clip(upper=0))
    if len(d) < 30 or d.pos.gt(0).sum() < 5 or d.neg.lt(0).sum() < 5:
        return {"n": int(len(d))}
    f = "d_ap ~ pos + neg + C(par)" + (" + C(kom)" if kom_fe else "") + kontroll
    fit = ols(d, f)
    ut = {"b_pos": koef(fit, "pos"), "b_neg": koef(fit, "neg"), "n": int(fit.nobs), "n_kom": int(d.kom.nunique())}
    # asymmetri: |b+| − |b−|; med begge negative er det b− − b+ (> 0 betyr sperrehake)
    t = fit.t_test("neg - pos = 0")
    diff, se = float(t.effect[0]), float(t.sd[0][0])
    ut["asym_bneg_minus_bpos"] = {"b": r(diff), "se": r(se), "ki95": [r(diff - 1.96 * se), r(diff + 1.96 * se)],
                                  "p": r(float(t.pvalue), 4)}
    ut["andel_tilbake"] = r(fit.params["neg"] / fit.params["pos"]) if fit.params["pos"] != 0 else None
    return ut


def t2(p, spk="sp90", bastkol="bastion"):
    ut = {}
    for fe in (False, True):
        blokk = {}
        for g, m in grupper(p, bastkol).items():
            blokk[g] = asym(p[m], spk, kom_fe=fe)
        # placebo: Ap-svake distriktskommuner (rullerende Ap-snitt i nedre kvartil innen valgpar)
        q25 = p.groupby("par").ap_rull.transform(lambda s: s.quantile(0.25))
        blokk["placebo_ap_svake_distrikt"] = asym(p[p.distrikt & (p.ap_rull <= q25)], spk, kom_fe=fe)
        blokk["placebo_ap_svake_alle"] = asym(p[p.ap_rull <= q25], spk, kom_fe=fe)
        blokk["distrikt_bastion_bef_kontroll"] = asym(p[p.distrikt & p[bastkol]], spk, kom_fe=fe, kontroll=" + dlog_bef")
        ut["kommune_FE" if fe else "periode_FE"] = blokk
    # delperioder (distrikts-bastioner og alle distrikt)
    u = p[(p.t1 <= 1989) & (p.fl0 < 0.05) & (p.fl1 < 0.05)]
    ut["1953-1989_uten_felleslister"] = {g: asym(u[m], "sp") for g, m in grupper(u, bastkol).items()
                                         if g in ("distrikt_bastion", "distrikt_ikke_bastion", "sentral")}
    ut["delperioder"] = {}
    for navn, sub in {"1953-1989": p[p.t1 <= 1989], "1989-2025": p[p.t0 >= 1989]}.items():
        ut["delperioder"][navn] = {g: asym(sub[m], spk) for g, m in grupper(sub, bastkol).items()
                                   if g in ("distrikt_bastion", "distrikt_ikke_bastion", "sentral")}
    return ut


# ---------------------------------------------------------------- T3 Dose–respons
def t3(p):
    bred = {}
    for kol in ["ap", "sp90", "frp", "h"]:
        bred[kol] = p.pivot(index="kom", columns="t1", values=f"{kol}1")
        bred[kol][1945] = p[p.t1 == 1949].set_index("kom")[f"{kol}0"]
    bef = p.pivot(index="kom", columns="t1", values="bef1")
    info = p[p.par == "1989-1993"].set_index("kom")[["distrikt", "bastion", "bastion_fast", "ap_rull"]]
    ut = {}
    for navn, (a0, a1, slutter) in {"1989-1993": (1989, 1993, [1993, 1997, 2001, 2005, 2009, 2013]),
                                    "2013-2021": (2013, 2021, [2017, 2021, 2025])}.items():
        dose = bred["sp90"][a1] - bred["sp90"][a0]
        if navn == "2013-2021":
            info = p[p.par == "2013-2017"].set_index("kom")[["distrikt", "bastion", "bastion_fast", "ap_rull"]]
        blokk = {}
        for gnavn, m in {"alle_distrikt": info.distrikt, "distrikt_bastion_rull": info.distrikt & info.bastion,
                         "distrikt_bastion_fast": info.distrikt & info.bastion_fast,
                         "sentral": ~info.distrikt}.items():
            kom = m[m].index
            rad = {"n": int(len(kom)), "dose_snitt": r(dose[kom].mean(), 2)}
            for s in slutter:
                d = pd.DataFrame({"dose": dose[kom], "d_ap": bred["ap"].loc[kom, s] - bred["ap"].loc[kom, a0],
                                  "d_sp": bred["sp90"].loc[kom, s] - bred["sp90"].loc[kom, a0],
                                  "ap0": bred["ap"].loc[kom, a0],
                                  "dbef": np.log(bef.loc[kom, s] / bef.loc[kom, a0]) * 100}).dropna()
                if len(d) < 8:
                    continue
                fa = ols(d, "d_ap ~ dose + ap0 + dbef", klynge=None)
                fs = ols(d, "d_sp ~ dose + ap0 + dbef", klynge=None)
                rad[f"til_{s}"] = {"ap": koef(fa, "dose"), "sp90": koef(fs, "dose"),
                                   "ap_uten_kontroll": r(ols(d, "d_ap ~ dose", klynge=None).params["dose"])}
            blokk[gnavn] = rad
        ut[navn] = blokk
    return ut


# ---------------------------------------------------------------- T4 Hendelsesstudie
def t4(p, land):
    rel = {}
    for kol in ["ap", "sp90", "frp", "h"]:
        b = p.pivot(index="kom", columns="t1", values=f"{kol}1")
        rel[kol] = b - land.loc[b.columns, kol].values
    ut, tabell = {}, []
    for hend, (grunnpar, aarliste, basis) in {
            "1993": ("1989-1993", [1981, 1985, 1989, 1993, 1997, 2001, 2005, 2009], 1989),
            "2021": ("2013-2017", [2005, 2009, 2013, 2017, 2021, 2025], 2013)}.items():
        g = p[p.par == grunnpar].set_index("kom")
        a0, a1 = (1989, 1993) if hend == "1993" else (2013, 2021)
        dose = p.pivot(index="kom", columns="t1", values="sp901")
        dose = dose[a1] - dose[a0]
        blokk = {}
        for bk in ("bastion", "bastion_fast"):
            gr = g.distrikt & g[bk]
            kom = gr[gr].index
            if len(kom) < 10:
                blokk[bk] = {"n": int(len(kom)), "merknad": "for få kommuner"}
                continue
            med = dose[kom].median()
            for nivå, sel in {"høy_dose": kom[dose[kom] >= med], "lav_dose": kom[dose[kom] < med]}.items():
                rad = {"n": int(len(sel)), "dose_snitt": r(dose[sel].mean(), 2)}
                for kol in ["ap", "sp90", "frp", "h"]:
                    s = rel[kol].loc[sel, aarliste].sub(rel[kol].loc[sel, basis], axis=0)
                    rad[kol] = {int(a): r(s[a].mean(), 2) for a in aarliste}
                    for a in aarliste:
                        tabell.append({"hendelse": hend, "bastion": bk, "dose": nivå, "parti": kol, "aar": a,
                                       "snitt": s[a].mean(), "se": s[a].std() / np.sqrt(s[a].notna().sum()),
                                       "n": int(s[a].notna().sum())})
                blokk.setdefault(bk, {})[nivå] = rad
            # forskjell høy − lav i Ap etter bølgen (varig?)
            h, l = blokk[bk]["høy_dose"]["ap"], blokk[bk]["lav_dose"]["ap"]
            blokk[bk]["ap_høy_minus_lav"] = {a: r(h[a] - l[a], 2) for a in h}
        ut[hend] = blokk
    # Stablet hendelsesstudie over alle første lokale bølger (1953–2017) i distriktet
    first = p[p.lokal_bolge & p.testbar & p.distrikt].groupby("kom").first()[["t0", "t1", "bastion"]]
    apr = rel["ap"]
    aar = list(apr.columns)
    stabel = []
    for kom, e in first.iterrows():
        i0 = aar.index(e.t0)
        # kontroll: distriktskommuner uten lokal bølge i samme par og som ikke har hatt første bølge før
        for k in range(-2, 5):
            j = i0 + k
            if 0 <= j < len(aar) and j - k >= 0:
                stabel.append({"kom": kom, "t0": e.t0, "bastion": bool(e.bastion), "k": k,
                               "ap_rel": apr.loc[kom, aar[j]] - apr.loc[kom, e.t0]})
    st = pd.DataFrame(stabel)
    ktr = []
    forste_t0 = first.t0
    dist_kom = p[p.distrikt].kom.unique()
    for t0 in first.t0.unique():
        i0 = aar.index(t0)
        # ikke-behandlet til og med t0+4 valg (ingen første bølge før eller i vinduet)
        vindu_slutt = aar[min(i0 + 4, len(aar) - 1)]
        k_kom = [k for k in dist_kom if (k not in forste_t0.index) or (forste_t0[k] > vindu_slutt)]
        for k in range(-2, 5):
            j = i0 + k
            if 0 <= j < len(aar):
                v = apr.loc[k_kom, aar[j]] - apr.loc[k_kom, t0]
                ktr.append({"t0": t0, "k": k, "ap_rel_kontroll": v.mean(), "n_kontroll": len(k_kom)})
    ktr = pd.DataFrame(ktr)
    st = st.merge(ktr, on=["t0", "k"], how="left")
    st["diff"] = st.ap_rel - st.ap_rel_kontroll
    sam = st.groupby(["bastion", "k"]).agg(ap_rel=("ap_rel", "mean"), kontroll=("ap_rel_kontroll", "mean"),
                                          diff=("diff", "mean"), diff_se=("diff", lambda s: s.std() / np.sqrt(len(s))),
                                          n=("diff", "size")).reset_index()
    sam_tidlig = st[st.t0 < 1989].groupby(["bastion", "k"]).agg(diff=("diff", "mean"), n=("diff", "size")).reset_index()
    ut["stablet_lokale_bolger"] = {
        "beskrivelse": "Første lokale bølge (Sp+fl ≥ 10 pp) per distriktskommune; Ap relativt til landet, normert til valget før bølgen (k=0 er t0, k=1 er bølgevalget t1). Kontroll: distriktskommuner uten første bølge før t0+4 valg.",
        "alle": [{k: (r(v, 2) if isinstance(v, float) else v) for k, v in rad.items()} for rad in sam.to_dict("records")],
        "bare_bølger_før_1989": [{k: (r(v, 2) if isinstance(v, float) else v) for k, v in rad.items()} for rad in sam_tidlig.to_dict("records")],
        "antall_hendelser": int(len(first)), "fordeling_t0": {int(k): int(v) for k, v in first.t0.value_counts().sort_index().items()},
    }
    pd.DataFrame(tabell).to_csv(ARB / "t4_hendelse.csv", index=False, float_format="%.4f")
    sam.to_csv(ARB / "t4_stablet.csv", index=False, float_format="%.4f")
    return ut


# ---------------------------------------------------------------- T5 Volatilitet
PRE = ["1973-1977", "1977-1981", "1981-1985", "1985-1989"]
POST = ["1997-2001", "2001-2005", "2005-2009", "2009-2013"]


def t5(p, pedkol="ped90", bastkol="bastion", median=False):
    g = p[p.par == "1989-1993"].set_index("kom")
    grense = g.loc[g.distrikt & g[bastkol], "d_sp90"].median() if median else 10
    beh = (g.distrikt & g[bastkol] & (g.d_sp90 >= grense))
    grp = pd.Series(np.select([beh, g.distrikt & g[bastkol] & ~beh, g.distrikt & ~g[bastkol], ~g.distrikt],
                              ["rammet_bastion", "a_bastion_lav_dose", "b_distrikt_ikke_bastion", "c_sentral"], "x"),
                    index=g.index)
    d = p[p.par.isin(PRE + POST)].copy()
    d["grp"] = d.kom.map(grp)
    d["post"] = d.par.isin(POST).astype(int)
    ut = {"n_grupper": grp.value_counts().to_dict(), "dosegrense": r(grense, 2), "snitt": {}}
    for kol in (pedkol, "ped_uten_sp"):
        m = d.groupby(["grp", "post"])[kol].mean().unstack()
        ut["snitt"][kol] = {gr: {"før": r(m.loc[gr, 0], 2), "etter": r(m.loc[gr, 1], 2), "endring": r(m.loc[gr, 1] - m.loc[gr, 0], 2)}
                            for gr in m.index}
        ut[f"did_{kol}"] = {}
        for sam in ["a_bastion_lav_dose", "b_distrikt_ikke_bastion", "c_sentral"]:
            s = d[d.grp.isin(["rammet_bastion", sam])].assign(beh=lambda x: (x.grp == "rammet_bastion").astype(int))
            fit = ols(s, f"{kol} ~ beh:post + C(par) + C(kom)")
            ut[f"did_{kol}"][f"mot_{sam}"] = {**koef(fit, "beh:post"), "n": int(fit.nobs)}
    # FrP- og H-utslag etter (snitt |Δ|) og ny Sp-bølge 2013–21
    etter = p[p.par.isin(POST)].assign(grp=lambda x: x.kom.map(grp))
    ut["abs_utslag_etter"] = {kol: etter.groupby("grp")[kol].apply(lambda s: r(s.abs().mean(), 2)).to_dict()
                              for kol in ["d_frp", "d_h", "d_ap", "d_sp90"]}
    sp = p.pivot(index="kom", columns="t1", values="sp901")
    dose93 = sp[1993] - sp[1989]
    dose21 = sp[2021] - sp[2013]
    dist = g.index[g.distrikt]
    ut["dose93_mot_dose1321_distrikt"] = {"korrelasjon": r(np.corrcoef(dose93[dist], dose21[dist])[0, 1]),
                                         "helning": helning(pd.DataFrame({"y": dose21[dist], "x": dose93[dist]}), "y", "x")}
    ut["ny_bølge_2013_2021_per_gruppe"] = {gr: r(dose21[grp[grp == gr].index].mean(), 2) for gr in grp.unique()}
    # tabell for figur: snitt per par og gruppe
    tab = p[p.testbar].assign(grp=lambda x: x.kom.map(grp)).groupby(["grp", "par", "t1"])[[pedkol, "ped_uten_sp"]].mean().reset_index()
    return ut, tab, grp


def t5_forskjøvet(p, pedkol="ped90"):
    """Første lokale bølge (alle år fra 1953): TWFE ped ~ etter + periode-FE + kommune-FE, distriktet.
    Bølgeparet og paret rett etter (tilbakefallet) tas ut fordi de mekanisk er flyktige."""
    d = p[p.testbar & p.distrikt].copy()
    first = d[d.lokal_bolge].groupby("kom").t1.min()
    d["forste"] = d.kom.map(first)
    aar = sorted(d.t1.unique())
    nest = {a: aar[aar.index(a) + 1] if aar.index(a) + 1 < len(aar) else 9999 for a in aar}
    d = d[~((d.t1 == d.forste) | (d.t1 == d.forste.map(nest)))]
    d["etter"] = (d.forste.notna() & (d.t1 > d.forste)).astype(int)
    ut = {}
    for navn, sub in {"alle_distrikt": d, "første_bølge_før_1989": d[(d.forste.isna()) | (d.forste < 1989)],
                      "første_bølge_1993": d[(d.forste.isna()) | (d.forste == 1993)]}.items():
        fit = ols(sub, f"{pedkol} ~ etter + C(par) + C(kom)")
        ut[navn] = {**koef(fit, "etter"), "n": int(fit.nobs)}
        fit2 = ols(sub, "ped_uten_sp ~ etter + C(par) + C(kom)")
        ut[navn + "|ped_uten_sp"] = {**koef(fit2, "etter"), "n": int(fit2.nobs)}
    return ut


# ---------------------------------------------------------------- T6 Hvor går de?
def t6(p):
    ut = {}
    x = "d_sp90"
    for par in TILBAKEFALL:
        d = p[p.par == par]
        blokk = {}
        for navn, m in {"alle_distrikt": d.distrikt, "distrikt_bastion_fast": d.distrikt & d.bastion_fast,
                        "sentral": ~d.distrikt}.items():
            s = d[m]
            # andel av Sp-tapet som gikk til parti q = −helning (helningene summerer til −1)
            blokk[navn] = {"n": int(len(s)), "snitt_d_sp90": r(s.d_sp90.mean(), 2),
                           "andel_av_tap_til": {q: r(-ols(s, f"d_{q} ~ {x}", klynge=None).params[x]) for q in ANDRE},
                           "snitt_d": {q: r(s[f"d_{q}"].mean(), 2) for q in ANDRE}}
        ut[par] = blokk
    # Lokale tilbakefall: paret rett etter en lokal bølge der Sp går tilbake, alle år fra 1953, periode-FE
    q = p.sort_values(["kom", "t1"]).copy()
    q["forrige_bolge"] = q.groupby("kom").lokal_bolge.shift(1).fillna(False).astype(bool)
    lt = q[q.forrige_bolge & (q.d_sp90 < 0) & q.testbar]
    blokk = {}
    for navn, m in {"distrikt": lt.distrikt, "distrikt_før_1989": lt.distrikt & (lt.t1 <= 1989),
                    "distrikt_bastion_rull": lt.distrikt & lt.bastion}.items():
        s = lt[m]
        if len(s) < 15:
            blokk[navn] = {"n": int(len(s))}
            continue
        blokk[navn] = {"n": int(len(s)),
                       "andel_av_tap_til": {pp: r(-ols(s, f"dl_{pp} ~ dl_sp90 + C(par)", klynge=None).params["dl_sp90"])
                                            for pp in ANDRE}}
    ut["lokale_tilbakefall"] = blokk
    # Symmetri-sjekk: andel av Sp-gevinsten som kom fra Ap i bølgen vs andel av tapet som gikk til Ap i tilbakefallet
    sym = {}
    for bolge, tilb in [("1989-1993", "1993-1997"), ("2017-2021", "2021-2025")]:
        for navn, mk in {"alle_distrikt": lambda d: d.distrikt, "distrikt_bastion_fast": lambda d: d.distrikt & d.bastion_fast}.items():
            b, t = p[p.par == bolge], p[p.par == tilb]
            b, t = b[mk(b)], t[mk(t)]
            sym[f"{bolge}|{navn}"] = {"andel_fra_ap_i_bølgen": r(-ols(b, "d_ap ~ d_sp90", klynge=None).params["d_sp90"]),
                                     "andel_til_ap_i_tilbakefallet": r(-ols(t, "d_ap ~ d_sp90", klynge=None).params["d_sp90"])}
    ut["symmetri"] = sym
    return ut


# ---------------------------------------------------------------- T8 Langsom drift 1953–89
def t8(p):
    d = p[p.testbar & (p.t1 <= 1989)]
    ut = {}
    for spk in ("sp90", "sp"):
        blokk = {}
        andre = ["ap", "hvk", "frp", "sv", "nkp", "andre", "mdg", "rodt"] + (["fl"] if spk == "sp" else [])
        for navn, m in {"alle_distrikt": d.distrikt, "distrikt_bastion_rull": d.distrikt & d.bastion,
                        "distrikt_bastion_fast": d.distrikt & d.bastion_fast, "sentral": ~d.distrikt}.items():
            s = d[m]
            blokk[navn] = {"n": int(len(s)),
                           **{q: helning(s, f"d_{q}", f"d_{spk}", fe=["par", "kom"]) for q in ("ap", "hvk")},
                           "alle_partier_b": {q: r(ols(s, f"d_{q} ~ d_{spk} + C(par) + C(kom)").params[f"d_{spk}"]) for q in andre}}
        ut[spk] = blokk
    # Uten felleslister: bare kommune-par der gruppe 90 er 0 både i t0 og t1 (da er sp90 = sp)
    u = d[(d.fl0 < 0.05) & (d.fl1 < 0.05)]
    blokk = {}
    for navn, m in {"alle_distrikt": u.distrikt, "distrikt_bastion_rull": u.distrikt & u.bastion,
                    "distrikt_bastion_fast": u.distrikt & u.bastion_fast, "sentral": ~u.distrikt}.items():
        s = u[m]
        blokk[navn] = {"n": int(len(s)), **{q: helning(s, f"d_{q}", "d_sp", fe=["par", "kom"]) for q in ("ap", "hvk", "h", "v", "krf")}}
    ut["uten_felleslister"] = blokk
    # Kumulativt 1953 → 1989 (nivåendring) i distriktet
    b = {k: p.pivot(index="kom", columns="t1", values=f"{k}1") for k in ["ap", "sp90", "hvk", "h", "v", "krf"]}
    info = p[p.par == "1953-1957"].set_index("kom")
    kum = {}
    for navn, m in {"alle_distrikt": info.distrikt, "distrikt_bastion_fast": info.distrikt & info.bastion_fast,
                    "sentral": ~info.distrikt}.items():
        kom = m[m].index
        dd = pd.DataFrame({k: b[k].loc[kom, 1989] - b[k].loc[kom, 1953] for k in b})
        kum[navn] = {"n": int(len(kom)), **{f"snitt_d_{k}": r(dd[k].mean(), 2) for k in b},
                     "helning_ap_på_sp90": helning(dd.rename(columns={"sp90": "x"}), "ap", "x"),
                     "helning_hvk_på_sp90": helning(dd.rename(columns={"sp90": "x"}), "hvk", "x")}
    # Distriktskommuner der Sp (+fl) faktisk vokste ≥ 5 pp 1953→1989 (som Sømna)
    kom = info.index[info.distrikt]
    vekst = (b["sp90"].loc[kom, 1989] - b["sp90"].loc[kom, 1953])
    kom5 = vekst[vekst >= 5].index
    dd = pd.DataFrame({k: b[k].loc[kom5, 1989] - b[k].loc[kom5, 1953] for k in b})
    kum["distrikt_sp_vekst_minst_5pp"] = {"n": int(len(kom5)), **{f"snitt_d_{k}": r(dd[k].mean(), 2) for k in b},
                                          "andel_av_sp_vekst_fra_ap": r(-dd.ap.mean() / dd.sp90.mean()),
                                          "andel_av_sp_vekst_fra_hvk": r(-dd.hvk.mean() / dd.sp90.mean()),
                                          "snitt_alle_kommuner_d_ap": r(p[p.t1 == 1989].ap1.mean() - p[p.t1 == 1957].ap0.mean(), 2)}
    ut["kumulativt_1953_1989"] = kum
    return ut


# ---------------------------------------------------------------- T7 Sømna og tilsvarende
def t7(p, land):
    b = {k: p.pivot(index="kom", columns="t1", values=f"{k}1") for k in ["ap", "sp90", "frp", "h"]}
    for k in b:
        b[k][1945] = p[p.t1 == 1949].set_index("kom")[f"{k}0"]
        b[k] = b[k][sorted(b[k].columns)]
    info = p[p.par == "1989-1993"].set_index("kom")
    apr = b["ap"] - land.loc[b["ap"].columns, "ap"].values
    dose93 = b["sp90"][1993] - b["sp90"][1989]
    dose21 = b["sp90"][2021] - b["sp90"][2013]
    varig = apr[[1997, 2001, 2005, 2009, 2013]].mean(axis=1) - apr[[1981, 1985, 1989]].mean(axis=1)
    regel = {"distrikt": "sentralitet 5–6", "ap_fast_min": 45, "dose93_min": 15, "ap_rel_endring_maks": -5,
             "sp90_2021_min": 35, "rangering": "dose93 + dose2013–21, høyest først, 8 kommuner utenom Sømna"}
    kand = info[(info.distrikt) & (info.ap_fast >= 45)].index
    kand = [k for k in kand if dose93[k] >= 15 and varig[k] <= -5 and b["sp90"].loc[k, 2021] >= 35]
    rang = (dose93[kand] + dose21[kand]).drop("1812", errors="ignore").sort_values(ascending=False)
    valgt = ["1812"] + list(rang.index[:8])
    rader = []
    for k in valgt:
        rader.append({"kom": k, "navn": info.loc[k, "navn"], "ap_fast_1953_69": r(info.loc[k, "ap_fast"], 1),
                      "dose93": r(dose93[k], 1), "dose13_21": r(dose21[k], 1), "ap_rel_endring": r(varig[k], 1),
                      "oppfyller_regel": bool(k in kand)})
    serie = []
    for k in valgt:
        for kol in b:
            for a in b[kol].columns:
                serie.append({"kom": k, "navn": info.loc[k, "navn"], "parti": kol, "aar": int(a), "prosent": b[kol].loc[k, a]})
    pd.DataFrame(serie).to_csv(ARB / "t7_serier.csv", index=False, float_format="%.3f")
    n_kand = len(kand)
    return {"regel": regel, "antall_som_oppfyller_regel": n_kand, "valgt": rader,
            "sømna_oppfyller_regel": bool(dose93["1812"] >= 15 and varig["1812"] <= -5 and b["sp90"].loc["1812", 2021] >= 35
                                          and info.loc["1812", "ap_fast"] >= 45)}


# ---------------------------------------------------------------- Robusthet
def nøkkeltall(p, land=None, spk="sp90", bastkol="bastion"):
    """Et lite sett nøkkeltall som kjøres i hver robusthetsvariant."""
    ut = {}
    d93 = p[p.par == "1989-1993"]
    s = d93[d93.distrikt & d93[bastkol]]
    ut["T1_helning_1993_distrikt_bastion"] = r(ols(s, f"d_ap ~ d_{spk}", klynge=None).params[f"d_{spk}"]) if len(s) > 8 else None
    d21 = p[p.par == "2017-2021"]
    s = d21[d21.distrikt & d21.bastion_fast]
    ut["T1_helning_2021_distrikt_bastion_fast"] = r(ols(s, f"d_ap ~ d_{spk}", klynge=None).params[f"d_{spk}"]) if len(s) > 8 else None
    a = asym(p[p.distrikt & p[bastkol]], spk)
    ut["T2_b_pos"] = a.get("b_pos", {}).get("b")
    ut["T2_b_neg"] = a.get("b_neg", {}).get("b")
    ut["T2_asym"] = a.get("asym_bneg_minus_bpos", {}).get("b")
    ut["T2_asym_p"] = a.get("asym_bneg_minus_bpos", {}).get("p")
    a2 = asym(p[p.distrikt], spk)
    ut["T2_asym_alle_distrikt"] = a2.get("asym_bneg_minus_bpos", {}).get("b")
    q25 = p.groupby("par").ap_rull.transform(lambda x: x.quantile(0.25))
    a3 = asym(p[p.distrikt & (p.ap_rull <= q25)], spk)
    ut["T2_asym_placebo_ap_svake"] = a3.get("asym_bneg_minus_bpos", {}).get("b")
    # T3: dose 1989–93 mot Ap 1989→2009, alle distrikt
    bred = p.pivot(index="kom", columns="t1", values="ap1")
    sp = p.pivot(index="kom", columns="t1", values=f"{spk}1")
    info = d93.set_index("kom")
    kom = info.index[info.distrikt]
    if 2009 in bred:
        dd = pd.DataFrame({"dose": sp.loc[kom, 1993] - sp.loc[kom, 1989], "y": bred.loc[kom, 2009] - bred.loc[kom, 1989],
                           "y93": bred.loc[kom, 1993] - bred.loc[kom, 1989], "ap0": bred.loc[kom, 1989]}).dropna()
        ut["T3_dose_ap_1989_2009_distrikt"] = r(ols(dd, "y ~ dose + ap0", klynge=None).params["dose"])
        ut["T3_dose_ap_1989_1993_distrikt"] = r(ols(dd, "y93 ~ dose + ap0", klynge=None).params["dose"])
    try:
        t5r, _, _ = t5(p, bastkol=bastkol)
        ut["T5_did_ped90_mot_b"] = t5r["did_ped90"]["mot_b_distrikt_ikke_bastion"]["b"]
        ut["T5_did_ped90_mot_c"] = t5r["did_ped90"]["mot_c_sentral"]["b"]
    except Exception as e:   # for få observasjoner i en variant
        ut["T5_feil"] = str(e)[:80]
    return ut


def robusthet(p, land):
    ut = {"hoved_sp90": nøkkeltall(p), "sp_alene": nøkkeltall(p, spk="sp"),
          "bastion_fast": nøkkeltall(p, bastkol="bastion_fast"), "bastion_q75": nøkkeltall(p, bastkol="bastion_q75")}
    for g in (45, 55):
        pg, _ = bygg_panel(bastion_grense=g)
        ut[f"bastion_{g}"] = nøkkeltall(pg[pg.testbar])
    ps = les_panel("panel_stabil.csv")
    ut["stabile_enheter"] = nøkkeltall(ps[ps.testbar])
    ph = p[(p.sikker0 == "høy") & (p.sikker1 == "høy") & ~p.est]
    ut["bare_høy_sikkerhet_uten_estimert"] = nøkkeltall(ph)
    ut["bare_høy_sikkerhet_uten_estimert"]["n_rader"] = int(len(ph))
    loo = {}
    for f in sorted(p.fylke.unique()):
        loo[FYLKE.get(f, f)] = nøkkeltall(p[p.fylke != f])
    ut["ett_fylke_ute"] = loo
    ut["ett_fylke_ute_spenn"] = {k: [r(min(v[k] for v in loo.values() if v.get(k) is not None)),
                                     r(max(v[k] for v in loo.values() if v.get(k) is not None))]
                                 for k in ut["hoved_sp90"] if k not in ("T5_feil",) and all(v.get(k) is not None for v in loo.values())}
    return ut


def kv(pkv, landkv, p_st):
    """Kommunestyrevalg parallelt: bølger defineres av KV-landstall (Sp+fl ≥ 3 pp).
    Fast bastion hentes fra stortingsvalg (ST 1953–69), rullerende bastion fra KV selv."""
    fast = p_st.drop_duplicates("kom").set_index("kom")["bastion_fast"]
    pkv = pkv.assign(bastion_fast=pkv.kom.map(fast).fillna(False).astype(bool))
    aar = list(landkv.index)
    bolger = [f"{aar[i-1]}-{aar[i]}" for i in range(1, len(aar))
              if landkv.loc[aar[i], "sp90"] - landkv.loc[aar[i-1], "sp90"] >= 3 and aar[i - 1] >= 1953]
    d = pkv[pkv.testbar]
    ut = {"kv_bolger": bolger, "T1": {}}
    for par in bolger:
        s = d[d.par == par]
        ut["T1"][par] = {g: helning(s[m], "d_ap", "d_sp90") for g, m in grupper(s, "bastion_fast").items()
                         if g in ("distrikt_bastion", "distrikt_ikke_bastion", "sentral")}
    ut["T2"] = {g: asym(d[m]) for g, m in grupper(d).items() if g in ("distrikt_bastion", "distrikt_ikke_bastion", "sentral", "alle_distrikt")}
    ut["T2_bastion_fast_fra_ST"] = asym(d[d.distrikt & d.bastion_fast])
    ut["T2_delperioder"] = {per: {g: asym(sub[m]) for g, m in grupper(sub, "bastion_fast").items()
                                  if g in ("distrikt_bastion", "distrikt_ikke_bastion", "sentral")}
                            for per, sub in {"1955-1987": d[d.t1 <= 1987], "1987-2023": d[d.t0 >= 1987]}.items()}
    q25 = d.groupby("par").ap_rull.transform(lambda x: x.quantile(0.25))
    ut["T2"]["placebo_ap_svake_distrikt"] = asym(d[d.distrikt & (d.ap_rull <= q25)])
    return ut


def main():
    p_all = les_panel()
    land = pd.read_csv(ARB / "landstall_st.csv", index_col=0)
    landkv = pd.read_csv(ARB / "landstall_kv.csv", index_col=0)
    p = testbar(p_all)
    res = {"låst_sha_panel": LÅST["panel_sha256"]["panel.csv"], "merknad": "Alle tall regnet av steg3_tester.py"}
    res["T1"] = {"sp90": t1(p), "sp_alene": t1(p, "sp")}
    res["T2"] = {"sp90": t2(p), "sp_alene": t2(p, "sp"), "bastion_fast_sp90": t2(p, bastkol="bastion_fast")}
    res["T3"] = t3(p_all)
    res["T4"] = t4(p_all, land)
    t5r, tab, grp = t5(p)
    t5r["forskjøvet_første_lokale_bølge"] = t5_forskjøvet(p)
    t5f, _, _ = t5(p, bastkol="bastion_fast")
    t5r["bastion_fast"] = {k: t5f[k] for k in ("n_grupper", "did_ped90", "did_ped_uten_sp")}
    t5m, _, _ = t5(p, median=True)
    t5r["median_deling"] = {k: t5m[k] for k in ("n_grupper", "dosegrense", "snitt", "did_ped90", "did_ped_uten_sp")}
    _, tabm, grpm = t5(p, median=True)
    tabm.to_csv(ARB / "t5_volatilitet_median.csv", index=False, float_format="%.4f")
    t5mf, _, _ = t5(p, bastkol="bastion_fast", median=True)
    t5r["median_deling_bastion_fast"] = {k: t5mf[k] for k in ("n_grupper", "dosegrense", "did_ped90", "did_ped_uten_sp")}
    t5p, _, _ = t5(p, pedkol="ped")
    t5r["ped_rå_uten_fellesliste_korreksjon"] = t5p["did_ped"]
    res["T5"] = t5r
    tab.to_csv(ARB / "t5_volatilitet.csv", index=False, float_format="%.4f")
    grp.rename("grp").to_csv(ARB / "t5_grupper.csv")
    res["T6"] = t6(p)
    res["T7"] = t7(p_all, land)
    res["T8"] = t8(p_all)
    res["KV_parallell"] = kv(les_panel("panel_kv.csv"), landkv, p_all)
    res["robusthet"] = robusthet(p, land)
    (ARB / "resultater.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("skrev", ARB / "resultater.json")


if __name__ == "__main__":
    main()
