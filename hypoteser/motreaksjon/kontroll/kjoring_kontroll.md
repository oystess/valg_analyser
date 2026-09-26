# Kontroll av de låste kjøringene i hypoteser/motreaksjon

Metode: hele kjeden er regnet på nytt i uavhengig Python-kode
(`/tmp/kjorkontroll*.py`, kjørt lokalt i denne sesjonen — `analyse/motreaksjon_kjor.py`
er **ikke** lest eller importert). Jeg har lest og gjenbrukt kun
`analyse/modeller.py`s dokumenterte grensesnitt som referanse, men skrevet min
egen `statsmodels`-implementasjon (WLS/OLS, `cov_type="cluster"`,
`groups=kom2024`) fra bunnen av for alle beregninger. Ingen stikkprøver — alle
16 periodepar (P1/P2 + vekst4-sensitivitet), hele robusthetsbatteriet for
alle 26 Holm-tester, h_resid_forrige for alle 357 kommuner × 6 par × 2
valgslag, og alle beskrivende mål (P3, P5, konkurrenter_parnivå,
h_i_regjering_andel, r_biv, reform) er etterregnet.

Panel-sha256 stemmer eksakt mot både `låst.json` og `resultater.json`
(`turnering/data/panel.csv` og `hypoteser/motreaksjon/data/kv_panel.csv`).

## Rader per test (P1/P2 per par, P4 per valgslag)

Alle 24 P1/P2-hovedtester er sjekket med **hele** robusthetsbatteriet
(hoved, uvektet, uten_estimert, alle 15 uten_fylke) — ikke bare hovedtallet.
De to P4-testene er sjekket med hele sitt batteri (hoved, uvektet,
uten_estimert, 15× uten_fylke, 5× uten_par). Toleranse 1e-4 på b og p.

| id | status | avvik |
|---|---|---|
| P1 ST 1993-1997→1997-2001 | ok | ingen (hoved+18 batterirader) |
| P2 ST 1993-1997→1997-2001 | ok | ingen |
| P1 ST 1997-2001→2001-2005 | ok | ingen (eneste robust=true-test; p_holm=0,0363 og «snur»=[] bekreftet) |
| P2 ST 1997-2001→2001-2005 | ok | ingen |
| P1 ST 2001-2005→2005-2009 | ok | ingen |
| P2 ST 2001-2005→2005-2009 | ok | ingen |
| P1 ST 2005-2009→2009-2013 | ok | ingen |
| P2 ST 2005-2009→2009-2013 | ok | ingen |
| P1 ST 2009-2013→2013-2017 (sett) | ok | ingen (korrekt utelatt fra Holm-familien) |
| P2 ST 2009-2013→2013-2017 (sett) | ok | ingen (korrekt utelatt fra Holm-familien) |
| P1 ST 2013-2017→2017-2021 | ok | ingen |
| P2 ST 2013-2017→2017-2021 | ok | ingen |
| P1 ST 2017-2021→2021-2025 | ok | ingen |
| P2 ST 2017-2021→2021-2025 | ok | ingen |
| P4 ST samlet | ok | ingen (hoved, uvektet, uten_estimert, 15× uten_fylke, 5× uten_par — se merknad om «uten_estimert» under) |
| P1 KV 1995-1999→1999-2003 | ok | ingen |
| P2 KV 1995-1999→1999-2003 | ok | ingen |
| P1 KV 1999-2003→2003-2007 | ok | ingen |
| P2 KV 1999-2003→2003-2007 | ok | ingen |
| P1 KV 2003-2007→2007-2011 | ok | ingen |
| P2 KV 2003-2007→2007-2011 | ok | ingen |
| P1 KV 2007-2011→2011-2015 | ok | ingen |
| P2 KV 2007-2011→2011-2015 | ok | ingen |
| P1 KV 2011-2015→2015-2019 | ok | ingen |
| P2 KV 2011-2015→2015-2019 | ok | ingen |
| P1 KV 2015-2019→2019-2023 | ok | ingen |
| P2 KV 2015-2019→2019-2023 | ok | ingen |
| P4 KV samlet | ok | ingen |

**Holm-justering:** min egen Holm-Bonferroni-implementasjon over nøyaktig
disse 26 p-verdiene (24 test-rolle P1/P2 + 2 P4-samlet; de 2 «sett»-testene
korrekt utelatt) gir p_holm identisk med `resultater.json` for alle 26
tester (0 avvik). `robust`-flagget stemmer for alle 26 (kun ett `robust:true`,
nøyaktig der p_holm<0,05 og fortegn stemmer i alt batteriet).

