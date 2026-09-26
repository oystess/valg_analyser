# Djevelens advokat: motreaksjonshypotesen (Høyre-mobilisering → Sp-motreaksjon)

Grunnlag: `hypoteser/motreaksjon/låst.json`, `parvis.csv`, `resultater.json`, samt tre egne, ikke låste utregninger på tall som allerede ligger i `parvis.csv` (ingen ny kjøring på panelet). Alt om «kommuner» under; ingen påstander om individuelle velgerbevegelser.

## 1) Enkleste alternative forklaring

Mønsteret i 2009–13 → 2013–17 er trolig ikke en Høyre‑spesifikk mobiliserings‑/motreaksjonsmekanisme, men et trekk ved *store Sp-bølger generelt*: når Sp gjør et uvanlig stort nasjonalt hopp (her +4,9 pp, `sp_nasj_t1` i raden for 2013–17), blir sammenhengen mellom befolkningsvekst og Sp-endring uvanlig sterk i geografisk retning — noe H32 i `turnering/RAPPORT.md` allerede har vist for 1989–93 og 2013–17, uavhengig av hva Høyre gjorde i forrige periode. Testen mot de andre periodeparene (`resultater.json`: «P1_P2»: «ikke støttet», 0 av 6 i både ST og KV) og den positive (ikke negative) sammenhengen mellom Høyre-gradienten i t og Sp-gradienten i t+1 (P3, se pkt. 2) peker begge mot at 2009–13→2013–17 var et enkeltstående, sterkt Sp-bølge-år, ikke en gjentakbar respons på Høyres vekstmobilisering.

## 2) Innvendinger, rangert

**a) P3 går motsatt vei av hypotesen, og det er ikke ett enkeltpar som driver det.**
Låst spesifikasjon forventer *negativ* korrelasjon mellom Høyre-gradienten i t (b_P1) og Sp-gradienten i t+1 (b_P2) over testparene. Den faktiske korrelasjonen er sterkt *positiv*: Pearson 0,830 (ST, n=6), 0,933 (KV, n=6), 0,862 samlet (`resultater.json`, `status.P3`). Egen sjekk (leave-one-out på de samme tallene i `parvis.csv`, ikke låst): korrelasjonen holder seg positiv og over 0,64 uansett hvilket av de 6 parene som fjernes i ST (0,64–0,94) og over 0,83 i KV (0,83–0,99). Det er altså ikke ett spesialtilfelle som skaper mønsteret — det er en stabil, motsatt-rettet sammenheng. Dette er den kraftigste innvendingen: selve mekanismen testen er bygget rundt (mer Høyre-vekstgevinst → mer Sp-vekst-tap etterpå) finner ingen støtte i noen av periodene utenom den ene som genererte hypotesen.

**b) Spesifisitetskravet svikter helt: 0 av de robuste P1-tilfellene gir robust P2.**
`resultater.json` → `status.spesifisitet.samlet`: «P2_robust_når_P1_robust»: «0 av 1», «P2_robust_når_P1_ikke»: «0 av 11». Det eneste testparet der Høyre-gradienten var robust positiv (ST 1997–2001→2001–2005, `b_P1=0,135`, Holm-p=0,036) ga en Sp-gradient i t+1 som er *positiv*, ikke negativ (`b_P2=0,014`), og ikke robust. Hypotesens kjernepåstand — at motreaksjonen kommer spesifikt der Høyre mobiliserte — har dermed null treff i datasettet utenfor settperioden.

**c) Kontrollene ser ikke ut til å ha «drept» et reelt mønster i de fleste periodene — signalet var allerede svakt i de rå (bivariate) tallene.**
Sammenligner man `r_biv_sp_t1` (uten kontroller) mot `b_P2` (med `sp_t0` og `sent_indeks`) i `parvis.csv`, har de samme fortegn i 4 av 6 ST-par og 4 av 6 KV-par. I to KV-par (1999–2003→2003–07 og 2011–2015→2015–2019) snur kontrollene fortegnet fra positivt til negativt — her *kan* kontrollene ha maskert eller (motsatt) avdekket noe reelt, og det siste paret (2011–15→2015–19, `b_P2=-0,105`, det mest negative i hele KV-utvalget) er faktisk det testparet som ligger nærmest hypotesens forventning. Men samlet sett er «kontrollene fjerner mønsteret»-forklaringen bare treffende for 2 av 12 par — den forklarer ikke hvorfor mønsteret uteblir i de resterende 10.

**d) Sp sin egen nasjonale bølgestørrelse henger sammen med styrken på vekstgradienten, men i motsatt retning i ST og KV — et tegn på at n=6 er for lite til å bære konklusjoner om «hvorfor».**
`resultater.json` → `konkurrenter_parnivå`: korrelasjonen mellom `b_P2` og `sp_nasj_t1` er +0,797 i ST, men −0,848 i KV (samlet −0,322). At fortegnet snur mellom valgslagene, med bare 6 datapunkter i hver, viser at denne typen periodenivå-korrelasjoner er svært ustabile og ikke bør brukes til å underbygge verken hypotesen eller motforklaringene med særlig tillit.

