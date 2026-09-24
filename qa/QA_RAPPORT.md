# QA-rapport: valgdatasettet 1987–2025 på 2024-kommuner

*2026-09-24. Plan og kriterier står i [`QA_PROMPT.md`](QA_PROMPT.md). Automatiske kontroller står i [`kontroll/automatiske_kontroller.md`](kontroll/automatiske_kontroller.md).*

## Sammendrag

Det gamle datasettet hadde flere alvorlige feil. **Stortingsvalget 1989 var telt ca. 1,3 ganger for høyt** (i Oslo nøyaktig dobbelt), og **den gamle kodeoversettingen førte hele kommuner til feil 2024-kommune**. Eksempler er Vang (Hedmark) → Vang (Valdres), Leikanger → Lærdal, Re → Holmestrand og Halsa → Aure. I tillegg var prosentandelene ikke offisielle, rådataene lå ikke i repoet, og befolkningen var 0 for fem kommuner før 2020.

Datasettet er nå bygget på nytt fra SSB-rådata som ligger i repoet, med en kodeoversetting som er kontrollert mot SSB for hvert år. **Alle harde kontroller går gjennom**:
- Summene i rådata og ferdigtabell er like.
- Landstallene er like SSBs for alle år og partier som er testet.
- 18 476 celler for uendrede kommuner er like SSBs 2024-aggregat, uten ett eneste avvik.
- Befolkningen er lik SSBs aggregat (14 459 kommune/år).
- Byggingen er reproduserbar: to kjøringer gir identiske filer.

**Analysene er ikke kjørt på nytt** (etter avtale). Lista over hva som endres står nederst. Hovedfunnet i Senteropprøret-analysen står seg: sammenhengen mellom befolkningsvekst og økningen i Sp 1989→93 er nesten uendret. Nivåene endres derimot.

## 1. Feil som ble funnet

| # | Feil | Konsekvens | Status |
|---|---|---|---|
| F1 | **Stortingsvalget 1989 ble lastet inn to ganger** i `hent_data.py`, fordi to nedlastinger som overlappet, ble summert. Samme type feil som tidligere ble rettet for befolkning. | Totalen i 1989 ble 3,51 mill. mot riktig 2,65 mill. Ap fikk 51,8 % nasjonalt (riktig 34,3 %) og Sp 4,9 % (riktig 6,5 %). 85 % av kommune/parti-cellene hadde feil på mer enn 0,5 pp. | Rettet |
| F2 | **Kommuner ble koblet på navn før noe annet.** `0414 Vang` (Hedmark) → `3454 Vang` (Valdres). | Vang i Valdres fikk 10 900 stemmer i 1989 (riktig 942), og Sp 1989 ble 7,3 % (riktig 33,0 %). | Rettet |
| F3 | **Små grenseoverføringer ble brukt som oversetting av hele kommuner** (`grenser_mapping.csv`, hentet ut med Haiku). Leikanger ble ført til Lærdal fordi 32 personer ble overført i 1992. | Lærdal fikk Leikangers stemmer i alle valg før 2020, og Sp i KV 1987 ble 9,4 % (Sp stilte ikke egen liste i Lærdal). | Rettet |
| F4 | **Feil i `kommunereform_mapping.csv`**, som var skrevet for hånd og uten kilde: Re → Holmestrand (riktig Tønsberg), Audnedal → Lindesnes (riktig Lyngdal), Sandøy → Molde (riktig Ålesund), Roan → Osen (riktig Åfjord), Halsa → Aure (riktig Heim), Leksvik → Inderøy (riktig Indre Fosen), Gaular → Fjaler (riktig Sunnfjord), Snillfjord og Tysfjord ikke delt, og feil år for Hof. | Stemmene i de berørte kommunene havnet i feil kommune i alle år før 2020. Sammen med F2 og F3 hadde 2–10 % av kommune/parti-cellene per år avvik på mer enn 0,5 pp. Dette er målt på andelen av de 9 partiene utenom 1989, og RV er tatt med. | Rettet. Tabellen brukes ikke lenger. |
| F5 | **Delte kommuner ble ikke fordelt.** Hele Ålesund 2020–2023 ble ført på Ålesund, og Haram fikk 0. | Haram manglet helt i ST 2021 og fikk 0 i KV 2019. | Rettet (fordeling etter befolkning, merket `estimert`) |
| F6 | **Nevneren var summen av 9 partier**, ikke alle godkjente stemmer. | Alle andeler var for høye, og mest der «Andre» og lokale lister var store, for eksempel i kommunevalg. | Rettet. `prosent` bruker nå alle stemmer, og `prosent_9parti` beholdes for sammenligning. |
| F7 | **Rødt manglet før 2009.** RV (parti 11) og Fylkeslistene for miljø og solidaritet (15, RVs liste i 1989) ble utelatt. | Tidsserien for Rødt begynte først i 2009. | Rettet. Kodene 11 og 15 inngår nå i 55. |
| F8 | **Befolkningen var 0** for Heim, Hitra, Orkland, Narvik og Hamarøy i 1986–2019, fordi SSB ikke lager tidsserier for delte kommuner. | Veksttallene for disse kommunene ble uendelige eller manglet, og kommunene falt ut av analysene (n = 352). | Rettet med egen oversetting |
| F9 | **Datasettet kunne ikke reproduseres.** Rådataene lå i en midlertidig sesjonsmappe. | Ingen kunne kontrollere eller bygge datasettet på nytt. | Rettet. Rådataene ligger i `data/raw/ssb/` med manifest. |
| F10 | **Sentralitetskoblingen:** kommentaren i `analyse*.py` sier «laveste = mer sentral», men kode 0 betyr *minst* sentral. Når kommuner slås sammen, blir den minst sentrale delen brukt, og koblingen gikk dessuten gjennom den feilaktige `kom_mapping`. | 4 kommuner fikk ulik klasse: Molde, Færder, Kinn og Ullensvang. | Ny `sentralitet_2024.csv` (klassen til den største delen). Analysene er ikke endret. |
| F11 | **Kommunestyrevalg holdes for strukturen som gjelder fra året etter** (KV 1987 → 1988-kommuner, KV 2019 → 2020-kommuner, KV 2023 → 2024-kommuner). | Dette ble ikke håndtert eksplisitt i det gamle skriptet. | Håndteres nå, og antallet logges. |

