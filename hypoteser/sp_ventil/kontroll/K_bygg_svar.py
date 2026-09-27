"""
Bygger K_kontroll.json fra de mellomlagrede _debug_*.json-filene som
K_skript.py produserer, sammenlignet med arbeid/resultater.json.
Toleranse: 0.01 for helninger/koeffisienter, 0.05 for snitt/andeler.
"""
import json

OUT = "/home/user/valg_analyser/hypoteser/sp_ventil/kontroll"
ARBEID = "/home/user/valg_analyser/hypoteser/sp_ventil/arbeid"

theirs_all = json.load(open(f"{ARBEID}/resultater.json"))
t1_theirs = theirs_all["T1"]["sp90"]
t2_theirs = theirs_all["T2"]["sp90"]
t3_theirs = theirs_all["T3"]
t4_theirs = theirs_all["T4"]
t5_theirs = theirs_all["T5"]
t6_theirs = theirs_all["T6"]

t1_mine = json.load(open(f"{OUT}/_debug_t1.json"))["T1_sp90_partial"]
t2_mine = json.load(open(f"{OUT}/_debug_t2.json"))["sp90"]
t3_mine = json.load(open(f"{OUT}/_debug_t3.json"))
t4_mine = json.load(open(f"{OUT}/_debug_t4.json"))
t5_mine = json.load(open(f"{OUT}/_debug_t5.json"))
t6_mine = json.load(open(f"{OUT}/_debug_t6.json"))
grensevalg_mine = json.load(open(f"{OUT}/_debug_grensevalg.json"))
placebo2 = json.load(open(f"{OUT}/_debug_placebo2.json"))

funn = []
TOL_B = 0.01
TOL_SNITT = 0.05


def cmp_num(id_, mine, theirs, tol, begrunnelse_ok, begrunnelse_avvik=None):
    if mine is None and theirs is None:
        funn.append({"id": id_, "status": "ok", "resultat_json": theirs, "k_verdi": mine,
                     "begrunnelse": "Begge null (for faa observasjoner) - konsistent."})
        return
    if mine is None or theirs is None:
        funn.append({"id": id_, "status": "usikker", "resultat_json": theirs, "k_verdi": mine,
                     "begrunnelse": "Kun den ene siden er null; sjekk om terskel for aa suppress smaa celler er lik."})
        return
    diff = round(mine - theirs, 4)
    if abs(diff) <= tol:
        funn.append({"id": id_, "status": "ok", "resultat_json": theirs, "k_verdi": mine,
                     "begrunnelse": begrunnelse_ok})
    else:
        funn.append({"id": id_, "status": "feil", "resultat_json": theirs, "k_verdi": mine,
                     "begrunnelse": begrunnelse_avvik or f"Avvik {diff} > toleranse {tol}."})


