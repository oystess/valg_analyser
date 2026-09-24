# Brief 7K – Uavhengig kontroll av de låste kjøringene

Du kontrollerer et annet agents arbeid. Du har ikke sett hvordan det ble laget.
Utgangspunktet ditt er «ikke godkjent». Godkjenning må begrunnes hypotese for hypotese.

INPUT:
  - Låste spesifikasjoner: /home/user/valg_analyser/turnering/låst.json
  - Panel: /home/user/valg_analyser/turnering/data/panel.csv (sjekk at sha256 = panel_sha256 i låst.json)
  - Resultatfilen som skal kontrolleres: /home/user/valg_analyser/turnering/resultater.json
KRITERIER / PROTOKOLL (slik resultatene skal være regnet):
  - Hver spesifikasjon: statsmodels formula (formel), WLS med vekt = kolonnen i «vekt» (OLS hvis null),
    rader filtrert med pandas query(utvalg) hvis ikke null, klyngerobuste standardfeil på kom2024
    (cov_type="cluster"). Nøkkelledd = koeffisienten med navnet i «nøkkelledd».
  - Robusthetsbatteri: uvektet; uten kommuner der estimert==True; ett og ett fylke utelatt (15);
    én og én periode utelatt (når utvalget har flere perioder); kommunevalg-parallell der «d_sp ~» byttes
    med «kv_d_sp ~» og sp_t0 med kv_sp_t0.
  - Holm-korreksjon over hovedkjøringenes p-verdier (6 stk).
  - Status: robust = forventet fortegn i hoved + Holm-p < 0,05 + forventet fortegn i uvektet,
    uten_estimert, alle uten_fylke og alle uten_periode (kjøringer der nøkkelleddet ikke kan identifiseres,
    teller ikke); ustabilt = forventet fortegn og Holm-p < 0,05 i hoved, men minst ett fortegnsskifte;
    ellers ikke_støttet.
VERKTØY: Python (pandas, statsmodels er installert). IKKE les eller importer noe fra
  /home/user/valg_analyser/analyse/ – skriv din egen kode fra protokollen over.

GJØR DETTE:
1. For HVER hypotese: regn hovedkjøringen, uvektet, uten_estimert, alle uten_fylke og uten_periode, og
   kommunevalg selv. Sammenlign b, se, p med resultater.json (toleranse 1e-6 relativt for b).
2. Regn Holm-justerte p og status selv, og sammenlign.
3. Negativ test: se etter spesifikasjoner der nøkkelleddet ikke måler påstanden i låst.json, og etter
   estimater som er drevet av én enkelt periode eller et lite antall kommuner (oppgi, ikke endre status).
4. Motstrid mellom resultatfil, låst.json og din egen utregning.
SVAR (skriv til /home/user/valg_analyser/turnering/kontroll/7K_kjoring.json):
  {"hypoteser": [{"id": "", "status_din": "", "status_fil": "", "b_din": 0, "b_fil": 0, "avvik": [],
                  "merknader": ""}],
   "holm": {"ok": true, "avvik": []}, "panel_hash_ok": true, "motstrid": [],
   "ikke_sjekket": ["…" eller "alt sjekket"], "konklusjon": {"status": "godkjent|ikke godkjent", "avvik": 0}}
RETUR (høyst 5 linjer): filsti, konklusjon, antall avvik, antall punkter ikke sjekket.
