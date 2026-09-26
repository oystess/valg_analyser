# Prompt: Tester «Høyre-mobilisering i vekstkommuner → Sp-motreaksjon»

*Skrevet 2026-09-26 i sesjonen som laget datasettet og hypoteseturneringen. Repo: `oystess/valg_analyser`, start fra branchen `claude/valganalyse-dataset-qa-f8s1df`.*

---

## Til deg som tar over (ny sesjon)

Du skal teste en hypotese Øystein formulerte etter å ha sett to figurer. **Svar på norsk (bokmål)**, og vær metodisk konservativ. Last disse skillene før du begynner: `anthropic-skills:agent-orkestrering` (arbeidsdeling, briefer og uavhengig kontroll) og `anthropic-skills:ssb-dataviz` (figurer). Du trenger ikke kjøre en hypoteseturnering. Her er det én forhåndsdefinert hypotese som skal testes.

### 1. Historien som skal testes

> I valg *t* mobiliserer Høyre i vekstkommuner: Høyre går mest fram der folketallet vokser. Høyre kommer i regjering, eller styrker posisjonen sin. I valget etter (*t+1*) kommer en motreaksjon, der Sp går mest fram i kommuner med nedgang, altså de kommunene Høyre-mobiliseringen ikke nådde.

Utgangspunktet er figurene `figurer/h_sp_2009_2013_befolkning.png` og `figurer/ap_sp_2013_2017_befolkning.png` (og `h_sp_2013_2017…`, `ap_sp_2009_2013…`). Grafene er laget med `analyse/figur_parti_vs_befolkning.py <parti> <periode>`. De viser at Høyre i 2009–13 gikk mest fram der folketallet vokste (r ≈ 0,36), mens Sp sto stille. I 2013–17 gikk Sp mest fram der folketallet falt (r ≈ −0,54), og Høyre sto stille.

**Viktig:** Hypotesen ble formulert *etter* at episoden 2009–2013 → 2013–2017 var sett. Den episoden kan derfor bare **illustrere**, ikke teste. Testen må skje på episoder og valgslag som ikke er sett. Se §4.

### 2. Data som finnes (ikke bygg på nytt uten grunn)

- `data/processed/stortingsvalg_2024.csv` og `kommunestyrevalg_2024.csv`: alle partier, 357 kommuner i 2024-inndeling, ST 1989–2025 og KV 1987–2023. Kolonnen `prosent` er andel av alle godkjente stemmer. Datasettet er kvalitetssikret (`qa/QA_RAPPORT.md`).
- `data/processed/befolkning_2024.csv`: befolkning 1.1. i 1986–2026.
- `turnering/data/panel.csv` (+ `datadictionary.md`): kommune × ST-periode. Den har `d_{parti}`, `{parti}_t0`, `vekst4_pst`, `vekst10_pst`, sentralitet, alder, utdanning, inntekt og næring. Kolonnen `kv_d_sp` finnes, men **ikke** `kv_d_h`. Bygg en tilsvarende KV-panel for alle partier med `analyse/felles.py` som mal.
- `analyse/modeller.py`: kjører formelspesifikasjoner med klyngerobuste standardfeil (kommune). `analyse/kjor_laste.py` er et robusthetsbatteri for låste spesifikasjoner. Gjenbruk begge.
- Regjeringssammensetning finnes ikke i repoet. Lag en liten tabell `hypoteser/motreaksjon/regjeringer.csv` (år, statsminister, partier) fra allmenn kunnskap, og kontroller den i kode mot kjente årstall.

### 3. Operasjonalisering (lås før testing)

Formuler og lås følgende **før** du ser på episodene i §4. Skriv dem til `hypoteser/motreaksjon/låst.json` med tidspunkt og sha256 av panelene.