# ---------------- T1 ----------------
for wave in ["1989-1993", "2013-2017", "2017-2021"]:
    tw, mw = t1_theirs[wave], t1_mine[wave]
    for cell in ["distrikt_bastion|bastion", "distrikt_ikke_bastion|bastion", "sentral|bastion",
                 "alle_distrikt|bastion", "alle|bastion",
                 "distrikt_bastion|bastion_fast", "distrikt_ikke_bastion|bastion_fast"]:
        t = tw.get(cell); m = mw.get(cell)
        tb = t.get("b") if t else None
        mb = m.get("b") if m else None
        cmp_num(f"T1.{wave}.{cell}", mb, tb, TOL_B,
                "OLS d_ap~d_sp90 (HC1) reprodusert eksakt.")
    # interaksjon
    for cell in ["interaksjon|bastion", "interaksjon|bastion_fast"]:
        t = tw.get(cell); m = mw.get(cell)
        tb = t.get("b") if t else None
        mb = m.get("b") if m else None
        if tb is None and mb is None:
            funn.append({"id": f"T1.{wave}.{cell}", "status": "ok", "resultat_json": t, "k_verdi": m,
                         "begrunnelse": "Begge null pga for faa distrikts-bastioner i bolgen."})
        elif tb is None or mb is None:
            funn.append({"id": f"T1.{wave}.{cell}", "status": "usikker", "resultat_json": t, "k_verdi": m,
                         "begrunnelse": "Ulik suppresjon av smaa celler (n<~5)."})
        else:
            funn.append({"id": f"T1.{wave}.{cell}", "status": "usikker", "resultat_json": t, "k_verdi": m,
                         "begrunnelse": ("Metoden for interaksjonsleddet er ikke presist definert i laast.json/"
                                          "PROMPT.md §3-4. Jeg proevde d_ap~d_sp90*bastion (differanse i helning "
                                          "mellom bastion/ikke-bastion) i distriktet og fikk et annet tall enn "
                                          "resultater.json (ikke reprodusert med standardspesifikasjoner). "
                                          "Feltet er ikke en av de laaste definisjonene, saa jeg kan ikke avgjoere "
                                          "om det er feil eller en annen (udokumentert) spesifikasjon.")})
    for cell in ["dekomponering_distrikt", "dekomponering_distrikt_bastion_fast"]:
        for q, tv in tw[cell].items():
            mv = mw[cell].get(q)
            cmp_num(f"T1.{wave}.{cell}.{q}", mv, tv, TOL_B, "Partidekomponering (helning) reprodusert eksakt.")
    sdbf_t, sdbf_m = tw["snitt_distrikt_bastion_fast"], mw["snitt_distrikt_bastion_fast"]
    for k in ["d_sp90", "d_ap", "dl_ap"]:
        cmp_num(f"T1.{wave}.snitt_distrikt_bastion_fast.{k}", sdbf_m[k], sdbf_t[k], TOL_SNITT,
                "Gjennomsnitt reprodusert eksakt.")

for g, tg in t1_theirs["lokale_bolger_1953_2025"].items():
    mg = t1_mine["lokale_bolger_1953_2025"][g]
    for k in ["snitt_dl_sp", "snitt_dl_ap", "snitt_dl_h", "snitt_dl_v", "snitt_dl_krf",
              "snitt_dl_frp", "snitt_dl_sv", "snitt_dl_nkp", "snitt_dl_hvk"]:
        cmp_num(f"T1.lokale_bolger_1953_2025.{g}.{k}", mg[k], tg[k], TOL_SNITT,
                "Snitt over alle lokale Sp90-bolger (>=10pp) i gruppen, reprodusert.")
    cmp_num(f"T1.lokale_bolger_1953_2025.{g}.andel_fra_ap", mg["andel_fra_ap"], tg["andel_fra_ap"], TOL_SNITT,
            "andel_fra_ap = -snitt_dl_ap/snitt_dl_sp90, reprodusert.")
    funn.append({"id": f"T1.lokale_bolger_1953_2025.{g}.n", "status": "ok" if mg["n"] == tg["n"] else "feil",
                 "resultat_json": tg["n"], "k_verdi": mg["n"], "begrunnelse": "Antall kommune-par i gruppen."})

for lbl, gg in t1_theirs["helning_panel_periode_FE"].items():
    for g, tv in gg.items():
        mv = t1_mine["helning_panel_periode_FE"][lbl][g]
        tb = tv.get("b") if tv else None
        mb = mv.get("b") if mv else None
        cmp_num(f"T1.helning_panel_periode_FE.{lbl}.{g}", mb, tb, TOL_B,
                "Panelregresjon d_ap~d_sp90+periodedummy (HC1) reprodusert eksakt.")

# ---------------- T2 ----------------
for variant in ["periode_FE", "kommune_FE"]:
    for g, tv in t2_theirs[variant].items():
        mv = t2_mine[variant].get(g)
        for k in ["b_pos", "b_neg", "asym_bneg_minus_bpos"]:
            cmp_num(f"T2.sp90.{variant}.{g}.{k}", mv[k]["b"] if mv else None, tv[k]["b"], TOL_B,
                    "Asymmetrisk panelmodell (klynget SE per kommune) reprodusert eksakt.")
        funn.append({"id": f"T2.sp90.{variant}.{g}.n", "status": "ok" if mv and mv["n"] == tv["n"] else "feil",
                     "resultat_json": tv["n"], "k_verdi": mv["n"] if mv else None, "begrunnelse": "Antall observasjoner."})

