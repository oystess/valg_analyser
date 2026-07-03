# Gjennomgang av analysen mot litteraturstudien

*Kritisk gjennomgang av prosjektet og analysene, vurdert opp mot hypotesene og
metodekravene i `litteratur_notat.md`. Utført 2026-07-02.*

---

## Sammendrag

Prosjektet har et uvanlig solid teoretisk fundament (litteraturnotatet) og et
metodedesign som følger den beste malen i litteraturen (Sánchez-García et al. 2025:
kommunepanel, FE + between, clustrede standardfeil). Rapporten er også ærlig der
funnene nyanserer hypotesene — særlig skillet mellom strukturell og dynamisk effekt.

Men gjennomgangen avdekket **én kritisk datafeil som underminerer hovedresultatet**:
Ap-stemmene for 1989 er dobbelttalt, slik at alle 1989-prosenter er gale — og
Senteropprøret-regresjonene (rapportens forside-funn, β=−0,69) er beregnet på korrupt
baseline. I tillegg er tre av litteraturnotatets hypoteser (H5, H6, H7) enten svakt
eller ikke testet.

---

## 1. Datakvalitet — funn fra revisjonen

### 1.1 KRITISK: Ap 1989 er dobbelttalt

Nasjonale stemmesummer i `stortingsvalg_2024.csv` for 1989 mot offisielle tall:

| Parti | Datasett | Offisielt (ca.) | Ratio |
|-------|---------:|----------------:|------:|
| **Ap** | **1 814 786** | **909 979** | **1,99** |
| Høyre | 588 682 | 588 966 | 1,00 |
| FrP | 345 185 | 344 890 | 1,00 |
| SV | 266 782 | 267 953 | 1,00 |
| KrF | 224 852 | 225 505 | 1,00 |
| Sp | 171 269 | 172 445 | 0,99 |
| Venstre | 84 740 | 84 896 | 1,00 |
| Rødt/RV | 0 | ~21 000 | 0,00 |

Alle partier unntatt Ap treffer offisielle tall nesten eksakt — Ap er **nøyaktig
doblet**. Alle andre valgår (1993–2025) er konsistente (totaler 0,93–1,00 av offisielt,
forklart av at «Andre»-stemmer ikke er med).

**Konsekvenser:**
- Nevneren (`total_stemmer`) for 1989 er oppblåst ~32 % → *alle* partiers
  1989-prosenter er for lave (unntatt Ap, som er altfor høy: ~52 % i data mot 34,3 %
  reelt). Eksempel: Halden viser Ap 64,1 % i 1989; reelt trolig ~47 %.
- Nasjonalserien viser Sp 4,9 % i 1989 mot offisielt 6,5 %.
- **Senteropprøret-regresjonene (β=−0,69 for ΔSp, +0,87 for ΔAp, 1989→1993) er
  beregnet på feil baseline.** Skjevheten er ikke tilfeldig støy: feilen i nevneren er
  proporsjonal med Ap-styrken i kommunen, som selv korrelerer med sentrum/periferi.
  ΔAp er kraftig overdrevet (fall fra kunstig høyt nivå), ΔSp er overdrevet der Ap sto
  sterkt. Fortegnene kan overleve en korreksjon, men størrelsene og
  sentralitetsgradienten kan ikke stoles på før dataene er fikset.
- Panel-modellene bruker 1989 som ett av ti valgår — mindre utslag der, men
  between-gjennomsnittene for Ap er også påvirket.

**Trolig årsak:** `hent_data.py` aggregerer SSB MCP tool-result-JSON-filer som ikke er
committet; en duplisert nedlastingsfil for Ap/1989 ville gitt akkurat dette mønsteret.

**Anbefalt fiks (to alternativer):**
1. *Kirurgisk:* Halver Ap-stemmene for 1989 per kommune, rekonstruer `total_stemmer`
   og `prosent`. Forsvarlig gitt at ratioen er eksakt 2 og alle andre partier stemmer.
2. *Robust:* Hent SSB 08092 for 1989 på nytt via SSB MCP og kjør `hent_data.py` på
   rene filer. Foretrekkes, siden det også kan avdekke om Rødt/RV manglet i uttrekket.

Deretter må rekjøres: `analyse.py`, `analyse_2017.py` (tre-bølge-sammenligningen),
`analyse_2021.py` (1993-referansen), `matrise.py` (1989-kvadranter) og
`analyse_panel.py`.

### 1.2 Vang-kollisjon i grensemappingen