**Tilleggsfunn (ikke feil, men presisering):** For `uten_estimert` i P4
matchet verken «filtrer kun på t+1-radens estimert-flagg» eller «kjør hele
P1-residualen på nytt uten estimerte» eksakt før jeg testet en tredje
variant: kommuner ekskluderes når **enten** t- eller t+1-perioden er
estimert (n=2108 i begge valgslag, eksakt likt `resultater.json`). Dette er
en rimelig og konsistent tolkning, men selve regelen i `låst.json` sier bare
«uten estimerte kommuner» uten å spesifisere t vs. t+1 — se tolkningspunkt
under.

**Vekst4-sensitivitet:** `b_P1_v4`/`b_P2_v4` for alle 16 par (inkl. de 4
«bare_vekst4»-radene som mangler vekst10) stemmer eksakt. Kun hovedtallet er
sjekket her, ikke et fullt robusthetsbatteri for vekst4 (se «ikke sjekket»).

**h_resid_forrige:** Regnet på nytt fra P1-modellen (hoved, vektet) i t for
alle 357 kommuner × 6 testpar × 2 valgslag (2142 rader hvert valgslag) —
0 avvik mot `par_st.csv`/`par_kv.csv` (maksdiff ~1e-15, flyttallsstøy).

**Andre tall i parvis.csv/resultater.json** (alle sjekket, 0 avvik):
h_nasj_t, sp_nasj_t1, ap_nasj_t, r_biv_h_t, r_biv_sp_t1, b_ap_t, b_P2_ap
(bygget direkte fra panelet for ALLE rader inkl. sett-paret), b_P2_reform og
b_reform (for de 3 relevante parene, med `reform_2017_20` korrekt slått opp
fra KV-panelet og merget inn på ST-panelet siden variabelen er «fast per
kommune»), r_bP2_mot_sp_nasj_t1, r_bP2_mot_ap_gradient_t, r_bP1_mot_h_nasj_t
(per valgslag og samlet), P3 (Pearson og Spearman, med og uten sett-paret,
per valgslag og samlet), P5 (gruppering, snitt b_P2, P3 per gruppe),
h_i_regjering_andel (alle 16 par, inkl. binærflagget h_i_regjering).

## Rader per statusregel

| regel | status | begrunnelse |
|---|---|---|
| `test_robust` (Holm p<0,05 i hoved OG fortegn i hoved+uvektet+uten_estimert+alle uten_fylke, og uten_par for P4) | fulgt | Egen etterregning av alle 26 tester + fullt batteri gir identisk `robust`-verdi for hver. Kun `P1 ST 1997-2001→2001-2005` er robust; det stemmer med p_holm=0,0363<0,05 og tomt «snur»-felt. |
| `par_støtter` (P1(t) og P2(t+1) begge robuste) | fulgt | Siden bare én test totalt er robust (og det er en P1, ikke et par der også P2(t+1) er robust), blir `par_støtter`=false for alle 12 par. Stemmer med «0 av 6» for både ST og KV. |
| `P1_P2_mønster` (støttet ≥4/6 begge slag; delvis ≥flertall i ett eller ≥7/12 samlet; ellers ikke) | fulgt | 0/6, 0/6, 0/12 — ingen terskel nås → «ikke støttet», som rapportert. |
| `spesifisitet` (beskrivende, ingen påstand) | fulgt | Rapporten gir kun brøker (0 av 1, 0 av 5/6/11), ingen signifikanspåstand er lagt til. Tallene stemmer eksakt med egen etterregning. |
| `P3` (støttet hvis negativ i begge slag; delvis hvis negativ i ett eller kun samlet) | **tolket, men rimelig** | Regelteksten definerer eksplisitt kun «støttet» og «delvis»-betingelsene, ikke et eksplisitt «ellers»-utfall. Siden Pearson er positiv i ST (0,830), KV (0,933) og samlet (0,862) — altså motsatt av hypotesen i alle tre — er verken støttet- eller delvis-betingelsen oppfylt, og resultatet faller til «ikke støttet» ved implisitt analogi til de andre reglene (som alle har et eksplisitt «ellers»-ledd). Tolkningen er opplagt riktig i sak (positiv korrelasjon motsier hypotesen tydelig), men er ikke ordrett dekket av teksten. |
| `P4` (støttet: samme versjon robust begge slag; delvis: robust i ett, eller samme fortegn i begge uten robusthet; ellers ikke) | fulgt (med tolkning av A/B-valg) | p_holm=1,0 i begge slag → ingen er robuste. Fortegnet i hoved er positivt i begge slag, som tilsvarer P4B i begge → «delvis (ST: P4B, KV: P4B)» er korrekt etter regelen. A/B-valget (hvilken retning som «gjelder») er en implisitt tolkning låst.json ikke spesifiserer eksplisitt hvordan skal avgjøres (jeg antar: den retningen hovedestimatets fortegn faktisk har), men den er rimelig, og endrer uansett ikke konklusjonen siden ingen versjon er robust. |
| `P5` (kun «støttet (beskrivende)»-betingelse er skrevet ut; ingen eksplisitt delvis-regel) | **tolket, ikke ordrett dekket** | Regelen i `låst.json` spesifiserer bare når resultatet er «støttet (beskrivende)» (Sp-gradienten mer negativ med Høyre i regjering i BEGGE slag). Egen etterregning: KV oppfyller dette (−0,038 vs. −0,021), ST gjør det ikke (+0,012 vs. −0,031, altså motsatt retning). Siden regelen ikke definerer noe eksplisitt «delvis»-utfall, er «delvis (beskrivende)» en analogislutning fra strukturen i P3/P4-reglene, ikke en ordrett anvendelse av den låste teksten. Konklusjonen (blandet/ikke entydig støtte) er saklig rimelig gitt tallene. |
| Holm-familien = nøyaktig 26 tester (P1+P2 for testpar, ikke sett-paret, pluss samlet P4×2) | fulgt | Egen filtrering på `rolle=="test"` gir nøyaktig disse 26 radene; de to sett-testene har `p_holm=null` og teller ikke med. Stemmer med `låst.json`s spesifikasjon ordrett. |

