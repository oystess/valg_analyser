# Hypoteseturnering: «left behind» og periferistemmer i norske kommuner 1987–2025

*Utkast 2026-09-24. Kombinerer skillene `hypoteseturnering` (metode) og `agent-orkestrering` (arbeidsdeling, briefer, uavhengig kontroll og kostnadstak). Arbeidet starter ikke før spørsmålene i §9 er besvart og planen er godkjent.*

---

## 1. Sluttprodukt (én setning)

Et sett hypoteser om hvorfor kommuner stemmer som de gjør langs periferiaksen. Hypotesene skal springe ut av left behind-tradisjonen og H1–H7 i `litteratur_notat.md`, være rangert i en blindet turnering og være testet på låste holdout-data. Til dette hører en ny, modulær analysekode som erstatter `analyse*.py` og `matrise.py`, og en rapport som skiller **bekreftede**, **ikke bekreftede** og **forkastede** hypoteser.

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

**Advarsel om forurensning:** Frøene og de tidligere analysene er laget etter at *alle* dataene er sett. Holdout beskytter mot at agentene tilpasser seg dataene, men ikke mot det vi allerede vet. Rapporten skal si dette eksplisitt. En «bekreftelse» av en frøhypotese er derfor svakere enn en bekreftelse av en ny hypotese.

## 3. Forslag til spørsmål, enhet og holdout (bekreftes i §9)

- **Hovedspørsmål (utfall):** Endring i Sps andel av godkjente stemmer mellom to påfølgende stortingsvalg, per 2024-kommune (`Δ Sp`, prosentpoeng). Utfallet samler H1–H3 og H6–H7 i én skarp variabel.
- **Sekundære utfall** (bare robusthet, ingen egen turnering): samme endring i kommunevalg (H4), og endring i Sp + FrP samlet (en «protestblokk», H6).
- **Analyseenhet:** Kommune × valgperiode (357 × 9 ST-endringer). Tolkes bare på kommunenivå.
- **Holdout (forslag):** Geografisk blokk: 5 av 15 fylker i 2024-inndelingen holdes ute for alle år, trukket med fast seed og stratifisert på landsdel. Tidsholdout er vanskelig her, fordi H1 og H3 handler om bestemte episoder, og fordi 2021 og 2025 allerede er analysert. En eventuell tilleggstest på ST 2025 er et alternativ (§9).
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
| Sentralitet | SSBs offisielle indeks 2020 (6 klasser) | fast | Erstatter `sentralitet.csv`, som har ukjent kilde |
| Fylke og landsdel (2024) | Kodelister | fast | Til holdout og faste effekter |

Hentes via SSB-MCP til `data/raw/ssb/` med manifest, samme løype som i QA-runden. Hver variabel kontrolleres i kode: landstall, 357 kommuner, ingen hull.

Resultat: `turnering/data/panel.csv` (kommune × valgperiode) og `turnering/data/datadictionary.md`. Deretter deles panelet i `explore.csv` og `holdout.csv`, og holdout-hashen logges. **Holdout-stien skal aldri stå i en brief.**

## 5. Rollefordeling (hypoteseturnering × agent-orkestrering)

Orkestratoren (hovedtråden) gjør alt som krever hele bildet, og alle tall regnes i kode (orkestreringsskillen §7). Agentene får hvert sitt avgrensede oppdrag med selvstendig brief (orkestreringsskillen §5).

