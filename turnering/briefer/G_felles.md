# Felles brief for generatorer (G1–G4)

MÅL: Foreslå 8 hypoteser om **hvilke kommunekjennetegn som følger med endringer i Senterpartiets
oppslutning i stortingsvalg** i norske kommuner 1989–2025. Hypotesene skal rangeres i en blindet
turnering, og de beste kjøres til slutt med låste spesifikasjoner og et robusthetsbatteri.
Formålet er **beskrivende**: vi kartlegger sammenhenger på kommunenivå, ikke årsaker. Det finnes
ingen holdout-data; du ser hele panelet.

SPØRSMÅL / UTFALL: `d_sp` = endring i Sp-andel (prosentpoeng) fra stortingsvalg t0 til t1.
ANALYSEENHET: kommune (2024-inndeling, 357) × valgperiode (9 perioder, 1989–1993 … 2021–2025).

INPUT:
  - Panel: /home/user/valg_analyser/turnering/data/panel.csv
  - Datadictionary: /home/user/valg_analyser/turnering/data/datadictionary.md  (les den først)
  - Kjører for spesifikasjoner: /home/user/valg_analyser/analyse/modeller.py
    Bruk: `python3 analyse/modeller.py '<json>'` fra /home/user/valg_analyser, eller
    `from modeller import kjør` (sys.path.insert(0, 'analyse')). Klyngerobuste SE på kommune er innebygd.
  - Litteraturgrunnlag (frø): /home/user/valg_analyser/litteratur_notat.md, avsnitt 1–7

FRØ (fra litteraturnotatet – ta stilling, ikke gjengi ukritisk):
  H1 Periferieffekten er strukturell, men intensiteten topper seg rundt utløsere (1993, 2019–21).
  H2 Befolkningsnedgang forsterker periferieffekten (tjenestetap, identitet, relativ deprivasjon).
  H3 Effekten av befolkningsnedgang er episodisk sterkere, særlig 2015–2021.
  H4 Effekten er sterkere i kommunevalg enn stortingsvalg.
  H5 Kommunevalg leder stortingsvalg.
  H6 Sp og FrP konkurrerer om de samme periferivelgerne (routing).
  H7 Utflytting av unge gir eldre, mer stedsbundet velgermasse → sterkere Sp-effekt.

REGLER (lekkasje og nivå):
  - Utfallet er d_sp. IKKE bruk andre partiers t1-andeler eller d_{annet parti} (inkl. d_frp,
    d_sp_frp) som forklaringsvariabler – andeler summerer mekanisk til 100. {parti}_t0 er tillatt.
  - IKKE bruk sp_t1 eller noe annet som inneholder utfallet. kv_d_sp og kv_sp_t0 er tillatt
    (kommunevalget ligger to år før t1 og måler noe annet), men merk det i mekanismen.
  - Formuler alt på kommunenivå («kommuner med X …»), aldri om personer.
  - `sp_t0` bør som hovedregel være med som kontroll (regresjon mot middelverdien er sterk).
  - Inntekt finnes bare fra periode 2005–2009, næringsandeler bare fra 2009–2013: bruk da
    `utvalg`, f.eks. "t0 >= 2009".
  - Hver testspesifikasjon MÅ kjøre feilfritt med analyse/modeller.py før du leverer den.

KRAV TIL LEVERANSEN:
  1. Ta eksplisitt stilling til minst to frø (spiss, avgrens eller motsi dem).
  2. Minst tre av de 8 hypotesene skal være nye (ikke varianter av frøene).
  3. Hver hypotese har falsifisering og en entydig testspesifikasjon.
  4. Rapporter eksplorative tall fra panelet som rådata (koeffisient, KI, n) i eksplorativ_evidens.
  5. Unngå å levere 8 varianter av samme idé.

SVARFORMAT – skriv en JSON-liste til /home/user/valg_analyser/turnering/hyp/<DIN-ID>.json:
[
 {
  "id": "<DIN-ID>-01",
  "påstand": "én setning, kommunenivå",
  "mekanisme": "hvorfor mønsteret kan finnes (2–4 setninger)",
  "forhold_til_frø": "H2: spisser … | ny",
  "operasjonalisering": {"utfall": "d_sp", "forklaring": ["..."], "retning": "+/-", "kontroller": ["..."]},
  "testspesifikasjon": {"formel": "...", "nøkkelledd": "...", "forventet_fortegn": "+|-",
                        "utvalg": null, "vekt": "vekt_stemmer_t0"},
  "falsifisering": "hvilket resultat ville avkrefte mønsteret",
  "eksplorativ_evidens": "b = …, 95 % KI […, …], p = …, n = … (fra modeller.py)"
 }, ...
]

KILDER OG VERKTØY: Read, Bash/Python mot filene over. Ingen websøk.
GRENSER: Ikke endre filer utenfor turnering/hyp/. Ikke les andre generatorers filer. Ikke still spørsmål.
RETUR TIL ORKESTRATOR (høyst 5 linjer): filsti, antall hypoteser, hvilke frø du tok stilling til, problemer.
