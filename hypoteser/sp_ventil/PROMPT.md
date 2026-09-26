# Prompt: Sp som «ventil» for Ap-bastioner i distriktet – og velgere som ikke kommer tilbake

*Utkast 2026-09-26. Arbeidet følger skillen `agent-orkestrering`. Det starter ikke før spørsmålene i §9 er besvart.*

---

## 1 Bakgrunn og påstand

Utgangspunktet er en fortelling fra Sømna (2024-kode 1812): kommunen stemte Ap i lang tid, så kom
en periode med fremgang for Sp, og de velgerne kom ikke tilbake til Ap. Stortingsvalgtallene i
`data/processed/stortingsvalg_1945.csv` viser det samme mønsteret:

| | 1945–69 | 1989 | 1993 | 1997–2013 | 2017 | 2021 | 2025 |
|---|---|---|---|---|---|---|---|
| Ap i Sømna | 40–56 % | 37 % | 23 % | 19–34 % | 23 % | 22 % | 28 % |
| Sp i Sømna | 8–18 % | 20 % | 48 % | 21–29 % | 44 % | 50 % | 28 % |

**Påstanden som skal undersøkes, i tre ledd:**

- **P1 Erosjon:** I Aps distriktsbastioner tar Sp velgere fra Ap i Sp-bølgene: der Sp går mest fram, går Ap mest tilbake.
- **P2 Sperrehake:** Når Sp-bølgen trekker seg tilbake, tar Ap igjen mindre enn partiet tapte. Tapet er altså asymmetrisk.
- **P3 Løsere velgere:** Etter den første store Sp-bølgen blir velgerne i disse kommunene mer flyktige («utro»). Det skal vises som høyere volatilitet og større utslag i senere valg, både mot Sp og mot andre partier (FrP, H).

Undersøkelsen er **deskriptiv**. Vi bruker aggregerte kommunetall, så vi kan ikke se at det er *de samme velgerne*
som går Ap → Sp → andre. Det skal stå tydelig i rapporten (økologisk feilslutning), og der det finnes
individdata (Valgundersøkelsen), skal de brukes som kontroll (§5, agent L).

## 2 Data

- `data/processed/stortingsvalg_1945.csv` og `kommunestyrevalg_1945.csv`, med 2024-kommuner, partigrupper og `sikkerhet`
  (se `utvidelse_1945/QA_RAPPORT.md`). Varianten `*_1945_stabil.csv` (279 stabile enheter) brukes i robusthetstestene.
- `data/processed/befolkning_1951.csv` og `sentralitet_2024.csv` (SSB sentralitetsklasse 1–6).
- **Felleslister (gruppe 90):** Sp stilte på felleslister med KrF og V i flere fylker 1973–89 (nasjonalt Sp 1981 ser for lavt ut, 4,2 %).
  Alle mål på Sp skal derfor også beregnes med variant «Sp + felleslister». Resultater som bare holder i én variant, skal merkes.
- Sikkerhet `lav` (1945–49) brukes bare som bakgrunn, ikke i testene.

## 3 Operasjonalisering (endres bare etter svar i §9)

- **Distriktskommune:** sentralitetsklasse 5–6 (2024).
- **Ap-bastion:** defineres *rullerende*: Ap ≥ 50 % i snitt ved de to stortingsvalgene før valget som testes.
  Da kan bølger fra 1950-tallet og framover testes uten at bastionen er definert i samme periode som den testes i.
  Som robusthet brukes i tillegg en fast definisjon (snitt 1953–69) og øvre kvartil.
- **Sp-bølge, nasjonal:** Sp (inkl. felleslister) går fram ≥ 3 pp nasjonalt. Med Sp + felleslister gjelder det bare 1993 og 2017–21.
  «Bølgen» i 1953 (+4,0 pp for Sp alene) skyldes at Bondepartiet i 1949 stilte på felleslister (6,1 %).
