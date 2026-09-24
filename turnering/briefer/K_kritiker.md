# Brief – Kritiker

MÅL: Vurder hver hypotese i en blindet hypoteseturnering om norske kommunevalgdata, og gi dom:
`godkjent`, `revider` (med konkret endring) eller `forkast` (med begrunnelse). Forkastede går ikke
videre til turneringen. Formålet med analysen er BESKRIVENDE (sammenhenger på kommunenivå, ingen
holdout), så hypotesene skal ikke påstå årsakseffekter i testen – mekanismen er bare begrunnelse.

INPUT:
  - Hypoteser: /home/user/valg_analyser/turnering/hyp/samlet.json   (eller filen orkestratoren oppgir)
  - Datadictionary: /home/user/valg_analyser/turnering/data/datadictionary.md
  - Panel: /home/user/valg_analyser/turnering/data/panel.csv
  - Kjører: /home/user/valg_analyser/analyse/modeller.py  (`python3 analyse/modeller.py '<json>'`)
IGNORER: Hvem som har laget hypotesene (id-ene er anonyme – ikke prøv å gjette).

SJEKKLISTE (for HVER hypotese):
  S1 Testbar med variablene som finnes? Kjør testspesifikasjonen med modeller.py – feiler den, er det `revider`.
  S2 Triviell eller tautologisk (f.eks. mekanisk regresjon mot middelverdien uten mer innhold)?
  S3 Lekkasje: bruker den d_{annet parti}, {parti}_t1, d_sp_frp eller noe annet som inneholder utfallet?
  S4 Økologisk feilslutning: påstås noe om personer?
  S5 Omvendt kausalitet / åpenbar konfundering som gjør påstanden misvisende selv som beskrivelse
     (f.eks. mangler sp_t0 som kontroll uten begrunnelse)?
  S6 Entydig spesifikasjon: kan den kjøres uten skjønn? Stemmer nøkkelledd og forventet_fortegn med påstanden?
  S7 Duplikat: er den i praksis lik en annen hypotese? (Forkast den svakest spesifiserte og nevn hvilken den dupliserer.)

SVARFORMAT (skriv til filen orkestratoren oppgir, standard
/home/user/valg_analyser/turnering/hyp/kritikk.json):
[{"id": "H01", "dom": "godkjent|revider|forkast",
  "sjekkliste": {"S1": "ok|problem: …", … "S7": "ok|duplikat av H.."},
  "begrunnelse": "…",
  "revidert_testspesifikasjon": null eller {"formel": …, "nøkkelledd": …, "forventet_fortegn": …, "utvalg": …, "vekt": …},
  "revidert_påstand": null eller "…"}]
Én rad per hypotese. En revidert spesifikasjon MÅ kjøre feilfritt i modeller.py.
KILDER OG VERKTØY: Read, Bash/Python. Ingen websøk. GRENSER: Skriv bare til svarfilen. Ikke still spørsmål.
RETUR (høyst 5 linjer): filsti, antall godkjent/revider/forkast, problemer.
