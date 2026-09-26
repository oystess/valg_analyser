# Kontroll av hypoteser/motreaksjon/data/kv_panel.csv

Metode: hele panelet er regnet på nytt fra kildefilene i uavhengig Python-kode
(`/tmp/kvkontroll.py`, kjørt lokalt i denne sesjonen — ikke lest fra
`analyse/kv_panel.py` eller `analyse/felles.py`), og deretter sammenlignet
celle for celle mot `kv_panel.csv` (`/tmp/kvsammenlign.py`), med toleranse
0,001 for tall. Alle 3213 rader × alle nøkkelkolonner er sjekket — ingen
stikkprøver.

Kilder brukt: `data/processed/kommunestyrevalg_2024.csv`,
`data/processed/befolkning_2024.csv`, `data/processed/sentralitet_2024.csv`,
`data/processed/kodemapping_2024.csv`.

## Resultat per kolonne

| kolonne | status | antall avvik | eksempel |
|---|---|---|---|
| kom2024 (nøkkel) | ok | 0 | 357 unike 2024-kommuner, alle til stede |
| periode / t0 / t1 | ok | 0 | alle 9 perioder 1987‑1991 … 2019‑2023 korrekt utledet fra t0,t1 |
| ap_t0, ap_t1, d_ap | ok | 0 | — |
| frp_t0, frp_t1, d_frp | ok | 0 | — |
| h_t0, h_t1, d_h | ok | 0 | — |
| krf_t0, krf_t1, d_krf | ok | 0 | — |
| sp_t0, sp_t1, d_sp | ok | 0 | — |
| sv_t0, sv_t1, d_sv | ok | 0 | — |
| v_t0, v_t1, d_v | ok | 0 | — |
| mdg_t0, mdg_t1, d_mdg | ok | 0 | — |
| rodt_t0, rodt_t1, d_rodt | ok | 0 | — |
| andre_t0, andre_t1, d_andre | ok | 0 | — |
| vekt_stemmer_t0 | ok | 0 | lik `total_stemmer` i t0 for alle rader |
| estimert | ok | 0 | logisk ELLER av `estimert` i t0 og t1, verifisert mot kildens bool-flagg |
| bef_t0 | ok | 0 | lik befolkning 1.1. i t0 fra befolkning_2024.csv |
| vekst4_pst | ok | 0 | (bef t1/bef t0 − 1)·100, ingen avvik > 0,001 pp |
| vekst10_pst | ok | 0 | (bef t1/bef (t1−10) − 1)·100 der t1−10 ≥ 1986; tom ellers (se negativ test) |
| sent_indeks | ok | 0 | slått opp fra sentralitet_2024.csv på kom2024 |
| sent_klasse | ok | 0 | slått opp fra sentralitet_2024.csv på kom2024 |
| fylke | ok | 0 | avledet fra de to første sifrene i kom2024 mot offisiell 2024-fylkesliste (15 fylker), ingen avvik |
| reform_2017_20 | ok | 0 | True nøyaktig når kodemapping_2024 (aar=2016) har >1 distinkt kode med andel>0 for kommunen |
| navn | ok (tilleggssjekk) | 0 | matcher navn i kommunestyrevalg_2024.csv for alle rader |
| ln_bef_t0 | ok (tilleggssjekk, ikke i spesifikasjonen) | 0 | ln(bef_t0), maksimalt avvik ~5e‑5 (flyttallsavrunding) |
| landsdel | ikke i spesifikasjonen | — | internt konsistent 1-til-1 mot fylke, men ingen formell fasit gitt i oppdraget — se «ikke sjekket» |

**Konklusjon per kolonne: alle spesifiserte kolonner er kontrollert og funnet korrekte (0 avvik av 3213 rader for hver).**

## Negative tester

