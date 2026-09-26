# Rapport: Valgdatasettet utvidet tilbake til 1945

*2026-09-26. Bygget etter `utvidelse_1945/PROMPT.md` (svar i §8), med samme metode som QA-runden i `qa/`.*

## 1 Hva som er bygget

| Fil (`data/processed/`) | Innhold |
|---|---|
| `kodemapping_1945.csv` | Hver historisk kommunekode × år 1945–1985 → 2024-kommune(r) med andel og metode (26 632 rader) |
| `stortingsvalg_1945.csv` | 21 stortingsvalg 1945–2025 på 357 2024-kommuner, 12 partigrupper |
| `kommunestyrevalg_1945.csv` | 21 kommunestyrevalg 1945–2023 på samme form |
| `befolkning_1951.csv` | Folkemengde 1951–2026 på 2024-kommuner |
| `stabile_enheter.csv` | 357 kommuner → 279 stabile enheter (36 enheter slår sammen 2–10 kommuner) |
| `*_1945_stabil.csv` | Valgfilene aggregert til stabile enheter |

Kolonner i valgfilene: `kom2024, navn, aar, parti, stemmer, total_stemmer, prosent, estimert, sikkerhet`.
De eksisterende `*_2024.csv`-filene (1987–) er uendret; de nye filene er identiske med dem i overlappen (C3).

**Partigrupper (samme for hele perioden):** 01 Ap · 02 FrP (inkl. ALP 1973) · 03 H · 04 KrF ·
05 Sp (inkl. Bondepartiet) · 06 SV (inkl. SF 1961–69 og Sosialistisk Valgforbund 1973) · 07 V ·
08 MDG · 55 Rødt (inkl. RV/FMS) · 09 NKP · 90 Felleslister · 99 Andre.

**Sikkerhet:** `høy` = 1986– eller harmonisert folketall er nøyaktig lik SSBs egen 2024-serie (06913);
`middels` = 1951–85 der delinger er fordelt etter rapport 99/13 eller SSB fører deler på «Rest»;
`lav` = 1945–50 (1951-struktur uten folketall).

| Periode | Andel kommuner med `høy` (ST) |
|---|---|
| 1945–49 | 0 % (alle `lav`) |
| 1953–61 | ~66 % |
| 1965–73 | ~93 % |
| 1977–85 | 99 % (5 `middels`) |
| 1989– | 100 % |

## 2 Metode

1. **Kodemapping bakover** (`scripts/bygg_kodemapping_1945.py`): Fra 1985 og bakover til 1951 løses hvert år
   datadrevet – folketallet i de historiske kodene (SSB 06913) må summere eksakt til SSBs 2024-aggregat.
   Kodegjenbruk håndteres ved at identitet = grunnkode + år. Der kodene opphører, overstyrer
   grenseendringer fra SSB-rapport 99/13 (hentet av Pa/Pb) løseren; delinger fordeles etter folketallet
   som ble overført. Delvise overføringer under 10 % av kommunens folketall er holdt hele.
   1945–1950 bruker 1951-strukturen pluss hendelsene i perioden.
2. **Valg** (`scripts/bygg_datasett_1945.py`): Stemmer fordeles med andelene. Kommunestyrevalg holdt for
   neste års struktur (f.eks. KV 1963) kjennes igjen ved at kommuner som forsvant ved årsskiftet ikke har stemmer.
3. **Stabile enheter** (`scripts/bygg_stabile_enheter.py`): 2024-kommuner som deler ≥ 5 % av en historisk
   kode begge veier, slås sammen (union-find). Gir tall som ikke avhenger av fordelingsnøkler.

## 3 Kontroller

### Automatiske (`scripts/kontroller_datasett_1945.py` → `kontroll/automatiske_kontroller.md`) – 0 harde feil

| | Resultat |
|---|---|
| C1 Bevaring | Alle stemmer i SSB-rådata gjenfinnes per år og gruppe (avvik < 1 stemme) |
| C2 Landstall | Ap, H, Sp (+Bondepartiet), NKP (ST) og Ap, H, Sp (KV) lik SSB alle år 1945–85 |
| C3 Overlapp | 0 avvik mot `*_2024.csv` fra 1987 |
| C4 Befolkning | 10 512 av 11 983 kommune-år 1951–85 er eksakt lik SSB; 819 kommune-år (63 kommuner, mest Nordland/Troms/Vestland) avviker > 10 % fordi SSB fører delte områder på «Rest» |
| C5 Kontinuitet | Ingen kommune forsvinner/dukker opp; 40 hopp > 8 % år til år, alle små kommuner (kraftutbygging o.l.) |
| C6 Struktur | 357 kommuner alle år fra 1949 (ST) / 1967 (KV); 1945–63 mangler noen få der kommunen ikke fantes |

### Agentkontroller

| Agent | Oppgave | Resultat |
|---|---|---|
| Pa, Pb | Hente grenseendringer 1945–85 fra rapport 99/13 | 294 + 520 hendelser |
| Ka | Blindet kontroll av Pa | Godkjent: 290 ok, 4 usikre (3 er motstrid i selve kilden, korrekt notert) |
| Kb | Blindet kontroll av Pb | Godkjent: 517 ok, 3 usikre |
| KD | Uavhengig datakontroll av ferdige filer | Se §4 |

## 4 KD – uavhengig datakontroll

*(fylles inn når KD er ferdig)*

## 5 Kjente begrensninger

- **1945–1950 er `lav` sikkerhet:** SSB har ikke folketall per kommune før 1951, så delinger i perioden
  fordeles med 1951-tall.
- **SSB «Rest»:** Der SSB selv fører delte områder på én kommune eller «Rest», avviker vårt folketall fra SSBs
  2024-serie (C4). Vi følger rapport 99/13, som er mer presis, men tallene er ikke eksakt lik SSBs.
- **Felleslister** (gruppe 90) er egen kategori. Robusthetsvarianten der fellesliste-stemmer fordeles på
  partiene er **ikke laget**: SSB oppgir ikke hvilke partier som inngår i hver liste før 1985.
  Analyser av Sp/KrF/V/H i 1950–70-årene bør derfor sjekke at resultatet tåler at felleslister holdes utenfor.
- **1973:** NKP stilte på Sosialistisk Valgforbund og har derfor 0 i ST 1973; alt ligger i SV (06).
  Det nye Folkepartiet (1973–77) ligger i 99.
- Delvise overføringer under 10 % av en kommunes folketall er ikke fordelt (kommunen er holdt hel).

## 6 Avvik fra planen

- Fellesliste-varianten ble ikke laget (se over).
- Kode 79 (Sosialistisk Valgforbund) var først falt i 99; oppdaget i landstallskontrollen og rettet før
  commit a6b3176. KD fikk beskjed underveis.
- Terskelen for stabile enheter ble satt til 5 % (lavere terskel ga urimelig store enheter).

## 7 Dekning

5 agentstarter: Pa, Pb (hovedmodell), Ka, Kb og KD (kontrollører med annen modell, blindet for produsentens resonnement). Ingen nye starter
utover planen.