Vang i Valdres (3454) har 10 900 stemmer i 1989 — reelt ~950. Dette er trolig **Vang i
Hedmark** (0414, innlemmet i Hamar 1992) som er feilmappet til navnebroren i Valdres.
Hamar mangler da tilsvarende stemmer. Mappingene i `grenser_mapping.csv` ble ekstrahert
fra PDF med Claude Haiku — denne kollisjonen viser at ekstraksjonen trenger en
valideringsrunde mot kjente sammenslåinger (flere navnebrødre finnes: Våler, Herøy,
Bø, Os, Sande, Nes …). Merk at Våler-forvekslingen allerede er fikset i commit
`7708c86` — samme sjekk bør kjøres systematisk for alle navnebrødre.

### 1.3 Mindre forhold

- **Rødt/RV mangler helt i 1989** (~21 000 stemmer, 0,8 %). Kode 55 fantes kanskje ikke
  i SSB-uttrekket for 1989 (RV). Påvirker nevneren marginalt.
- **`total_stemmer` er 9-partisummen**, ikke alle godkjente stemmer: «Andre»-lister er
  utenfor. Prosentene er dermed «andel av de ni store», systematisk 0–7 % høyere enn
  offisielle andeler (verst i 1993, da Andre var store). For *differanser* mellom år er
  dette nesten nøytralt, men tall som presenteres som partioppslutning bør enten
  reskaleres eller fotnoteres i rapporten.
- **`dpop5` beregnes men brukes ikke** i noen modell (kun `dpop10`). Enten ta den i
  bruk (robusthet, jf. Sánchez-García som bruker 5 og 10 år) eller fjerne beregningen.

---

## 2. Hypotesedekning: litteraturnotatet mot faktisk empiri

| Hyp. | Innhold (kort) | Status i analysen | Vurdering |
|------|----------------|-------------------|-----------|
| H1 | Strukturell periferi-effekt, episodisk intensitet | **Testet, støttet** | Between (β=−0,22***, R²=0,40) fanger det strukturelle; år-for-år β-tabellen (2021-analysen) fanger episodikken. God operasjonalisering. |
| H2 | Befolkningsnedgang forsterker, interaksjon m/ sentralitet + inntektskontroll | **Delvis testet** | Split-sample per sentralitet i stedet for interaksjonsledd; inntekt/ledighet mangler (erkjent i notatets tabell 8). Mekanismeseparasjonen (tjeneste/identitet/deprivasjon) er ikke mulig med disse dataene. |
| H3 | Episodisk sterkere: 1993, 2019–2021 | **Testet — delvis AVKREFTET** | År-β-tabellen viser 1993*** og 2017***, men **2021 ≈ 0 (p=0,95)**. 2021-bølgen var ikke befolkningsgradert. Dette er et reelt teorifunn som fortjener mer plass — se pkt. 4.2. |
| H4 | Sterkere effekt i kommunevalg | **Testet — IKKE støttet** | FE: Sp KV β=−0,047 n.s.; between: KV ≈ STV (−0,20 vs −0,22). Rapporten sier ikke eksplisitt at H4 falt — bør sies. |
| H5 | Kommunevalg leder stortingsvalg | **Svakt testet** | Se pkt. 3.1 — designet kan ikke skille «ledelse» fra ren persistens. |
| H6 | Sp–FrP-konkurranse om periferivelgerne | **Ikke testet** (kun deskriptiv tidsserie i 2021-analysen) | Ingen regresjonstest av «svak-FrP-år → sterk geografisk Sp-effekt». Testbar med eksisterende data — se pkt. 3.2. |
| H7 | Aldersseleksjon (unge flytter, eldre blir) | **Ikke testet** | Krever alderssammensetning (SSB 07459/05803, ikke hentet). |

**Notatets egne blindflekker (del 7) står seg:** ingen kausal identifikasjon er
etablert (pkt. 7.1), og rapportens språk bør fortsatt holde seg til samvariasjon —
konklusjonsseksjonen gjør stort sett dette, men «for hver prosent lavere vekst økte
Sp-andelen med 0,69 pp» er på grensen til kausal formulering.

---

## 3. Metodiske svakheter i testene som finnes

### 3.1 H5 («KV leder STV») er ikke en ledelses-test ennå

`timing_test()` regresserer STV-oppslutning på KV-oppslutning to år før, med kommune-
og år-effekter. Positiv β (+0,156***) er *konsistent* med ledelse, men partioppslutning
er sterkt persistent på kommunenivå: KV_t−2 plukker opp autokorrelasjon, ikke
nødvendigvis informasjon. Litteraturnotatet ber selv om Granger-logikk. Minimumskrav:

