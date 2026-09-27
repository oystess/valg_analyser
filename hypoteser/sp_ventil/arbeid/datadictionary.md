# Dataordbok: analysepanelet (`arbeid/panel.csv`)

Bygget av `analyse/sp_ventil/steg1_panel_laas.py` fra `data/processed/`. Én rad per 2024-kommune × valgpar
(stortingsvalg t0 → t1), 7139 rader, 357 kommuner, 20 valgpar (1945–49 til 2021–25).
`panel_kv.csv` er det samme for kommunestyrevalg, og `panel_stabil.csv` for 279 stabile enheter.

| Kolonne | Innhold |
|---|---|
| kom, navn | 2024-kommunenummer (eller stabil enhet) og navn |
| t0, t1, par | Valgår før og etter, og «t0-t1» |
| `<p>0`, `<p>1` | Oppslutning i prosent ved t0 og t1. p ∈ ap, frp, h, krf, sp, sv, v, mdg, nkp, rodt, fl (felleslister, gruppe 90), andre |
| sp90 | Sp + felleslister (gruppe 90). Hele gruppe 90 regnes til Sp. Det overvurderer Sp noe, fordi felleslistene også rommet KrF/V |
| hvk | H + V + KrF (uten felleslister) |
| `d_<p>` | Endring t0 → t1 i prosentpoeng |
| `dl_<p>` | Endring relativt til landet: d_p minus landsendringen (stemmevektet landstall) |
| ped | Pedersen-indeks, ½·Σ\|Δp\| over de 12 gruppene |
| ped90 | Pedersen med Sp og felleslister slått sammen (fjerner kunstig flyktighet når Sp bytter mellom egen liste og felleslister) |
| ped_uten_sp | ½·Σ\|Δp\| over alle partier unntatt Sp og felleslister («utslag hos andre partier») |
| sikker0, sikker1 | Laveste `sikkerhet` blant radene for kommunen i t0 og t1 |
| est | Minst én partirad ved t0 eller t1 er `estimert` (fordelt etter nøkkel) |
| sent, distrikt | SSB sentralitetsklasse 2024. distrikt = klasse (5, 6) |
| ap_rull, bastion | Ap-snitt ved t0 og valget før t0. bastion = ap_rull ≥ 50.0 % |
| ap_fast, bastion_fast, bastion_q75 | Ap-snitt ST 1953–69. Bastion ved ≥ 50.0 % eller øvre kvartil |
| bef0, bef1, dlog_bef | Folketall (nærmeste år ≥ 1951) og 100·ln(bef1/bef0) |
| fylke | To første sifre i 2024-nummeret |
| nasj_d_sp90, nasj_d_sp | Landsendring for Sp + felleslister og Sp alene |
| testbar | t0 ≥ 1953. Par med t0 = 1945 eller 1949 (sikkerhet «lav») er bare bakgrunn |
| lokal_bolge, lokal_bolge_sp | d_sp90 (d_sp) ≥ 10.0 pp |
| gruppe | distrikt_bastion / distrikt_ikke_bastion / sentral (rullerende bastion) |

Landstall per år: `landstall_st.csv` og `landstall_kv.csv`.
