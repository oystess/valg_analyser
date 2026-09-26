#!/usr/bin/env python3
"""
analyse/motreaksjon_las.py – Låser operasjonaliseringen av «Høyre-mobilisering → Sp-motreaksjon»
(hypoteser/motreaksjon/PROMPT.md §3–4) FØR episodene ses. Skriver hypoteser/motreaksjon/låst.json
med tidspunkt og sha256 av panelene. Kjøres én gang; analyse/motreaksjon_kjor.py nekter å kjøre
hvis panelene er endret.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent
MAPPE = ROT / "hypoteser" / "motreaksjon"
PANELER = {"ST": ROT / "turnering" / "data" / "panel.csv", "KV": MAPPE / "data" / "kv_panel.csv"}

ST_PER = ["1989-1993", "1993-1997", "1997-2001", "2001-2005", "2005-2009", "2009-2013", "2013-2017",
          "2017-2021", "2021-2025"]
KV_PER = ["1987-1991", "1991-1995", "1995-1999", "1999-2003", "2003-2007", "2007-2011", "2011-2015",
          "2015-2019", "2019-2023"]


def par(perioder):
    return [[perioder[i], perioder[i + 1]] for i in range(len(perioder) - 1)]


SETT = [["ST", "2009-2013", "2013-2017"]]

LÅST = {
    "hypotese": ("I valg t mobiliserer Høyre i vekstkommuner (Høyres endring henger positivt sammen med "
                 "befolkningsvekst). I valget etter (t+1) går Sp mest fram i kommuner med nedgang."),
    "sett_episode": {"par": SETT, "rolle": "bare illustrasjon – hypotesen er formulert etter å ha sett den; "
                                            "inngår ikke i Holm-familien eller i tellingen av testpar"},
    "periodepar": {"ST": par(ST_PER), "KV": par(KV_PER)},
    "hovedutvalg_av_par": ("Par der vekst10_pst finnes i periode t (ST: t fra 1993–1997, KV: t fra 1995–1999; "
                           "befolkning finnes fra 1986). Det gir 7 ST-par (6 test + 1 sett) og 6 KV-par. "
                           "Første par i hvert valgslag kjøres bare i sensitivitet med vekst4_pst."),
    "spesifikasjoner": {
        "P1": {"formel": "d_h ~ vekst10_pst + h_t0 + sent_indeks", "nøkkelledd": "vekst10_pst",
               "forventet_fortegn": "+", "vekt": "vekt_stemmer_t0", "utvalg": "periode == '{t}'"},
        "P2": {"formel": "d_sp ~ vekst10_pst + sp_t0 + sent_indeks", "nøkkelledd": "vekst10_pst",
               "forventet_fortegn": "-", "vekt": "vekt_stemmer_t0", "utvalg": "periode == '{t1}'"},
        "P2_ap": {"formel": "d_sp ~ vekst10_pst + sp_t0 + sent_indeks + d_ap_forrige + ap_t0",
                  "nøkkelledd": "vekst10_pst", "forventet_fortegn": "-", "vekt": "vekt_stemmer_t0",
                  "merknad": "konkurrent (b); kjøres på parfilen (t+1-rader med t-verdier som *_forrige)"},
        "P4": {"formel": "d_sp ~ h_resid_forrige + sp_t0 + sent_indeks + vekst10_pst + C(periode)",
               "nøkkelledd": "h_resid_forrige", "vekt": "vekt_stemmer_t0",
               "versjoner": {"P4A": {"forventet_fortegn": "-",
                                     "tekst": "Sp går mer fram i t+1 der Høyre gikk MINDRE fram i t enn veksten tilsier"},
                             "P4B": {"forventet_fortegn": "+",
                                     "tekst": "Sp går mer fram i t+1 der Høyre gikk MER fram i t enn veksten tilsier"}},
               "h_resid": ("residual fra P1-modellen (vektet) i periode t for kommunen; "
                           "slått sammen med periode t+1 på kom2024"),
               "utvalg": "alle testpar i valgslaget samlet (periode = t+1-perioden, faste effekter per par)"},
        "P4_ap": {"formel": "d_sp ~ h_resid_forrige + sp_t0 + sent_indeks + vekst10_pst + d_ap_forrige + ap_t0 + C(periode)",
                  "merknad": "konkurrent (b)"},
        "P4_rtm": {"formel": "d_sp ~ h_resid_forrige + sp_t0 + sent_indeks + vekst10_pst + d_sp_forrige + C(periode)",
                   "merknad": "konkurrent (a): regresjon mot middelverdien via Sps egen endring i t"},
        "reform": {"formel": "P2 og P4 med + reform_2017_20",
                   "merknad": "konkurrent (c), for par der t+1 er ST 2017–2021, KV 2015–2019 eller KV 2019–2023"},
        "sensitivitet_vekst4": "P1 og P2 med vekst4_pst i stedet for vekst10_pst, alle 8 par i hvert valgslag",
    },
    "standardfeil": "klyngerobuste på kommune (analyse/modeller.py::kjør)",
    "batteri": ("hoved (vektet), uvektet, uten estimerte kommuner, ett og ett fylke utelatt (15); "
                "for samlede P4 også ett og ett par utelatt"),
    "holm_familie": ("P1 i hvert testpar (6 ST + 6 KV), P2 i hvert testpar (6 + 6) og samlet P4 per valgslag (2) "
                     "= 26 tester. Tosidige p-verdier. P4A og P4B er samme koeffisient med motsatt forventet "
                     "fortegn og teller som én test per valgslag."),
    "status_regler": {
        "test_robust": ("Holm-justert p < 0,05 i hoved OG forventet fortegn i hoved, uvektet, uten estimerte og "
                        "alle uten_fylke (og alle uten_par for P4)"),
        "par_støtter": "P1 i t og P2 i t+1 er begge robuste",
        "P1_P2_mønster": ("støttet: par_støtter i flertallet (≥ 4 av 6) av testparene i BÅDE ST og KV; "
                          "delvis: flertall i ett valgslag, eller ≥ 7 av 12 samlet; ellers ikke støttet"),
        "spesifisitet": ("beskrivende: andel par med robust P2 blant par med robust P1, mot andelen blant par "
                         "uten robust P1. Hypotesen forutsier høyere andel i første gruppe."),
        "P3": ("beskrivende: Pearson- og Spearman-korrelasjon mellom b_P1(t) og b_P2(t+1) over testparene, "
               "per valgslag og samlet. Forventet negativ. Ingen signifikanspåstand. 'støttet (beskrivende)' "
               "hvis negativ i begge valgslag, 'delvis' hvis negativ i ett eller bare samlet."),
        "P4": ("støttet: samme versjon (A eller B) robust i begge valgslag; delvis: robust i ett, "
               "eller samme fortegn i begge uten robusthet; ikke støttet ellers"),
        "P5": ("beskrivende: Høyre i regjering i t+1 = Høyre med i regjeringen i minst halvparten av tiden "
               "mellom valgdagen som avslutter t og valgdagen som avslutter t+1 (valgdag tilnærmet 10. sept.). "
               "Sammenlign snitt b_P2(t+1) og P3-korrelasjon med og uten Høyre i regjering, per valgslag. "
               "'støttet (beskrivende)' hvis Sp-gradienten er mer negativ med Høyre i regjering i begge valgslag."),
    },
    "konkurrenter": {
        "a": "Sps nasjonale bølge slår ut der Sp står sterkt / regresjon mot middel: P4_rtm, og på parnivå b_P2(t+1) mot nasjonal Sp-endring i t+1",
        "b": "Ap-tap: P2_ap og P4_ap, og på parnivå b_P2(t+1) mot Ap-gradienten i t",
        "c": "Reform uavhengig av Høyres valgresultat: reform_2017_20-kontroll i P2/P4 for de aktuelle parene",
    },
}


def main():
    ut = MAPPE / "låst.json"
    if ut.exists():
        raise SystemExit("låst.json finnes allerede – låsen skal ikke skrives på nytt.")
    LÅST["låst_tidspunkt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    LÅST["panel_sha256"] = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in PANELER.items()}
    json.dump(LÅST, open(ut, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(ut, LÅST["låst_tidspunkt"], LÅST["panel_sha256"])


if __name__ == "__main__":
    main()
