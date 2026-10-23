# Plan: Utvide og kvalitetssikre kommunevalgdataene

*Lagt 2026-07-03. Status: plan — ikke igangsatt.*

## Utgangspunkt

`data/processed/kommunestyrevalg_2024.csv` (SSB 01180, 1987–2023, 357 kommuner,
9 partier) finnes allerede og brukes i `analyse_panel.py` (KV/STV-sammenligning,
timing-test H5). Men:

- Datasettet er **aldri revidert** mot offisielle tall. STV-revisjonen avdekket
  Ap-1989-dobling og Vang/Hamar-kollisjon — KV-dataene er bygget av samme
  pipeline (`hent_data.py` + grensemappingene) og kan ha tilsvarende feil.
- Tre datakilder mangler som ville styrke analysene:
  1. **Valgdeltakelse i kommunevalg** per kommune (stemmeberettigede + godkjente)
     — gir hjemmesitter-analysen (§5.4) også for KV, og deltakelse er i seg
     selv en misnøyeindikator.
  2. **Lokale lister / «Andre»** per kommune — bygdelister er en egen
     protestkanal i periferien som de 9 partiene ikke fanger. Relevant for H6
     og for «velgerreserven uten kanal»-tolkningen.
  3. (Sekundært) **Fylkestingsvalg** — flere observasjoner per periode, men
     lavere prioritet.

## Del 1 — Datainnhenting (delegeres til Sonnet)

Arbeidsdeling etter etablert mønster: Sonnet gjør volumarbeidet (billig),
kvalitetssikringen gjøres av en **annen** instans etterpå (to-instans-prinsippet
fra kronikk-arbeidet). Lærdommer som er bakt inn: Haiku-grensefeilen (Vang) →
egen valideringsdel; ukommitterte SSB-nedlastinger (1989-mysteriet) → **alle
uttrekk committes som CSV med proveniens**.

Sonnets oppdrag, i rekkefølge:

1. **Fasitfil først:** Hent offisielle *nasjonale* KV-resultater per parti per
   valgår 1987–2023 fra SSB 01180 (nivå: hele landet). Lagres som
   `data/processed/kv_fasit_nasjonal.csv`. Denne brukes av QA-en og skal hentes
   FØR kommunedataene, uavhengig av dem.
2. **Valgdeltakelse KV:** Finn og hent stemmeberettigede + godkjente stemmer
   per kommune per KV-år (SSB har egne deltakelse-/stemmerett-tabeller for
   kommunestyrevalg; søk også via tabellnummer-probing hvis MCP-søket er tynt
   — se erfaringene i gjennomgang §5.5). → `data/processed/kv_deltakelse.csv`.
3. **Andre/lokale lister:** Utvid uttrekket fra 01180 med partikoder utover de
   ni (særlig «Andre lister»/felleslister). → `data/processed/kv_andre_lister.csv`.
4. **Kobling:** Alle filer på 2024-kommunestruktur via `kom_mapping.csv`
   (samme mønster som `analyse_havbruk.py`/`analyse_mekanismer.py`). Kolonner:
   `kom2024, aar, ...`. Vang (3454)/Hamar (3403) skal IKKE spesialbehandles i
   innhentingen — de håndteres i QA.
5. **Leveranse:** CSV-ene + et frittstående skript `scripts/hent_kv_supplement.py`
   som dokumenterer nøyaktig tabell-ID, selection og dato for hvert uttrekk
   (reproduserbarhet), + 5–10 linjers sammendrag av hva som ble hentet.

Sonnet skal IKKE: endre eksisterende datafiler, kjøre analyser på dataene,
eller rette avvik den måtte oppdage (avvik rapporteres, rettes etter QA).

## Del 2 — Kvalitetssikring (kjøres av Fable/Opus, uavhengig av innhenteren)

Implementeres som `scripts/qa_kommunevalg.py` med maskinlesbar rapport
(`data/processed/qa_kv_rapport.csv`), slik at den kan rekjøres etter enhver
datafiks. Seks kontroller, i prioritert rekkefølge:

1. **Nasjonal fasit-sjekk** (metoden som fanget Ap-1989): summer stemmer per
   parti per KV-år fra kommunedataene, del på fasitfilen. Flagg ratio utenfor
   [0,97, 1,03]; ratio ≈ 2,0 eller ≈ 0,5 flagges særskilt som
   dublett-/manglende-fil-mistanke.
2. **Nevner-konsistens:** `total_stemmer` = partisum innen hver kommune-år?
   Andel «Andre» = total − 9-partisum ≥ 0 overalt?
3. **Deltakelse-sanity:** godkjente/stemmeberettigede innenfor [35 %, 90 %]
   per kommune-år; nasjonalt innenfor ±2 pp av offisiell KV-deltakelse.
4. **Navnebror-audit** (Vang-lærdommen): automatisk flagg for alle kommune-år
   der totalstemmer hopper >50 % mot begge nabovalg — fanger mappingkollisjoner
   (navnebrødre: Vang, Våler, Herøy, Bø, Os, Nes, Sande, Sund …).
5. **Befolknings-kontinuitet:** stemmeberettigede/befolkning (fra
   `befolkning_2024.csv`) skal ligge ~0,70–0,82 og bevege seg glatt; brudd =
   grensemappingfeil.
6. **KV↔STV-kryssvalidering:** kommunekorrelasjon for Ap- og Sp-andel mellom
   hvert KV og nærmeste STV (forventet r ≈ 0,8–0,9 per år); år med r < 0,6
   flagges. Uteliggerkommuner (residual > 3 σ) listes for stikkprøve.
7. **Manuelle stikkprøver:** 10 tilfeldige kommune-år + alle flaggede slås opp
   mot kjente resultater før dataene tas i bruk.

Først når QA-rapporten er ren (eller avvik er forklart og rettet) kobles de
nye dataene på analysene: §5.4-hjemmesitteranalysen for KV, lokale lister som
H6-utvidelse, og reestimering av timing-testen (H5) med lagget avhengig
variabel.

## Rekkefølge og omfang

| Steg | Hvem | Estimat |
|------|------|---------|
| 1. Fasitfil + deltakelse + andre-lister | Sonnet | én økt |
| 2. QA-skript + kjøring | Fable/Opus | én økt |
| 3. Avviksretting (om nødvendig) | Fable | avhenger av funn |
| 4. Kobling på analysene | Fable | én økt |

NB: Den permanente STV-1989-fiksen (tiltak 1 i gjennomgangen) er gjort
2026-07-04 (se `scripts/hent_stv_fiks.py`) — QA-metodikken herfra kan
gjenbrukes direkte på stortingsvalgdataene.
