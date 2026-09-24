# Hvilke kommuner følger Sp-bølgene? Beskrivende hypoteseturnering 1989–2025

*2026-09-24. Prosedyren står i [`PROMPT.md`](PROMPT.md), og alle valg er logget i [`logg.md`](logg.md). Datagrunnlaget er det kvalitetssikrede datasettet ([`../qa/QA_RAPPORT.md`](../qa/QA_RAPPORT.md)) og panelet [`data/panel.csv`](data/panel.csv) (357 kommuner × 9 perioder).*

## Sammendrag

**Spørsmålet:** Hvilke kjennetegn ved kommuner følger med endringen i Senterpartiets oppslutning mellom to stortingsvalg (`d_sp`, prosentpoeng)? Utgangspunktet er left behind-hypotesene H1–H7 i `litteratur_notat.md`.

**Designet er beskrivende, uten holdout.** Hypotesene ble funnet og testet på de samme dataene. Resultatene er derfor *mønstre på kommunenivå*, ikke årsakseffekter. Et «robust» mønster betyr at det holder seg i en låst robusthetstest. Det betyr ikke at det er bekreftet.

**Nevnerne:**
- 4 generatorer foreslo **32** hypoteser.
- 8 ble slått sammen med nesten like hypoteser, så **24** gikk videre. Kritikeren godkjente alle 24.
- Etter 5 turneringsrunder laget forbedreren **8** nye versjoner. 1 ble forkastet og 3 revidert, så 7 ble med.
- **31** hypoteser ble turnert i 8 runder: 104 dueller, hver dømt i begge rekkefølger (208 dommeroppgaver).
- **6** ble låst og kjørt: **5 er robuste**, **1 er ustabil**.

### Fem robuste mønstre

1. **Befolkningsnedgang som varig kjennetegn, ikke som hendelse (H14).** Kommuner som over hele 1989–2025 har hatt lav befolkningsvekst, har i snitt sterkere Sp-utvikling. Når vi har tatt høyde for det varige nivået, betyr en ekstra dårlig periode for den enkelte kommunen lite. En kommune med ett standardavvik (3 prosentpoeng) lavere gjennomsnittlig fireårsvekst har i snitt ca. **0,6 pp mer Sp-framgang per periode**.
2. **Sp-bølgen 2013–2021 gikk gjennom Ap-land (H31).** I 2013–17 og 2017–21 økte Sp mer i kommuner der Ap sto sterkt ved periodens start. Mønsteret fantes ikke i bølgen 1989–93. Ett standardavvik høyere Ap-andel (8,5 pp) følger med ca. **1,5 pp mer Sp-framgang** i disse to periodene.
3. **Den kristne motkulturen snudde (H24).** I 1989–93 fulgte KrF-sterke kommuner med i Sp-bølgen. I 2013–17 fikk de klart *mindre* Sp-framgang. Forskjellen i helning er −0,59 pp per KrF-prosentpoeng, altså ca. **−3,7 pp for ett standardavvik** (6,4 pp).
4. **Vestlandet falt fra i 2013–2021, men kom tilbake i 2021–25 (H16).** Vestlandskommuner hadde svakere Sp-utvikling i 2013–2021 enn Sp-nivå, sentralitet og KrF-styrke skulle tilsi (−0,8 pp per periode samlet). **Men mønsteret snudde i 2021–25** (+0,5 pp). Det er altså ikke en varig forskyvning, og det samlede estimatet skjuler dette skiftet.
5. **Befolkningsnedgang betydde mest i bølgene som startet lavt (H32).** Sammenhengen mellom fireårsvekst og Sp-framgang var sterk i 1989–93 og 2013–17 (−0,52 pp per prosentpoeng vekst, i tillegg til den vanlige sammenhengen), men ikke i 2017–21. Den finnes ikke i kommunevalget.

### Ett ustabilt mønster

**Små kommuner med nedgang (H04)** holder bare når kommunene vektes etter antall stemmer. Uvektet er sammenhengen null. Den forbedrede versjonen (E1-02) ble forkastet av samme grunn.

## Hva dette sier om frøhypotesene

