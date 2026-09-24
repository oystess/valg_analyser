# Hypoteseturnering: «left behind» og periferistemmer i norske kommuner 1987–2025

*Utkast 2026-09-24. Kombinerer skillene `hypoteseturnering` (metode) og `agent-orkestrering` (arbeidsdeling, briefer, uavhengig kontroll og kostnadstak). Arbeidet starter ikke før spørsmålene i §9 er besvart og planen er godkjent.*

---

## 1. Sluttprodukt (én setning)

En **beskrivende** kartlegging av hvilke kommunekjennetegn som følger med endringer i periferistemmene (Sp) i 1989–2025. Kartleggingen tar utgangspunkt i left behind-tradisjonen og H1–H7 i `litteratur_notat.md`. De mønstrene som er verdt å beskrive, velges ut i en blindet turnering og kjøres deretter med låste spesifikasjoner på hele datasettet. Til dette hører en ny, modulær analysekode som erstatter `analyse*.py` og `matrise.py`, og en rapport som skiller **robuste mønstre**, **svake eller ustabile mønstre** og **forkastede hypoteser**.

## 2. Utgangspunkt: hypotesene vi beholder som frø

Hypotesene fra litteraturnotatet brukes som **frø**. Generatorene skal ta stilling til dem, spisse dem eller utfordre dem, men de får ikke forrang i turneringen. De konkurrerer på like vilkår med nye forslag.

| Frø | Kort | Kjerne |
|---|---|---|
| H1 | Rokkan og periferi | Periferieffekten er strukturell, men intensiteten topper seg rundt utløsere (1993, 2019–21) |
| H2 | Left behind | Befolkningsnedgang forsterker periferieffekten gjennom tjenestetap, identitet og relativ deprivasjon |
| H3 | Episodisk | Effekten av befolkningsnedgang akselererer episodisk, sterkest 2015–2021 |
| H4 | KV mot ST | Effekten er sterkere i kommunevalg |
| H5 | Ledd | Kommunevalg leder stortingsvalg |
| H6 | Routing | Sp og FrP konkurrerer om de samme velgerne. Den geografiske Sp-effekten er sterkest når FrP er svak |
| H7 | Aldersseleksjon | Utflytting av unge gir en eldre og mer stedsbundet velgermasse, og det forklarer Sp-effekten |

**Beskrivende, ikke bekreftende (valgt 2026-09-24):** Det er ingen holdout. Generatorene ser hele datasettet, og mønstrene blir funnet og beskrevet på de samme dataene. Resultatene er derfor **beskrivelser av sammenhenger på kommunenivå**, ikke tester av årsakshypoteser. Rapporten skal ikke bruke ordene «bekreftet» eller «effekt». I stedet brukes «mønster», «sammenheng» og «robust eller ustabil». Turneringen brukes til å **prioritere** hvilke mønstre som er verdt å beskrive og forklare. Låsingen og robusthetsbatteriet i §6 erstatter holdout som vern mot å fiske fram tilfeldige funn.

## 3. Forslag til spørsmål og enhet (bekreftes i §9)

- **Hovedspørsmål (utfall):** Endring i Sps andel av godkjente stemmer mellom to påfølgende stortingsvalg, per 2024-kommune (`Δ Sp`, prosentpoeng). Utfallet samler H1–H3 og H6–H7 i én skarp variabel.
- **Sekundære utfall** (bare robusthet, ingen egen turnering): samme endring i kommunevalg (H4), og endring i Sp + FrP samlet (en «protestblokk», H6).
- **Analyseenhet:** Kommune × valgperiode (357 × 9 ST-endringer). Tolkes bare på kommunenivå.
- **Ingen holdout** (brukerens valg). Se robusthetsbatteriet i §6.
- **Lekkasjevern:** Andre partiers andeler *i samme valg* er ikke tillatt som forklaringsvariabler (de henger mekanisk sammen fordi andelene summerer til 100). Tillatt: laggede verdier og nasjonale nivåer. Det samme gjelder alt som er målt etter valgdagen.

## 4. Data: fase 0 (må på plass før turneringen)

Datasettet fra QA-runden (`data/processed/*_2024.csv`) har stemmer og befolkning. Left behind-hypotesene trenger flere forklaringsvariabler, som alle må harmoniseres til 2024-kommuner med `kodemapping_2024.csv` eller SSBs `agg_KommSummer`:

| Variabel | Kilde (forslag) | Periode | Merknad |
|---|---|---|---|
| Befolkningsendring 4 og 10 år | 07459 | 1986– | Har vi |
| Alderssammensetning (andel 67+ og 20–39) | 07459 med alder | 1986– | Samme tabell, 2024-aggregat finnes |
| Netto innenlands flytting | SSB flyttetabell | 1990-tallet– | Skiller flytting fra fødselsunderskudd (H7) |
| Inntekt (median husholdning eller per innbygger) | SSB inntektstabell | ca. 2005– | Begrenser tidsvinduet for H2 |
| Utdanningsnivå (andel med høyere utdanning) | SSB utdanningstabell | 1980-tallet– | Kontroll for sammensetning |
| Sysselsatte i primærnæring og industri | SSB sysselsettingstabell | ca. 2008– | Næringsstruktur |
| Sentralitet | SSBs sentralitetsindeks (Klass, 6 klasser + indeks 0–1000) | fast | **Ferdig:** `data/processed/sentralitet_2024.csv`, alle 357 kommuner |
| Fylke og landsdel (2024) | Kodelister | fast | Til faste effekter og kjøringer med ett fylke utelatt |

Hentes via SSB-MCP til `data/raw/ssb/` med manifest, samme løype som i QA-runden. Hver variabel kontrolleres i kode: landstall, 357 kommuner, ingen hull.

Resultat: `turnering/data/panel.csv` (kommune × valgperiode) og `turnering/data/datadictionary.md`. Panelet brukes i sin helhet av alle roller. Hashen logges i `logg.md`, slik at alle kjøringer bruker de samme dataene.

## 5. Rollefordeling (hypoteseturnering × agent-orkestrering)

Orkestratoren (hovedtråden) gjør alt som krever hele bildet, og alle tall regnes i kode (orkestreringsskillen §7). Agentene får hvert sitt avgrensede oppdrag med selvstendig brief (orkestreringsskillen §5).

| Steg | Rolle | Hvem | Modell | Input | Output |
|---|---|---|---|---|---|
| 0 | Datahenting og harmonisering | Orkestrator | standard | SSB-MCP | `panel.csv`, `datadictionary.md`, `logg.md` |
| 0K | **Kontroll av data** | Kontrollagent | sonnet | Rådata, manifest, `panel.csv` | `kontroll/data.json`: hver variabel regnet på nytt fra rådata |
| 2 | Generatorer | 4 agenter parallelt: **Mekanisme** (left behind og Rokkan), **Skeptiker** (alder, størrelse, urbanitet og sammensetning), **Struktur/geografi** (landsdel, kyst og innland, historisk Sp-styrke), **Kontrafaktisk** (partikonkurranse og routing, H6) | standard | Spørsmål, frø H1–H7, datadictionary, `panel.csv` | `hyp/G<n>.json`, 8 hypoteser hver |
| 3 | Deduplisering og blinding | Orkestrator | – | `hyp/*.json` | `hyp/samlet.json` med anonyme id-er |
| 4 | Kritiker | 1 agent (gjenbrukes i evolusjonsrundene) | sonnet | `samlet.json`, datadictionary | Dom per hypotese: godkjent, revider eller forkast |
| 5 | Dommer (Elo) | 1 agent, fortsettes med SendMessage over 8–12 par per runde | standard | Par i standardformat, begge rekkefølger | `dueller.csv` |
| 6 | Forbedrer (1–2 runder) | 1 agent, gjenbrukes | standard | Topp 25 % | Nye versjoner, som går til kritikeren igjen |
| 7 | Lås og kjør | Orkestrator | – | `låst.json` (hash og tidspunkt logges før kjøring) | Koeffisient, 95 % KI, p, Holm og robusthetsbatteriet (§6) |
| 7K | **Uavhengig kontroll av kjøringen** | Kontrollagent | sonnet | `låst.json`, `panel.csv`, orkestratorens resultatfil | Regner hver spesifikasjon på nytt uten å se koden. Avvik rapporteres som uenighet. |
| 8 | Ny analysekode og rapport | Orkestrator | – | Alt over | `analyse/` og `turnering/RAPPORT.md` |

