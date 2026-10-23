#!/usr/bin/env python3
"""
hent_stv_fiks.py — Proveniens og parser for den permanente 1989-fiksen og
STV-nevnerkorreksjonen (gjennomgang_analyse.md tiltak 1, gjennomført 2026-07-04).

HVA BLE FIKSET:
  1. 1989-laget i stortingsvalg_2024.csv var korrupt: Ap-stemmene dobbelttalt
     (1 814 786 mot offisielt 907 393), og Vang i Hedmark (0414, innlemmet i
     Hamar 1992) var feilmappet til Vang i Valdres (3454). Hele laget er
     erstattet med et ferskt SSB-uttrekk.
  2. RV-mysteriet oppklart: Rødt/RV «manglet» ikke i 1989 — RV stilte som del
     av Fylkeslistene for miljø og solidaritet (kode 15, 22 139 stemmer).
     Kode 55 (Rødt) fantes ikke i 1989; null er korrekt.
  3. Ny fil stv_prosent_korrigert.csv: partiprosent med ALLE godkjente stemmer
     som nevner (ikke bare 9-partisummen). «Andre» utgjorde 3,7 % i 2021
     (Pasientfokus m.fl.) og 4,5 % i 2025 — nevneren er ikke neglisjerbar.

DATAKILDER (SSB MCP, hentet 2026-07-04, tabell 08092
«Stortingsvalet. Godkjende røyster, etter parti/valliste (K) 1945-2025»):
  - Nasjonal fasit: Region="0" (Hele landet), PolitParti="*",
    ContentsCode=Godkjente1, Tid=1989..2025 → stv_fasit_nasjonal.csv
  - 1989 per kommune: Region=* (codelist vs_KommunValg, alle historiske koder),
    PolitParti = kodene med stemmer i 1989 (01-08, 10, 12, 14, 15, 24, 25),
    Tid=1989 → aggregert til 2024-struktur via kom_mapping.csv MED overstyring
    0414→3403 (Vang Hedmark → Hamar) → stv_1989_ny.csv
  - Andre-partier per kommune per år: per valgår, partikodene utenfor de ni
    store som hadde stemmer det året (fra fasitfilen), Region=vs_KommunValg
    → summert til stemmer_andre; godkjente_i_alt = verifisert 9-partisum
    + stemmer_andre → stv_total_godkjente.csv

VALIDERING (kjørt ved fiks):
  - Fasit-sjekk etter fiks: 85/85 parti×år innenfor ±3 % (de fleste eksakt).
  - Nasjonal totalsum per år: ratio 1,0000 mot fasit for 9 av 10 år.
  - Nasjonal Sp-serie med korrigert nevner reproduserer offisielle tall
    eksakt: 6,5 (1989), 16,7 (1993), 10,3 (2017), 13,5 (2021), 5,6 (2025).
  - Vang i Valdres 1989: 1 039 stemmer (før: 10 900); Hamar: 17 050.

KJENTE HULL (dokumentert, ikke feil i pipeline):
  - 2009: mikropartier med til sammen 3 692 stemmer (0,14 % — Demokratene,
    Abort-motstandernes liste m.fl.) finnes kun på nasjonalt nivå i SSBs
    tabell, aldri per kommune. stv_total_godkjente undervurderer 2009-totalen
    tilsvarende.

TEKNISK LÆRDOM: PolitParti="*" (87 koder) mot alle kommuner får SSB-MCP-økten
til å utløpe («session expired»); uttrekk med ≤ 16 eksplisitte koder per kall
fungerer. Rå tool-result-JSON ligger i sesjonens tasks-katalog og er IKKE
committet — men alle avledede CSV-er er det, og dette skriptet dokumenterer
nøyaktig selection for hvert kall slik at alt kan hentes på nytt.

Dette skriptet er dokumentasjon; re-nedlasting krever SSB MCP i en
Claude Code-økt. Parselogikken (regex, mapping, aggregering) er identisk
med den som ble kjørt, og bevart under.
"""

# Parse-mønsteret som ble brukt (for re-kjøring med nye rå-filer):
#
# import json, pandas as pd, csv as csvmod
# raw = pd.DataFrame(json.load(open(tool_result_fil))["rows"])
# raw["kom_gml"] = raw.Region.str.extract(r"(\d{4})")[0]      # IKKE ^-anker
# raw["parti"]   = raw.PolitParti.str.extract(r"^(\S+)")[0]
# raw["stemmer"] = pd.to_numeric(raw.Godkjente1, errors="coerce")
# mapping = {r["gammelt_nr"]: r["nr_2024"] for r in
#            csvmod.DictReader(open("data/processed/kom_mapping.csv"))
#            if r["nr_2024"]}
# mapping["0414"] = "3403"   # Vang (Hedmark) -> Hamar
# d = raw.dropna(subset=["stemmer", "kom_gml"]); d = d[d.stemmer > 0]
# d["kom2024"] = d.kom_gml.map(lambda x: mapping.get(x, x))
# agg = d.groupby(["kom2024", "parti"]).stemmer.sum()

if __name__ == "__main__":
    print(__doc__)