1. Kontroller for forrige STV: `sv_pst_t ~ kv_pst_{t−2} + sv_pst_{t−4}`.
2. Kjør reverstesten: `kv_pst_t ~ sv_pst_{t−2} + kv_pst_{t−4}` — H5 krever at
   KV→STV-koeffisienten er klart sterkere enn STV→KV.

Begge kan kjøres på eksisterende data uten nye kilder.

### 3.2 H6 er testbar i dag, men ligger urørt

FrP-data finnes i panelet (parti 02). To enkle tester:
- Utvid bølgeregresjonene (1993, 2017, 2021) med ΔFrP som kontroll/konkurrent-variabel.
- Interager `dpop10` med nasjonalt FrP-nivå per valgår i panelet: H6 predikerer at
  befolknings-/periferigradienten i Sp er brattest når FrP er svak (1993, 2021) —
  merk at 2021-nullfunnet (H3) allerede *utfordrer* H6, siden 2021 var et svakt FrP-år
  der gradienten skulle vært sterk. Dette spenningsforholdet er analytisk interessant
  og bør adresseres eksplisitt.

### 3.3 Uvektede kommuneregresjoner

Alle regresjoner teller Utsira likt med Oslo. Det er riktig for «kommunen som enhet»-
tolkningen (og matrise.py leverer det velgervektede komplementet — bra), men
hovedresultatene bør rapportere en befolkningsvektet variant som robusthetssjekk,
slik Sánchez-García gjør.

### 3.4 Sentralitetsindeksen er anakronistisk for tidlige år

SSBs 2020-indeks brukes for hele 1987–2025. For between-tolkninger er dette
akseptabelt (sentralitet er treg), men det bør stå som eksplisitt forbehold i
rapporten: en kommune klassifiseres etter *dagens* sentralitet, ikke 1989-sentralitet.
Ved kollisjon i mappingen velges dessuten «mest sentral» — konservativt for
periferifunn, som er riktig retning, men også dette bør dokumenteres i metodeboksen.

### 3.5 Nevner-hacket i nasjonalserien

`nasjonal_tidsserie()` bruker summen av Ap-radenes `total_stemmer` som nasjonal
nevner. Det fungerer bare fordi Ap finnes i alle kommune-år — og gjorde at
Ap-dobbelttellingen (pkt. 1.1) forplantet seg rett inn i alle partiers nasjonale
1989-andeler. Etter datafiks: beregn nevneren som `total_stemmer` per kommune-år
(unik verdi), ikke via et bestemt parti.

---

## 4. Rapporten mot funnene

### 4.1 Det som er bra

- Panel-seksjonen skiller eksplisitt strukturell (between) fra dynamisk (FE) effekt og
  viser ikke-signifikante FE-estimater i stedet for å gjemme dem. Dette er uvanlig
  redelig formidling og i god Rokkan-ånd: periferi-identitet er forankret, ikke volatil.
- 2021-nullfunnet (β≈0) presenteres åpent med tall.
- Metodeboksene oppgir gjennomgående n, R², p og KI.

### 4.2 Det som bør endres

1. **Forsidefunnet må reberegnes** etter 1989-fiksen (pkt. 1.1). Inntil da bør
   rapporten få en synlig fotnote/advarsel — den ligger offentlig på GitHub Pages.
2. **Duplisert «Senteropprøret 2021»-seksjon** i `index.html`: overskriften og
   inngangsteksten forekommer to ganger (én med markør, én uten) — en injeksjonsbug
   fra `analyse_2021.py`. Fjern dubletten og sørg for at seksjonen har start/slutt-merker.
3. **H4-avkreftelsen bør sies eksplisitt** («effekten er IKKE sterkere i kommunevalg»)
   — nullfunn med god teoriforankring er et funn, ikke et hull.
4. **H3/2021-avviket fortjener en tolkningsseksjon:** litteraturen (Nordregio,
   kommunereform-mekanismen) predikerte at 2021 skulle være befolkningsgradert — det
   var den ikke. En plausibel tolkning (2021 som *bred* sentraliserings-protest der
   også vekstkommuner i distriktene reagerte, jf. Auerbachs tillitsmekanisme) ville
   knyttet rapporten tettere til litteraturnotatet.
5. **Kausalspråket** strammes: «økte Sp-andelen med 0,69 pp» → «var Sp-veksten 0,69 pp
   høyere».