| Steg | Rolle | Hvem | Modell | Input | Output |
|---|---|---|---|---|---|
| 0 | Datahenting, harmonisering og split | Orkestrator | standard | SSB-MCP | `panel.csv`, `explore.csv`, `holdout.csv`, `logg.md` |
| 0K | **Kontroll av data** | Kontrollagent | sonnet | Rådata, manifest, `panel.csv` | `kontroll/data.json`: hver variabel regnet på nytt fra rådata |
| 2 | Generatorer | 4 agenter parallelt: **Mekanisme** (left behind og Rokkan), **Skeptiker** (alder, størrelse, urbanitet og sammensetning), **Struktur/geografi** (landsdel, kyst og innland, historisk Sp-styrke), **Kontrafaktisk** (partikonkurranse og routing, H6) | standard | Spørsmål, frø H1–H7, datadictionary, `explore.csv` | `hyp/G<n>.json`, 8 hypoteser hver |
| 3 | Deduplisering og blinding | Orkestrator | – | `hyp/*.json` | `hyp/samlet.json` med anonyme id-er |
| 4 | Kritiker | 1 agent (gjenbrukes i evolusjonsrundene) | sonnet | `samlet.json`, datadictionary | Dom per hypotese: godkjent, revider eller forkast |
| 5 | Dommer (Elo) | 1 agent, fortsettes med SendMessage over 8–12 par per runde | standard | Par i standardformat, begge rekkefølger | `dueller.csv` |
| 6 | Forbedrer (1–2 runder) | 1 agent, gjenbrukes | standard | Topp 25 % | Nye versjoner, som går til kritikeren igjen |
| 7 | Lås og holdout-test | Orkestrator | – | `låst.json` (hash og tidspunkt før holdout åpnes) | Effekt, 95 % KI, p, Holm |
| 7K | **Uavhengig kontroll av holdout-testen** | Kontrollagent | sonnet | `låst.json`, holdout-sti (først nå), orkestratorens resultatfil | Regner hver test på nytt uten å se koden. Avvik rapporteres som uenighet. |
| 8 | Ny analysekode og rapport | Orkestrator | – | Alt over | `analyse/` og `turnering/RAPPORT.md` |

Generatorene får en fast sjekkliste fra frøene. Hver generator skal:
1. ta stilling til minst to frø (spisse, avgrense eller motsi),
2. foreslå minst tre hypoteser som *ikke* er frø,
3. gi hver hypotese en falsifiseringsbetingelse og en testspesifikasjon som kan kjøres uten skjønn. Spesifikasjonen skal inneholde modell, klyngerobuste standardfeil på kommunenivå, eventuelle faste effekter og vekting.

## 6. Metoderegler (utover skillene)

- Modeller med kommuneendringer skal ha **klyngerobuste standardfeil** (kommune) og valgperiode som fast effekt, med mindre hypotesen gjelder nettopp periodeforskjeller.
- **Vekting:** Hovedspesifikasjonen vektes med antall godkjente stemmer i forrige valg, og uvektet rapporteres som robusthet (små kommuner er støyete).
- **Estimerte kommuner** (`estimert = True`: Heim, Hitra, Orkland, Narvik, Hamarøy før 2020, og Ålesund og Haram i 2021) tas med, men holdout-testen rapporteres også uten dem.
- Et funn er **bekreftet** bare hvis retningen stemmer og det er signifikant etter Holm-korreksjon over de K låste testene på holdout.
- **Økologisk nivå:** Alle formuleringer skal være «kommuner med X …», aldri «velgere med X …».

## 7. Ny analysekode (erstatter `analyse*.py` og `matrise.py`)

```
analyse/
  felles.py        les datasett, harmoniser og bygg panel (én kilde til sannhet)
  variabler.py     definisjoner av avledede variabler (Δ-er, vekst, lag)
  modeller.py      FE-, OLS- og klyngerobuste modeller, Holm
  kjør_låste.py    kjører låst.json mot holdout, uten skjønn
  figurer.py       figurer for bekreftede funn (dataviz-skillen)
turnering/         PROMPT.md, logg.md, hyp/, dueller.csv, låst.json, RAPPORT.md
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
| Kontroll av holdout (7K) | 1 |
| **Sum** | **9 starter** (under taket på 10) |

Fast overhead er ca. 9 × 70 000 ≈ 0,63 mill. tokens. Med ca. 150–250 parvise dommer og to evolusjonsrunder blir anslaget 1,5–2,5 mill. tokens totalt. Planen har mer enn 4 agenter og må derfor **godkjennes før oppstart**.

## 9. Spørsmål til Øystein

Se samtalen. Svarene føres inn her.
