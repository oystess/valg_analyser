# Brief K – uavhengig kontroll av T1–T6 (Sp som «ventil» for Ap-bastioner)

Du kontrollerer en annen agents analyse. Du har ikke sett hvordan den ble laget.
Utgangspunktet ditt er «ikke godkjent». Godkjenning må begrunnes rad for rad.

## Bakgrunn (kort)
Påstanden: I Aps distriktsbastioner tar Sp velgere fra Ap i Sp-bølgene (P1). Når Sp faller tilbake, tar Ap igjen mindre
enn partiet tapte (P2). Etter den første store bølgen blir velgerne mer flyktige (P3). Analysen er deskriptiv og bruker aggregerte kommunetall.

## INPUT (kilde)
- `/home/user/valg_analyser/data/processed/stortingsvalg_1945.csv`: kolonnene kom2024, navn, aar, parti, stemmer, total_stemmer, prosent, estimert, sikkerhet.
  Partikoder: 01 Ap, 02 FrP, 03 H, 04 KrF, 05 Sp, 06 SV, 07 V, 08 MDG, 09 NKP, 55 Rødt, 90 felleslister, 99 andre.
- `/home/user/valg_analyser/data/processed/kommunestyrevalg_1945.csv` (samme format, KV)
- `/home/user/valg_analyser/data/processed/stortingsvalg_1945_stabil.csv` (279 stabile enheter, kolonne `enhet`) og `stabile_enheter.csv`
- `/home/user/valg_analyser/data/processed/sentralitet_2024.csv` (kom2024, sent_klasse 1–6)
- `/home/user/valg_analyser/data/processed/befolkning_1951.csv` (kom2024, aar, befolkning)
- Operasjonaliseringen: `/home/user/valg_analyser/hypoteser/sp_ventil/PROMPT.md` §3 og §4, og de låste valgene i `/home/user/valg_analyser/hypoteser/sp_ventil/låst.json`.
- Dataordbok (definisjoner av kolonner, ikke kode): `/home/user/valg_analyser/hypoteser/sp_ventil/arbeid/datadictionary.md`

## RESULTAT SOM SKAL KONTROLLERES
`/home/user/valg_analyser/hypoteser/sp_ventil/arbeid/resultater.json` (nøklene T1–T6 og robusthet).

## IGNORER / IKKE LES
Ikke åpne noe under `/home/user/valg_analyser/analyse/sp_ventil/`, `arbeid/panel*.csv` eller `arbeid/t*.csv`. Du skal regne selv fra `data/processed/`.
Ikke kontroller T7, T8 eller figurene. Ikke les RAPPORT.md.

## Presise definisjoner (slik de er brukt; kontroller at de er fulgt, og regn selv)
- Andeler: stemmer per parti / sum stemmer over alle 12 grupper i kommune-år × 100. Landstall: stemmevektet (sum stemmer).
- sp90 = Sp + gruppe 90 (hele felleslisten regnes til Sp). «Sp alene» = gruppe 05.
- Valgpar t0 → t1 er påfølgende stortingsvalg. Testbare par: t0 ≥ 1953 (1945–49 er bare bakgrunn).
- Distrikt: sentralitetsklasse 5–6. Rullerende bastion for par t0→t1: snitt av Ap ved t0 og valget før t0 ≥ 50 %.
  Fast bastion: snitt Ap ST 1953, 57, 61, 65, 69 ≥ 50 %. Grupper: distrikt_bastion, distrikt_ikke_bastion, sentral.
- T1: Per nasjonal bølge (par 1989-1993, 2013-2017, 2017-2021) OLS tverrsnitt d_ap på d_sp90 per gruppe (HC1-SE).
  «dekomponering_distrikt» er helningen d_q på d_sp90 for hvert parti q i distriktet (skal summere til ca. −1).
- T2: Panel over alle testbare par. d_ap = b_pos·max(d_sp90,0) + b_neg·min(d_sp90,0) + periodedummyer (+ kommunedummyer i «kommune_FE»),
  SE klynget på kommune. asym = b_neg − b_pos (> 0 betyr at Ap tar igjen mindre enn det tapte). Placebo: rullerende Ap-snitt ≤ nedre kvartil innen valgpar.
- T3: Tverrsnitt, dose = sp90(1993) − sp90(1989). y = ap(År) − ap(1989). Kontroller: ap(1989) og 100·ln(bef(År)/bef(1989)) (befolkning ved nærmeste år ≥ 1951). HC1.
  Gruppering etter status i paret 1989-1993. Tilsvarende for dose 2013→2021 med y = ap(År) − ap(2013) og gruppering etter paret 2013-2017.