---

## 5. Tilleggsanalyse (2026-07-02): Proteststemmens livssyklus

Hypotesen «1993 = distrikt/sak, 2017 = left behind» ble testet med standardiserte
bølgeregresjoner (korrigert 1989-baseline i minnet), implementert i
`scripts/analyse_mekanismer.py` og injisert i rapporten. Hovedtall:

| Bølge | Std-β(vekst) alene | ...m/ sentralitetskontroll | R² sentralitet alene | Etterspill |
|-------|-------------------:|---------------------------:|---------------------:|------------|
| 1993 | −0,40*** | −0,24 (60 % består) | 0,21 (> vekst 0,16) | Kollaps: −12 pp innen 1997, r=−0,65 |
| 2017 | −0,54*** | −0,39 (74 % består) | 0,23 (< vekst 0,29) | Varte: +5,1 pp videre til 2021 |
| 2021 | −0,00 n.s. | — | 0,03 | Metning: bred nasjonal bølge |
| 2025 (Sp-fall) | +0,37*** | +0,25 | 0,15 | Brattest fall der oppturen var størst (r=−0,75) |
| 2025 (FrP) | +0,17** | +0,06 n.s. | 0,07 | FrP-bølgen er IKKE left behind-gradert |

**Tolkninger med konsekvens for hypotesene:**
- **H1/H2 presiseres:** 1993 var gradert etter *statisk* periferi (sentralitet slår
  vekst), 2017 etter *faktisk forvitring* (vekst slår sentralitet og overlever
  kontroll). To distinkte mekanismer, begge innenfor Rokkan-rammen.
- **H3 ytterligere nyansert:** «akselerasjon etter 2015» stemmer for 2017, men 2021
  var ikke-gradert (metning + nasjonalisering) og 2025 reverserte gradienten.
- **H6 svekkes i sin geografiske form:** FrPs 2025-bølge er nasjonal og svakt
  *sentralt* dreid (β≈0 etter kontroll; korr ΔSp/ΔFrP per kommune bare −0,17).
  Kanalbyttet Sp→FrP skjedde altså ikke kommune-for-kommune i periferien —
  Auerbach-mekanismen («party supply») må eventuelt virke via nasjonal
  dagsorden, ikke via lokal left behind-erfaring. Left behind-potensialet står
  uten tydelig kanal per 2025: det strukturelle distriktsforspranget til Sp er
  intakt (nivåforskjellen minst–mest sentral er som i 2013).
- Regjeringsdeltakelsen 2021–2025 som forklaring på kollapsen er konsistent med
  anti-etablissement-logikken i Sánchez-García: et regjeringsparti kan ikke bære
  protest. (Ikke direkte testet — krever f.eks. sammenligning med Sps fall etter
  regjeringsdeltakelsen 2005–2013.)

NB: 1993-radene bygger på minne-korreksjonen av Ap-1989 (pkt. 1.1) og er robuste i
fortegn og størrelsesorden, men skal reberegnes når datafiksen er gjort permanent.

### 5.1 Oppfølging (2026-07-02): Ble left behind-mekanismen avterritorialisert i 2025?

Hypotese (fra prosjekteier): 2017 fanget den *geografisk konsentrerte* gruppen som
fikk det verre; i 2022–2025 rammet samme mekanisme (opplevd tap → protest) gjennom
renter og kjøpekraft — som ikke følger kommunegrenser. Testet med SSB-data hentet
via MCP: medianinntekt etter skatt per kommune (tabell 06944, vekst 2021→2024) og
andel 25–44 år (tabell 07459, 2021) som renteeksponerings-proxy.

Resultater (n=349, standardiserte koeffisienter, ΔFrP 2021→2025):

| Prediktor | Bivariat | I full modell (m/ sentralitet) |
|---|---:|---:|
| Medianinntektsvekst 2021→24 | −0,05 n.s. | −0,07 n.s. |
| **Andel 25–44 år** | **+0,24***​ | **+0,20**​ |
| Befolkningsvekst (dpop10) | +0,17** | −0,07 n.s. |

- **Kommunal inntektsklemme predikerer ingenting** — men mest fordi den knapt
  varierer geografisk: IQR for nominell inntektsvekst 2021→24 er bare 17,0–19,8 %.
  Kjøpekraftssjokket var *nasjonalt uniformt* på kommunenivå. (NB: målet fanger
  heller ikke renteutgifter, som ikke trekkes fra i «inntekt etter skatt».)