- **Manglende perioder:** Ingen. Alle 9 forventede perioder (1987‑1991 … 2019‑2023) er til stede, med nøyaktig 357 rader hver (357 × 9 = 3213). OK.
- **Duplikater (kom2024, periode):** 0 duplikater. OK.
- **d_h / d_sp forvekslet med andre partier:** Nei. Siden hele d_-settet for alle 10 partier er uavhengig regnet på nytt fra `prosent` i kildefilen og sammenlignet celle for celle uten avvik, er det utelukket at d_h eller d_sp er byttet om med et annet parti (en slik forveksling ville gitt store avvik i minst to kolonner). OK.
- **vekst10_pst mangler nøyaktig for 1987‑1991 og 1991‑1995:** Bekreftet. `vekst10_pst` er tom for alle 357 rader i disse to periodene (t1−10 = 1981 og 1985, begge < 1986), og utfylt (0 manglende) for de øvrige 7 periodene. OK.

## Plausibilitet — nasjonalt vektet snitt (vekt = vekt_stemmer_t0)

| periode | d_h (vektet snitt, pp) | d_sp (vektet snitt, pp) |
|---|---|---|
| 1987‑1991 | −1,78 | +4,37 |
| 1991‑1995 | −1,53 | +0,32 |
| 1995‑1999 | +1,11 | −3,26 |
| 1999‑2003 | −3,37 | −0,16 |
| 2003‑2007 | +1,15 | +0,06 |
| 2007‑2011 | **+8,50** | −1,01 |
| 2011‑2015 | −4,90 | +1,81 |
| 2015‑2019 | −3,20 | **+6,13** |
| 2019‑2023 | +5,67 | **−6,08** |

Vurdering: Tallene er i tråd med kjent norsk valghistorie og ser ikke urimelige ut:
- Høyre-framgangen i perioden 2007‑2011 (+8,5 pp vektet) samsvarer med det velkjente store Høyre-oppsvinget ved kommunestyrevalget 2011.
- Senterparti-framgangen i 2015‑2019 (+6,1 pp vektet) samsvarer med Sp sin kjente fremgang ved valget 2019 (bl.a. drevet av kommunereform-motstand).
- Sp sin tilbakegang i 2019‑2023 (−6,1 pp) er også konsistent med at partiet falt tilbake fra 2019-toppen ved valget 2023.

Ingen urimelige utslag observert.

## IKKE SJEKKET

- **landsdel**: kolonnen er ikke del av den oppgitte spesifikasjonen (ingen formel/fasit for landsdel er gitt i oppdraget), så den er ikke kontrollert mot en ekstern fasit — kun observert at den er internt 1-til-1 konsistent med `fylke`.
- **Radrekkefølge** i filen: ikke kontrollert (spesifikasjonen sier ingenting om sortering, og innhold er sjekket via nøkkel-join, ikke posisjon).
- **Kildefilenes egen kvalitet** (f.eks. om `prosent` i kommunestyrevalg_2024.csv er riktig utledet fra stemmetall, om befolkningstall er riktige, om kodemapping_2024 selv stemmer med historiske kommunesammenslåinger): dette er inndata og ligger utenfor kontrolloppdraget, som gjelder kv_panel.csv sin konsistens med disse kildene — ikke kildenes egen korrekthet.
- Har ikke lest `analyse/kv_panel.py` eller `analyse/felles.py`, slik oppdraget krevde.

## Konklusjon

**GODKJENT.**

Alle spesifiserte kolonner (10 partiers t0/t1/d_-verdier, vekt_stemmer_t0,
estimert, bef_t0, vekst4_pst, vekst10_pst, sent_indeks, sent_klasse, fylke,
reform_2017_20, samt kom2024/periode/t0/t1 som nøkler) er uavhengig
etterregnet fra kildefilene og stemmer eksakt (0 avvik av 3213 rader, innenfor
toleranse 0,001) med `kv_panel.csv`. Alle negative tester og
plausibilitetssjekker er bestått uten anmerkning.
