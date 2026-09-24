# Brief A2 – Kommuneendringer 1987–1999 fra SSB-rapport 99/13

MÅL: Trekk ut ALLE endringer i kommuneinndelingen med endringstidspunkt fra og med 1.1.1987
til og med rapportens siste dato, fra SSBs «Historisk oversikt over endringer i kommune- og
fylkesinndelingen» (Rapporter 99/13). Resultatet brukes til å oversette valgresultater fra
historiske kommunekoder til dagens kommuner, og til å avgjøre om stemmer må fordeles.

INPUT: /home/user/valg_analyser/data/raw/rapp_9913.pdf (90 sider). Les ALLE sider.
  Tekst kan hentes med Python: `import pymupdf; d=pymupdf.open(PATH); d[i].get_text()`
  (pymupdf er installert). Sidetall i svaret = PDF-sideindeks + 1.

IGNORER: Endringer med tidspunkt før 1.1.1987. Fylkesendringer som ikke endrer
  kommunenummer eller -område. Alle andre filer i repoet (ikke åpne data/raw/grenser_mapping.csv
  eller data/raw/kommunereform_mapping.csv – du skal lage en uavhengig liste).

KRITERIER / SJEKKLISTE:
  K1 Sammenslåinger: to eller flere kommuner slås sammen (hele eller deler).
  K2 Delinger: en kommune deles i flere.
  K3 Grenseendringer/overføringer av områder mellom kommuner (inkl. små, med folketall).
  K4 Navneendringer og nummerendringer (kommunenummer byttes uten arealendring,
     f.eks. ved fylkesbytte).
  K5 Rapportens dekningsperiode: siste endringsdato rapporten dekker, og om den har
     egne tabeller/lister (f.eks. alfabetisk kodeliste, oppsummeringstabell) som bekrefter
     endringene.
  Søk med varianter: «Sammenslåinger», «Delinger», «Grensejusteringer», «overført»,
  «Endringer i kommunenummer», «Navneendring», datoformater «1.1.1988», «1.1.1992» osv.
  Rapporten er ordnet per fylke (01 Østfold … 20 Finnmark); gå gjennom hvert fylke.

KILDER OG VERKTØY: Read, Grep, Bash/Python mot PDF-filen. Ingen websøk.
GRENSER: Ikke endre filer utenfor /home/user/valg_analyser/qa/arbeid/. Ikke vurder
  utenfor kriteriene. Ikke still spørsmål – merk usikkerhet i feltet «usikker».

SVARFORMAT (skrives til /home/user/valg_analyser/qa/arbeid/A2_grenser.json):
  {"dekning": {"siste_dato": "", "side": 0, "merknad": ""},
   "endringer": [
     {"id": "A2-001", "kriterium": "K1|K2|K3|K4", "fylke": "05 Oppland",
      "dato": "1.1.1992", "fra_kode": "0414", "fra_navn": "Vang",
      "omraade": "hele kommunen | beskrivelse av delområde ordrett",
      "folkemengde": 12345 eller null, "til_kode": "0403", "til_navn": "Hamar",
      "sitat": "ordrett tekst fra PDF (kort, nok til å finne stedet)",
      "side": 21, "usikker": false, "merknad": ""}
   ],
   "fylker_gjennomgått": ["01 Østfold", ...]}
  Én rad per (fra_kode, til_kode, dato). Ved sammenslåing A+B→C: én rad per gammel kommune.
  Ved deling A→X+Y: én rad per ny kommune.

KRAV:
- List ALLE forekomster fra 1987 og senere, ikke bare de viktigste.
- Oppgi side for hvert funn og et kort ordrett sitat.
- Skriv «ingen funn» (tom liste + merknad) for fylker uten endringer i perioden.
- Hold det som står i kilden atskilt fra egen tolkning (tolkning i «merknad»).
- Ikke regn summer i tekst.
- Merk usikre treff (f.eks. uleselig tabellayout, uklar dato) med "usikker": true.

RETUR TIL ORKESTRATOR (høyst 5 linjer):
  filsti, antall funn per kriterium, siste dato rapporten dekker, eventuelle problemer.
