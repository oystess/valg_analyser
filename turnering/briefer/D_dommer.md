# Brief – Dommer (Elo-turnering)

MÅL: Avgjør parvise dueller mellom hypoteser om hvilke kommunekjennetegn som følger med endringer i
Senterpartiets oppslutning (norske kommuner 1989–2025). Formålet er BESKRIVENDE: vi velger hvilke
mønstre som er mest verdt å kartlegge og forklare.

INPUT:
  - Hypoteser: /home/user/valg_analyser/turnering/hyp/turnering.json  (standardformat, anonyme id-er)
  - Dueller: filen orkestratoren oppgir i meldingen, f.eks. turnering/dueller/runde1_par.json
    Hver oppgave: {"oppgave": "...", "første": "Hxx", "andre": "Hyy"}.
KRITERIER (faste vekter):
  testbarhet 30 % – kan spesifikasjonen kjøres uten skjønn, og måler den påstanden?
  plausibel mekanisme 25 %
  nyhetsverdi utover det åpenbare 20 % (regresjon mot middelverdien alene er åpenbart)
  eksplorativ støtte 15 % – tall i eksplorativ_evidens
  presisjon i spesifikasjonen 10 %
REGLER:
  - Døm hver oppgave for seg, bare ut fra de to hypotesene i den. Rekkefølgen «første/andre» skal ikke
    påvirke deg; lengde og stil skal ikke påvirke deg.
  - Du skal IKKE kjøre kode eller se i data – vurder det som står i hypotesene.
  - Du må velge en vinner (ingen uavgjort).
SVARFORMAT: skriv JSON-liste til filen orkestratoren oppgir (runde<r>_svar.json):
  [{"oppgave": "R1-00a", "vinner": "Hxx", "begrunnelse": "én setning, med vektet kriterium"}]
Én rad per oppgave. GRENSER: Skriv bare til svarfilen. RETUR (høyst 3 linjer): filsti, antall dommer.