- T4: Ap og sp90 relativt til landet (kommune − landstall), normert til 1989 (for 1993) eller 2013 (for 2021). Distrikts-bastioner (rullerende i paret 1989-93 / fast for 2021)
  delt på median dose innenfor gruppen (≥ median = høy).
- T5: Pedersen «ped90» = ½·Σ|Δ| over partiene der Sp og felleslister er slått sammen til én gruppe. «ped_uten_sp» = ½·Σ|Δ| over alle partier unntatt Sp og felleslister.
  Før = par 1973-77, 77-81, 81-85, 85-89; etter = 1997-01, 01-05, 05-09, 09-13. Gruppe «rammet» = distrikt, rullerende bastion i 1989-93 og d_sp90(89→93) ≥ 10 (hovedvariant)
  eller ≥ median innen distrikts-bastionene («median_deling»). DiD: ped ~ beh:post + periodedummyer + kommunedummyer, klynget på kommune.
- T6: I tilbakefallsparene 1993-1997 og 2021-2025: «andel_av_tap_til» q = −(helning d_q på d_sp90), tverrsnitt per gruppe.

## GJØR DETTE, I REKKEFØLGE
1. Regn på nytt i Python (pandas/statsmodels er installert) fra `data/processed/` HVERT tall under T1 (alle tre bølger), T2 (sp90: periode_FE og kommune_FE, alle grupper + placebo; delperioder),
   T3 (1989-1993, alle grupper, alle sluttår), T4 (1993 og 2021, ap-seriene), T5 (did_ped90, median_deling) og T6 (andel_av_tap_til for ap, frp, h, krf).
   Sammenlign med resultater.json. Toleranse: 0,01 for helninger/koeffisienter, 0,05 for snitt. List hvert avvik.
2. Grensevalg som driver resultatet: kjør T1 (1993, distrikt_bastion), T2-asym (distrikt_bastion) og T5-DiD med alternative grenser du selv velger
   (for eksempel bastion 40/45/55/60 %, distrikt = klasse 4–6, lokal dose 5/15 pp, Sp alene i stedet for sp90, uten 2021–25). Rapporter hvilke konklusjoner som snur.
3. Placebo: sjekk at placeboen i T2 er riktig konstruert, og foreslå/kjør en bedre placebo mot regresjon mot gjennomsnittet hvis du ser en (f.eks. H-bastioner og ΔH mot ΔSp, eller falske bølgeår).
4. Negativ test/motstrid: se etter tall i resultater.json som strider mot hverandre eller mot definisjonene over (f.eks. grupper med for få kommuner som likevel brukes).
5. Konkluder først når punkt 1–4 er gjort.

## VERKTØY
Read, Grep, Bash/Python. Ingen websøk. Ikke endre filer utenom svarfilen og egne skript i `/home/user/valg_analyser/hypoteser/sp_ventil/kontroll/`.

## SVAR (skrives til `/home/user/valg_analyser/hypoteser/sp_ventil/kontroll/K_kontroll.json`, norsk bokmål)
{"funn": [{"id": "T1.1989-1993.distrikt_bastion|bastion", "status": "ok|feil|usikker", "resultat_json": ..., "k_verdi": ..., "begrunnelse": ""}, ...],
 "kriterier": [{"id": "T1".."T6", "status": "komplett|mangler", "hva_mangler": ""}],
 "grensevalg": [{"variant": "", "nøkkeltall": "", "verdi": ..., "snur_konklusjon": true/false, "kommentar": ""}],
 "placebo": {"vurdering": "", "egne_tester": [...]},
 "falske_positiver": [...], "motstrid": [...] eller "ingen funnet",
 "ikke_sjekket": [...] eller "alt sjekket",
 "konklusjon": "godkjent|ikke godkjent", "antall": {"ok": n, "feil": n, "usikker": n}}
Legg også skriptet ditt i `kontroll/K_skript.py`.
Et svar uten ikke_sjekket-listen eller uten én rad per kontrollert tall og per kriterium er ugyldig.
Ikke skriv om arbeidet. Rapporter bare status og avvik.

RETUR TIL ORKESTRATOR (høyst 5 linjer): filsti, konklusjon, antall avvik, antall punkter som ikke er sjekket, og de viktigste grensevalgene som snur konklusjoner.