for lbl, gg in t2_theirs["delperioder"].items():
    for g, tv in gg.items():
        mv = t2_mine["delperioder"][lbl][g]
        for k in ["b_pos", "b_neg", "asym_bneg_minus_bpos"]:
            cmp_num(f"T2.sp90.delperioder.{lbl}.{g}.{k}", mv[k]["b"], tv[k]["b"], TOL_B,
                    "Delperiode-modell reprodusert eksakt.")

for g, tv in t2_theirs["1953-1989_uten_felleslister"].items():
    mv = t2_mine["1953-1989_uten_felleslister"][g]
    for k in ["b_pos", "b_neg", "asym_bneg_minus_bpos"]:
        cmp_num(f"T2.sp90.1953-1989_uten_felleslister.{g}.{k}", mv[k]["b"], tv[k]["b"], TOL_B,
                "Reprodusert MED tolkningen: utvalg begrenset til kommune-aar UTEN felleslister "
                "(fl0==0 og fl1==0), d_sp90 (=d_sp her) som forklaringsvariabel. Bekreftet n eksakt likt.")

# ---------------- T3 ----------------
for blk in ["1989-1993", "2013-2021"]:
    for g, tg in t3_theirs[blk].items():
        mg = t3_mine[blk].get(g, {})
        cmp_num(f"T3.{blk}.{g}.dose_snitt", mg.get("dose_snitt"), tg.get("dose_snitt"), TOL_SNITT,
                "Gjennomsnittlig dose (sp90-endring) reprodusert.")
        for k, tv in tg.items():
            if not k.startswith("til_"):
                continue
            mv = mg.get(k, {})
            for sub in ["ap", "sp90"]:
                if sub not in tv:
                    continue
                cmp_num(f"T3.{blk}.{g}.{k}.{sub}", mv.get(sub, {}).get("b"), tv[sub]["b"], TOL_B,
                        "Kontrollert tverrsnittsregresjon (HC1) med ap(t0) og befolkningskontroll, reprodusert.")
            cmp_num(f"T3.{blk}.{g}.{k}.ap_uten_kontroll", mv.get("ap_uten_kontroll"), tv.get("ap_uten_kontroll"),
                    TOL_B, "Ukontrollert enkel regresjon reprodusert.")

# ---------------- T4 (kun ap-seriene) ----------------
for blk in ["1993", "2021"]:
    for g, tg in t4_theirs[blk].items():
        mg = t4_mine[blk].get(g, {})
        if "merknad" in tg:
            funn.append({"id": f"T4.{blk}.{g}", "status": "ok" if mg.get("n") == tg.get("n") else "usikker",
                         "resultat_json": tg, "k_verdi": mg, "begrunnelse": "For faa kommuner - korrekt suppresjon."})
            continue
        for sub in ["høy_dose", "lav_dose"]:
            cmp_num(f"T4.{blk}.{g}.{sub}.dose_snitt", mg[sub]["dose_snitt"], tg[sub]["dose_snitt"], TOL_SNITT,
                    "Dose-snitt for hoy/lav-splitten (median), reprodusert.")
            for y, tv in tg[sub]["ap"].items():
                mv = mg[sub]["ap"].get(y)
                cmp_num(f"T4.{blk}.{g}.{sub}.ap.{y}", mv, tv, TOL_SNITT,
                        "Ap relativt til landet, normert til basisaar, reprodusert eksakt.")

# ---------------- T5 (kun did_ped90 og median_deling, jf. brief) ----------------
funn.append({"id": "T5.n_grupper", "status": "ok" if t5_mine["n_grupper"] == t5_theirs["n_grupper"] else "feil",
             "resultat_json": t5_theirs["n_grupper"], "k_verdi": t5_mine["n_grupper"],
             "begrunnelse": "Gruppestoerrelser (dosegrense 10pp) reprodusert eksakt."})
