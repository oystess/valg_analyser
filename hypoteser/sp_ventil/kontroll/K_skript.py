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
    for p in ["sp", "ap", "h", "v", "krf", "frp", "sv", "nkp", "hvk"]:
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