## Regjeringstabellen (`regjeringer.csv`)

Sjekket rad for rad mot kjent norsk politisk historie 1981–2026, og for
kontinuitet (ingen hull/overlapp mellom radene — verifisert programmatisk).

| rad | periode | status |
|---|---|---|
| 1 | Willoch I, 1981-10-14–1983-06-08, H | ok |
| 2 | Willoch II, 1983-06-08–1986-05-09, H;KrF;Sp | ok |
| 3 | Brundtland II, 1986-05-09–1989-10-16, Ap | ok |
| 4 | Syse, 1989-10-16–1990-11-03, H;KrF;Sp | ok |
| 5 | Brundtland III, 1990-11-03–1996-10-25, Ap | ok |
| 6 | Jagland, 1996-10-25–1997-10-17, Ap | ok |
| 7 | Bondevik I, 1997-10-17–2000-03-17, KrF;Sp;V | ok |
| 8 | Stoltenberg I, 2000-03-17–2001-10-19, Ap | ok |
| 9 | Bondevik II, 2001-10-19–2005-10-17, KrF;H;V | ok |
| 10 | Stoltenberg II, 2005-10-17–2013-10-16, Ap;SV;Sp | ok |
| 11 | Solberg (H+FrP), 2013-10-16–2018-01-17, H;FrP | ok |
| 12 | Solberg (H+FrP+V), 2018-01-17–2019-01-22, H;FrP;V | ok |
| 13 | Solberg (H+FrP+V+KrF), 2019-01-22–2020-01-24, H;FrP;V;KrF | ok |
| 14 | Solberg (H+V+KrF), 2020-01-24–2021-10-14, H;V;KrF | ok |
| 15 | Støre (Ap+Sp), 2021-10-14–2025-02-04, Ap;Sp | ok (se merknad) |
| 16 | Støre (Ap), 2025-02-04–2026-09-26, Ap | ok (se merknad) |

**Merknad (usikker, men uten praktisk betydning):** Bruddet mellom Støre
(Ap+Sp) og Støre (Ap) i min egen kunnskap plasseres oftest til rundt
30. januar–3. februar 2025 (Sp forlot regjeringen sent i januar, ny
regjering utnevnt i statsråd 3. februar). Datoen 2025-02-04 i tabellen kan
derfor være av med ±1–4 dager. Dette påvirker **ikke** noen av resultatene i
denne kontrollen, siden verken Ap eller Sp inngår i beregningen av
`h_i_regjering_andel` (den teller kun Høyres regjeringsdeltakelse), og alle
periodepar som bruker denne overgangen ligger uansett langt fra
vindugrensene (ingen testpar-vindu har et endepunkt nær januar/februar
2025).