- **Andelen 25–44 år er den sterkeste prediktoren for FrP-vekst** og absorberer
  hele «vekstkommune-dreiningen» fra §5 — den skyldtes alderssammensetning.
  FrP vokste mest der den renteeksponerte generasjonen bor (+14,6 pp i øverste
  kvintil mot +12,2 i nederste).
- Sps fall var størst der det er *få* unge og befolkningsnedgang (−15,9 pp mot
  −10,2) — 2017/2021-gevinstene fordampet mest i de eldste fraflyttingskommunene.

**Tolkning:** Hypotesen støttes i presisert form. Mekanismen (relativ deprivasjon →
protest) består, men tapet er **avterritorialisert**: i 2017 var «de som fikk det
verre» definert av *sted* (fraflytting, tjenestetap → Sp), i 2022–25 av *livsfase og
balanse* (unge huseiere med gjeld → FrP), spredt på tvers av kommuner. Derfor finnes
det ingen geografisk gradient å måle — protesten har flyttet fra kartet til
husholdningsregnskapet. Dette forklarer også hvorfor Sp ikke kunne fange den:
Sps merkevare kanaliserer *stedstap*, FrPs kanaliserer *husholdningsøkonomi*
(avgifter, drivstoff, strøm, renter).

**Forbehold:** Økologisk slutning — alderssammensetning på kommunenivå beviser ikke
individatferd; bør valideres mot Valgundersøkelsen 2025. Direkte gjeldsdata per
kommune (gjeldsgrad, andel med gjeld > 3× inntekt) ble ikke funnet i SSB-MCP-indeksen
— finnes i SSBs inntekts- og formuesstatistikk på ssb.no og bør hentes (nytt punkt
i tiltakslisten).

### 5.2 Ny delanalyse (2026-07-03): Velstående periferi — havbruk som demper

Hypotese (prosjekteier): Havbruksfondet er en velstandsindikator langs kysten;
mye havbrukspenger bør være en *motsatt* indikator på Sp-vekst i 2017. Fase 1
testet med proxy (andel sysselsatte i akvakultur, SN2007 03.2, SSB 13470,
4. kv 2017 — committet som `data/processed/akvakultur_syss_2017.csv`;
skript: `scripts/analyse_havbruk.py`).

**Funn (ΔSp 2013→2017, n=350):**
- Ukontrollert: ingen effekt (+0,05 n.s.) — havbrukskommuner *er* periferi,
  og de to effektene maskerer hverandre.
- Med kontroll for befolkningsvekst 2007–17 og sentralitet: **std-β=−0,12 (p=0,013)**.
- Innad i periferien (sentralitet 0–1, n=173): −0,14 (p=0,061).
- Deskriptivt i periferien: uten akvakultur +14,0 pp Sp; med mye (>2 % av
  sysselsettingen) +11,5 pp — ved identisk befolkningsnedgang (−1,4 mot −1,2 %).

**Tolkning:** Støtter og skjerper left behind-lesningen av 2017: mekanismen er
opplevd forvitring, ikke fraflytting per se. Lokal velstand fra havbruk
(arbeidsplasser, eiendomsskatt, optimisme) demper protesten selv der folketallet
faller. Konsistent med Sánchez-Garcías moderator-funn (effekten sterkest ved lav
inntekt/høy ledighet) — dette er samme moderator med motsatt fortegn.

**Status/fase 2:** Havbruksfondets faktiske utbetalinger per kommune
(fiskeridir.no) er blokkert av sesjonens nettverkspolicy; filene lastes opp
manuelt. Da testes kr per innbygger direkte mot ΔSp 2017, 2021-nivået og
2025-fallet. Forbehold fase 1: sysselsettingsandel måler aktivitet, ikke
kommuneinntekt; havbrukskommuner kan avvike også på fiskeritradisjon og
EU-historikk (1994-nei-kysten).

### 5.3 Ny delanalyse (2026-07-03): Aps distriktsbastioner — elastiske, ikke stabile

Spørsmål (prosjekteier): Har Aps distriktsbastioner vært stabile hele tiden,
eventuelt mer stabile enn andre steder? Skript: `scripts/analyse_bastioner.py`
(injiserer egen rapportseksjon). Definisjon: sentralitet 0–1 og Ap ≥
periferimedianen i 2005; fire grupper (bastion × sentralitet), korrigert
1989-baseline, n=355.

**Funn:**
1. **Elastisitet, ikke stabilitet:** Bastionene ble rystet i 1993 (−5,7 pp) og
   2001 (−8,0 pp), men hentet alt tilbake begge ganger (tilbake på 42,8 % i
   2005). «Stabiliteten fra 2005» er hjemvending, ikke ro.
