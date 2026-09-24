# QA av valgdatasettet: orkestreringsprompt

*Utkast 2026-09-24. Skrevet etter skillen `agent-orkestrering`. Arbeidet starter ikke før spørsmålene i §7 er besvart og planen er godkjent.*

---

## 1. Sluttprodukt (én setning)

Et reproduserbart og dokumentert datasett med stortingsvalg 1989–2025, kommunestyrevalg 1987–2023 og befolkning 1986–2026 på 2024-kommunestruktur. Hver kommunekodeoversetting skal ha kilde, og hvert år skal være avstemt mot SSBs offisielle landstall. Til datasettet hører en QA-rapport som sier hva som var feil, hva som er rettet, og hvilke analyser som må kjøres på nytt.

## 2. Hva som skal kvalitetssikres

Byggekjeden slik den er i dag:

| Steg | Fil | Metode i dag |
|---|---|---|
| Nedlasting | *(ikke i repoet)* | JSON fra SSB-MCP (tabell 08092, 01180 og 07459), lagret i en midlertidig `tool-results`-mappe fra en tidligere Claude-sesjon |
| Grenseendringer 1987–1998 | `data/raw/grenser_mapping.csv` (53 rader) | Hentet fra `rapp_9913.pdf` (100 s.) med Claude Haiku (`scripts/grenser.py` og `les_grenser_pdf.py`) |
| Reformer 1999–2024 | `data/raw/kommunereform_mapping.csv` (123 rader) | Skrevet for hånd eller av en modell. Kilden er ikke dokumentert. |
| Kodeoversetting | `scripts/hent_data.py` → `data/processed/kom_mapping.csv` | Eksakt navnematch først, så reformtabell, så normalisert navn, så grensetabell |
| Aggregering | `hent_data.py` → `stortingsvalg_2024.csv`, `kommunestyrevalg_2024.csv`, `befolkning_2024.csv` | Summerer stemmer per 2024-kode. «Prosent» er regnet av summen for 9 partier. |
| Bruk | `analyse*.py`, `matrise.py`, `analyse_panel.py`, `panel_resultater.csv`, HTML-figurer | Leser de prosesserte filene |

## 3. Funn fra forhåndssjekken (orkestratoren, 2026-09-24)

Jeg fant disse funnene med raske kodesjekker, før noen subagenter ble startet. De viser at en full QA er nødvendig.

- **F1 – Stortingsvalget 1989 er kraftig overtelt.** Summen av stemmer for de 9 partiene er 3,51 mill. i 1989, mot 2,38 mill. i 1993. Forholdet mellom 1989 og 1993 er ca. 1,5 i *alle* 357 kommuner (median 1,48). Aps nasjonale andel blir 51,8 % i 1989 (faktisk ca. 34 %). I Oslo er Ap-stemmene 178 828. Sannsynlig årsak er at flere nedlastinger av 1989 er lastet inn to ganger, altså samme type feil som den som allerede er rettet for befolkningstallene (commit 945f7ad). **Senteropprøret-analysen (ΔSp og ΔAp 1989→1993) er bygget på disse tallene.**
- **F2 – Navnematch først gir feil kobling.** `0414 Vang` (Hedmark, slått inn i Hamar i 1992) er oversatt til `3454 Vang` (Valdres). Vang i Valdres får dermed 10 900 stemmer i 1989, mot 942 i 1993. Den samme logikken kan ha rammet andre kommuner med samme navn, som Nes, Bø, Os, Våler, Sande, Herøy, Hole, Frosta og Fjære.
- **F3 – Kommuner som ble delt, er ikke delt.** Mappingen er en `dict`, så én gammel kode får bare ett mål. Ålesund og Haram (2020–2023) gir derfor 0 stemmer for 1580 Haram i KV 2019, og Haram mangler helt i ST 2021. Det samme gjelder alle delinger i 1987–1998.
- **F4 – Nevneren er ikke offisiell.** `prosent` = partiets stemmer / summen av 9 partier. «Andre» og blanke stemmer er ikke med, så andelene er systematisk høyere enn SSBs. Effekten varierer mellom år og kommuner, for eksempel der det er store lokale lister i kommunevalg.
- **F5 – Datasettet kan ikke reproduseres.** Rå-JSON-filene ligger ikke i repoet. `DEFAULT_TOOL_RESULTS` peker på en sesjonsmappe som ikke finnes lenger.
- **F6 – Hull og nuller.** Enkelte kommune-år har 0 eller manglende total, for eksempel 1816 i KV 2019 og 1151, 1856 og 4629 i KV 2015. Det må avklares om dette skyldes flertallsvalg (personvalg), manglende data eller feil i oversettingen.
- **F7 – 267 av 1 170 historiske koder er ikke oversatt.** De fleste er trolig fra før 1987 og har ingen betydning, men det må bekreftes at ingen koder med stemmer i 1987–2025 faller bort i stillhet (`skipped`).

## 4. Vurdering etter skillen (§1)

- **T2 er nådd.** `rapp_9913.pdf` er 100 sider og må gjennomgås fullstendig, fordi Haiku-ekstraksjonen er uverifisert.
- **T3 er nådd.** Å hente data på nytt fra SSB (tre tabeller, mange spørringer og store JSON-svar) ville fylt hovedkonteksten.
- Resten (kodegjennomgang, avstemming og ny bygging) er under terskelen, og det gjør orkestratoren selv.

**Valg:** 3 arbeidere og 3 kontrollører. Det er mer enn 4 agenter, så **planen må godkjennes før oppstart**.