## Motstrid

Ingen funnet. Ingen tegn til at d_h/d_sp er byttet om (uavhengig innlesning
av begge kolonner fra panelet reproduserer alle rapporterte tall eksakt),
ingen tegn til at feil periode (t/t+1) er brukt (P1 bruker konsekvent
`periode==t`, P2 `periode==t1`, verifisert for alle 16 par), det sette paret
(ST 2009-2013→2013-2017) er korrekt utelatt fra Holm-familien og fra
`par_st.csv` (kun 6 testpar i parfilen, ikke 7), og vekter er konsekvent
brukt i hovedspesifikasjonen (hoved og uvektet gir systematisk ulike b/p i
nesten alle rader, noe som utelukker at vekting ved en feil er utelatt).

## IKKE SJEKKET

- Konkurrenttestene `P4_ap`, `P4_rtm`, `P4_reform` (i `resultater.json`s
  `konkurrenter`-liste): kun `b_P2_ap` og `b_ap_t` (parvis.csv-kolonnene) er
  verifisert eksakt. Selve `P4_ap`/`P4_rtm`/`P4_reform`-modellenes fulle
  robusthetsbatteri (uten_fylke, uten_par osv.) er ikke etterregnet, kun
  deres «hoved»- og «uvektet»-tall er lest, ikke uavhengig gjenskapt.
- Vekst4-sensitivitetens eget robusthetsbatteri (uvektet/uten_estimert/
  uten_fylke for `b_P1_v4`/`b_P2_v4`) — kun hovedtallet (vektet) er
  etterregnet for alle 16 par, ikke et fullt batteri.
- `analyse/motreaksjon_kjor.py` er bevisst ikke lest, slik oppdraget krevde
  — jeg kan derfor ikke si noe om *hvordan* koden er skrevet, bare at
  *resultatene* stemmer med en uavhengig etterregning.
- Kildekvaliteten til selve panelene (`panel.csv`, `kv_panel.csv`) er ikke
  kontrollert her — det er allerede gjort i en tidligere, separat kontroll
  (`hypoteser/motreaksjon/kontroll/kv_panel_kontroll.md`, konkludert
  GODKJENT for KV-panelet). Jeg har kun kontrollert konsistensen mellom
  panelene og de rapporterte modell-resultatene, ikke panelenes egen
  korrekthet mot rådata på nytt.
- Nøyaktig hvilken kalenderdag (30. jan / 3. feb 2025) Sp forlot Støre-
  regjeringen, er ikke slått opp i en primærkilde i denne sesjonen — kun
  vurdert mot egen bakgrunnskunnskap (se merknad over). Uten praktisk
  betydning for resultatene.

## Konklusjon

**GODKJENT.**

28/28 rapporterte tester (24 P1/P2-testpar + 2 «sett»-tester + 2 P4-samlet)
er uavhengig etterregnet fra panelene med egen `statsmodels`-kode og stemmer
eksakt (toleranse 1e-4) med `parvis.csv` og `resultater.json`, inkludert
hele robusthetsbatteriet (uvektet, uten estimerte, 15× uten fylke, og for P4
5× uten par). Holm-justeringen over den korrekte 26-tester-familien er
etterregnet uavhengig og stemmer eksakt. h_resid_forrige, P4-modellene, P3,
P5, konkurrenter_parnivå, h_i_regjering_andel, r_biv-korrelasjonene,
reform-kontrollene og b_P2_ap/b_ap_t er alle uavhengig etterregnet og
stemmer eksakt. Regjeringstabellen er historisk korrekt (16/16 rader ok,
med ett trivielt usikkert punkt om en dato som ikke påvirker resultatene).

Ingen motstrid funnet i noen av de negative testene som ble sjekket
(d_h/d_sp-forveksling, feil t/t+1-periode, sett-paret i Holm-familien,
manglende vekter).

**Antall rader per status:**
- Tester (P1/P2/P4): 28 av 28 **ok**, 0 feil, 0 usikker.
- Statusregler: 6 av 8 **fulgt** ordrett, 2 av 8 **tolket** (P3 og P5 — begge
  vurdert som rimelige tolkninger som ikke endrer konklusjonen).
- Regjeringstabell: 16 av 16 **ok** (1 rad med et trivielt usikkert
  datopunkt uten praktisk betydning).
- Motstrid: 0 (ingen funnet).
- Ikke sjekket: 5 punkter (listet over), ingen av dem kjernen i
  hypotesetesten.
