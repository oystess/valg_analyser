# valg_analyser

Analyse og visualisering av norske valgdata og meningsmålinger. Hovedleveransen er
en statisk HTML-rapport (`index.html`) som publiseres til GitHub Pages, og som
undersøker sammenhengen mellom **befolkningsvekst** og **partioppslutning** i norske
kommuner ved stortingsvalg.

## Hovedfunn (den publiserte rapporten)

**Hypotese:** Ap tapte velgere til Sp fra 2013 til 2017 i kommuner med lavest
befolkningsvekst. Analysen bekrefter dette statistisk (p < 0,0001):

- Sterk negativ korrelasjon mellom endring i Ap-oppslutning og endring i
  Sp-oppslutning per kommune (ΔAp vs ΔSp).
- Kommuner med lav/negativ befolkningsvekst 2006–2016 hadde signifikant større
  Ap-fall og større Sp-vekst 2013→2017.
- Sammenhengen er robust også når man kontrollerer for SSBs sentralitetsindeks.

## Repostruktur

```
.
├── index.html              # Generert rapport (GitHub Pages-forsiden). IKKE rediger for hånd.
├── scripts/
│   ├── analyse.py          # Hovedskript: leser data, kjører OLS-regresjoner, genererer index.html
│   ├── Alle meningsmålinger.R   # Henter meningsmålinger fra pollofpolls.no (eldre R-arbeidsflyt)
│   ├── Videre analyser.R        # Videre R-analyse av polls.csv (blokkinndeling m.m.)
│   ├── Valgresultat.R           # R: bearbeider valgresultat 2013/2017 per kommune
│   ├── befolkningstall.R        # R: henter befolkningstall fra SSBs API
│   └── valganalyser v01.R       # R: eldre parsing av Norstat-målinger
├── data/
│   ├── raw/                 # Kildedata (SSB-eksporter, valgresultater, sentralitet, distriktstall)
│   │   ├── data_valg_1317.csv   # SSB 08092, valg 2013/2017 (pre-2020 kommunekoder)
│   │   ├── data_valg_2125.csv   # SSB 08092, valg 2021/2025 (2024-kommunekoder)
│   │   ├── distriktstall.xlsx   # Befolkning (B06/B16) + 10-årig vekst + sentralitet
│   │   ├── sentralitet.csv      # SSBs sentralitetsindeks (4 grupper)
│   │   └── valg2009/2013/2017*.csv  # Rå valgresultater per parti/kommune
│   └── processed/
│       ├── polls.csv       # Meningsmålinger (pollofpolls, gallupsnitt) – auto-oppdatert ukentlig
│       └── polls.rds       # R-serialisert variant av samme
├── output/Rplot.png        # Eldre R-plot
└── .github/workflows/      # CI: se under
```

## Hovedskriptet: `scripts/analyse.py`

Selvforsynt Python-skript som produserer hele `index.html`.

**Kjøring:**
```bash
pip install numpy pandas statsmodels plotly openpyxl
python scripts/analyse.py      # kjør fra repo-roten
```

**Merk om filstier:** Funksjonene bruker relative stier fra repo-roten
(f.eks. `data/raw/data_valg_1317.csv`), så skriptet må kjøres fra repo-roten.

**Flyt i skriptet:**
1. `hent_*` – leser rå CSV/Excel.
2. `prosesser_valg` / `prosesser_befolkning` / `last_sentralitet` – tidy-format.
3. `bygg_analysedata` – merger valg 2013/2017 + befolkningsvekst + sentralitet,
   beregner `delta_<parti>`.
4. `kjor_regresjoner` – OLS (statsmodels), bivariat + multivariat.
5. Plotly-figurer: nasjonal tidsserie, ΔAp-vs-ΔSp-scatter, to regresjonsscatter
   med KI-bånd.
6. `bygg_html` – setter alt inn i en Tailwind-basert HTML-mal (Plotly + Inter-font
   via CDN) og skriver `index.html`.

Partikoder, partifarger og sentralitetsnavn ligger som konstanter øverst.

## GitHub Actions (`.github/workflows/`)

- **update-polls.yml** – Cron hver mandag 06:00 UTC (+ manuell trigger). Laster ned
  fersk `gallupsnitttabell` fra pollofpolls.no og committer `data/processed/polls.csv`
  hvis endret. (Dette er kilden til de hyppige "Update polls.csv"-commitene.)
- **deploy.yml** – Deployer hele repoet til GitHub Pages ved push til `master`.
- **jekyll-gh-pages.yml** – Alternativ Jekyll-deploy (også ved push til `master`).
  `.nojekyll` finnes i roten, så Pages serverer filene rått uten Jekyll-prosessering.
  De to deploy-workflowene overlapper – vurder å konsolidere til én.

## Datakilder

- **SSB tabell 08092** – stortingsvalg, oppslutning per kommune/parti.
- **Distriktsindikatorene** – befolkning (B06/B16) og 10-årig vekst 2006–2016.
- **SSBs sentralitetsindeks** – kommuner i 4 sentralitetsgrupper.
- **pollofpolls.no** – nasjonale meningsmålinger (gallupsnitt).

Det finnes en `SSB_MCP`-server tilgjengelig i miljøet for å hente ferske SSB-data direkte.

## Status og aktuelle oppgaver for Fable

- R-skriptene er en eldre arbeidsflyt; Python-skriptet er den aktive analysen.
  Meningsmålingsdataene (`polls.csv`) brukes foreløpig ikke av `analyse.py` – kun
  valg-/befolkningsdata. Mulig utvidelse: koble polls inn i rapporten.
- To overlappende Pages-deploy-workflows kan ryddes.
- Repoet ble nylig reorganisert i `data/`, `scripts/`, `output/` (PR #10); sjekk at
  alle stier stemmer etter flyttingen.

## Historikk

Utviklingsspråk startet i R, ble utvidet med et Python-basert analyse- og
rapportverktøy, og reorganisert i logiske undermapper (PR #10). Nåværende
publiserte rapport bruker Tailwind CSS + Plotly 3.4.0.