## 2. Hva som er gjort

1. **Rådata** (`data/raw/ssb/`, se [`MANIFEST.md`](../data/raw/ssb/MANIFEST.md)): SSB 08092, 01180 og 07459 er hentet på nytt med *alle* partier og *alle* historiske koder, SSBs egne 2024-aggregater og kodelister. Summen over kodene er lik SSBs landstall.
2. **Kodeoversetting** (`scripts/bygg_kodemapping.py` → `data/processed/kodemapping_2024.csv`): Oversettingen er datadrevet og bruker ikke navn. For hvert år 1986–2026 skal befolkningen i de historiske kodene summere *nøyaktig* til SSBs «Kommuner 2024, sammenslåtte tidsserier». Det gir en kontroll med heltallslikhet for hver kobling. Unntakene der SSB ikke har tidsserie, er satt eksplisitt og merket:
   - **Snillfjord** (delt i 2020): 15,3 % til Heim, 33,9 % til Hitra og 50,8 % til Orkland.
   - **Tysfjord** (delt i 2020): 42,2 % til Narvik og 57,8 % til Hamarøy.
   - **Ålesund 2020–2023**: 13,8 % til Haram.

   Andelene for Snillfjord og Tysfjord er anslått fra befolkningsendringen 1.1.2019 → 1.1.2020. Andelen for Ålesund er anslått fra befolkningen 1.1.2024. Kommunene er små, så usikkerheten gjelder få stemmer.
3. **Datasett** (`scripts/bygg_datasett.py`, som erstatter `hent_data.py`): Kolonnene er `kom2024, navn, aar, parti, stemmer, total_stemmer, prosent, sum_9parti, prosent_9parti, dekning, estimert`.
   - Partier: 01–08, 55 (Rødt, RV og FMS) og **99 Andre**.
   - Befolkningen gjelder 1.1. i hvert år. Analysene bør bruke **1.1. i valgåret** (dokumentert, ikke håndhevet).
   - `kom_mapping.csv` beholdes for bakoverkompatibilitet, men er nå generert fra den nye oversettingen.