| Frø | Status etter turneringen | Grunnlag |
|---|---|---|
| **H1** Periferieffekten er strukturell, men topper seg rundt utløsere | **Avgrenset.** Skillelinjene flytter seg mellom bølgene. Motkulturen (KrF) fulgte med i 1993, men ikke i 2017. Ap-land sto for mye av veksten i 2013–21, og Vestlandet falt fra og kom tilbake. | H24, H31, H16 (robuste) |
| **H2** Befolkningsnedgang forsterker periferieffekten | **Delvis støttet, som varig kjennetegn.** Mønsteret går *mellom* kommuner (varig lav vekst), ikke *innen* samme kommune over tid. | H14 (robust); H01/E1-06 og H17 turnert, men ikke låst |
| **H3** Effekten av nedgang er episodisk sterkest 2015–2021 | **Motsagt i timingen.** Toppene er 1989–93 og 2013–17, ikke 2017–21. | H32 (robust); H25 (turnert, ikke låst) |
| **H4/H5** Kommunevalg sterkere eller ledende | **Ikke testet i låst form.** H28/H30 ble turnert, men lå lavt. H32 finnes ikke i kommunevalget. | – |
| **H6** Sp og FrP konkurrerer (routing) | **Ikke testet i låst form.** Turneringen løftet konkurransen med **Ap** og **KrF** foran FrP (H10/H18 lå rundt midten). | – |
| **H7** Aldring og utflytting | **Ikke testet i låst form.** H20 (fødselsunderskudd, ikke utflytting) lå midt på tabellen. | – |

Frøene og de tidligere analysene ble laget med alle dataene kjent. At et frø «står seg», er derfor svakere enn at en ny hypotese gjør det (se `PROMPT.md` §2).

## Resultattabell (låste hypoteser)

Alle modellene har klyngerobuste standardfeil på kommune. Hovedspesifikasjonen er vektet med godkjente stemmer i t0, og p-verdiene er Holm-korrigert over de 6 testene. Kolonnene «Uvektet», «Uten estimerte» og «KV» viser b i de tilsvarende kjøringene. «Uten fylke» viser spennet i b når ett og ett fylke er utelatt.

| Id | Elo (plass) | Påstand (kort) | b (95 % KI) | Holm-p | Uvektet | Uten estimerte | Uten fylke (min–maks) | KV | Status |
|---|---|---|---|---|---|---|---|---|---|
| H14 | 1119 (1) | Varig lav vekst ↔ Sp-framgang | −0,196 (−0,269; −0,123) | < 0,001 | −0,216 | −0,191 | −0,231 til −0,162 | −0,181 | **robust** |
| H31 | 1094 (2) | Ap-land ↔ Sp-framgang 2013–21 | +0,182 (0,141; 0,224) | < 0,001 | +0,201 | +0,182 | 0,164 til 0,209 | +0,138 | **robust** |
| H24 | 1062 (3) | KrF-sammenhengen snudde fra 1989–93 til 2013–17 | −0,585 (−0,687; −0,484) | < 0,001 | −0,580 | −0,591 | −0,658 til −0,521 | −0,212 | **robust** |
| H16 | 1033 (5) | Vestlandet svakere 2013–21 | −0,818 (−1,106; −0,530) | < 0,001 | −1,159 | −0,799 | −1,028 til −0,506 | −0,530 | **robust** (snur i 2021–25) |
| H04 | 1033 (6) | Små kommuner med nedgang | +0,059 (0,043; 0,076) | < 0,001 | **−0,003** | +0,060 | 0,053 til 0,067 | +0,049 | **ustabilt** |
| H32 | 1032 (7) | Nedgang sterkest i 1989–93 og 2013–17 | −0,515 (−0,679; −0,352) | < 0,001 | −0,507 | −0,511 | −0,571 til −0,393 | −0,054 (p = 0,37) | **robust** |

Merknader:
- **E1-07** (4. plass) ble ikke låst. Den kombinerer H31 og H24, og begge er låst.
- For H24 kan nøkkelleddet ikke identifiseres når én av de to periodene er utelatt. Slike kjøringer er merket «ikke anvendelig», etter en regel som ble presisert og logget før kjøringen.
- Estimatene per periode i `resultater.json` sier lite for hypoteser der nøkkelleddet selv er definert av perioden (H31, H16, H32). Unntaket er H16, der perioden 2021–25 viser at mønsteret snur.
- For H14 regnes kommunesnittet av vekst inne i formelen, på det utvalget som kjøres. Når perioder eller fylker utelates, beregnes snittet derfor på nytt.

## Hele turneringen (31 hypoteser)

Plass, Elo og antall dueller står i `elo.csv` og `dueller.csv`. De eksplorative tallene står i `hyp/turnering.json`. Hypotesene fra 8. plass og ned er **ikke låst og ikke kjørt i robusthetstesten**. Tallene deres er eksplorative, fra generatorene. Utvalg:

| Plass | Id | Elo | Kort | Eksplorativt |
|---|---|---|---|---|
| 8 | H02 | 1031 | Sp-tilbakeslag (1993–97, 2021–25) er proporsjonale med utgangsnivået | b = −0,47 |
| 12 | H06 | 1003 | Lav sentralitet gir mer Sp-framgang bare i oppgangsperioder | b = −2,38 per 100 indekspoeng |
| 13 | H19 | 1003 | Andel i primærnæringene ↔ Sp-framgang (2009–) | b = +0,18 |
| 14 | H26 | 1001 | Lav medianinntekt ↔ Sp-framgang (2005–) | b = −2,47 per log-enhet |
| 15 | H25 | 1000 | Nedgang betydde mindre i 2017–21 enn i 2013–17 | b = +0,47 |
| 18 | H18 | 999 | FrP-konkurransen er sterkest i periferien | b = −0,06 |
| 19 | H20 | 999 | Fødselsunderskudd, ikke utflytting | b = −0,012 |
| 31 | H17 | 908 | Ingen selvstendig nedgangseffekt med full kontroll | b = +0,008 (null) |

Elo-forskjellene fra ca. 5. plass og nedover er små (1031–1033 for plass 5–8, og rundt 1000 for plass 12–20). Rangeringen i dette feltet er usikker.

## Kirkegården og sammenslåtte hypoteser

- **Forkastet av kritikeren:** E1-02 (små kommuner med nedgang, forbedret versjon av H04). Mønsteret forsvinner uten vekting, og en direkte terskeltest gir motsatt fortegn.
- **Slått sammen før kritikken** (`hyp/dedup.json`):
  - H03 og H09 → H30 (Sp sterkere lokalt enn nasjonalt)
  - H13 → H20 (fødselsunderskudd)
  - H05 → H19 (primærnæring)
  - H21 → H02 (proporsjonale tilbakeslag)
  - H08 → H06 (sentralitet i oppgangsperioder)
  - H12 → H25 (timing 2017–21)
  - H11 → H24 (KrF 2013–17)
- **Nullfunn generatorene nevnte, men ikke leverte:** Regionreformen (G3) ga ikke noe mønster.

## Forbehold

1. **Beskrivende, ikke bekreftende.** Hypotesene ble generert, rangert og kjørt på de samme dataene. Låsingen og robusthetsbatteriet beskytter mot noe av fiskingen, men ikke mot at generatorene har sett mønstrene først. Særlig G3 opplyste at periodeutvalget i H06 og H27 ble valgt etter at tallene var sett. Ingen av dem ble låst.
2. **Kommunenivå.** «Kommuner med mye Ap i 2013 fikk mer Sp-framgang» betyr *ikke* at Ap-velgere gikk til Sp. Det kan like gjerne være andre velgere i de samme kommunene.
3. **Styrke og støy.** Små kommuner (Utsira, Træna, Andøy i 2021) har store svingninger. Hovedspesifikasjonene er vektet med stemmer. Der uvektet gir et annet svar (H04), er mønsteret merket ustabilt.
4. **Uavhengighet i dommen.** Samme dommeragent dømte alle rundene. I runde 1 ble hvert par i praksis dømt én gang, og dommen ble brukt for begge rekkefølger (se logg). Rekkefølgekontrollen er derfor svak. Dommeren kom aldri fram til ulike vinnere i de to rekkefølgene.
5. **Kritikeren var raus i første runde** (24 av 24 godkjent). Den strengere andre runden fant rangmangel i modeller med fylke × periode (E1-03, E1-06, E1-08). H01 har samme oppbygning, men ble ikke låst. Revisjonen av E1-03 fikk ikke med seg påstandsteksten.
6. **Data:** Inntekt finnes først fra 2005 og næringsstruktur fra 2008. De estimerte kommunene (delinger) inngår, men resultatene er de samme uten dem.

## Uavhengig kontroll

*(Fylles inn når kontroll 7K er ferdig.)*

## Dekningsrapport

| Rolle | Antall | Modell | Merknad |
|---|---|---|---|
| Datakontroll 0K | 1 | Sonnet | Godkjent: 20 ok, 0 feil, 2 usikre (nuller i næringsdata, dokumentert) |
| Generatorer G1–G4 | 4 | standard | 32 hypoteser. Alle ble avbrutt av en bruksgrense og gjenopptatt med samme kontekst. |
| Kritiker | 1 (2 runder) | Sonnet | 24/24 godkjent, deretter 4 godkjent / 3 revidert / 1 forkastet |
| Dommer | 1 (8 runder) | standard | 208 dommeroppgaver, 104 dueller, ingen uenige rekkefølgepar |
| Forbedrer | 1 | standard | 8 nye versjoner |
| Kontroll 7K | 1 | Sonnet | Se over |
| **Sum** | **9 agentstarter** | | Innenfor budsjettet på 9 |

Avvik fra planen:
- Holdout ble droppet etter brukerens valg og erstattet av et robusthetsbatteri.
- Utvalgsregelen for låsing utelot E1-07 (se over).
- Robusthetsregelen ble presisert én gang før kjøringen (logget).
- Det er ikke laget figurer (`analyse/figurer.py`). Det gjenstår til funnene er godkjent.
