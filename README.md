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
- **Riksvalg leder lokalvalg (H5 snudd):** Med lagget avhengig variabel og reverstest
  er STV→KV-effekten (~+0,33) tre ganger sterkere enn KV→STV (~+0,11) — den
  opprinnelige «kommunevalg forutser stortingsvalg»-konklusjonen var persistens.
- **Bygdelistene er den tredje protestkanalen:** left behind-graderte (−0,28***),
  høstet av Sp i 1993 (+0,20***), og med bredt comeback i 2023 (+3,0 pp) mens Sp
  kollapset. NB: kommune-korrelasjonen med Sp-fallet er mekanisk andelsskvis
  (ikke sterkere enn for Ap/Høyre) — hvem listene tok velgere fra, krever individdata.
- **Fire bølger, tre mekanismer:** 1993 var sak-mobilisering gradert etter *statisk*
  periferi (og kollapset innen 1997); 2017 var left behind-gradert — faktisk
  befolkningsforvitring bar effekten, og gevinsten varte; 2021 var nasjonal metning
  uten gradient; 2025-kollapsen var brattest der oppturen var størst, mens FrPs
  samtidige bølge *ikke* var geografisk gradert. Se `scripts/analyse_mekanismer.py`.
- **2025: protesten avterritorialisert.** Kjøpekraftssjokket 2021–24 var geografisk
  uniformt (IQR 17,0–19,8 % inntektsvekst) og predikerer ikke ΔFrP; sterkeste
  prediktor er andelen 25–44-åringer (renteeksponert generasjon), som absorberer
  hele vekstkommune-dreiningen. Tapet fulgte livsfase/gjeld, ikke sted — Sp
  kanaliserer stedstap, FrP husholdningsøkonomi.
- **Aps bastioner var elastiske, ikke stabile:** rystelsene i 1993 og 2001 ble
  fullt gjenopprettet; 2017 er den første uten hjemvending (−6,2 pp under
  2013-nivå fortsatt i 2025). Da Sp kollapset i 2025 gikk bastionvelgerne videre
  til FrP (+13,5 pp), ikke hjem til Ap (+1,6). Kaskaden Ap → Sp → FrP.

1989-laget i `stortingsvalg_2024.csv` ble revidert mot offisielle SSB-tall 2026-07-04
(fasit-sjekk 85/85 parti×år; se `scripts/hent_stv_fiks.py` for proveniens).

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
│   ├── analyse_havbruk.py   # Velstående periferi: akvakultur demper Sp-byks 2017 (fase 2 venter på Havbruksfond-data)
│   ├── analyse_bastioner.py # Aps distriktsbastioner 1989–2025: elastiske til 2017, så kaskaden Ap→Sp→FrP (injiserer)
│   ├── analyse_panel.py     # FE/between-panel 1987–2025 + timing-test (→ panel_plot.html)
│   ├── grenser.py           # Kommunegrense-mapping 1987–1998 fra SSB-PDF (Claude API)
│   ├── les_grenser_pdf.py   # PDF-ekstraksjon med Claude Haiku
│   ├── hent_stv_fiks.py     # Proveniens/parser for den permanente 1989-fiksen + STV-nevnerkorreksjon (2026-07-04)
│   └── *.R                  # Eldre R-arbeidsflyt (inaktiv)
├── data/
│   ├── raw/                 # Kildedata: sentralitet, grensemappinger, rapp_9913.pdf, m.m.
│   └── processed/
│       ├── stortingsvalg_2024.csv    # SSB 08092, 1989–2025, 357 kommuner (2024-grenser)
│       ├── kommunestyrevalg_2024.csv # SSB 01180, 1987–2023, samme struktur
│       ├── befolkning_2024.csv       # SSB 07459, 1986–2026
│       ├── kom_mapping.csv           # Historisk kommunekode → 2024-kode
│       ├── panel_resultater.csv      # Koeffisienter fra analyse_panel.py
│       ├── kjopekraft_2124.csv       # SSB 06944/07459: medianinntekt 2021/2024 + antall 25–44 år
│       ├── akvakultur_syss_2017.csv  # SSB 13470: sysselsatte i akvakultur per kommune, 4. kv 2017
│       ├── polls.csv                 # pollofpolls gallupsnitt — auto-oppdatert ukentlig
│       ├── stv_fasit_nasjonal.csv    # SSB 08092 nasjonal fasit per parti/år (1989–2025), brukt til QA
│       ├── stv_1989_ny.csv           # Ferskt SSB-uttrekk for 1989 per kommune (erstatter det korrupte laget)
│       ├── stv_total_godkjente.csv   # Alle godkjente STV-stemmer per kommune-år (9-partisum + Andre)
│       ├── stv_prosent_korrigert.csv # STV-partiprosent med alle godkjente stemmer som nevner
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

1. **✅ Løst 2026-07-04:** Ap 1989-dobbeltellingen og Vang/Hamar-kollisjonen i
   `stortingsvalg_2024.csv` er rettet med et ferskt SSB-uttrekk (fasit-sjekk 85/85);
   den antatte «Rødt/RV mangler i 1989»-feilen viste seg å være en misforståelse
   (RV stilte som Fylkeslistene for miljø og solidaritet, kode 15 — kode 55 fantes
   ikke i 1989). Se `scripts/hent_stv_fiks.py`.
2. `total_stemmer` i `stortingsvalg_2024.csv`/`kommunestyrevalg_2024.csv` er fortsatt
   summen av de 9 partiene, ikke alle godkjente stemmer. Korrigerte partiprosenter med
   alle godkjente stemmer som nevner finnes nå i `stv_prosent_korrigert.csv` (STV) og
   `kv_prosent_korrigert.csv` (KV) — men rapportens eldre basisseksjoner bruker
   fremdeles 9-partinevneren.
3. **Duplisert «Senteropprøret 2021»-seksjon** i `index.html` (injeksjonsbug).
4. Injeksjonsmerker mangler i `analyse.py`-malen (se advarsel over).
5. To overlappende Pages-deploy-workflows (`deploy.yml` + `jekyll-gh-pages.yml`).
6. `polls.csv` oppdateres ukentlig, men brukes ikke i rapporten ennå.
7. **Kjent hull:** 2009-mikropartier (3 692 stemmer, 0,14 %) finnes kun på nasjonalt
   nivå hos SSB, ikke per kommune — `stv_total_godkjente.csv` undervurderer
   2009-totalen tilsvarende.

## GitHub Actions

- **update-polls.yml** — cron hver mandag 06:00 UTC: laster ned ferskt gallupsnitt fra
  pollofpolls.no og committer `data/processed/polls.csv`.
- **deploy.yml** / **jekyll-gh-pages.yml** — deployer repoet til GitHub Pages ved push
  til `master`. NB: en push til master publiserer altså rapporten umiddelbart.

## Historikk

Startet som R-analyse av meningsmålinger, videreført som Python-analyse av valget
2013→2017 (bevart på branchen `gammel-master`), og utvidet juni 2026 til fullt
kommunepanel 1987–2025 med Senteropprøret som hovedcase.