4. **Kontroller** (`scripts/kontroller_datasett.py`) kjøres etter hver bygging og feiler med kode 1 ved avvik.

Kjøring: `python scripts/bygg_kodemapping.py && python scripts/bygg_datasett.py && python scripts/kontroller_datasett.py`

## 3. Kontrollresultater (kriteriene K1–K7)

| Kriterium | Resultat |
|---|---|
| K1 Fullstendighet | Alle 848 koder med stemmer i 1987–2025 og alle koder med befolkning i 1986–2026 er oversatt. 357 kommuner per år. |
| K2 Entydighet | Hver kode og hvert år har en eksplisitt oversetting med metode: `arvet`, `eksakt`, `eksakt-sum`, `delt` eller `kjent 2020`. Andelene summerer til 1. |
| K3 Delinger | 3 delinger er fordelt og merket `estimert`: 40 kommune/år i hvert valgslag. Små grenseoverføringer (22 stykker, 2 602 personer i 1987–1996) er ikke fordelt, fordi både SSB og den nye oversettingen behandler dem som del av koden de lå i. |
| K4 Avstemming | Summen i rådata er lik ferdigtabellen for alle år (avvik < 0,01 stemmer, som skyldes avrunding av delte stemmer). Landstallene for Ap, FrP, H og Sp er like SSBs i alle 20 valg. 12 145 ST-celler og 6 331 KV-celler for uendrede kommuner er like SSB, med 0 avvik. |
| K5 Kontinuitet | Stemmer per innbygger: 26 ST- og 4 KV-verdier ligger mer enn 6 MAD fra årsmedianen. Alle gjelder svært små kommuner, som Utsira, Træna, Båtsfjord og Hasvik, der dette er realistisk. Ingen tyder på feil i koblingen. |
| K6 Befolkning | 357 × 41 år, lik SSBs aggregat i 14 459 kommune/år. Bevisste avvik er Ålesund og Haram 2020–2023. Heim, Hitra, Orkland, Narvik og Hamarøy før 2020 er egen oversetting, der SSB har 0. |
| K7 Reproduserbarhet | To kjøringer gir identiske filer (md5). Byggingen avhenger bare av filer i repoet. |

**Kryssjekk mot PDF-rapporten:** A2 fant 28 sammenslåinger i 1987–1996 i SSB-rapport 99/13. 27 stemmer med den datadrevne oversettingen. Det siste (224 personer fra Ringsaker til Hamar i 1992) er en overføring av en del av en kommune, der Ringsaker-koden fortsatte. Den behandles som en grenseendring, både av SSB og her.

## 4. Hva som endres i analysene (ikke kjørt på nytt)

| Fil eller analyse | Berøres av | Forventet endring |
|---|---|---|
| `analyse.py`, Senteropprøret 1989→93 (`index.html`, `pedersen.html`, `ap_sp_frp_ts.html`, `sp_taper.html`, `ap_bonus.html`) | F1, F2, F3, F4, F6, F8 | Nasjonalt: Sp 1989 går fra 4,9 til 6,5 % og Ap fra 51,8 til 34,3 %. Gjennomsnittlig ΔSp per kommune går fra 18,8 til 15,4 pp. **Sammenhengen med befolkningsvekst 1986–90 står seg:** helningen går fra −0,69 til −0,62 og r fra −0,43 til −0,44. n går fra 352 til 357. |
| `analyse_2017.py` (2013→17) | F4, F6, F10 | Små nasjonale endringer (Sp 2017: 10,5 → 10,3 %). Andelene for sammenslåtte kommuner endres. |
| `analyse_2021.py`, `seksjon_2021.html` | F4, F5, F6, F10 | Haram og Ålesund kommer med i 2021. Sp 2021 nasjonalt: 14,0 → 13,5 %. |
| `matrise.py` (`matrise.html`, `sp_matrise_1721.html`, `kvadrant_sp.html`) | F4, F6, F8, F10 | Kvadrantplasseringen kan endres for kommunene som var koblet feil (F2–F5), og for de fem som tidligere manglet. |
| `analyse_panel.py` → `panel_resultater.csv`, `panel_plot.html` | Alle over | Hele panelet 1987–2025 må estimeres på nytt. 1989 og kommunevalgene er mest endret: 10–16 % av KV-cellene har endringer på mer enn 2 pp på grunn av den nye nevneren. |
| `litteratur_notat.md` | – | Tallene der er hentet fra litteraturen (Sp 6,5 → 16,7 %), og de stemmer med det nye datasettet (6,5 → 16,7 %). Det gamle datasettet ga 4,9 → 17,4 %. |

