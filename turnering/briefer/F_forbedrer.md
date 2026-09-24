# Brief – Forbedrer (evolusjon)

MÅL: Lag forbedrede versjoner av de beste hypotesene i en turnering om hvilke kommunekjennetegn som
følger med endringer i Sp-oppslutning (d_sp). Formålet er BESKRIVENDE.
INPUT: filen orkestratoren oppgir (topp 25 % i standardformat), datadictionary
  /home/user/valg_analyser/turnering/data/datadictionary.md, panel
  /home/user/valg_analyser/turnering/data/panel.csv og kjøreren analyse/modeller.py.
OPPGAVE: For hver innsendt hypotese: spiss, forenkle eller kombiner (maks 1 ny versjon per hypotese,
pluss inntil 2 kombinasjoner). Behold standardformatet; lag nye testspesifikasjoner som kjører
feilfritt i modeller.py; sett "forelder": ["Hxx", …]. Samme lekkasjeregler som før (ingen d_{annet parti},
{parti}_t1 eller d_sp_frp som forklaring). Formuler alt på kommunenivå.
SVARFORMAT: JSON-liste i standardformatet (id "E<runde>-01" …, pluss "forelder") til filen orkestratoren oppgir.
GRENSER: Skriv bare til svarfilen. RETUR (høyst 5 linjer): filsti, antall nye, problemer.
