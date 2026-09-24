# Datadictionary: turnering/data/panel.csv

**Enhet:** Én rad per 2024-kommune (357) × stortingsvalgperiode t0 → t1 (9 perioder: 1989–1993 … 2021–2025), til sammen 3 213 rader.
**Bygget av:** `analyse/felles.py` fra rådata i `data/raw/ssb/` og `data/processed/`. Alle tellinger er harmonisert til 2024-kommuner med `kodemapping_2024.csv`.
**Nivå:** Alle sammenhenger gjelder kommuner, ikke personer.

| Variabel | Enhet | Definisjon | Kilde og år |
|---|---|---|---|
| kom2024, navn | – | Kommunenummer og -navn i 2024 | SSB-kodelister |
| periode, t0, t1 | år | Stortingsvalg ved start og slutt av perioden | – |
| fylke, landsdel | kategori | Fylke 2024 (15) og landsdel (Oslo/Akershus, Østlandet, Innlandet, Agder, Vestlandet, Trøndelag, Nord-Norge) | Kommunenummer |
| sent_klasse | 1–6 | SSBs sentralitetsklasse (1 = mest sentral, 6 = minst) | Klass, fast |
| sent_indeks | 0–1000 | SSBs sentralitetsindeks | Klass, fast |
| estimert | bool | Kommunens stemmer er delvis fordelt etter befolkning (delte kommuner: Heim, Hitra, Orkland, Narvik, Hamarøy før 2020; Ålesund og Haram 2021) | QA |
| vekt_stemmer_t0 | antall | Godkjente stemmer i ST t0 (vekt) | SSB 08092 |
| {parti}_t0, {parti}_t1 | % | Partiets andel av alle godkjente stemmer i ST t0 og t1. Parti: ap, frp, h, krf, sp, sv, v, mdg, rodt (inkl. RV/FMS), andre | SSB 08092 |
| d_{parti} | pp | {parti}_t1 − {parti}_t0 | – |
| **d_sp** | pp | **Hovedutfall:** endring i Sp-andel fra ST t0 til ST t1 | – |
| d_sp_frp | pp | d_sp + d_frp («protestblokk», bare robusthet) | – |
| kv_sp_t0 | % | Sp-andel i kommunevalget i året t0 − 2 | SSB 01180 |
| kv_d_sp | pp | Endring i Sp-andel mellom kommunevalgene t0 − 2 og t1 − 2 (bare robusthet) | SSB 01180 |
| bef_t0, ln_bef_t0 | personer | Befolkning 1.1. t0, og logaritmen | SSB 07459 |
| vekst4_pst | % | Befolkningsvekst 1.1. t0 → 1.1. t1 | SSB 07459 |
| vekst10_pst | % | Befolkningsvekst 1.1. (t1 − 10) → 1.1. t1 (mangler for 1989–1993) | SSB 07459 |
| nettoinnfl_per1000 | per 1000 | Nettoinnflytting (innenlands og fra utlandet) summert over kalenderårene t0 … t1 − 1, per 1000 innbyggere 1.1. t0 | SSB 06913 |
| fodselsovsk_per1000 | per 1000 | Fødselsoverskudd summert over samme år, per 1000 innbyggere | SSB 06913 |
| andel_67p_t0 | % | Andel 67 år og eldre, 1.1. t0 | SSB 07459 |
| andel_19_34_t0 | % | Andel 19–34 år, 1.1. t0 | SSB 07459 |
| d_andel_67p | pp | Endring i andel 67+ fra t0 til t1 | SSB 07459 |
| andel_hoyutd_t0 | % | Andel med universitets- eller høgskoleutdanning blant personer 16+, året før t0 | SSB 09429 |
| inntekt_median_t0 | kr | Median inntekt etter skatt, alle husholdninger, året før t0. **Bare fra periode 2005–2009** (for den perioden: 2005). For sammenslåtte kommuner er verdien et husholdningsvektet snitt av medianene (tilnærming). | SSB 06944 |
| andel_primaer_t0 | % | Andel sysselsatte (bosted, 15–74 år, 4. kvartal) i jordbruk, skogbruk og fiske, året før t0. **Bare fra periode 2009–2013.** | SSB 07984 |
| andel_industri_t0 | % | Tilsvarende for industri | SSB 07984 |
| andel_offentlig_t0 | % | Tilsvarende for offentlig administrasjon, undervisning og helse- og sosialtjenester | SSB 07984 |

**Lekkasjevern:** Andre partiers andeler i t1 og d_{annet parti} regnes som del av utfallet og kan **ikke** brukes som forklaringsvariabler for d_sp, fordi andelene summerer mekanisk til 100. Nivåer i t0 ({parti}_t0) er tillatt.
**Nuller:** Rådatafilene i `data/raw/ssb/` er lagret uten rader med verdien 0. En næring som mangler for en kommune, betyr derfor 0 sysselsatte i næringen (for eksempel industri i Utsira og Leka), og andelen settes til 0.
**Kjente begrensninger:** Utdanning har noen hundre personer per år med ukjent kommune fra 2003. Flyttetallene har under 300 personer per år med ukjent kommune. Små kommuner har store, støyete endringer: Andøy fikk Sp 72 % i 2021, og Træna og Utsira har få velgere.