Generatorene får en fast sjekkliste fra frøene. Hver generator skal:
1. ta stilling til minst to frø (spisse, avgrense eller motsi),
2. foreslå minst tre hypoteser som *ikke* er frø,
3. gi hver hypotese en falsifiseringsbetingelse og en testspesifikasjon som kan kjøres uten skjønn. Spesifikasjonen skal inneholde modell, klyngerobuste standardfeil på kommunenivå, eventuelle faste effekter og vekting.

## 6. Metoderegler (utover skillene)

- Modeller med kommuneendringer skal ha **klyngerobuste standardfeil** (kommune) og valgperiode som fast effekt, med mindre hypotesen gjelder nettopp periodeforskjeller.
- **Vekting:** Hovedspesifikasjonen vektes med antall godkjente stemmer i forrige valg, og uvektet rapporteres som robusthet (små kommuner er støyete).
- **Estimerte kommuner** (`estimert = True`: Heim, Hitra, Orkland, Narvik, Hamarøy før 2020, og Ålesund og Haram i 2021) tas med, men mønstrene rapporteres også uten dem.
- **Robusthetsbatteri** (erstatter holdout; alt låses i `låst.json` før kjøring). Hvert mønster kjøres
  1. vektet og uvektet,
  2. med og uten estimerte kommuner,
  3. med ett og ett fylke utelatt (15 kjøringer; gjelder stabilitet, ikke prediksjon),
  4. per valgperiode (er mønsteret stabilt, eller drevet av ett valg?),
  5. i kommunevalg som parallell.
- Et mønster er **robust** når retningen er den samme i alle kjøringene 1–3, det er signifikant etter Holm-korreksjon i hovedspesifikasjonen, og ingen enkeltperiode eller enkeltfylke alene skaper det. Ellers kalles det **ustabilt**. Frøhypoteser og nye hypoteser rapporteres adskilt.
- **Økologisk nivå:** Alle formuleringer skal være «kommuner med X …», aldri «velgere med X …».

## 7. Ny analysekode (erstatter `analyse*.py` og `matrise.py`)

```
analyse/
  felles.py        les datasett, harmoniser og bygg panel (én kilde til sannhet)
  variabler.py     definisjoner av avledede variabler (Δ-er, vekst, lag)
  modeller.py      FE-, OLS- og klyngerobuste modeller, Holm
  kjør_låste.py    kjører låst.json med robusthetsbatteriet, uten skjønn
  figurer.py       figurer for bekreftede funn (dataviz-skillen)
turnering/         PROMPT.md, logg.md, data/, hyp/, dueller.csv, låst.json, RAPPORT.md
```

De gamle skriptene flyttes til `arkiv/` og slettes ikke. Nettsiden (`index.html`) oppdateres bare når du har godkjent funnene.

## 8. Budsjett (TR fra orkestreringsskillen)

| Del | Agentstarter |
|---|---|
| Kontroll av data (0K) | 1 |
| Generatorer | 4 |
| Kritiker (gjenbrukes) | 1 |
| Dommer (gjenbrukes via SendMessage) | 1 |
| Forbedrer (gjenbrukes) | 1 |
| Kontroll av kjøringen (7K) | 1 |
| **Sum** | **9 starter** (under taket på 10) |

Fast overhead er ca. 9 × 70 000 ≈ 0,63 mill. tokens. Med ca. 150–250 parvise dommer og to evolusjonsrunder blir anslaget 1,5–2,5 mill. tokens totalt. Planen har mer enn 4 agenter og må derfor **godkjennes før oppstart**.

## 9. Spørsmål til Øystein og svarene

| # | Spørsmål | Svar |
|---|---|---|
| 1 | Utfall | **OK (2026-09-24):** Δ Sp i stortingsvalg. KV og Sp + FrP brukes som robusthet. |
| 2 | Holdout | **Dropp holdout.** Målet er beskrivende. Robusthetsbatteriet (§6) brukes i stedet. |
| 3 | Tidsvindu | **OK (2026-09-24):** hele perioden for befolkning, alder, utdanning og sentralitet. Inntekt og næring bare i en undermodell 2005–2025. |
| 4 | Sentralitet | **Løst.** SSBs indeks er levert av Øystein, se `data/raw/ssb/sentralitet_klass.csv`. |
| 5 | Budsjett | **OK (2026-09-24):** 9 agentstarter, ca. 1,5–2,5 mill. tokens |
| 6 | Nettsiden | **OK (2026-09-24):** oppdateres først etter at rapporten er godkjent |
| 7 | Gamle skript | **OK (2026-09-24):** arkiveres i `arkiv/` |
