# Brief Ka – Kontroll av Pa (kommuneendringer 1945–1986, fylke 01 Østfold til og med 10 Vest-Agder)

Du kontrollerer et annet agents arbeid. Du har ikke sett hvordan det ble laget.
Utgangspunktet ditt er «ikke godkjent». Godkjenning må begrunnes rad for rad.

INPUT (kilde): /home/user/valg_analyser/data/raw/rapp_9913.pdf – sidene for fylkene 01 Østfold til og med 10 Vest-Agder og fylkesoversikten
  s. 86–89. Tekst: `import pymupdf; d=pymupdf.open(PATH); d[i].get_text()` (side = indeks+1). Ved tvil om
  tabellayout: lagre `d[i].get_pixmap(dpi=150)` som PNG og les bildet.
KRITERIER (ordrett som arbeideren fikk): Trekk ut ALLE endringer i kommuneinndelingen med endringstidspunkt
  1.1.1945–31.12.1986 for fylkene 01 Østfold til og med 10 Vest-Agder: K1 sammenslåinger, K2 delinger, K3 grenseendringer/overføringer
  (også små, med folketall), K4 navne-/nummerendringer. For hver rad: fra_kode, fra_navn, hele_kommunen,
  folketall i området, dato, til_kode, til_navn.
RESULTAT SOM SKAL KONTROLLERES: /home/user/valg_analyser/utvidelse_1945/arbeid/Pa.json
VERKTØY: Read, Bash/Python. Ingen websøk. Ikke åpne andre filer i repoet.

GJØR DETTE, I REKKEFØLGE:
1. For HVER rad: sjekk i kode at sitatet finnes på oppgitt side (tillat whitespace-forskjeller). Sjekk
   manuelt (tekst eller sidebilde) at fra_kode, til_kode, dato og ikke minst FOLKETALL hører til samme
   område i tabellen – tall kan lett forskyves én rad i pdf-teksten. Ingen stikkprøver.
2. For HVER sammenslåing der en kommune fordeles på flere mottakere: sjekk at alle delene er med.
3. Søk selv etter endringer i perioden som mangler (datoer 1945–1986, «Sammenslåinger», «Delinger»,
   «overført», «Grensejusteringer»), og list dem.
4. Negativ test: dobbeltføringer, endringer utenfor perioden eller fylkene, snudd retning.
5. Konkluder først når 1–4 er gjort for alt.

SVAR (skriv til /home/user/valg_analyser/utvidelse_1945/kontroll/Ka.json):
  {"rader": [{"id": "", "status": "ok|feil|usikker", "feltfeil": {"felt": "riktig verdi"}, "begrunnelse": "", "side": 0}],
   "mangler": [{"beskrivelse": "", "side": 0, "sitat": "", "fra_kode": "", "til_kode": "", "folkemengde": null, "dato": ""}],
   "falske_positiver": [], "motstrid": [],
   "ikke_sjekket": ["…" eller "alt sjekket"],
   "konklusjon": {"status": "godkjent|ikke godkjent", "ok": 0, "feil": 0, "usikker": 0, "mangler": 0}}
Et svar uten ikke_sjekket eller uten én rad per id er ugyldig. Ikke skriv om arbeidet – rapporter status og avvik.
RETUR (høyst 5 linjer): filsti, konklusjon, antall feil/mangler, antall ikke sjekket.
