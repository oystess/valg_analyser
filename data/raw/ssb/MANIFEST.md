# Rådata fra SSB (hentet 2026-09-24)

Alle filer er hentet fra SSBs PxWebApi v2 via SSB-MCP-verktøyet (`ssb_get_data`,
`format=csv`, `value_display=UseCodes`). Rader med verdien «.» (ikke eksisterende
kombinasjon) og, for 01180, «0», er fjernet. Ellers er tallene uendret.

Kontroll: summen over alle kommunekoder er lik SSBs landstall (region 0 eller uten
regionfilter) for hvert år og parti. Se `scripts/kontroller_datasett.py` (C2).

| Fil | Tabell | Utvalg |
|---|---|---|
| `st08092_<år>.csv` | 08092 Stortingsvalg, godkjente stemmer | Region: `*`, kodeliste `vs_KommunValg` (alle historiske koder). PolitParti: `*`. Tid: <år>. ContentsCode: `Godkjente1` |
| `kv01180_<år>.csv` | 01180 Kommunestyrevalg, godkjente stemmer | Region: `*`, kodeliste `vs_KommunerV`. PolitParti: `*`. Tid: <år>. ContentsCode: `Godkjente1` |
| `st08092_agg2024.csv` | 08092 | Region: `*`, kodeliste `agg_KommunValg2025` (SSBs 2024-aggregat, bare tall der koden er den samme). Alle partier, 1989–2025. Omformet til langt format |
| `kv01180_agg2024.csv` | 01180 | Region: `*`, kodeliste `agg_KommunerV1`. Alle partier, 1987–2023. Langt format |
| `bef07459_kommuner.csv` | 07459 Befolkning 1.1. | Region: `*`, kodeliste `vs_Kommun` (alle historiske koder). Tid: `*` (1986–2026). Kjønn og alder eliminert (sum) |
| `bef07459_agg2024.csv` | 07459 | Region: `*`, kodeliste `agg_KommSummer` («Kommuner 2024, sammenslåtte tidsserier»). Tid: `*` |
| `koder_08092.csv`, `koder_01180.csv`, `koder_07459.csv` | Kodelister | Kode og SSB-etikett med gyldighetsperiode, f.eks. «Halden (-2019)» |

Viktige egenskaper ved SSB-kildene:
- Partikoder: 11 = Rød Valgallianse (1973–2007), 55 = Rødt (2007–), 15 = Fylkeslistene for miljø
  og solidaritet (RVs liste ved stortingsvalget 1989), 90–92 = lokale lister og andre.
- `agg_KommunValg2025`/`agg_KommunerV1` gir tall bare for 2024-kommuner med samme kode som
  i valgåret (f.eks. gamle Stavanger 1989 uten Finnøy og Rennesøy). Aggregatene kan derfor bare
  brukes som fasit for uendrede kommuner.
- `agg_KommSummer` setter 0 for Heim, Hitra, Orkland, Narvik og Hamarøy før 2020 (delinger) og
  fører hele Ålesund 2020–2023 på nye Ålesund (1508).

## Sentralitet

`sentralitet_klass.csv`: SSBs sentralitetsindeks, lastet ned av Øystein fra SSBs klassifikasjonssider
(Klass, fil `klassifikasjon-koder-2682-nb.csv`) 2026-09-24. Nivå 1 = klasse 01 (høy) – 06 (lav);
nivå 2 = kommunekode med indeksverdi (0–1000) i feltet `notes`. Historiske koder har samme verdi
som kommunen de gikk inn i. Dekker alle 357 kommuner i 2024-strukturen; indeksverdiene ligger
innenfor klassegrensene for alle koder (kontrollert). Erstatter `data/raw/sentralitet.csv`
(4 klasser, ukjent kilde, trolig SSBs eldre sentralitetsstandard) i nye analyser.

## Utvidelse 1945–1986 (hentet 2026-09-26)

| Fil | Tabell | Utvalg |
|---|---|---|
| `st08092_<år>.csv`, år 1945–1985 | 08092 | Som over, `vs_KommunValg`, alle partier. «.» og 0 fjernet |
| `kv01180_<år>.csv`, år 1945–1983 | 01180 | Som over, `vs_KommunerV`, alle partier. «.» og 0 fjernet |
| `bef06913_kommuner.csv` | 06913 Befolkning 1.1. | Region `vs_Kommuner1951` (alle koder fra 1951, med suffiks som «0119u» for gjenbrukte koder), `Folkemengde`, 1951–1990 |
| `bef06913_agg2024.csv` | 06913 | Region `agg_KommSummerHist` («Kommuner 2024, sammenslåtte tidsserier»), 1951–1990. SSB setter 0 for 26 kommuner i minst ett år og fører delte områder på «Rest» |
| `koder_06913.csv` | 06913 | Kodeliste med etiketter og gyldighetsperiode |

Merk: Valgtabellene gjenbruker kommunenumre (f.eks. 0119 = Øymark før 1964, Marker fra 1964). 06913 skiller dem med suffiks. Kodens identitet et gitt år avgjøres derfor av hvilken kode som har befolkning det året.
