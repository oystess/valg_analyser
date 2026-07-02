# valg_analyser

Analyse av sammenhengen mellom **befolkningsutvikling** og **partioppslutning** i norske
kommuner 1987–2025, med Senterpartiets tre bølger (1993, 2017, 2021) som omdreiningspunkt.
Hovedleveransen er en interaktiv HTML-rapport (`index.html`) publisert på GitHub Pages.

Teorigrunnlag og hypoteser (H1–H7) er dokumentert i **`litteratur_notat.md`**
(Rokkan/Valen, Aardal, Jennings & Stoker, Auerbach 2024, Sánchez-García 2025, Nordregio 2025).
En kritisk gjennomgang av analysen mot litteraturen ligger i **`gjennomgang_analyse.md`**.

## Hovedfunn (per publisert rapport)

- **Strukturell, ikke dynamisk:** Between-estimatoren viser at kommuner med vedvarende
  befolkningsnedgang har systematisk høyere Sp-oppslutning (β=−0,22***, R²=0,40) og lavere
  Ap-oppslutning (β=−0,53***) over hele perioden. Fixed effects-modellene (within) viser
  derimot ingen signifikant dynamisk effekt — kortsiktige vekstsvingninger innen en kommune
  flytter ikke Sp-andelen.
- **Bølgene er ulike:** 1993- og 2017-bølgene var befolkningsgradert (β=−0,48*** i 1993);
  2021-bølgen var det *ikke* (β≈0, p=0,95) — den var bred og nasjonal.
- **Kommunevalg leder stortingsvalg:** KV-oppslutning predikerer STV-oppslutning to år
  senere (Sp: +0,156***), kontrollert for kommune- og år-effekter.
- **Fire bølger, tre mekanismer:** 1993 var sak-mobilisering gradert etter *statisk*
  periferi (og kollapset innen 1997); 2017 var left behind-gradert — faktisk
  befolkningsforvitring bar effekten, og gevinsten varte; 2021 var nasjonal metning
  uten gradient; 2025-kollapsen var brattest der oppturen var størst, mens FrPs
  samtidige bølge *ikke* var geografisk gradert. Se `scripts/analyse_mekanismer.py`.

> ⚠️ **Kjent datafeil:** Ap-stemmene for 1989 i `stortingsvalg_2024.csv` er dobbelttalt
> (se «Kjente feil» under). 1989-baserte tall (inkl. Senteropprøret-regresjonen β=−0,69)
> må regnes på nytt etter datafiks. Se `gjennomgang_analyse.md` for detaljer.

## Repostruktur

```
.
├── index.html               # Publisert rapport. GENERERT + INJISERT — ikke rediger for hånd
├── litteratur_notat.md      # Teorigrunnlag og hypoteser H1–H7
├── gjennomgang_analyse.md   # Kritisk gjennomgang av analysen mot litteraturen (2026-07)
├── scripts/
│   ├── hent_data.py         # Bygger data/processed/*.csv fra SSB MCP-nedlastinger (JSON)
│   ├── analyse.py           # HOVEDSKRIPT: Senteropprøret 1989→1993 + basis-index.html
│   ├── analyse_2017.py      # Dybde 2013→2017 + tre-bølge-sammenligning (injiserer)
│   ├── analyse_2021.py      # Dybde 2017→2021 + år-for-år β-tabell (injiserer)
│   ├── matrise.py           # 2×2 sentralitet × befolkningsretning, velgervektet (injiserer)
│   ├── analyse_mekanismer.py # Fire bølger, tre mekanismer: 1993/2017/2021/2025 (injiserer, idempotent)
│   ├── analyse_panel.py     # FE/between-panel 1987–2025 + timing-test (→ panel_plot.html)
│   ├── grenser.py           # Kommunegrense-mapping 1987–1998 fra SSB-PDF (Claude API)
│   ├── les_grenser_pdf.py   # PDF-ekstraksjon med Claude Haiku
│   └── *.R                  # Eldre R-arbeidsflyt (inaktiv)
├── data/
│   ├── raw/                 # Kildedata: sentralitet, grensemappinger, rapp_9913.pdf, m.m.
│   └── processed/
│       ├── stortingsvalg_2024.csv    # SSB 08092, 1989–2025, 357 kommuner (2024-grenser)
│       ├── kommunestyrevalg_2024.csv # SSB 01180, 1987–2023, samme struktur
│       ├── befolkning_2024.csv       # SSB 07459, 1986–2026
│       ├── kom_mapping.csv           # Historisk kommunekode → 2024-kode
│       ├── panel_resultater.csv      # Koeffisienter fra analyse_panel.py
│       ├── polls.csv                 # pollofpolls gallupsnitt — auto-oppdatert ukentlig
│       └── *.html                    # Genererte figurfragmenter
└── .github/workflows/       # update-polls (cron), deploy + jekyll-gh-pages (Pages)
```