Anbefaling: bytt sentralitetskoblingen i analysene til `sentralitet_2024.csv`, og velg bevisst mellom `prosent` (offisiell) og `prosent_9parti`. Kjør så analysene på nytt.

## 5. Åpne spørsmål og begrensninger

- **Kilden til `sentralitet.csv` er udokumentert.** Den har 4 klasser (0–3) og 428 koder, altså kommunestrukturen fra 2016–2017, og den er ikke SSBs offisielle 6-delte sentralitetsindeks. Den bør erstattes av SSBs sentralitetsindeks 2020 eller 2024 for 2024-kommunene, fra Klass eller SSB-tabell. Det er ikke gjort her, fordi Klass-API-et er sperret i dette miljøet.
- **Estimerte delinger:** Snillfjord (ca. 1 000 innbyggere) og Tysfjord (ca. 1 900) er fordelt med andeler anslått fra befolkningsendringen. Ålesund og Haram 2020–2023 er fordelt etter befolkningen i 2024. Stemmemønstrene kan avvike fra befolkningsandelen.
- **Stemmesteder utenfor kommunen:** SSB fører forhåndsstemmer på bostedskommunen, så dette krever ingen korrigering.
- **Parti 99 Andre** omfatter lokale lister, som i noen kommunevalg er svært store. Analyser av endring i partioppslutning i kommunevalg bør ta hensyn til dette.

## 6. Dekningsrapport

| Del | Utført av | Modell | Resultat |
|---|---|---|---|
| Forhåndssjekk og funn F1–F7 | Orkestrator | standard | Se `QA_PROMPT.md` §3 |
| A1 Rådata | Orkestrator (avvik fra planen, se under) | standard | 20 valgfiler, 2 valgaggregater, 2 befolkningsfiler og 3 kodelister |
| A2 Grenser 1987–1996 (PDF, 90 s.) | Arbeidsagent | standard | 55 endringer (28 sammenslåinger, 22 overføringer og 5 samiske navneformer). `arbeid/A2_grenser.json` |
| K1 Kontroll av A2 | Kontrollagent | Sonnet | Godkjent: 55/55 ok, alle kriterier komplette, ingenting uten kontroll. `kontroll/K1_A2.json` |
| A3 Reformer 1999–2024 | Erstattet av datadrevet oversetting mot SSB-fasit (orkestrator) | – | Fant 9 feil i den gamle reformtabellen (F4) |
| K2 Kontroll av A3 og ny oversetting | Erstattet av kontroller i kode (C1–C5) og kryssjekk mot A2 | – | 0 harde feil |

**Avvik fra den godkjente planen** (6 agenter): Det ble brukt 2 agenter, ikke 6.
- **A1 ble ikke egen agent.** Store SSB-svar lagres rett til fil, så nedlastingen fylte ikke hovedkonteksten (T3 var ikke oppfylt).
- **A3 og K2 falt bort.** Klass-API-et er sperret, og SSBs befolkningsaggregat gir en strengere og uavhengig fasit (heltallslikhet per år) enn en manuell gjennomgang av en reformliste.
- **K1a og K1b ble slått sammen til K1**, fordi PDF-teksten er 139 kB, altså under grensen for én kontrollør.

Uenighet mellom arbeider og kontroll: ingen.

**Ikke kontrollert:**
- Partier utenom Ap, FrP, H og Sp mot SSBs landstall. Bevaringskontrollen C1 dekker indirekte alle partier.
- Om lokale lister (90–92) i enkelte kommuner egentlig er avleggere av nasjonale partier.
- Innholdet i analysene og HTML-tekstene.