## 5. Plan

### Deloppgaver

| ID | Utsnitt | Nøyaktig input | Modell | Output |
|---|---|---|---|---|
| **A1** Rådata | SSB-nedlasting | SSB-MCP: 08092 (1989–2025), 01180 (1987–2023) og 07459 (1986–2026). *Alle* partier, inkludert «Andre»/«Øvrige» og totalt antall godkjente stemmer. Én spørring per år. | standard | `data/raw/ssb/<tabell>_<år>.json` + `arbeid/A1_manifest.json` (spørring, radantall, sjekksum, landstotal per år) |
| **A2** Grenser 1987–1998 | `data/raw/rapp_9913.pdf`, alle sider | PDF + fylkesoversikten i `les_grenser_pdf.py`. Arbeideren **ser ikke** `grenser_mapping.csv` før egen liste er ferdig. | standard | `arbeid/A2_grenser.json`: én rad per endring, med side, type, berørte personer og om endringen påvirker *stemmer* (sammenslåing eller deling) eller bare grenser |
| **A3** Reformer 1999–2024 | SSB Klass (kommuneinndeling, klassifikasjon 131, endringer og korrespondanser 1999–2024) | Klass-API eller -sider + `kommunereform_mapping.csv` | standard | `arbeid/A3_reformer.json`: hver kodeendring med kilde-URL, inkludert delinger (2020→2024: Ålesund/Haram, og fylkeskodebytter i 2024) |
| **O** Orkestrator | Kode og avstemming | `hent_data.py`, prosesserte filer, A1–A3 | standard | Ny mapping, ny bygging og QA-rapport (se nedenfor) |
| **K1a/K1b** Kontroll A2 | PDF-en delt i to (fylke 01–10 og 11–20) | PDF-utsnitt, K-kriteriene, `A2_grenser.json` | **sonnet** | `kontroll/K1a.json`, `kontroll/K1b.json` |
| **K2** Kontroll A3 og ny mapping | Klass + ny `kom_mapping.csv` | Kriterier, `A3_reformer.json`, ny mapping | **sonnet** | `kontroll/K2.json` |

A1 kontrolleres i kode av orkestratoren, med avstemming mot publiserte landstall. Den trenger ikke egen kontrollagent.

### Kriterier (felles for arbeidere og kontroll)

- **K1 Fullstendighet:** Hver kommune som har eksistert mellom 1987 og 2025, finnes med kode, navn og gyldighetsperiode.
- **K2 Entydighet:** Hver historisk kode får en *eksplisitt* oversetting med kilde. Navnematch er bare lov som forslag, og da merket «navnematch – verifisert mot kilde X».
- **K3 Delinger:** Når én gammel kode fordeles på flere nye, oppgis fordelingsnøkkelen: befolkning i området som ble overført, eller krets- eller stemmedata. Hvis ingen nøkkel finnes, merkes enheten «ikke fordelbar», og det føres en regel for hvordan den håndteres.
- **K4 Avstemming nasjonalt:** For hvert valgår skal summen av godkjente stemmer i kommunene være lik SSBs landstall, med 0 i avvik (utenlandsstemmer og Svalbard føres for seg). Partiandelene nasjonalt skal være lik de offisielle med ±0,05 pp.
- **K5 Kontinuitet per kommune:** Endringen i antall godkjente stemmer fra valg til valg, relativt til endringen i befolkning, skal ligge innenfor et fastsatt intervall. Alt utenfor intervallet listes og forklares.
- **K6 Befolkning:** Én rad per kommune og år. Summen skal være lik landstallet i 07459.
- **K7 Reproduserbarhet:** `python scripts/hent_data.py` skal gi identiske filer fra rådata som ligger i repoet, uten avhengighet til sesjonsmapper.

### Rekkefølge

1. A1, A2 og A3 kjøres parallelt. Samtidig går O gjennom `hent_data.py` og alle skriptene som bruker de prosesserte filene.
2. K1a, K1b og K2 kontrollerer. Deretter er det høyst én ny runde, og det som fortsatt er uavklart, rapporteres som uenighet.
3. O bygger mappingen på nytt (eksplisitte tabeller i stedet for navnematch først), bygger datasettet på nytt og kjører K4–K7 i kode.
4. O skriver `qa/QA_RAPPORT.md` med før/etter-diff per kommune og år, en dekningsrapport og en liste over analyser og figurer som endres (spesielt 1989→1993).
5. Analysene kjøres **ikke** på nytt i denne runden, med mindre du ber om det (se §7).

### Kostnad (TR)

6 agentstarter × ca. 70 000 = ca. 420 000 tokens i fast overhead, pluss selve arbeidet. Mitt anslag er 0,6–0,9 mill. tokens totalt. Det er under taket på 10 agentstarter.

## 6. Briefer

Fullstendige briefer (etter malene i skillen) skrives til `qa/briefer/` når planen er godkjent, fordi flere felt avhenger av svarene i §7. Faste krav som gjelder alle:

- Rådata med kilde (fil, side eller URL, rad). Ingen summer eller andeler i tekst.
- Retur til orkestratoren på høyst 5 linjer: filsti, antall funn og problemer.
- Ikke endre filer utenfor `arbeid/`, `kontroll/` og `data/raw/ssb/`.
- Kontrollørene starter fra «ikke godkjent». Svaret skal ha én rad per funn og per kriterium, og en IKKE SJEKKET-liste.

## 7. Spørsmål til Øystein før oppstart

Se samtalen. Svarene føres inn her.
