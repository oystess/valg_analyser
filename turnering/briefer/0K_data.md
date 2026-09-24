# Brief 0K – Kontroll av analysepanelet

Du kontrollerer et annet agents arbeid. Du har ikke sett hvordan det ble laget.
Utgangspunktet ditt er «ikke godkjent». Godkjenning må begrunnes variabel for variabel.

INPUT (kilde):
  /home/user/valg_analyser/data/raw/ssb/bef07459_alder_kommuner.csv  (kode, alder F340–F345, aar, verdi)
  /home/user/valg_analyser/data/raw/ssb/flytt06913_kommuner.csv      (Fodselsoverskudd, Nettoinnflytting)
  /home/user/valg_analyser/data/raw/ssb/utd09429_kommuner.csv        (nivaa 00 = i alt, 03a/04a = UH kort/lang)
  /home/user/valg_analyser/data/raw/ssb/innt06944_kommuner.csv       (InntSkatt = median, AntallHushold)
  /home/user/valg_analyser/data/raw/ssb/syss07984_kommuner.csv       (naering 00-99, 01-03, 10-33, 84, 85, 86-88)
  /home/user/valg_analyser/data/processed/stortingsvalg_2024.csv, kommunestyrevalg_2024.csv, sentralitet_2024.csv
  /home/user/valg_analyser/data/processed/kodemapping_2024.csv  (kode, aar, kom2024, andel: oversetting av
      historiske koder til 2024-kommuner; slå opp (kode, aar), ellers (kode, aar+1), ellers (kode, aar-1))
KRITERIER: Definisjonene i /home/user/valg_analyser/turnering/data/datadictionary.md (les den).
RESULTAT SOM SKAL KONTROLLERES: /home/user/valg_analyser/turnering/data/panel.csv
VERKTØY: Read, Bash/Python (pandas er installert). Ikke les /home/user/valg_analyser/analyse/felles.py –
  du skal regne uavhengig fra kildene og definisjonene.

GJØR DETTE, I REKKEFØLGE:
1. For HVER variabel i datadictionary: regn den på nytt i egen kode for ALLE rader (ikke stikkprøver)
   og sammenlign med panel.csv (toleranse 0,01 for andeler/pp, 0,5 for tellinger, 1 kr for inntekt).
2. Tell rader per periode (skal være 357) og manglende verdier per variabel og periode; sjekk at
   manglende verdier bare finnes der datadictionary sier de skal mangle.
3. Negativ test: se etter umulige verdier (andeler utenfor 0–100, negative befolkningstall), og etter
   rader der d_sp ≠ sp_t1 − sp_t0.
4. Motstrid: sjekk at datadictionary og panel stemmer overens (kolonner som finnes i én men ikke den andre).
5. Konkluder først når 1–4 er gjort for alt.

SVAR (skrives til /home/user/valg_analyser/turnering/kontroll/0K_data.json):
  {"variabler": [{"navn": "", "status": "ok|feil|usikker", "n_rader_sjekket": 0, "n_avvik": 0,
                  "eksempler_avvik": [], "begrunnelse": ""}],
   "struktur": {"rader_per_periode": {}, "manglende": {}},
   "umulige_verdier": [], "motstrid": [],
   "ikke_sjekket": ["...", eller "alt sjekket"],
   "konklusjon": {"status": "godkjent|ikke godkjent", "ok": 0, "feil": 0, "usikker": 0}}
Et svar uten ikke_sjekket eller uten én rad per variabel er ugyldig.
RETUR TIL ORKESTRATOR (høyst 5 linjer): filsti, konklusjon, antall avvik, antall punkter ikke sjekket.