2. **Ikke mer stabile enn andre:** within-kommune-std er høyest i bastionene i
   alle epoker. Det stabile er *rangeringen* (Spearman ≈ +0,91 mellom alle
   valgpar — selv over 2017-skjelvet). Ap-kartet er konstant; nivået er det ikke.
3. **2017 er unik som rystelsen uten hjemvending:** 2021 ±0,0, 2025 +1,6;
   fortsatt −6,2 pp under 2013-nivået i 2025, mot −0,8 i ikke-bastionene.
   Aps strukturelle problem etter 2017 er spesifikt bastion-erosjon.
4. **Kaskaden Ap → Sp → FrP:** I bastionene: 2013→17 ΔAp −7,9 / ΔSp +13,4 /
   ΔFrP −1,5 (FrP falt!); 2021→25 ΔSp −16,3 / ΔAp +1,6 / ΔFrP +13,5.
   Velgerne Sp ristet løs vendte ikke hjem — de gikk videre til FrP.
   korr(ΔAp,ΔSp) 2021→25 = −0,53: noe direkte hjemvending, marginal i nivå.

**Tolkning:** Konsistent med dealignment-perspektivet: 2017 brøt en langvarig
parti-identitet (klasse × sted), og løsrevne velgere forblir bevegelige.
Knytter §5 (livssyklus) og §5.1 (avterritorialisering) sammen: bastionvelgeren
gikk fra stedslojalitet (Ap) via stedsprotest (Sp) til økonomiprotest (FrP).

### 5.4 Robusthetssjekk (2026-07-03): Hjemmesitter-alternativet

Innvending mot kaskaden Ap→Sp→Frp: Sp-kollapsen 2025 kunne skyldes at
2017/2021-velgerne satte seg hjemme, ikke at de gikk videre. Testet med
personer med stemmerett per kommune (SSB 13448, committet som
`data/processed/stemmerett_2125.csv`); deltakelse-proxy = 9-partistemmer /
stemmeberettigede (nivået undervurderes pga. «Andre», men endringen 2021→25
er sammenlignbar på tvers av kommuner).

**Funn (n=354):** Deltakelsen steg nasjonalt (proxy 73,4 → 75,5 %). Den
utviklet seg svakest der Sp falt mest — korr(ΔSp, Δdeltakelse) = +0,35;
kvintilen med størst Sp-fall hadde −0,7 pp deltakelse mot +1,8 i kvintilen
med minst; bastionene −0,3 mot +1,4 i sentrale kommuner.

**Konklusjon:** Hjemmesitting er en reell, men liten kanal: 1–2,5 pp
differensiell deltakelse mot 16–21 pp differensielt Sp-fall. Hoveddelen av
Sp-kollapsen gikk til andre partier, ikke til sofaen. Kaskade-tolkningen
består; begge kronikkversjonene har fått en defensiv setning om dette.

## 6. Prioritert tiltaksliste

| # | Tiltak | Omfang |
|---|--------|--------|
| 1 | Fiks Ap-1989 (helst re-nedlasting via SSB MCP), legg til RV 1989, fiks Vang→Hamar | Middels |
| 2 | Rekjør hele analysekjeden og oppdater rapporten; sjekk hvor mye β-ene flytter seg | Liten (når 1 er gjort) |
| 3 | Fjern duplisert 2021-seksjon; legg injeksjonsmerker i `analyse.py`-malen | Liten |
| 4 | H5: lagget avhengig variabel + reverstest | Liten |
| 5 | H6: FrP-kontroll i bølgeregresjonene + interaksjonstest | Liten–middels |
| 6 | Valider grensemappingen systematisk mot navnebror-kommuner | Liten |
| 7 | Hent inntekt (SSB 12558) og alder (07459) → H2-moderatorer og H7 | Middels |
| 8 | Befolkningsvektet robusthetsvariant av hovedregresjonene | Liten |
| 9 | Hent gjeldsgrad per kommune (SSB inntekts-/formuesstatistikk) → direkte test av rentesmerten bak FrP-2025; valider aldersfunnet (§5.1) mot Valgundersøkelsen 2025 | Middels |

---

*Gjennomgang utført med utgangspunkt i `litteratur_notat.md` (2026-06-11),
`panel_resultater.csv`, alle skript i `scripts/`, og revisjonsberegninger mot
offisielle valgresultater 1989–2025.*
