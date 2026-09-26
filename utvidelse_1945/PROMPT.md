# Prompt: Utvide valgdatasettet tilbake til 1945

*Utkast 2026-09-26. Metoden er den samme som i QA-runden (`qa/QA_PROMPT.md`, `qa/QA_RAPPORT.md`), og arbeidet følger skillen `agent-orkestrering`. Arbeidet starter ikke før spørsmålene i §8 er besvart og planen er godkjent.*

---

## 1. Sluttprodukt (én setning)

Stortingsvalg 1945–2025 og kommunestyrevalg 1945–2023 på fast kommunestruktur. Hver kodeoversetting har kilde, hvert år er avstemt mot SSBs landstall, delinger er dokumentert med fordelingsnøkkel, og en QA-rapport sier hva som er sikkert og hva som er estimert.

## 2. Forhåndssjekk (2026-09-24/26)

| Kilde | Dekning | Funn |
|---|---|---|
| SSB 08092 Stortingsvalg | 1945–2025, alle historiske koder (`vs_KommunValg`) | ST 1945: 744 kommuner med stemmer, 1 485 225 godkjente stemmer i de ni største kategoriene. Bondepartiet (71) er Sps forløper, og NKP (09) er stort (176 535). |
| SSB 01180 Kommunestyrevalg | 1945–2023 | Ikke sjekket i detalj ennå |
| SSB 06913 Befolkning | Per historisk kode fra 1951 (`vs_Kommuner1951`) og «Kommuner 2024, sammenslåtte tidsserier» (`agg_KommSummerHist`) | **Fasiten har hull:** SSB fører 268 197 personer (1951), 288 956 (1961) og 171 888 (1971) på «Rest» og setter 0 for 2024-kommuner som ble berørt av delinger (Ringerike, Heim, Orkland, Narvik, Hamarøy, Rana, Brønnøy, Sørreisa m.fl. i ulike år). Metoden med heltallslikhet virker for resten. |
| SSB 07459 Befolkning | Fra 1986 | Allerede brukt |
| `data/raw/rapp_9913.pdf` | Alle endringer 1838–1996, med **folketallet i områder som ble overført** | Den eneste kilden til fordelingsnøkler for delinger før 1986. A2/K1 har bare hentet ut endringer fra 1987 og senere. |
| Felleslister (partikode 90a–90h) | Fra 1960-tallet | ST 1965: ca. 37 500 stemmer. Må ha en regel (§8, spørsmål 2). |
| Befolkning 1945–1950 | **Mangler i SSB-tabellene** | For valgene i 1945, 1947 og 1949 må vi bruke 1951-strukturen og endringene 1945–1950 fra PDF-en. |

## 3. Metode (utvidelse av den som ble brukt for 1986–2026)

1. **Rådata:** Hent 08092 (1945–1985) og 01180 (1945–1983) med alle partier og alle historiske koder, pluss 06913 per historisk kode og som 2024-aggregat for 1951–1986. Lagre i `data/raw/ssb/` med manifest.
2. **Kodeoversetting 1951–1985:** `scripts/bygg_kodemapping.py` utvides bakover. For hvert år skal befolkningen i de historiske kodene summere nøyaktig til SSBs 2024-aggregat. Der SSB har 0 eller «Rest», brukes delingsnøkler fra PDF-en: folketallet i det overførte området delt på folketallet i den gamle kommunen. Hver deling merkes `estimert` med sidehenvisning.
3. **1945–1950:** Oversettingen fra 1951, pluss eksplisitte endringer 1945–1950 fra PDF-en.
4. **Kontroller** (utvid `scripts/kontroller_datasett.py`):
   - bevaring mellom rådata og ferdigtabell
   - landstall per parti og år mot SSB
   - uendrede kommuner mot SSBs aggregat
   - befolkning mot 06913-aggregatet
   - for delte kommuner: at folketallene fra PDF-en summerer til den gamle kommunens folketall innenfor ±2 %, ellers flagges de
5. **Overlapp:** 1987–2025 skal bli identisk med dagens datasett. Det testes i kode.

## 4. Arbeidsdeling (agent-orkestrering)

