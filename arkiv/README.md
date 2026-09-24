# Arkiv

Gamle analyseskript og mellomresultater (til og med september 2026). Filene er ikke i bruk. De bygget på det gamle datasettet, som hadde feil (se `qa/QA_RAPPORT.md`): dobbelttelling av ST 1989, kommuner koblet på navn, en reformtabell med feil, og prosent regnet av 9 partier.

- `scripts/analyse*.py`, `scripts/matrise.py`: Analysene bak dagens `index.html` (Senteropprøret, 2017, 2021, matrise og panel). Figurene i `data/processed/*.html` er laget av disse og **er ikke oppdatert** med det nye datasettet.
- `scripts/grenser.py`, `scripts/les_grenser_pdf.py`: Haiku-uttrekk av grenseendringer, erstattet av `scripts/bygg_kodemapping.py`.
- `data/panel_resultater.csv`: Resultater fra den gamle panelanalysen.
- `data/kommunereform_mapping.csv`, `data/grenser_mapping.csv`: Gamle koblingstabeller (med kjente feil, se QA-rapporten F3–F4).

Nye analyser ligger i `analyse/` og `turnering/`.
