#!/usr/bin/env python3
"""
turnering/verktoy.py – Orkestratorens verktøy for hypoteseturneringen.

  python turnering/verktoy.py samle            hyp/G*.json -> hyp/samlet.json (blindet, H01…)
  python turnering/verktoy.py par <runde>      lag parvise dueller (sveitsisk) -> dueller/runde<r>_par.json
  python turnering/verktoy.py elo              les dommer-svar, oppdater Elo -> dueller.csv, elo.csv

Blinding: generator-id fjernes; nøkkelen (anonym id -> opprinnelig id) ligger i
hyp/nokkel.json, som aldri gis til kritiker, dommer eller forbedrer.
Hvert par dømmes to ganger med byttet rekkefølge (A/B og B/A). Uenige dommer = uavgjort.
Elo: start 1000, K = 32.
"""
import csv
import json
import random
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parent
HYP = ROT / "hyp"
DUELL = ROT / "dueller"
SEED = 20260924
FELT_TIL_DOMMER = ["id", "påstand", "mekanisme", "operasjonalisering", "testspesifikasjon",
                   "falsifisering", "eksplorativ_evidens"]


def samle():
    alle = []
    for f in sorted(HYP.glob("G*.json")):
        alle += json.load(open(f, encoding="utf-8"))
    rnd = random.Random(SEED)
    rnd.shuffle(alle)
    nøkkel, ut = {}, []
    for i, h in enumerate(alle, 1):
        ny = f"H{i:02d}"
        nøkkel[ny] = h["id"]
        h2 = {k: h[k] for k in FELT_TIL_DOMMER + ["forhold_til_frø"] if k in h}
        h2["id"] = ny
        ut.append(h2)
    json.dump(ut, open(HYP / "samlet.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(nøkkel, open(HYP / "nokkel.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(ut)} hypoteser samlet og blindet -> hyp/samlet.json")


def les_elo(ids):
    elo = {i: 1000.0 for i in ids}
    f = ROT / "elo.csv"
    if f.exists():
        for r in csv.DictReader(open(f, encoding="utf-8")):
            if r["id"] in elo:
                elo[r["id"]] = float(r["elo"])
    return elo


def tidligere_par():
    sett = set()
    f = ROT / "dueller.csv"
    if f.exists():
        for r in csv.DictReader(open(f, encoding="utf-8")):
            sett.add(frozenset((r["a"], r["b"])))
    return sett


def par(runde, ids_fil="turnering_ids.json"):
    ids = json.load(open(ROT / ids_fil, encoding="utf-8"))
    elo = les_elo(ids)
    brukt = tidligere_par()
    rnd = random.Random(SEED + int(runde))
    rekke = sorted(ids, key=lambda i: (-elo[i], rnd.random()))
    ledig, parliste = list(rekke), []
    while len(ledig) > 1:
        a = ledig.pop(0)
        for j, b in enumerate(ledig):
            if frozenset((a, b)) not in brukt:
                parliste.append((a, b))
                ledig.pop(j)
                break
    # hvert par i begge rekkefølger, stokket
    oppgaver = []
    for n, (a, b) in enumerate(parliste):
        oppgaver.append({"oppgave": f"R{runde}-{n:02d}a", "første": a, "andre": b})
        oppgaver.append({"oppgave": f"R{runde}-{n:02d}b", "første": b, "andre": a})
    rnd.shuffle(oppgaver)
    DUELL.mkdir(exist_ok=True)
    json.dump(oppgaver, open(DUELL / f"runde{runde}_par.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"Runde {runde}: {len(parliste)} par, {len(oppgaver)} dommeroppgaver"
          + (f", {ledig[0]} står over" if ledig else ""))


def elo_oppdater(runde):
    oppg = {o["oppgave"]: o for o in json.load(open(DUELL / f"runde{runde}_par.json", encoding="utf-8"))}
    svar = {s["oppgave"]: s for s in json.load(open(DUELL / f"runde{runde}_svar.json", encoding="utf-8"))}
    mangler = set(oppg) - set(svar)
    if mangler:
        raise SystemExit(f"Mangler dom for {sorted(mangler)}")
    ids = json.load(open(ROT / "turnering_ids.json", encoding="utf-8"))
    elo = les_elo(ids)
    grupper = {}
    for k, o in oppg.items():
        grupper.setdefault(k[:-1], []).append((o, svar[k]["vinner"]))
    nye = []
    for g, lst in sorted(grupper.items()):
        vinnere = {v for _, v in lst}
        a, b = sorted({lst[0][0]["første"], lst[0][0]["andre"]})
        if len(vinnere) == 1 and vinnere <= {a, b}:
            v = vinnere.pop()
            s_a = 1.0 if v == a else 0.0
            utfall = v
        else:
            s_a, utfall = 0.5, "uavgjort"
        ea = 1 / (1 + 10 ** ((elo[b] - elo[a]) / 400))
        elo[a] += 32 * (s_a - ea)
        elo[b] += 32 * ((1 - s_a) - (1 - ea))
        nye.append({"runde": runde, "par": g, "a": a, "b": b, "utfall": utfall,
                    "dom_1": lst[0][1], "dom_2": lst[1][1]})
    f = ROT / "dueller.csv"
    ny_fil = not f.exists()
    with open(f, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["runde", "par", "a", "b", "utfall", "dom_1", "dom_2"])
        if ny_fil:
            w.writeheader()
        w.writerows(nye)
    with open(ROT / "elo.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "elo"])
        for i, e in sorted(elo.items(), key=lambda x: -x[1]):
            w.writerow([i, round(e, 1)])
    uav = sum(1 for n in nye if n["utfall"] == "uavgjort")
    print(f"Runde {runde}: {len(nye)} dueller, {uav} uavgjort (uenige dommer). Topp 8:")
    for i, e in sorted(elo.items(), key=lambda x: -x[1])[:8]:
        print(f"  {i} {e:.0f}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "samle":
        samle()
    elif cmd == "par":
        par(sys.argv[2])
    elif cmd == "elo":
        elo_oppdater(sys.argv[2])
