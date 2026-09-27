"""
Uavhengig kontroll (Brief K) av hypoteser/sp_ventil/arbeid/resultater.json.
Regner T1-T6 (hovedvariant sp90, samt utvalgte sp_alene/robusthetstall) på nytt
fra data/processed/, uten a lese arbeid/panel*.csv, arbeid/t*.csv eller koden
i analyse/sp_ventil/.

Kjores fra repo-roten. Skriver ingenting til data/processed eller arbeid/.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm

pd.set_option("display.width", 160)

BASE = "/home/user/valg_analyser"
DATA = f"{BASE}/data/processed"
ARBEID = f"{BASE}/hypoteser/sp_ventil/arbeid"
OUT = f"{BASE}/hypoteser/sp_ventil/kontroll"

PARTI_MAP = {1: "ap", 2: "frp", 3: "h", 4: "krf", 5: "sp", 6: "sv", 7: "v",
             8: "mdg", 9: "nkp", 55: "rodt", 90: "fl", 99: "andre"}
PARTIER = list(PARTI_MAP.values())
ELECTION_YEARS = [1945, 1949, 1953, 1957, 1961, 1965, 1969, 1973, 1977, 1981,
                   1985, 1989, 1993, 1997, 2001, 2005, 2009, 2013, 2017, 2021, 2025]

# ---------------------------------------------------------------------------
# 1) Rådata og oppslutning (§: "Andeler: stemmer per parti / sum stemmer over
#    alle 12 grupper i kommune-aar x 100. Landstall: stemmevektet (sum stemmer)")
# ---------------------------------------------------------------------------
raw = pd.read_csv(f"{DATA}/stortingsvalg_1945.csv", dtype={"kom2024": str})
raw["gruppe"] = raw["parti"].map(PARTI_MAP)
assert raw["gruppe"].isna().sum() == 0, "ukjent partikode"

# kommune-nivaa: pivot til bred tabell med stemmer per gruppe
piv = raw.pivot_table(index=["kom2024", "aar"], columns="gruppe", values="stemmer", aggfunc="sum").fillna(0.0)
piv = piv[PARTIER]
sum_stemmer = piv.sum(axis=1)
pct = piv.div(sum_stemmer, axis=0) * 100.0
pct.columns = [f"{p}" for p in PARTIER]
pct = pct.reset_index()
pct["sikkerhet"] = raw.groupby(["kom2024", "aar"])["sikkerhet"].agg(
    lambda s: sorted(s, key=lambda x: {"lav": 0, "middels": 1, "høy": 2, "hoy": 2}.get(x, 2))[0]).values
pct["estimert"] = raw.groupby(["kom2024", "aar"])["estimert"].any().values

pct["sp90"] = pct["sp"] + pct["fl"]
pct["hvk"] = pct["h"] + pct["v"] + pct["krf"]

# landstall (stemmevektet nasjonalt snitt)
nat = raw.groupby(["aar", "gruppe"])["stemmer"].sum().unstack("gruppe")
nat_tot = raw.groupby("aar")["stemmer"].sum()  # = sum over alle grupper (samme som total_stemmer sum)
nat_pct = nat.div(nat_tot, axis=0) * 100.0
nat_pct["sp90"] = nat_pct["sp"] + nat_pct["fl"]
nat_pct["hvk"] = nat_pct["h"] + nat_pct["v"] + nat_pct["krf"]

# sanity: landstall sp90 for par skal stemme med laast.json sine nasjonale endringer
laast = json.load(open(f"{BASE}/hypoteser/sp_ventil/låst.json", encoding="utf-8"))

# ---------------------------------------------------------------------------
# 2) Sentralitet, befolkning
# ---------------------------------------------------------------------------
sent = pd.read_csv(f"{DATA}/sentralitet_2024.csv", dtype={"kom2024": str})
sent_map = sent.set_index("kom2024")["sent_klasse"]

bef = pd.read_csv(f"{DATA}/befolkning_1951.csv", dtype={"kom2024": str})
bef_map = bef.set_index(["kom2024", "aar"])["befolkning"]

def bef_naermest(kom, aar):
    """Folketall ved naermeste tilgjengelige aar >= 1951."""
    a = max(aar, 1951)
    for delta in range(0, 6):
        for cand in (a + delta, a - delta):
            if (kom, cand) in bef_map.index:
                return bef_map.loc[(kom, cand)]
    return np.nan

# ---------------------------------------------------------------------------
# 3) Bygg panel: valgpar t0 -> t1 (paafolgende stortingsvalg)
# ---------------------------------------------------------------------------
pct_idx = pct.set_index(["kom2024", "aar"])
komner = sorted(pct["kom2024"].unique())

rows = []
for i in range(len(ELECTION_YEARS) - 1):
    t0, t1 = ELECTION_YEARS[i], ELECTION_YEARS[i + 1]
    tprev = ELECTION_YEARS[i - 1] if i >= 1 else None
    for kom in komner:
        if (kom, t0) not in pct_idx.index or (kom, t1) not in pct_idx.index:
            continue
        r0 = pct_idx.loc[(kom, t0)]
        r1 = pct_idx.loc[(kom, t1)]
        row = {"kom": kom, "t0": t0, "t1": t1, "par": f"{t0}-{t1}"}
        for p in PARTIER + ["sp90", "hvk"]:
            row[f"{p}0"] = r0[p]
            row[f"{p}1"] = r1[p]
            row[f"d_{p}"] = r1[p] - r0[p]
        row["sikker0"] = r0["sikkerhet"]
        row["sikker1"] = r1["sikkerhet"]
        row["est"] = bool(r0["estimert"]) or bool(r1["estimert"])
        # rullerende Ap-bastion: snitt Ap ved t0 og valget FOR t0
        if tprev is not None and (kom, tprev) in pct_idx.index:
            ap_rull = (r0["ap"] + pct_idx.loc[(kom, tprev)]["ap"]) / 2.0
        else:
            ap_rull = np.nan
        row["ap_rull"] = ap_rull
        row["sent"] = sent_map.get(kom, np.nan)
        b0 = bef_naermest(kom, t0)
        b1 = bef_naermest(kom, t1)
        row["bef0"], row["bef1"] = b0, b1
        row["dlog_bef"] = 100 * np.log(b1 / b0) if b0 and b1 and b0 > 0 else np.nan
        rows.append(row)

panel = pd.DataFrame(rows)
panel["distrikt"] = panel["sent"].isin([5, 6])
panel["testbar"] = panel["t0"] >= 1953
panel["bastion"] = panel["ap_rull"] >= 50.0

# Bastion fast: snitt Ap ST 1953,57,61,65,69 >= 50%
fast_years = [1953, 1957, 1961, 1965, 1969]
ap_fast = pct_idx.reset_index()
ap_fast = ap_fast[ap_fast["aar"].isin(fast_years)].groupby("kom2024")["ap"].mean()
panel["ap_fast"] = panel["kom"].map(ap_fast)
panel["bastion_fast"] = panel["ap_fast"] >= 50.0
q75 = ap_fast.quantile(0.75)
panel["bastion_q75"] = panel["ap_fast"] >= q75

def gruppe(row):
    if not row["distrikt"]:
        return "sentral"
    return "distrikt_bastion" if row["bastion"] else "distrikt_ikke_bastion"
panel["gruppe"] = panel.apply(gruppe, axis=1)

# landsendring (stemmevektet) per par, for dl_ og for aa reprodusere laast.json's
# "nasjonale_endringer" som konsistenssjekk
nat_pct2 = nat_pct.reset_index()
def nasj_d(par_par, p):
    t0, t1 = par_par
    return float(nat_pct2.loc[nat_pct2.aar == t1, p].values[0] - nat_pct2.loc[nat_pct2.aar == t0, p].values[0])

for p in ["ap", "sp90", "sp"]:
    panel[f"nasj_d_{p}"] = panel.apply(lambda r: nasj_d((r.t0, r.t1), p), axis=1)
    panel[f"dl_{p}"] = panel[f"d_{p}"] - panel[f"nasj_d_{p}"]
for p in ["frp", "h", "krf", "sv", "v", "rodt", "mdg", "nkp", "andre", "hvk"]:
    panel[f"nasj_d_{p}"] = panel.apply(lambda r: nasj_d((r.t0, r.t1), p), axis=1)
    panel[f"dl_{p}"] = panel[f"d_{p}"] - panel[f"nasj_d_{p}"]

panel["lokal_bolge"] = panel["d_sp90"] >= 10.0
panel["lokal_bolge_sp"] = panel["d_sp"] >= 10.0

testbar = panel[panel["testbar"]].copy()

print("panel rader:", len(panel), "testbar:", len(testbar), "kommuner:", panel.kom.nunique())

# ---------------------------------------------------------------------------
# Konsistenssjekk: nasjonale endringer mot laast.json
# ---------------------------------------------------------------------------
nat_check = {}
for row in laast["nasjonale_endringer"]:
    par = row["par"]
    t0, t1 = (int(x) for x in par.split("-"))
    my_sp = nasj_d((t0, t1), "sp")
    my_sp90 = nasj_d((t0, t1), "sp90")
    my_ap = nasj_d((t0, t1), "ap")
    nat_check[par] = {
        "d_sp_diff": round(my_sp - row["d_sp"], 3),
        "d_sp90_diff": round(my_sp90 - row["d_sp90"], 3),
        "d_ap_diff": round(my_ap - row["d_ap"], 3),
    }

# ---------------------------------------------------------------------------
# Hjelpefunksjoner for regresjon
# ---------------------------------------------------------------------------
def ols_hc1(df, yv, xv):
    d = df[[yv, xv]].dropna()
    if len(d) < 3 or d[xv].std() == 0:
        return None
    X = sm.add_constant(d[xv])
    m = sm.OLS(d[yv], X).fit(cov_type="HC1")
    b = m.params[xv]
    se = m.bse[xv]
    return {"b": round(b, 3), "se": round(se, 3),
            "ki95": [round(b - 1.96 * se, 3), round(b + 1.96 * se, 3)],
            "p": round(m.pvalues[xv], 4), "n": int(len(d))}

def ols_hc1_multi(df, yv, xvs):
    d = df[[yv] + xvs].dropna()
    if len(d) < len(xvs) + 2:
        return None
    X = sm.add_constant(d[xvs])
    m = sm.OLS(d[yv], X).fit(cov_type="HC1")
    return m, d

# =====================================================================
# T1: per naasjonal boelge, tverrsnitt d_ap paa d_sp90 per gruppe (HC1)
# =====================================================================
BOLGER = ["1989-1993", "2013-2017", "2017-2021"]
T1 = {"sp90": {}}
for par in BOLGER:
    d = testbar[testbar.par == par]
    res = {}
    for g, sub in [("distrikt_bastion", d[d.gruppe == "distrikt_bastion"]),
                   ("distrikt_ikke_bastion", d[d.gruppe == "distrikt_ikke_bastion"]),
                   ("sentral", d[d.gruppe == "sentral"]),
                   ("alle_distrikt", d[d.distrikt]),
                   ("alle", d)]:
        r = ols_hc1(sub, "d_ap", "d_sp90")
        res[f"{g}|bastion"] = r if r else {"b": None, "n": int(len(sub))}
    # interaksjon: d_ap ~ d_sp90 + bastion + d_sp90:bastion  (kun i distrikt)
    dd = d[d.distrikt].dropna(subset=["d_ap", "d_sp90", "bastion"]).copy()
    dd["bastion_i"] = dd["bastion"].astype(int)
    dd["inter"] = dd["d_sp90"] * dd["bastion_i"]
    if dd["bastion_i"].sum() >= 5 and (~dd["bastion_i"].astype(bool)).sum() >= 5:
        X = sm.add_constant(dd[["d_sp90", "bastion_i", "inter"]])
        m = sm.OLS(dd["d_ap"], X).fit(cov_type="HC1")
        b, se = m.params["inter"], m.bse["inter"]
        res["interaksjon|bastion"] = {"b": round(b, 3), "se": round(se, 3),
                                       "ki95": [round(b - 1.96 * se, 3), round(b + 1.96 * se, 3)],
                                       "p": round(m.pvalues["inter"], 4)}
    else:
        res["interaksjon|bastion"] = {"b": None, "merknad": f"bare {int(dd.bastion_i.sum())} distrikts-bastioner"}
    # bastion_fast-variant
    for g, sub in [("distrikt_bastion", d[d.distrikt & d.bastion_fast]),
                   ("distrikt_ikke_bastion", d[d.distrikt & ~d.bastion_fast])]:
        r = ols_hc1(sub, "d_ap", "d_sp90")
        res[f"{g}|bastion_fast"] = r if r else {"b": None, "n": int(len(sub))}
    dd2 = d[d.distrikt].dropna(subset=["d_ap", "d_sp90", "bastion_fast"]).copy()
    dd2["bf_i"] = dd2["bastion_fast"].astype(int)
    dd2["inter"] = dd2["d_sp90"] * dd2["bf_i"]
    X = sm.add_constant(dd2[["d_sp90", "bf_i", "inter"]])
    m = sm.OLS(dd2["d_ap"], X).fit(cov_type="HC1")
    b, se = m.params["inter"], m.bse["inter"]
    res["interaksjon|bastion_fast"] = {"b": round(b, 3), "se": round(se, 3),
                                        "ki95": [round(b - 1.96 * se, 3), round(b + 1.96 * se, 3)],
                                        "p": round(m.pvalues["inter"], 4)}
    # dekomponering_distrikt: helning d_q paa d_sp90 for hvert parti q, i distrikt (rullerende bastion)
    decomp = {}
    for q in ["ap", "frp", "h", "krf", "sv", "v", "rodt", "mdg", "nkp", "andre"]:
        r = ols_hc1(d[d.distrikt], f"d_{q}", "d_sp90")
        decomp[q] = r["b"] if r else None
    res["dekomponering_distrikt"] = decomp
    decomp_bf = {}
    for q in ["ap", "frp", "h", "krf", "sv", "v", "rodt", "mdg", "nkp", "andre"]:
        r = ols_hc1(d[d.distrikt & d.bastion_fast], f"d_{q}", "d_sp90")
        decomp_bf[q] = r["b"] if r else None
    res["dekomponering_distrikt_bastion_fast"] = decomp_bf
    sub = d[d.distrikt & d.bastion_fast]
    res["snitt_distrikt_bastion_fast"] = {
        "d_sp90": round(sub["d_sp90"].mean(), 2), "d_ap": round(sub["d_ap"].mean(), 2),
        "dl_ap": round(sub["dl_ap"].mean(), 2), "n": int(len(sub))}
    T1["sp90"][par] = res

# lokale boelger 1953-2025 (ALLE par, lokal_bolge==True, testbar)
lok = testbar[testbar.lokal_bolge]
res_lok = {}
for g, sub in [("distrikt_bastion", lok[lok.gruppe == "distrikt_bastion"]),
               ("distrikt_ikke_bastion", lok[lok.gruppe == "distrikt_ikke_bastion"]),
               ("sentral", lok[lok.gruppe == "sentral"])]:
    entry = {"n": int(len(sub))}
    entry["snitt_dl_sp"] = round(sub["dl_sp90"].mean(), 2)  # feltnavn "sp" i resultater.json = sp90 her
    for p in ["ap", "h", "v", "krf", "frp", "sv", "nkp", "hvk"]:
        entry[f"snitt_dl_{p}"] = round(sub[f"dl_{p}"].mean(), 2)
    entry["andel_fra_ap"] = round(-entry["snitt_dl_ap"] / entry["snitt_dl_sp"], 3)
    res_lok[g] = entry
T1["sp90"]["lokale_bolger_1953_2025"] = res_lok

# helning_panel_periode_FE: paneldata med periodedummy, per periode-vindu og gruppe
def periode_fe_helning(df, periods_label, t0_lo, t0_hi, gruppe_navn):
    sub = df[(df.t0 >= t0_lo) & (df.t0 <= t0_hi)]
    if gruppe_navn == "alle_distrikt":
        sub = sub[sub.distrikt]
    else:
        sub = sub[sub.gruppe == gruppe_navn]
    sub = sub.dropna(subset=["d_ap", "d_sp90"]).copy()
    if sub.par.nunique() < 2 or len(sub) < 5:
        r = ols_hc1(sub, "d_ap", "d_sp90")
        return r
    try:
        m = smf.ols("d_ap ~ d_sp90 + C(par)", data=sub).fit(cov_type="HC1")
        b, se = m.params["d_sp90"], m.bse["d_sp90"]
        return {"b": round(b, 3), "se": round(se, 3),
                "ki95": [round(b - 1.96 * se, 3), round(b + 1.96 * se, 3)],
                "p": round(m.pvalues["d_sp90"], 4), "n": int(len(sub))}
    except Exception:
        return None

hpfe = {}
for lbl, lo, hi in [("1953-1989", 1953, 1985), ("1989-2025", 1989, 2021), ("alle", 1953, 2021)]:
    hpfe[lbl] = {}
    for g in ["distrikt_bastion", "distrikt_ikke_bastion", "sentral", "alle_distrikt"]:
        hpfe[lbl][g] = periode_fe_helning(testbar, lbl, lo, hi, g)
T1["sp90"]["helning_panel_periode_FE"] = hpfe

json.dump({"nat_check": nat_check, "T1_sp90_partial": T1["sp90"]},
          open(f"{OUT}/_debug_t1.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("T1 sp90 ferdig (delvis lagret til _debug_t1.json)")

# =====================================================================
# T2: panel over alle testbare par, asymmetrisk helning, klynget SE
# =====================================================================
def asym_model(df, xcol="d_sp90", ycol="d_ap", kommune_fe=False, extra=None, min_periods=1):
    d = df.dropna(subset=[ycol, xcol]).copy()
    if len(d) < 10:
        return None
    d["pos"] = d[xcol].clip(lower=0)
    d["neg"] = d[xcol].clip(upper=0)
    terms = ["pos", "neg"]
    if d["par"].nunique() > 1:
        terms.append("C(par)")
    if kommune_fe:
        terms.append("C(kom)")
    if extra:
        d = d.dropna(subset=[extra])
        terms.append(extra)
    formula = f"{ycol} ~ " + " + ".join(terms)
    m = smf.ols(formula, data=d).fit(cov_type="cluster", cov_kwds={"groups": d["kom"]})
    bpos, bneg = m.params["pos"], m.params["neg"]
    sepos, seneg = m.bse["pos"], m.bse["neg"]
    cov = m.cov_params()
    var_asym = cov.loc["neg", "neg"] + cov.loc["pos", "pos"] - 2 * cov.loc["neg", "pos"]
    se_asym = np.sqrt(max(var_asym, 0))
    asym = bneg - bpos
    from scipy import stats as sstats
    tstat = asym / se_asym if se_asym > 0 else np.nan
    dfree = m.df_resid
    pval = 2 * (1 - sstats.t.cdf(abs(tstat), dfree)) if se_asym > 0 else np.nan
    return {
        "b_pos": {"b": round(bpos, 3), "se": round(sepos, 3),
                   "ki95": [round(bpos - 1.96 * sepos, 3), round(bpos + 1.96 * sepos, 3)],
                   "p": round(m.pvalues["pos"], 4)},
        "b_neg": {"b": round(bneg, 3), "se": round(seneg, 3),
                   "ki95": [round(bneg - 1.96 * seneg, 3), round(bneg + 1.96 * seneg, 3)],
                   "p": round(m.pvalues["neg"], 4)},
        "n": int(len(d)), "n_kom": int(d["kom"].nunique()),
        "asym_bneg_minus_bpos": {"b": round(asym, 3), "se": round(se_asym, 3),
                                   "ki95": [round(asym - 1.96 * se_asym, 3), round(asym + 1.96 * se_asym, 3)],
                                   "p": round(pval, 4) if not np.isnan(pval) else None},
        "andel_tilbake": round(bneg / bpos, 3) if bpos != 0 else None,
    }

# placebo: Ap-svak = ap_rull <= nedre kvartil, beregnet INNEN valgpar
q25_per_par = testbar.groupby("par")["ap_rull"].transform(lambda s: s.quantile(0.25))
testbar["ap_svak"] = testbar["ap_rull"] <= q25_per_par

T2 = {"sp90": {"periode_FE": {}, "kommune_FE": {}}}
groups_t2 = {
    "distrikt_bastion": testbar.gruppe == "distrikt_bastion",
    "distrikt_ikke_bastion": testbar.gruppe == "distrikt_ikke_bastion",
    "sentral": testbar.gruppe == "sentral",
    "alle_distrikt": testbar.distrikt,
    "alle": pd.Series(True, index=testbar.index),
    "placebo_ap_svake_distrikt": testbar.ap_svak & testbar.distrikt,
    "placebo_ap_svake_alle": testbar.ap_svak,
}
for variant, kfe in [("periode_FE", False), ("kommune_FE", True)]:
    for g, mask in groups_t2.items():
        T2["sp90"][variant][g] = asym_model(testbar[mask], kommune_fe=kfe)
    T2["sp90"][variant]["distrikt_bastion_bef_kontroll"] = asym_model(
        testbar[testbar.gruppe == "distrikt_bastion"], kommune_fe=kfe, extra="dlog_bef")

# delperioder (periode_FE, ingen kommune-FE) for 1953-1989 og 1989-2025, 3 grupper
T2["sp90"]["delperioder"] = {}
for lbl, lo, hi in [("1953-1989", 1953, 1985), ("1989-2025", 1989, 2021)]:
    T2["sp90"]["delperioder"][lbl] = {}
    sub = testbar[(testbar.t0 >= lo) & (testbar.t0 <= hi)]
    for g in ["distrikt_bastion", "distrikt_ikke_bastion", "sentral"]:
        T2["sp90"]["delperioder"][lbl][g] = asym_model(sub[sub.gruppe == g], kommune_fe=False)

# 1953-1989_uten_felleslister: utvalg begrenset til kommune-aar UTEN felleslister
# (fl0==0 og fl1==0, dvs. gruppe 90 fantes ikke der/da), d_sp90 (=d_sp naar fl=0) som x.
sub89 = testbar[(testbar.t0 >= 1953) & (testbar.t0 <= 1985)]
mask_no_fl = (sub89["fl0"] == 0) & (sub89["fl1"] == 0)
sub89_nofl = sub89[mask_no_fl]
T2["sp90"]["1953-1989_uten_felleslister"] = {}
for g in ["distrikt_bastion", "distrikt_ikke_bastion", "sentral"]:
    T2["sp90"]["1953-1989_uten_felleslister"][g] = asym_model(
        sub89_nofl[sub89_nofl.gruppe == g], xcol="d_sp90", kommune_fe=False)

json.dump(T2, open(f"{OUT}/_debug_t2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("T2 sp90 ferdig")

# =====================================================================
# T3: dose-respons, tverrsnitt
# =====================================================================
def get_pct(kom, aar, p):
    try:
        return pct_idx.loc[(kom, aar), p]
    except KeyError:
        return np.nan

def t3_block(base_par, dose_t0, dose_t1, end_years, group_defs):
    base = testbar[testbar.par == base_par].set_index("kom")
    out = {}
    for gname, mask_fn in group_defs.items():
        sub = base[mask_fn(base)].copy()
        sub["dose"] = sub["ap0"]*0 + (sub.index.map(lambda k: get_pct(k, dose_t1, "sp90") - get_pct(k, dose_t0, "sp90")))
        sub["ap0v"] = sub.index.map(lambda k: get_pct(k, dose_t0, "ap"))
        entry = {"n": int(len(sub)), "dose_snitt": round(sub["dose"].mean(), 2)}
        for Y in end_years:
            sub["y_ap"] = sub.index.map(lambda k: get_pct(k, Y, "ap")) - sub["ap0v"]
            sub["y_sp90"] = sub.index.map(lambda k: get_pct(k, Y, "sp90")) - sub.index.map(lambda k: get_pct(k, dose_t0, "sp90"))
            sub["bY"] = sub.index.map(lambda k: bef_naermest(k, Y))
            sub["b0"] = sub.index.map(lambda k: bef_naermest(k, dose_t0))
            sub["z"] = 100 * np.log(sub["bY"] / sub["b0"])
            d = sub.dropna(subset=["dose", "ap0v", "z", "y_ap"])
            if len(d) < 10:
                continue
            res_y = {}
            for yv in ["y_ap", "y_sp90"]:
                X = sm.add_constant(d[["dose", "ap0v", "z"]])
                m = sm.OLS(d[yv], X).fit(cov_type="HC1")
                b, se = m.params["dose"], m.bse["dose"]
                res_y["ap" if yv == "y_ap" else "sp90"] = {
                    "b": round(b, 3), "se": round(se, 3),
                    "ki95": [round(b - 1.96*se, 3), round(b + 1.96*se, 3)], "p": round(m.pvalues["dose"], 4)}
            m0 = sm.OLS(d["y_ap"], sm.add_constant(d["dose"])).fit(cov_type="HC1")
            res_y["ap_uten_kontroll"] = round(m0.params["dose"], 3)
            entry[f"til_{Y}"] = res_y
        out[gname] = entry
    return out

groupdefs_8993 = {
    "alle_distrikt": lambda b: b["distrikt"],
    "distrikt_bastion_rull": lambda b: b["distrikt"] & b["bastion"],
    "distrikt_bastion_fast": lambda b: b["distrikt"] & b["bastion_fast"],
    "sentral": lambda b: ~b["distrikt"],
}
T3 = {}
T3["1989-1993"] = t3_block("1989-1993", 1989, 1993, [1993, 1997, 2001, 2005, 2009, 2013], groupdefs_8993)

groupdefs_1321 = {
    "alle_distrikt": lambda b: b["distrikt"],
    "distrikt_bastion_rull": lambda b: b["distrikt"] & b["bastion"],
    "distrikt_bastion_fast": lambda b: b["distrikt"] & b["bastion_fast"],
    "sentral": lambda b: ~b["distrikt"],
}
T3["2013-2021"] = t3_block("2013-2017", 2013, 2021, [2017, 2021, 2025], groupdefs_1321)

json.dump(T3, open(f"{OUT}/_debug_t3.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("T3 ferdig")

# =====================================================================
# T4: hendelsesstudie, Ap relativt til landet, normert til baseline-aar
#     (kun ap-seriene, jf. brief pkt 1)
# =====================================================================
def ap_rel(kom, aar):
    v = get_pct(kom, aar, "ap")
    if pd.isna(v):
        return np.nan
    n = nat_pct2.loc[nat_pct2.aar == aar, "ap"]
    if len(n) == 0:
        return np.nan
    return v - float(n.values[0])

def t4_block(base_par, dose_t0, dose_t1, baseline_year, years, mask_fn):
    base = testbar[testbar.par == base_par].set_index("kom")
    sub = base[mask_fn(base)].copy()
    sub["dose"] = sub.index.map(lambda k: get_pct(k, dose_t1, "sp90") - get_pct(k, dose_t0, "sp90"))
    sub = sub.dropna(subset=["dose"])
    if len(sub) < 4:
        return {"n": int(len(sub)), "merknad": "for faa kommuner"}
    med = sub["dose"].median()
    hi = sub[sub["dose"] >= med]
    lo = sub[sub["dose"] < med]
    out = {}
    for lbl, grp in [("høy_dose", hi), ("lav_dose", lo)]:
        entry = {"n": int(len(grp)), "dose_snitt": round(grp["dose"].mean(), 2)}
        ap_series = {}
        base_vals = {k: ap_rel(k, baseline_year) for k in grp.index}
        for Y in years:
            vals = [ap_rel(k, Y) - base_vals[k] for k in grp.index
                    if not pd.isna(ap_rel(k, Y)) and not pd.isna(base_vals[k])]
            ap_series[str(Y)] = round(float(np.mean(vals)), 2) if vals else None
        entry["ap"] = ap_series
        out[lbl] = entry
    out["ap_høy_minus_lav"] = {str(Y): round(out["høy_dose"]["ap"][str(Y)] - out["lav_dose"]["ap"][str(Y)], 2)
                                 for Y in years}
    return out

T4 = {"1993": {}, "2021": {}}
T4["1993"]["bastion"] = t4_block("1989-1993", 1989, 1993, 1989,
                                  [1981, 1985, 1989, 1993, 1997, 2001, 2005, 2009],
                                  lambda b: b["distrikt"] & b["bastion"])
T4["1993"]["bastion_fast"] = t4_block("1989-1993", 1989, 1993, 1989,
                                       [1981, 1985, 1989, 1993, 1997, 2001, 2005, 2009],
                                       lambda b: b["distrikt"] & b["bastion_fast"])
base_2021 = testbar[testbar.par == "2013-2017"].set_index("kom")
n_bastion_2021 = int((base_2021["distrikt"] & base_2021["bastion"]).sum())
T4["2021"]["bastion"] = {"n": n_bastion_2021, "merknad": "for faa kommuner"}
T4["2021"]["bastion_fast"] = t4_block("2013-2017", 2013, 2021, 2013,
                                       [2005, 2009, 2013, 2017, 2021, 2025],
                                       lambda b: b["distrikt"] & b["bastion_fast"])

json.dump(T4, open(f"{OUT}/_debug_t4.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("T4 (ap-seriene) ferdig")

# =====================================================================
# T5: Pedersen-indeks, foer/etter, DiD (kun did_ped90 og median_deling, jf. brief)
# =====================================================================
PARTS_PED90 = ["ap", "frp", "h", "krf", "sp90", "sv", "v", "mdg", "nkp", "rodt", "andre"]
PARTS_PED_UTEN_SP = ["ap", "frp", "h", "krf", "sv", "v", "mdg", "nkp", "rodt", "andre"]
panel["ped90"] = 0.5 * sum(panel[f"d_{p}"].abs() for p in PARTS_PED90)
panel["ped_uten_sp"] = 0.5 * sum(panel[f"d_{p}"].abs() for p in PARTS_PED_UTEN_SP)

FOR_PAR = ["1973-1977", "1977-1981", "1981-1985", "1985-1989"]
ETTER_PAR = ["1997-2001", "2001-2005", "2005-2009", "2009-2013"]

base8993 = testbar[testbar.par == "1989-1993"].set_index("kom")

def t5_grupper(dosegrense_mode="fast10"):
    b = base8993
    is_bastion_distr = b["distrikt"] & b["bastion"]
    if dosegrense_mode == "fast10":
        grense = 10.0
    else:
        grense = b.loc[is_bastion_distr, "d_sp90"].median()
    rammet = is_bastion_distr & (b["d_sp90"] >= grense)
    lav = is_bastion_distr & (b["d_sp90"] < grense)
    ikke_bastion = b["distrikt"] & ~b["bastion"]
    sentral = ~b["distrikt"]
    return {
        "rammet_bastion": set(b.index[rammet]),
        "a_bastion_lav_dose": set(b.index[lav]),
        "b_distrikt_ikke_bastion": set(b.index[ikke_bastion]),
        "c_sentral": set(b.index[sentral]),
        "dosegrense": round(grense, 2),
    }

def t5_did(grupper, yvar):
    fp = panel[panel.par.isin(FOR_PAR + ETTER_PAR)].copy()
    fp["post"] = fp["par"].isin(ETTER_PAR).astype(int)
    out = {}
    for mot in ["a_bastion_lav_dose", "b_distrikt_ikke_bastion", "c_sentral"]:
        koms = grupper["rammet_bastion"] | grupper[mot]
        d = fp[fp.kom.isin(koms)].copy()
        d["beh"] = d["kom"].isin(grupper["rammet_bastion"]).astype(int)
        d = d.dropna(subset=[yvar])
        try:
            m = smf.ols(f"{yvar} ~ beh*post + C(par) + C(kom)", data=d).fit(
                cov_type="cluster", cov_kwds={"groups": d["kom"]})
            b_, se_ = m.params["beh:post"], m.bse["beh:post"]
            out[f"mot_{mot}"] = {"b": round(b_, 3), "se": round(se_, 3),
                                   "ki95": [round(b_ - 1.96*se_, 3), round(b_ + 1.96*se_, 3)],
                                   "p": round(m.pvalues["beh:post"], 4), "n": int(len(d))}
        except Exception as e:
            out[f"mot_{mot}"] = {"error": str(e), "n": int(len(d))}
    return out

def t5_snitt(grupper):
    out = {}
    for yvar in ["ped90", "ped_uten_sp"]:
        out[yvar] = {}
        for g, koms in grupper.items():
            if g == "dosegrense":
                continue
            f_ = panel[(panel.par.isin(FOR_PAR)) & (panel.kom.isin(koms))][yvar].mean()
            e_ = panel[(panel.par.isin(ETTER_PAR)) & (panel.kom.isin(koms))][yvar].mean()
            out[yvar][g] = {"før": round(f_, 2), "etter": round(e_, 2), "endring": round(e_ - f_, 2)}
    return out

g_hoved = t5_grupper("fast10")
T5 = {
    "n_grupper": {k: len(v) for k, v in g_hoved.items() if k != "dosegrense"},
    "dosegrense": g_hoved["dosegrense"],
    "snitt": t5_snitt(g_hoved),
    "did_ped90": t5_did(g_hoved, "ped90"),
    "did_ped_uten_sp": t5_did(g_hoved, "ped_uten_sp"),
}
g_med = t5_grupper("median")
T5["median_deling"] = {
    "n_grupper": {k: len(v) for k, v in g_med.items() if k != "dosegrense"},
    "dosegrense": g_med["dosegrense"],
    "snitt": t5_snitt(g_med),
    "did_ped90": t5_did(g_med, "ped90"),
    "did_ped_uten_sp": t5_did(g_med, "ped_uten_sp"),
}

json.dump(T5, open(f"{OUT}/_debug_t5.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("T5 (did_ped90, median_deling) ferdig")

# =====================================================================
# T6: andel_av_tap_til i tilbakefallsparene 1993-1997 og 2021-2025
# =====================================================================
def t6_block(par):
    d = testbar[testbar.par == par]
    out = {}
    for g, mask in [("alle_distrikt", d.distrikt),
                     ("distrikt_bastion_fast", d.distrikt & d.bastion_fast),
                     ("sentral", ~d.distrikt)]:
        sub = d[mask]
        entry = {"n": int(len(sub)), "snitt_d_sp90": round(sub["d_sp90"].mean(), 2)}
        andel, snitt_d = {}, {}
        for q in ["ap", "frp", "h", "krf", "sv", "v", "rodt", "mdg", "nkp", "andre"]:
            r = ols_hc1(sub, f"d_{q}", "d_sp90")
            andel[q] = round(-r["b"], 3) if r else None
            snitt_d[q] = round(sub[f"d_{q}"].mean(), 2)
        entry["andel_av_tap_til"] = andel
        entry["snitt_d"] = snitt_d
        out[g] = entry
    return out

T6 = {"1993-1997": t6_block("1993-1997"), "2021-2025": t6_block("2021-2025")}
json.dump(T6, open(f"{OUT}/_debug_t6.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("T6 ferdig")

# =====================================================================
# Punkt 2 i brief: grensevalg som driver resultatet
# =====================================================================
def t1_1993_distrikt_bastion(sent_klasser, bastion_grense, xcol):
    d = testbar[testbar.par == "1989-1993"].copy()
    d["distrikt_v"] = d["sent"].isin(sent_klasser)
    d["bastion_v"] = d["ap_rull"] >= bastion_grense
    sub = d[d.distrikt_v & d.bastion_v]
    return ols_hc1(sub, "d_ap", xcol)

def t2_asym_distrikt_bastion(sent_klasser, bastion_grense, xcol, drop_last=False):
    d = testbar.copy()
    if drop_last:
        d = d[d.par != "2021-2025"]
    d["distrikt_v"] = d["sent"].isin(sent_klasser)
    d["bastion_v"] = d["ap_rull"] >= bastion_grense
    sub = d[d.distrikt_v & d.bastion_v]
    return asym_model(sub, xcol=xcol, kommune_fe=False)

def t5_did_hoved(sent_klasser, bastion_grense, dosegrense, xcol):
    b = testbar[testbar.par == "1989-1993"].set_index("kom").copy()
    b["distrikt_v"] = b["sent"].isin(sent_klasser)
    b["bastion_v"] = b["ap_rull"] >= bastion_grense
    is_bast = b["distrikt_v"] & b["bastion_v"]
    rammet = is_bast & (b[xcol] >= dosegrense)
    ikke_bastion = b["distrikt_v"] & ~b["bastion_v"]
    grupper = {"rammet_bastion": set(b.index[rammet]),
               "b_distrikt_ikke_bastion": set(b.index[ikke_bastion])}
    fp = panel[panel.par.isin(FOR_PAR + ETTER_PAR)].copy()
    fp["post"] = fp["par"].isin(ETTER_PAR).astype(int)
    koms = grupper["rammet_bastion"] | grupper["b_distrikt_ikke_bastion"]
    d = fp[fp.kom.isin(koms)].copy()
    d["beh"] = d["kom"].isin(grupper["rammet_bastion"]).astype(int)
    try:
        m = smf.ols("ped90 ~ beh*post + C(par) + C(kom)", data=d).fit(
            cov_type="cluster", cov_kwds={"groups": d["kom"]})
        return {"b": round(m.params["beh:post"], 3), "p": round(m.pvalues["beh:post"], 4),
                "n_rammet": len(grupper["rammet_bastion"]), "n_mot": len(grupper["b_distrikt_ikke_bastion"])}
    except Exception as e:
        return {"error": str(e)}

GRENSEVALG = []
base_case = dict(sent=[5, 6], bastion=50.0, dose=10.0, x="d_sp90")
variants = [
    ("hovedvariant", dict(base_case)),
    ("bastion_40", dict(base_case, bastion=40.0)),
    ("bastion_45", dict(base_case, bastion=45.0)),
    ("bastion_55", dict(base_case, bastion=55.0)),
    ("bastion_60", dict(base_case, bastion=60.0)),
    ("distrikt_4_6", dict(base_case, sent=[4, 5, 6])),
    ("lokal_dose_5", dict(base_case, dose=5.0)),
    ("lokal_dose_15", dict(base_case, dose=15.0)),
    ("sp_alene", dict(base_case, x="d_sp")),
]
for name, v in variants:
    t1 = t1_1993_distrikt_bastion(v["sent"], v["bastion"], v["x"])
    t2 = t2_asym_distrikt_bastion(v["sent"], v["bastion"], v["x"])
    t5 = t5_did_hoved(v["sent"], v["bastion"], v["dose"], v["x"].replace("d_", "d_") if v["x"] == "d_sp90" else "d_sp")
    GRENSEVALG.append({
        "variant": name,
        "T1_1993_distrikt_bastion_b": t1["b"] if t1 else None,
        "T1_1993_n": t1["n"] if t1 else None,
        "T2_asym_b": t2["asym_bneg_minus_bpos"]["b"] if t2 else None,
        "T2_asym_p": t2["asym_bneg_minus_bpos"]["p"] if t2 else None,
        "T5_did_b_mot_ikke_bastion": t5.get("b"),
        "T5_did_p": t5.get("p"),
    })
# uten 2021-2025 (kun relevant for T2, siden T1/T5-hovedparet er 1989-1993)
t2_u = t2_asym_distrikt_bastion([5, 6], 50.0, "d_sp90", drop_last=True)
GRENSEVALG.append({
    "variant": "uten_2021-2025_T2_only",
    "T2_asym_b": t2_u["asym_bneg_minus_bpos"]["b"], "T2_asym_p": t2_u["asym_bneg_minus_bpos"]["p"],
})

json.dump(GRENSEVALG, open(f"{OUT}/_debug_grensevalg.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("Grensevalg ferdig")
for row in GRENSEVALG:
    print(row)

# =====================================================================
# Punkt 3: forbedret placebo mot regresjon mot gjennomsnittet
#  - "falskt bolgeaar": bruk d_sp90 fra NESTE valgpar (t1->t2) i stedet for
#    det samtidige paret (t0->t1) som forklaringsvariabel for d_ap i t0->t1.
#    Hvis dette gir samme sterke asymmetri, svekker det tolkningen.
# =====================================================================
panel_sorted = panel.sort_values(["kom", "t0"]).reset_index(drop=True)
panel_sorted["d_sp90_neste"] = panel_sorted.groupby("kom")["d_sp90"].shift(-1)
testbar_fake = testbar.merge(
    panel_sorted[["kom", "t0", "d_sp90_neste"]], on=["kom", "t0"], how="left")

fake_placebo = asym_model(
    testbar_fake[testbar_fake.gruppe == "distrikt_bastion"].dropna(subset=["d_sp90_neste"]),
    xcol="d_sp90_neste", kommune_fe=False)

json.dump({"falskt_bolgeaar_placebo_distrikt_bastion": fake_placebo},
          open(f"{OUT}/_debug_placebo2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("Placebo (falskt bolgeaar) ferdig:", fake_placebo["asym_bneg_minus_bpos"] if fake_placebo else None,
      "b_pos", fake_placebo["b_pos"] if fake_placebo else None)