- **T2 er oppfylt:** PDF-en på 90 sider må leses i sin helhet for 1945–1986.
- **Arbeidere:** 2 (fylke 01–10 og fylke 11–20). Hver trekker ut *alle* endringer 1945–1986 med dato, fra- og tilkode, områdebeskrivelse og folketall, som i A2-briefen, men for hele perioden.
- **Kontroll:** 2 kontrollagenter (`sonnet`), én per halvdel, som sjekker hvert funn mot PDF-en og leter etter det som mangler.
- **Datakontroll:** 1 kontrollagent (`sonnet`) regner landstall, bevaring og delingsnøkler på nytt fra rådata, uten å se koden.
- **Orkestrator:** Nedlasting (store SSB-svar lagres rett til fil), oversetting, bygging, kontroller i kode og rapport.
- **Sum:** 5 agentstarter, ca. 0,35 mill. tokens i overhead. Anslått totalt 0,8–1,2 mill. tokens. Det er mer enn 4 agenter, så planen **må godkjennes**.

## 5. Kjente vanskeligheter

- **Sammenslåingsbølgen 1958–1967** (Schei-komiteen): Antall kommuner gikk fra 744 til 454, med mange delinger av grenser. Dette er hoveddelen av arbeidet.
- **Partikontinuitet:**
  - Bondepartiet (71) → Sp (05, fra 1959)
  - Sosialistisk Folkeparti (70, 1961–69) → SV (06)
  - NKP (09) står alene
  - RV (11, 1973–2007) → Rødt
  - Anders Langes parti (75, 1973) → FrP (02)
  - Det nye Folkepartiet (74, 1973–77) og Det Liberale Folkepartiet (12) er utbrytere fra Venstre
- **Felleslister:** Særlig borgerlige felleslister (Sp/KrF/V) i ST 1965–1973 og mange lokale felleslister i KV.
- **Flertallsvalg:** I små kommuner med flertallsvalg (personvalg) mangler partistemmer, særlig i kommunevalg. Datasettet har allerede kolonnen `dekning` som fanger dette.
- **Svalbard og utenlandsstemmer:** Sjekkes mot landstallene.
- **Befolkningsvariabler før 1986:** Bare folketall, fødselsoverskudd og flytting (06913, fra 1951). Alder, utdanning og inntekt finnes ikke på kommunenivå i SSB-tabellene så langt tilbake.

## 6. Leveranse

- `data/processed/stortingsvalg_1945.csv`, `kommunestyrevalg_1945.csv`, `befolkning_1951.csv` og `kodemapping_1945.csv`. De eksisterende filene for 1987+ beholdes uendret, med en test som bekrefter at overlappen er identisk.
- `utvidelse_1945/QA_RAPPORT.md` med kontrollresultater, liste over delinger med nøkkel og kilde (side i PDF-en), dekningsrapport og hva som er estimert.
- Kode i `scripts/` (utvidet bygg-, mapping- og kontrollskript), commit og push.

## 7. Grenser

- Ikke endre analysene eller `index.html`.
- Ikke lag pull request.
- Hent ikke nye datakilder utover SSB-tabellene og PDF-en i repoet uten å spørre.

## 8. Spørsmål til Øystein og svarene (2026-09-26: «Ja, kjør i denne sesjonen hvis det ikke blir mye dyrere»)

| # | Spørsmål | Svar |
|---|---|---|
| 1 | Kommunestruktur | 2024-kommuner (delinger estimert og merket) som hovedfil, pluss stabile enheter som alternativ |
| 2 | Felleslister | Egen kategori som standard. Fordeling etter forrige valg som robusthetsvariant. |
| 3 | Partikontinuitet | Bondepartiet → Sp, SF → SV, ALP → FrP, RV → Rødt. NKP står for seg selv. |
| 4 | Valgene før 1951 | 1951-strukturen med endringene 1945–1950, merket som mindre sikre |
| 5 | Filer | Egne `*_1945.csv`-filer. 1987+ uendret, med test av overlappen. |
| 6 | Tilleggsvariabler | Bare folketall, fødselsoverskudd og flytting før 1986 |
| 7 | Plan og kostnad | Godkjent (5 agenter) |
| 8 | Hvor | Denne sesjonen |