## Kjøring

```bash
pip install numpy pandas statsmodels plotly linearmodels
# Alle skript kjøres fra repo-roten:
python scripts/analyse.py        # ⚠️ se advarsel under
python scripts/analyse_2017.py
python scripts/analyse_2021.py
python scripts/matrise.py
python scripts/analyse_mekanismer.py  # injiserer m/ egne merker — trygg å rekjøre
python scripts/analyse_panel.py  # → panel_plot.html + panel_resultater.csv
```

`grenser.py`/`les_grenser_pdf.py` krever i tillegg `anthropic`, `pymupdf`/`poppler-utils`
og `ANTHROPIC_API_KEY` — de trengs bare for å gjenskape grensemappingene.

### ⚠️ Regenererings-advarsel — les før du kjører `analyse.py`

`index.html` bygges i **lag**: `analyse.py` skriver basissiden, deretter *injiserer*
`analyse_2017.py`, `analyse_2021.py` og `matrise.py` sine seksjoner mellom
HTML-kommentarmerker (`<!-- === SLUTT ... === -->`) i den eksisterende filen.

**Basis-malen i `analyse.py` inneholder ikke disse merkene.** Kjører du `analyse.py`
alene, slettes alle injiserte seksjoner (~750 linjer), og delskriptene finner ikke
igjen injeksjonspunktene sine. Den committede `index.html` er altså et akkumulert
artefakt. Regenerer aldri rapporten uten å kjøre *hele* kjeden i rekkefølgen over —
og verifiser at alle seksjoner overlevde. (Å legge merkene inn i basis-malen er en
kjent utestående oppgave.)

## Datapipeline

1. **Nedlasting:** SSB-tabellene 08092/01180/07459 hentes via SSB MCP-verktøyet i en
   Claude Code-økt. Rå tool-result-JSON er **ikke committet** — bare de prosesserte CSV-ene.
2. **Kommunestruktur:** Alle årganger aggregeres til 2024-strukturen (357 kommuner) via
   `kom_mapping.csv`, bygget fra `grenser_mapping.csv` (1987–1998, ekstrahert fra SSB
   rapp_9913.pdf) + `kommunereform_mapping.csv` (2020/2024-reformene).
3. **Sentralitet:** SSBs sentralitetsindeks (pre-2020-koder) mappes til 2024-koder;
   ved kollisjon velges mest sentrale kategori.

## Kjente feil og utestående oppgaver

Prioritert (detaljer og evidens i `gjennomgang_analyse.md`):

1. **KRITISK — Ap 1989 dobbelttalt** i `stortingsvalg_2024.csv` (nasjonal sum 1,81 mill.
   mot offisielt ~0,91 mill.; alle andre partier stemmer). Alle 1989-prosenter er feil
   → Senteropprøret-regresjonene og nasjonalserien for 1989 må rekjøres etter fiks.
2. **Vang-kollisjon:** Vang i Valdres (3454) har fått Vang i Hedmarks 1989-stemmer
   (10 900 mot reelt ~950); Hamar mangler tilsvarende. Feil i grensemappingen.
3. **Rødt/RV mangler i 1989** (offisielt ~21 000 stemmer).
4. `total_stemmer` er summen av de 9 partiene, ikke alle godkjente stemmer —
   prosentene er andel av 9-partisum og ligger systematisk litt over offisielle tall.
5. **Duplisert «Senteropprøret 2021»-seksjon** i `index.html` (injeksjonsbug).
6. Injeksjonsmerker mangler i `analyse.py`-malen (se advarsel over).
7. To overlappende Pages-deploy-workflows (`deploy.yml` + `jekyll-gh-pages.yml`).
8. `polls.csv` oppdateres ukentlig, men brukes ikke i rapporten ennå.

## GitHub Actions

- **update-polls.yml** — cron hver mandag 06:00 UTC: laster ned ferskt gallupsnitt fra
  pollofpolls.no og committer `data/processed/polls.csv`.
- **deploy.yml** / **jekyll-gh-pages.yml** — deployer repoet til GitHub Pages ved push
  til `master`. NB: en push til master publiserer altså rapporten umiddelbart.

## Historikk

Startet som R-analyse av meningsmålinger, videreført som Python-analyse av valget
2013→2017 (bevart på branchen `gammel-master`), og utvidet juni 2026 til fullt
kommunepanel 1987–2025 med Senteropprøret som hovedcase.
