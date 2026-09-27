# Brief L – litteratur og individdata om velgerstrømmer Ap → Sp → andre

MÅL: Finn publiserte individdata (overgangstall/velgerstrømmer) og forskning om velgere som går fra Ap til Sp,
og fra Sp videre til andre partier (tilbake til Ap, FrP, H, andre), særlig rundt Sp-bølgene 1993 og 2017–2021
og tilbakefallene 1997 og 2025. Resultatet brukes som individnivå-kontroll av en aggregert kommuneanalyse
(hypotese: Sp er en «ventil» for Ap-velgere i distriktet, og de kommer ikke tilbake til Ap).

INPUT: Åpne nettkilder (websøk + henting). Prioriter:
- Valgundersøkelsen (NSD/Sikt, SSB-rapporter «Valgundersøkelsen 1989/1993/1997», ISF/Institutt for samfunnsforskning).
- Aardal & Valen «Konflikt og opinion» (1995), Aardal «Velgere i 90-årene» (1999), Aardal & Bergh (red.) «Valg og velgere» (2015, 2019),
  Bergh, Aardal m.fl. «Velgere og valgkamp» / «Et politisk jordskred?» (2021-valget, 2023), eventuelle 2025-publikasjoner.
- Forskning om Sp og EU-kampen 1972/1994, «periferiopprør» (Rokkan, Valen, Aarebrot, Stein Rokkan-tradisjonen, Fitjar, Ivarsflaten m.fl.).
- Velgerstrømmer fra NRK/TV 2/Respons/Norstat valgdagsmålinger (exit polls) 2017, 2021, 2025 – merk at dette er målinger, ikke valgundersøkelsen.
- Historisk (1950–1989): alt om Bondepartiet/Sp sin vekst i Ap-dominerte utkantstrøk (Nord-Norge, Trøndelag) og om Ap tapte til Sp da.
IGNORER: Våre egne data og filer i repoet; generell partihistorie uten tall; meningsmålinger uten overgangstall.

KRITERIER / SJEKKLISTE:
  K1: Overgangstall Ap → Sp (andel av Aps velgere forrige valg som stemte Sp), per valg: 1993, 1997, 2017, 2021, 2025 (og tidligere hvis finnes).
  K2: Overgangstall Sp → andre (hvor gikk Sp-velgerne fra forrige valg: tilbake til Ap, til FrP, H, sofa osv.), særlig 1997 og 2025.
  K3: Sammensetning av Sp-velgere i bølgevalg: andel som stemte Ap ved forrige valg.
  K4: Forskning om at velgere som forlater Ap i periferien ikke kommer tilbake / økt velgerflyktighet (volatilitet) over tid, inkl. nasjonale tall for andel partibyttere per valg (Valgundersøkelsen).
  K5: Forskning om Sp-vekst 1950–1989 i Ap-kommuner og hvem Sp tok fra (Ap vs. V/KrF/H), og om felleslister (Sp med KrF/V) 1973–89.
  K6: Forbehold i kildene (utvalgsstørrelse, erindringsskjevhet om tidligere stemme, forskjell mellom valgundersøkelse og valgdagsmåling).

KILDER OG VERKTØY: WebSearch, WebFetch, Read, Write. Python er lov for å lagre JSON. Ikke bruk andre kilder enn åpne nettkilder.
GRENSER: Ikke endre filer i repoet utenom svarfilen. Ikke tolk eller regn videre på våre data. Ikke finn på tall:
rapporter bare tall du har sett i kilden, med kilde (URL, tittel, tabell/side). Hvis et tall bare finnes gjengitt sekundært
(f.eks. i en avisartikkel om valgundersøkelsen), merk det som «sekundær». Ikke regn summer eller snitt.

SVARFORMAT (skrives til /home/user/valg_analyser/hypoteser/sp_ventil/arbeid/L_litteratur.json):
  {"funn": [
    {"id": "L01", "kriterium": "K1", "valg": "1993", "fra_parti": "Ap", "til_parti": "Sp",
     "tall": "12 %", "maal": "andel av Aps 1989-velgere",
     "sitat_eller_tall": "<ordrett eller nær ordrett fra kilden>",
     "kilde": {"tittel": "", "forfatter": "", "aar": "", "url": "", "side_tabell": ""},
     "primær_eller_sekundær": "primær|sekundær", "usikkerhet": "", "tolkning": ""}
   ],
   "kriterier_uten_funn": ["K..."],
   "søk_gjort": ["<søkestrenger brukt>"],
   "problemer": ""}
  Skriv også et kort sammendrag på norsk bokmål (høyst 1 side) til
  /home/user/valg_analyser/hypoteser/sp_ventil/arbeid/L_litteratur.md med de viktigste tallene og kildene.

KRAV:
- List ALLE relevante overgangstall du finner, ikke bare de viktigste.
- Oppgi kilde for hvert funn.
- Skriv «ingen funn» for kriterier uten treff (i kriterier_uten_funn).
- Hold det som står i kilden (sitat_eller_tall) atskilt fra egen tolkning.
- Rapporter rådata. Ikke regn summer, snitt eller andeler i tekst.
- Merk usikre treff og mulige falske treff eksplisitt (f.eks. om tallet er andel av avgiverpartiets eller mottakerpartiets velgere).
- Skriv på norsk bokmål.

RETUR TIL ORKESTRATOR (høyst 5 linjer):
  filsti, antall funn per kriterium, eventuelle problemer.
