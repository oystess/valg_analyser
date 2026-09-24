# Brief K1 – Kontroll av A2 (kommuneendringer 1987–1999 fra SSB-rapport 99/13)

Du kontrollerer et annet agents arbeid. Du har ikke sett hvordan det ble laget.
Utgangspunktet ditt er «ikke godkjent». Godkjenning må begrunnes rad for rad.

INPUT (kilde): /home/user/valg_analyser/data/raw/rapp_9913.pdf (90 sider, hele).
  Tekst: `import pymupdf; d=pymupdf.open(PATH); d[i].get_text()` (side = indeks+1).
KRITERIER (ordrett som arbeideren fikk):
  Trekk ut ALLE endringer i kommuneinndelingen med endringstidspunkt fra og med 1.1.1987
  til og med rapportens siste dato.
  K1 Sammenslåinger: to eller flere kommuner slås sammen (hele eller deler).
  K2 Delinger: en kommune deles i flere.
  K3 Grenseendringer/overføringer av områder mellom kommuner (inkl. små, med folketall).
  K4 Navneendringer og nummerendringer.
  K5 Rapportens dekningsperiode.
RESULTAT SOM SKAL KONTROLLERES: /home/user/valg_analyser/qa/arbeid/A2_grenser.json
VERKTØY: Read, Grep, Bash/Python. Ingen websøk. Ikke åpne andre filer i repoet.

GJØR DETTE, I REKKEFØLGE:
1. For HVERT funn: sjekk i kode at «sitat» står (tilnærmet ordrett, tillat whitespace-
   forskjeller) på oppgitt side. Sjekk dato, fra_kode, til_kode, folkemengde mot kilden.
   Les hvert avvik manuelt. Ikke stikkprøver.
2. For HVERT kriterium: søk selv i hele PDF-en etter datoer 1987–1999 (regex på
   «1.1.198[7-9]», «1.1.199\d», andre dd.mm.åååå i perioden), og ord som «Sammenslåinger»,
   «Delinger», «overført», «Grensejusteringer», «Endringer i kommunenummer», «Navneendring».
   List endringer i perioden som mangler i resultatet.
3. Negativ test: finn falske positiver – endringer før 1987, fylkesendringer uten
   kommuneendring, dobbeltføringer av samme endring.
4. Motstrid: funn som strider mot hverandre (f.eks. samme kode til to mål uten at
   det er en deling), eller retning som er snudd (fra/til).
5. Konkluder først når 1–4 er gjort for alt.

SVAR (skrives til /home/user/valg_analyser/qa/kontroll/K1_A2.json):
  {"funn": [{"id": "A2-001", "status": "ok|feil|usikker", "begrunnelse": "", "side": 0}],
   "kriterier": [{"id": "K1", "status": "komplett|mangler", "mangler": [{"beskrivelse": "", "side": 0, "sitat": ""}]}],
   "falske_positiver": [{"id": "", "begrunnelse": ""}],
   "motstrid": [] eller [{"ider": [], "beskrivelse": ""}],
   "ikke_sjekket": ["...", eller "alt sjekket"],
   "konklusjon": {"status": "godkjent|ikke godkjent", "ok": 0, "feil": 0, "usikker": 0}}
Et svar uten ikke_sjekket eller uten én rad per funn og per kriterium er ugyldig.
Ikke skriv om arbeidet. Rapporter bare status og avvik.
RETUR TIL ORKESTRATOR (høyst 5 linjer): filsti, konklusjon, antall avvik, antall punkter ikke sjekket.