**e) Mekanisk/måleteknisk: `vekst10_pst` overlapper 6 av 10 år mellom en periode og den neste.**
P1 bruker `vekst10_pst` målt i periode t, P2 bruker `vekst10_pst` målt i periode t+1 — men et tiårsvindu glir bare fire år mellom valg, så samme befolkningstrend (samme kommuner med varig vekst/nedgang, jf. H14 i `turnering/RAPPORT.md`) inngår i begge målingene. En kommune som er «vekstkommune» i t er nesten alltid det i t+1 også. Det svekker ikke i seg selv retningen av testen (P1 og P2 skal jo begge bruke `vekst10_pst`), men det betyr at «P1 i t» og «P2 i t+1» ikke er uavhengige observasjoner av vekst — de deler mesteparten av samme bakenforliggende, varige kommunekjennetegn. `sensitivitet_vekst4` (fireårsvekst, mindre overlapp) er beskrevet i `låst.json` men resultatene for `b_P1_v4`/`b_P2_v4` er ikke gått gjennom her (se pkt. 4).

**f) Andelene summerer til 100 — d_h og d_sp er ikke uavhengige på tvers av parti.**
Siden alle partiandeler i en kommune summerer til 100, er en kommunes d_h og d_sp mekanisk bundet sammen med d_ap, d_frp osv. Konkurrent (b) i `låst.json` (Ap-kontroll, `b_P2_ap`) forsøker å ta høyde for dette for Ap spesifikt, men ikke for de andre partiene. Dette trekker ikke i noen bestemt retning for hypotesen, men betyr at et «Sp ned»-funn alltid kan speile «et annet parti opp» like gjerne som spesifikt Høyre.

**g) Regjeringsvariabelen er dikotom og perfekt kollinær med periode i flere rader.**
`h_i_regjering_andel` er enten 0, 1, eller nær 0/1 for de fleste periodeparene (f.eks. `1,0` i 2009–13→2013–17, 2011–15→2015–19 og 2013–17→2017–21), så P5 («Sp-gradienten mer negativ når Høyre sitter i regjering») testes reelt på svært få uavhengige tilfeller. Status er da også bare «delvis (beskrivende)», og `resultater.json` sitt eget tall viser at snittet av `b_P2` i regjeringsperiodene (ST: +0,012, KV: −0,038) ikke systematisk er mer negativt enn i opposisjonsperiodene (ST: −0,031, KV: −0,021) — i ST er det faktisk omvendt.

## 3) Hva som ville styrket eller svekket konklusjonen

- **Styrket hypotesen:** om P3 hadde vært negativ (ikke positiv) og stabil over leave-one-out, og om det robuste P1-tilfellet (ST 1997–2001) hadde gitt en robust negativ P2 i neste periode. Ingen av delene skjer.
- **Styrket motforklaringen (Sp-bølge/periferi uavhengig av Høyre):** en direkte test av om styrken på vekst–Sp-gradienten (`|b_P2|`) korrelerer med *størrelsen* på det nasjonale Sp-hoppet (`|sp_nasj_t1|`) uavhengig av fortegn, kjørt på flere enn 6 punkter per valgslag (f.eks. slått sammen ST+KV med periodedummier), ville gitt et fastere svar enn de sprikende fortegnene i pkt. 2d.
- **Svekket motforklaringen:** om `b_P4` (Sp mot Høyres vekst-residual, som kontrollerer for selve vekstnivået) hadde vært robust negativ — det ville isolert en Høyre-spesifikk mekanisme fra den generelle vekstgradienten. I stedet er `b_P4` upresist og peker om noe i motsatt retning (P4B, ikke P4A) i begge valgslag, med p > 0,49 i hovedspesifikasjonen (`resultater.json`, «P4 ST samlet»/«P4 KV samlet»).

## 4) Ikke sjekket

- `vekst4_pst`-sensitiviteten (`b_P1_v4`, `b_P2_v4` i `parvis.csv`) er ikke gjennomgått par for par.
- `b_P2_ap`/Ap-konkurrenten og `reform_2017_20`-konkurrenten er ikke vurdert i detalj utover å konstatere at de finnes i `låst.json`.
- Effekten av kommunesammenslåinger og estimerte kommuner (`uten_estimert`-batteriet) på de spesifikke testparene er ikke gått gjennom rad for rad, bare konstatert at status-reglene inkluderer dette batteriet.
- Ingen ny regresjon er kjørt på `turnering/data/panel.csv` eller `kv_panel.csv`; alle tall i dette notatet kommer fra `parvis.csv`/`resultater.json` eller enkel etterregning på de samme tallene.
- Om resultatet er skjevt til fordel for eller mot hypotesen i valg av kontrollvariabler (`sp_t0`, `sent_indeks`) er ikke undersøkt utover sammenligningen i pkt. c; en formell test (f.eks. hvor mye p-verdien endres når kontrollene fjernes én om gangen) er ikke gjort.