- **P1 Høyre-gradient i t:** I periode *t* henger Høyres endring positivt sammen med befolkningsveksten (`d_h ~ vekst10_pst + h_t0 + sent_indeks`, vektet, med klyngerobuste SE).
- **P2 Sp-gradient i t+1 (motreaksjonen):** I periode *t+1* henger Sps endring negativt sammen med befolkningsveksten (`d_sp ~ vekst10_pst + sp_t0 + sent_indeks`).
- **P3 Koblingen (kjernetesten):** Over alle etterfølgende periodepar (t, t+1) i ST 1989–2025 og KV 1987–2023: jo sterkere Høyre-gradienten i *t* er, desto sterkere (mer negativ) er Sp-gradienten i *t+1*. Enheten er periodeparet. Med få par er dette beskrivende, så rapporter alle par i en tabell og vis en figur. Påstå ingen signifikans du ikke har.
- **P4 Lokal motreaksjon (kommunenivå):** Sp går mer fram i *t+1* i kommuner der Høyre gikk *mindre* fram i *t* enn befolkningsveksten tilsier (Høyre-residual fra P1), gitt `sp_t0`, `sent_indeks` og `vekst10_pst`. Alternativt: der Høyre gikk *mer* fram. Lås begge retningene som konkurrerende versjoner, og rapporter hvilken som får støtte.
- **P5 Regjeringsbetingelsen:** Motreaksjonen (P2 og P3) er sterkere når Høyre er i regjering mellom *t* og *t+1* (f.eks. 2001–05 og 2013–21). Med få regjeringsperioder er dette bare en beskrivelse.
- **Konkurrerende forklaringer som også må testes:**
  - (a) Sps nasjonale bølger slår proporsjonalt ut der Sp står sterkt fra før, altså regresjon mot middelverdien eller en multiplikativ effekt.
  - (b) Ap-tap: sammenhengen går gjennom Ap, ikke Høyre (se `turnering/RAPPORT.md`, H31: Sp-bølgen 2013–21 gikk gjennom Ap-land).
  - (c) Reformer uavhengig av Høyres valgresultat.
  - Kjør P2 og P4 med og uten `d_ap(t)` og `ap_t0` som kontroll.

### 4. Test på det som ikke er sett (erstatter holdout)

Brukeren valgte bort holdout i forrige runde. Her er den likevel mulig og viktig, fordi hypotesen er laget etter én episode:

1. **Sett (bare illustrasjon):** ST 2009–13 → 2013–17.
2. **Test, ST:** Alle andre periodepar i ST, særlig 1997–2001 → 2001–05 (Høyre fram i 2001 og i regjering med Bondevik II), 2013–17 → 2017–21 (Høyre i regjering, Sp-toppen i 2021) og 2017–21 → 2021–25.
3. **Test, KV (uavhengig valgslag):** KV 2007–11 → 2011–15 og KV 2011–15 → 2015–19 (Høyre-bølgen i 2011 og Sp-bølgen i 2019), og alle andre KV-par.
4. Et mønster regnes som **støttet** bare hvis retningen fra P1 → P2/P4 går igjen i flertallet av testparene i *begge* valgslag, og er robust etter batteriet i `kjor_laste.py` (vektet og uvektet, uten estimerte kommuner, med ett og ett fylke utelatt). Holm-korriger over de låste testene.

### 5. Arbeidsdeling (etter agent-orkestrering)

Materialet er lite (under T1), så gjør hovedarbeidet selv. Bruk subagenter bare der skillen sier det gir verdi:
- **1 uavhengig kontroll** (`model: sonnet`) av KV-panelet du bygger. Den skal regne på nytt fra rådata, uten å se koden din.
- **1 uavhengig kontroll** (`model: sonnet`) av de låste kjøringene.
- **Valgfritt: 1 «djevelens advokat»**, som får hypotesen, dataene og resultatene og leter etter den enkleste alternative forklaringen.

Til sammen er det 2–3 agentstarter. Vis planen på 2–3 linjer og kjør.

### 6. Leveranse

- `hypoteser/motreaksjon/RAPPORT.md`:
  - svar i én setning
  - tabell per periodepar (Høyre-gradient i *t*, Sp-gradient i *t+1*, med KI, valgslag og om Høyre satt i regjering)
  - P1–P5 med status (støttet, delvis eller ikke støttet)
  - de konkurrerende forklaringene
  - forbehold: kommunenivå, få episoder, og at hypotesen ble formulert etter å ha sett data
- **Figurer i SSB-stil:**
  - (1) Høyre-gradient i *t* mot Sp-gradient i *t+1*, ett punkt per periodepar, ST og KV med ulik markør
  - (2) en «før–etter»-figur for en testepisode (ikke 2009–17), laget med `figur_parti_vs_befolkning.py`
- **Kode** i `analyse/` (gjenbruk `felles.py` og `modeller.py`). Commit og push til branchen du startet på.
- Avslutt med en kort oppsummering til Øystein: hva som holdt, hva som ikke holdt, og hvor sikker du er.

### 7. Rammer

- Påstå aldri at velgere gikk fra Høyre til Sp, eller omvendt. Dette er kommunedata.
- Ikke oppdater `index.html`.
- Ikke lag pull request.
- Spør Øystein før du henter nye datakilder utover SSB-tabeller.
