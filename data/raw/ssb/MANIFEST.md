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
