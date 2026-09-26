# Brief KD – Uavhengig kontroll av valgdatasettet 1945–1985

Du kontrollerer et annet agents arbeid. Du har ikke sett hvordan det ble laget.
Utgangspunktet ditt er «ikke godkjent». Godkjenning må begrunnes kontroll for kontroll.

INPUT:
  Rådata: /home/user/valg_analyser/data/raw/ssb/st08092_<år>.csv (år 1945–1985) og kv01180_<år>.csv
    (1945–1983): kolonner Region (kommunekode, evt. med bokstavsuffiks), PolitParti, Godkjente1 <år>.
  Befolkning: data/raw/ssb/bef06913_kommuner.csv (kode, aar, befolkning; kode kan ha suffiks 'u'/'ut'),
    bef06913_agg2024.csv (SSBs 2024-aggregat, 0 = SSB har ikke tall).
  Endringer: utvidelse_1945/arbeid/Pa.json og Pb.json (kommuneendringer 1945–86 fra SSB-rapport 99/13,
    kontrollert og godkjent).
  Kodeoversetting: data/processed/kodemapping_1945.csv (kode, aar, kom2024, andel, metode). kode er
    befolkningstabellens kode (1951–85) eller grunnkoden (1945–50).
  Resultater: data/processed/stortingsvalg_1945.csv, kommunestyrevalg_1945.csv, befolkning_1951.csv,
    stabile_enheter.csv, *_1945_stabil.csv.
PROTOKOLL (slik resultatene skal være laget):
  - Partigrupper: 01,02(+75),03,04,05(+71 Bondepartiet),06(+70 SF),07,08,55(+11,+15),09 NKP,
    90 = alle koder som starter med «90», 99 = resten.
  - Grunnkode = de fire første sifrene i koden. En valgkode et år er befolkningskoden med samme
    grunnkode som har befolkning i «strukturåret». For kommunevalg er strukturåret året etter valgåret
    når ingen av grunnkodene som forsvant ved årsskiftet har stemmer; ellers valgåret. For 1945–1950
    brukes grunnkoden direkte. Stemmer × andel summeres per kom2024.
  - prosent = stemmer / total_stemmer i kommunen.
VERKTØY: Python/pandas. IKKE les noe i /home/user/valg_analyser/scripts/ – skriv egen kode.

GJØR DETTE:
1. Regn hele stortingsvalg_1945.csv og kommunestyrevalg_1945.csv på nytt for 1945–1985 fra rådata og
   kodemapping_1945.csv etter protokollen. Sammenlign ALLE celler (kom2024, aar, parti): stemmer og
   total_stemmer (toleranse 0,5). List avvik.
2. Sjekk at andelene i kodemapping_1945.csv summerer til 1 per (kode, aar), og at ingen stemmer fra
   rådata mangler oversetting (sum rådata = sum ferdigtabell per år).
3. For HVER rad i kodemapping_1945.csv med metode som inneholder «rapport»: finn endringene i Pa/Pb for
   koden (grunnkode) ved årsskiftet og sjekk at andelene er proporsjonale med folketallene der
   (tillat at én del uten folketall får resten). List avvik.
4. Befolkning: regn befolkning_1951.csv for 1951–1985 på nytt (bef06913 × andeler) og sammenlign.
   Tell hvor mange kommune/år som er eksakt lik SSB-aggregatet der det er > 0.
5. Plausibilitet: list 2024-kommuner der Ap-, H- eller Sp-andelen endres mer enn 25 prosentpoeng mellom
   to påfølgende valg av samme type før 1985, og vurder om det skyldes oversettingen.
6. Stabile enheter: sjekk at hver kom2024 er i nøyaktig én enhet, og at stemmene summerer.
SVAR (skriv til /home/user/valg_analyser/utvidelse_1945/kontroll/KD_data.json):
  {"kontroller": [{"id": "1", "status": "ok|feil|usikker", "n_sjekket": 0, "n_avvik": 0,
                   "eksempler": [], "begrunnelse": ""}, …],
   "ikke_sjekket": ["…" eller "alt sjekket"],
   "konklusjon": {"status": "godkjent|ikke godkjent", "avvik": 0}}
RETUR (høyst 5 linjer): filsti, konklusjon, antall avvik, antall punkter ikke sjekket.
