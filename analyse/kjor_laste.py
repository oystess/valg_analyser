#!/usr/bin/env python3
"""
analyse/kjor_laste.py – Kjører låste spesifikasjoner (turnering/låst.json) med robusthetsbatteri.

For hver spesifikasjon:
  hoved          som låst (normalt vektet med stemmer i t0)
  uvektet        samme uten vekt
  uten_estimert  uten kommuner med estimert fordeling
  uten_fylke_X   15 kjøringer, ett fylke utelatt om gangen
  uten_periode_X ett valgperiode utelatt om gangen (bare når utvalget har flere perioder)
  per_periode    estimat i hver periode for seg (beskrivende)
  kommunevalg    parallell med kv_d_sp / kv_sp_t0 (når formelen starter med «d_sp ~»)

Status:
  robust    = Holm-justert p < 0,05 i hoved, og forventet fortegn i hoved, uvektet,
              uten_estimert, alle uten_fylke og alle uten_periode
  ustabilt  = forventet fortegn og Holm p < 0,05 i hoved, men minst én robusthetskjøring snur fortegn
  ikke_støttet = ellers
Ingen skjønn: spesifikasjonene kjøres nøyaktig som låst.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from modeller import kjør, last_panel, PANEL  # noqa: E402

ROT = Path(__file__).resolve().parent.parent
LÅST = ROT / "turnering" / "låst.json"
UT = ROT / "turnering" / "resultater.json"


def med_utvalg(spes, ekstra):
    s = dict(spes)
    s["utvalg"] = f"({spes['utvalg']}) and ({ekstra})" if spes.get("utvalg") else ekstra
    return s


def holm(pverdier):
    idx = sorted(range(len(pverdier)), key=lambda i: pverdier[i])
    m, justert, maks = len(pverdier), [0.0] * len(pverdier), 0.0
    for rank, i in enumerate(idx):
        maks = max(maks, min(1.0, (m - rank) * pverdier[i]))
        justert[i] = maks
    return justert


def batteri(spes, df):
    res = {"hoved": kjør(spes, df)}
    s = dict(spes); s["vekt"] = None
    res["uvektet"] = kjør(s, df)
    res["uten_estimert"] = kjør(med_utvalg(spes, "estimert == False"), df)
    for f in sorted(df["fylke"].unique()):
        try:
            res[f"uten_fylke_{f}"] = kjør(med_utvalg(spes, f"fylke != '{f}'"), df)
        except Exception as e:  # noqa: BLE001
            res[f"uten_fylke_{f}"] = {"feil": str(e)}
    d = df.query(spes["utvalg"]) if spes.get("utvalg") else df
    perioder = sorted(d["periode"].unique())
    if len(perioder) > 1:
        for p in perioder:
            try:
                res[f"uten_periode_{p}"] = kjør(med_utvalg(spes, f"periode != '{p}'"), df)
            except Exception as e:  # noqa: BLE001
                res[f"uten_periode_{p}"] = {"feil": str(e)}
            try:
                res[f"per_periode_{p}"] = kjør(med_utvalg(spes, f"periode == '{p}'"), df)
            except Exception as e:  # noqa: BLE001
                res[f"per_periode_{p}"] = {"feil": str(e)}
    if spes["formel"].strip().startswith("d_sp ~"):
        kv = dict(spes)
        f = re.sub(r"^\s*d_sp\s*~", "kv_d_sp ~", spes["formel"])
        kv["formel"] = re.sub(r"\bsp_t0\b", "kv_sp_t0", f)
        try:
            res["kommunevalg"] = kjør(kv, df)
        except Exception as e:  # noqa: BLE001
            res["kommunevalg"] = {"feil": str(e)}
    return res


def main():
    låst = json.load(open(LÅST, encoding="utf-8"))
    df = last_panel()
    panel_hash = hashlib.sha256(PANEL.read_bytes()).hexdigest()
    if låst.get("panel_sha256") and låst["panel_sha256"] != panel_hash:
        raise SystemExit("Panelet er endret etter låsing – avbryter.")
    alle = []
    for h in låst["hypoteser"]:
        alle.append({"id": h["id"], "påstand": h["påstand"], "spes": h["testspesifikasjon"],
                     "res": batteri(h["testspesifikasjon"], df)})
    pj = holm([a["res"]["hoved"]["p"] for a in alle])
    for a, p in zip(alle, pj):
        a["p_holm"] = p
        forv = a["res"]["hoved"]["fortegn_som_forventet"]
        sjekk = [k for k in a["res"] if k.startswith(("uvektet", "uten_"))]
        # En kjøring der nøkkelleddet ikke kan identifiseres (f.eks. periodeledd når perioden er
        # utelatt), er «ikke anvendelig» og teller ikke som fortegnsskifte. Andre feil teller.
        ikke_anv = [k for k in sjekk if "feil" in a["res"][k] and "Nøkkelledd" in a["res"][k]["feil"]]
        snur = [k for k in sjekk if k not in ikke_anv and
                ("feil" in a["res"][k] or not a["res"][k]["fortegn_som_forventet"])]
        a["ikke_anvendelig"] = ikke_anv
        a["snur_fortegn_i"] = snur
        if forv and p < 0.05 and not snur:
            a["status"] = "robust"
        elif forv and p < 0.05:
            a["status"] = "ustabilt"
        else:
            a["status"] = "ikke_støttet"
    json.dump({"panel_sha256": panel_hash, "resultater": alle}, open(UT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    rad = []
    for a in alle:
        h = a["res"]["hoved"]
        rad.append({"id": a["id"], "b": round(h["b"], 3), "ki": f"[{h['ki_lav']:.3f}, {h['ki_høy']:.3f}]",
                    "p_holm": round(a["p_holm"], 4), "n": h["n"], "status": a["status"],
                    "snur": len(a["snur_fortegn_i"])})
    print(pd.DataFrame(rad).to_string(index=False))


if __name__ == "__main__":
    main()