- **Sp-bølge, lokal:** Sp (inkl. felleslister) går fram ≥ 10 pp i kommunen fra forrige valg. Denne definisjonen gjelder alle valg fra 1953,
  og fanger lokale bølger som ikke synes nasjonalt (f.eks. EU-valget 1973 og kraft- og landbrukssaker).
  **Tilbakefall** er neste valg der Sp går tilbake, nasjonalt eller lokalt.
- **Sammenligningsgrupper:** (a) distrikts-Ap-bastioner med liten lokal Sp-økning i bølgen, (b) distriktskommuner som ikke er bastioner,
  (c) sentrale kommuner.

## 4 Tester

Alle tester kjøres i kode (`analyse/sp_ventil/`). Hovedvarianten er stortingsvalg, med kommunestyrevalg som parallell.
Endringene måles i prosentpoeng. Nasjonale svingninger fjernes med periodefaste effekter, eller ved å måle mot landsendringen.

| Test | Hva | Mål / modell | Støtter påstanden hvis |
|---|---|---|---|
| T1 Erosjon | P1 | Per bølge: ΔAp mot ΔSp på kommunenivå, med og uten bastionsinteraksjon | Helningen er tydelig negativ og brattere i bastioner (nær −1) |
| T2 Asymmetri | P2 | Panel over alle valgpar: ΔAp = b⁺·max(ΔSp,0) + b⁻·min(ΔSp,0) + periode-FE (+ kommune-FE); klyngede SE | \|b⁺\| > \|b⁻\|, og forskjellen er størst i distrikts-bastioner |
| T3 Dose–respons | P2 | Lokal Sp-økning 1989→93 mot Aps nivåendring 1989→2009 (og 2013→21 mot 2013→25) | Større Sp-dose gir varig lavere Ap, også når Sp har falt tilbake |
| T4 Hendelsesstudie | P1–P2 | Ap og Sp relativt til landet, fra −3 til +4 valg rundt 1993 (og 2021), bastioner med høy og lav dose | Ap faller ved bølgen og kommer ikke tilbake til nivået før bølgen |
| T5 Volatilitet | P3 | Pedersen-indeks per kommune per valgpar; før og etter første store bølge, mot sammenligningsgrupper (diff-in-diff) | Volatiliteten øker mer i bastioner som ble rammet |
| T6 Hvor går de? | P3 | Når Sp faller tilbake: hvilke partier går fram (Ap, FrP, H, andre)? | Tilbakefallet går i hovedsak til andre partier enn Ap |
| T8 Langsom drift 1953–89 | P1 | Sp vokste langsomt i mange distriktskommuner fram til 1980-tallet (Sømna: 8 → 24 %). Hvem tapte: Ap, eller H/V/KrF? Kommune-FE-regresjon av ΔAp og Δ(H+V+KrF) mot ΔSp 1953–89 | Hvis Ap tapte lite i denne perioden, er 1993 et brudd og ikke en fortsettelse. Det er en viktig nyanse |
| T7 Sømna og tilsvarende | Case | Tidsserie 1945–2025 for Sømna og 5–10 kommuner med samme mønster, valgt etter regel i kode | Illustrasjon, ikke bevis |

**Alternative forklaringer som skal testes eller drøftes:** Aps nasjonale fall (håndteres med periode-FE),
aldring og fraflytting (kontroll for befolkningsendring, `befolkning_1951.csv`), generasjonsskifte,
FrP-veksten fra 1989, lokale kandidater og lister (KV), felleslister, regresjon mot gjennomsnittet
(bastioner kan bare gå ned; T2 skal også kjøres på «Ap-svake» kommuner som placebo), og at 2025 er det eneste valget etter 2021-bølgen.

**Robusthet:** stabile enheter; uten `estimert`/`middels`; ett fylke ute om gangen; bastionsgrense 45/55 %; Sp med og uten felleslister; KV parallelt.

## 5 Orkestrering

**Vurdering etter §1:** Valgdataene er strukturerte CSV-filer som leses i kode. De når ikke T1 og krever ingen arbeidsdeling.
Analysen gjøres derfor av hovedagenten. To avgrensede oppgaver trenger likevel egne agenter:

