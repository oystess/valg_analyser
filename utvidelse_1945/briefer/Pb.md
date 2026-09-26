# Brief Pb – Kommuneendringer 1945–1986 fra SSB-rapport 99/13 (fylke 11 Rogaland til og med 20 Finnmark)

MÅL: Trekk ut ALLE endringer i kommuneinndelingen med endringstidspunkt fra og med 1.1.1945 til og
med 31.12.1986 for fylkene **11 Rogaland til og med 20 Finnmark**, fra SSBs «Historisk oversikt over endringer i kommune- og
fylkesinndelingen» (Rapporter 99/13). Resultatet brukes til å oversette valgresultater 1945–1985 fra
historiske kommunekoder til dagens kommuner, og særlig til å FORDELE stemmer når en kommune ble delt
eller mistet et område. Folketallet for hvert område er derfor det viktigste feltet.

INPUT: /home/user/valg_analyser/data/raw/rapp_9913.pdf (90 sider). Tekst: `import pymupdf; d=pymupdf.open(PATH); d[i].get_text()`
  (pymupdf er installert; side = indeks+1). Les alle sider som gjelder dine fylker, og fylkesoversikten
  bakerst (s. 86–89) der den gjelder dine fylker. Tabellene har kolonnene: gammel enhet / område,
  «Folkemengde ved endring», «Endringstidspunkt», «Ny kommuneenhet». pdf-teksten kommer én celle per linje –
  sett sammen radene nøye og kontroller mot sidebildet ved tvil (`d[i].get_pixmap()` kan lagres som PNG og leses).
IGNORER: Endringer før 1.1.1945 og etter 31.12.1986. Andre fylker. Andre filer i repoet.

KRITERIER / SJEKKLISTE:
  K1 Sammenslåinger (hele kommuner eller deler inn i ny/eksisterende kommune).
  K2 Delinger (en kommune deles i flere).
  K3 Grenseendringer/overføringer av områder mellom kommuner (også små, med folketall).
  K4 Navneendringer og nummerendringer.
  For HVER rad: fra_kode og fra_navn (kommunen området kom FRA), om hele kommunen eller en del,
  folketallet i området (heltall, som oppgitt), dato, til_kode og til_navn.
  Rapporten ordner hvert fylke i «Sammenslåinger», «Delinger», «Grensejusteringer»/overføringer osv.
  Gå gjennom hvert fylke og hver underoverskrift.

KILDER OG VERKTØY: Read, Bash/Python mot PDF-filen. Ingen websøk.
GRENSER: Skriv bare til /home/user/valg_analyser/utvidelse_1945/arbeid/Pb.json. Ikke still spørsmål –
  merk usikkerhet i feltet «usikker».

SVARFORMAT:
  {"fylker_gjennomgått": ["01 Østfold", ...],
   "endringer": [
     {"id": "Pb-001", "kriterium": "K1|K2|K3|K4", "fylke": "", "dato": "1.1.1964",
      "fra_kode": "0524", "fra_navn": "Fåberg", "hele_kommunen": true,
      "omraade": "ordrett beskrivelse av området (eller 'hele kommunen')",
      "folkemengde": 13381 eller null, "til_kode": "0501", "til_navn": "Lillehammer",
      "sitat": "kort ordrett tekst fra PDF", "side": 21, "usikker": false, "merknad": ""}]}
  Én rad per (fra_kode, område, til_kode, dato). Når en kommune fordeles på flere, én rad per del –
  med hver dels folketall.

KRAV:
- List ALLE forekomster i perioden for dine fylker. Skriv tomme lister med merknad for fylker uten endringer.
- Oppgi side og kort sitat for hvert funn. Hold kilde og tolkning atskilt (tolkning i «merknad»).
- Ikke regn summer. Merk usikre rader (uleselig layout, uklar kobling mellom tall og område).

RETUR TIL ORKESTRATOR (høyst 5 linjer): filsti, antall funn per kriterium, antall usikre, problemer.