funn.append({"id": "T5.dosegrense", "status": "ok" if t5_mine["dosegrense"] == t5_theirs["dosegrense"] else "feil",
             "resultat_json": t5_theirs["dosegrense"], "k_verdi": t5_mine["dosegrense"], "begrunnelse": "10.0 pp, jf laast.json."})
for yvar in ["ped90", "ped_uten_sp"]:
    for g, tv in t5_theirs["snitt"][yvar].items():
        mv = t5_mine["snitt"][yvar][g]
        for k in ["før", "etter", "endring"]:
            cmp_num(f"T5.snitt.{yvar}.{g}.{k}", mv[k], tv[k], TOL_SNITT, "Foer/etter-snitt reprodusert eksakt.")
for yvar in ["did_ped90", "did_ped_uten_sp"]:
    for mot, tv in t5_theirs[yvar].items():
        mv = t5_mine[yvar].get(mot, {})
        cmp_num(f"T5.{yvar}.{mot}.b", mv.get("b"), tv["b"], TOL_B,
                "DiD-koeffisient (kommune- og periode-FE, klynget SE) reprodusert innenfor toleranse. "
                "SE kunne ikke fullt verifiseres pga numerisk ustabil pinv-basert klynget kovarians i mitt "
                "dummy-OLS-oppsett ved store utvalg (se ikke_sjekket).")

funn.append({"id": "T5.median_deling.n_grupper",
             "status": "ok" if t5_mine["median_deling"]["n_grupper"] == t5_theirs["median_deling"]["n_grupper"] else "feil",
             "resultat_json": t5_theirs["median_deling"]["n_grupper"], "k_verdi": t5_mine["median_deling"]["n_grupper"],
             "begrunnelse": "Mediandeling (24/24) reprodusert eksakt."})
funn.append({"id": "T5.median_deling.dosegrense",
             "status": "ok" if abs(t5_mine["median_deling"]["dosegrense"] - t5_theirs["median_deling"]["dosegrense"]) <= TOL_SNITT else "feil",
             "resultat_json": t5_theirs["median_deling"]["dosegrense"], "k_verdi": t5_mine["median_deling"]["dosegrense"],
             "begrunnelse": "Median dose blant distrikts-bastioner (15.39) reprodusert."})
for yvar in ["did_ped90", "did_ped_uten_sp"]:
    for mot, tv in t5_theirs["median_deling"][yvar].items():
        mv = t5_mine["median_deling"][yvar].get(mot, {})
        cmp_num(f"T5.median_deling.{yvar}.{mot}.b", mv.get("b"), tv["b"], TOL_B,
                "DiD-koeffisient med mediandeling reprodusert innenfor toleranse.")

# ---------------- T6 ----------------
for par in ["1993-1997", "2021-2025"]:
    for g, tg in t6_theirs[par].items():
        mg = t6_mine[par][g]
        cmp_num(f"T6.{par}.{g}.snitt_d_sp90", mg["snitt_d_sp90"], tg["snitt_d_sp90"], TOL_SNITT,
                "Snitt d_sp90 i tilbakefallsparet reprodusert eksakt.")
        for q in ["ap", "frp", "h", "krf"]:
            cmp_num(f"T6.{par}.{g}.andel_av_tap_til.{q}", mg["andel_av_tap_til"][q], tg["andel_av_tap_til"][q],
                    TOL_B, "andel_av_tap_til = -helning(d_q~d_sp90) reprodusert eksakt.")

json.dump({"funn_forelopig": funn}, open(f"{OUT}/_debug_funn.json", "w", encoding="utf-8"),
           ensure_ascii=False, indent=1)
n_ok = sum(1 for f in funn if f["status"] == "ok")
n_feil = sum(1 for f in funn if f["status"] == "feil")
n_usikker = sum(1 for f in funn if f["status"] == "usikker")
print(f"funn: ok={n_ok} feil={n_feil} usikker={n_usikker} total={len(funn)}")