| Agent | Grunnlag | Oppgave | Modell |
|---|---|---|---|
| **L – litteratur** | T3: websøk og kilder som ellers fyller hovedkonteksten | Finn individdata og forskning om velgerstrømmer Ap → Sp → andre (Valgundersøkelsen 1989/93/97, 2017/21/25; Aardal, Bergh m.fl.; Sp og EU-kampen; «periferiopprør»). Rapporter overgangstall med kilde (tabell/side). Ingen tolkning av våre data. | standard |
| **K – kontroll** | §6 | Får data, operasjonaliseringen i §3 og resultatfilen `arbeid/resultater.json`, men ikke koden. Regner T1–T6 på nytt uavhengig, leter etter valg av grenser som driver resultatet og sjekker placeboen | sonnet |

Estimert kostnad: 2 agentstarter × ca. 70 000 tokens, pluss hovedarbeidet. Én ekstra kontrollrunde er tillatt ved feil.
Briefene skrives etter malene i skillen til `hypoteser/sp_ventil/briefer/`.

## 6 Gjennomføring

1. Bygg analysepanelet (valgpar × kommune med ΔAp, ΔSp, ΔSp+90, Pedersen, befolkning, sentralitet, bastionsflagg). Skriv `datadictionary.md`.
2. Beregn Sp-bølger og tilbakefall nasjonalt. **Lås** definisjonene i `låst.json` (med sha256 av panelet) før T1–T6 kjøres.
3. Start L parallelt med steg 1–2.
4. Kjør T1–T7 og robusthet. Skriv `arbeid/resultater.json`.
5. Start K. Rett eventuelle feil og kjør høyst én ny kontrollrunde.
6. Sammenstill resultatene med individdataene fra L: Stemmer aggregat og individnivå overens?

## 7 Leveranser (`hypoteser/sp_ventil/`)

- `RAPPORT.md` med en konklusjon per ledd (P1–P3): *støttet / delvis / ikke støttet*, med effektstørrelser, robusthet og avvik fra K vist i klartekst.
  Den skal også ha en dekningsrapport og en egen seksjon om hva aggregerte data ikke kan vise.
- Figurer i SSB-stil (`figurer/`):
  (1) Sømna 1945–2025, Ap/Sp/FrP/H.
  (2) Hendelsesstudie rundt 1993 og 2021, bastioner med høy og lav dose.
  (3) Asymmetrikoeffisientene b⁺/b⁻ med konfidensintervall, per kommunegruppe.
  (4) Volatilitet før og etter.
- Kode i `analyse/sp_ventil/`, som skal kunne kjøres på nytt fra `data/processed/`.
- `index.html` oppdateres ikke før funnene er godkjent.

## 8 Grenser

Ingen nye datakilder til selve analysen uten å spørre. Ingen holdout, for dette er deskriptivt.
Tall regnes i kode. Tolkningen skal være ydmyk: «forenlig med», ikke «bevis for».

## 9 Spørsmål som må besvares før start

| # | Spørsmål | Standard hvis «ok» |
|---|---|---|
| 1 | Distrikt = sentralitet 5–6? (Alternativ: 4–6, eller befolkningsnedgang) | 5–6 |
| 2 | Bastion = Ap ≥ 50 % ved ST 1953–69? | Ja, med øvre kvartil som robusthet |
| 3 | Sp-bølger: både nasjonale (1993, 2017–21) og lokale (≥ 10 pp i kommunen, fra 1953)? | Ja, begge |
| 4 | Stortingsvalg som hovedvariant, kommunestyrevalg som parallell? | Ja |
| 5 | Skal agent L (litteratur og individdata) være med? | Ja |
| 6 | Kjøres i denne sesjonen eller i en ny (som motreaksjon-testen)? | Ny sesjon på egen gren `claude/sp-ventil` |

**Svar 2026-09-26:** «Ok». Alle standardsvarene i tabellen over gjelder. Arbeidet kjøres i ny sesjon på grenen `claude/sp-ventil`.
