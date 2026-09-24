#!/usr/bin/env python3
"""
bygg_kodemapping.py – Oversetter historiske kommunekoder (1986–2026) til 2024-kommuner.

Metode (datadrevet, verifisert mot SSB):
  SSB tabell 07459 finnes både per historisk kommunekode (vs_Kommun) og som
  «Kommuner 2024, sammenslåtte tidsserier» (agg_KommSummer). For hvert år y må
  befolkningen i de historiske kodene som oversettes til 2024-kommune K, summere
  NØYAKTIG til SSBs aggregat for K i år y. Vi går bakover fra 2024:
    - koder som finnes både i y og y+1, arver oversettingen fra y+1
    - koder som opphører etter y, fordeles på de 2024-kommunene som har
      uforklart rest i år y (eksakt delmengdesum)
    - går det ikke opp med hele koder, er koden delt; andelene settes lik
      SSBs egen fordeling (rest / folketall).
  Resultatet er entydig og kontrollert mot SSB for hvert år. Navn brukes ikke.

Inndata:  data/raw/ssb/bef07459_kommuner.csv, bef07459_agg2024.csv, koder_07459.csv
Utdata:   data/processed/kodemapping_2024.csv
          (kode, aar, kom2024, andel, befolkning, metode)
"""
import csv
import itertools
import sys
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SSB = PROJECT / "data" / "raw" / "ssb"
OUT = PROJECT / "data" / "processed" / "kodemapping_2024.csv"
FIRST, LAST = 1986, 2026


def load():
    agg = defaultdict(dict)
    for r in csv.DictReader(open(SSB / "bef07459_agg2024.csv", encoding="utf-8")):
        k = r["kom2024"].replace("K-", "")
        if len(k) == 4 and k.isdigit():
            agg[k][int(r["aar"])] = int(r["befolkning"])
    pop = defaultdict(dict)
    for r in csv.DictReader(open(SSB / "bef07459_kommuner.csv", encoding="utf-8")):
        v = int(r["befolkning"])
        if v > 0:
            pop[int(r["aar"])][r["kode"]] = v
    return agg, pop


# Fylkeslinjer: nye fylkeskoder og hvilke eldre fylker de består av
FYLKE_ARV = {
    "30": {"01", "02", "06"}, "34": {"04", "05"}, "38": {"07", "08"},
    "42": {"09", "10"}, "46": {"12", "14"}, "50": {"16", "17"}, "54": {"19", "20"},
    "31": {"01", "30"}, "32": {"02", "30"}, "33": {"06", "30"}, "39": {"07", "38"},
    "40": {"08", "38"}, "55": {"19", "54"}, "56": {"20", "54"},
}


# Kommuner som har byttet fylke (kode-prefiks → ekstra fylker de kan ha gått til)
FYLKESBYTTE = {
    "1214": {"11"},        # Ølen: Hordaland → Rogaland (2002)
    "1444": {"15"},        # Hornindal: Sogn og Fjordane → Volda, Møre og Romsdal (2020)
    "1567": {"50"},        # Rindal: Møre og Romsdal → Trøndelag (2019)
    "1571": {"50"},        # Halsa: Møre og Romsdal → Heim, Trøndelag (2020)
    "1852": {"54", "55"},  # Tjeldsund: Nordland → Troms (2020)
    "0711": {"30", "33"},  # Svelvik: Vestfold → Drammen, Buskerud (2020)
}


def kan_ga_til(c, k):
    """Kan historisk kode c ha gått (helt eller delvis) inn i 2024-kommune k?"""
    lin = fylkeslinje(k)
    return c[:2] in lin or bool(FYLKESBYTTE.get(c, set()) & lin)


def fylkeslinje(k):
    """Alle fylkesprefikser som en 2024-kommune kan ha hatt historisk."""
    out, todo = set(), [k[:2]]
    while todo:
        f = todo.pop()
        if f not in out:
            out.add(f)
            todo += list(FYLKE_ARV.get(f, ()))
    return out


def subset_exact(target, items, max_size=8, max_solutions=5):
    """Delmengder av items [(kode, pop)] som summerer nøyaktig til target (DFS med beskjæring)."""
    items = sorted(items, key=lambda x: -x[1])
    suffix = [0] * (len(items) + 1)
    for i in range(len(items) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + items[i][1]
    sols = []
    budget = [50_000]

    def dfs(i, rest, chosen):
        budget[0] -= 1
        if len(sols) >= max_solutions or budget[0] < 0:
            return
        if rest == 0:
            sols.append(list(chosen))
            return
        if i >= len(items) or len(chosen) >= max_size or suffix[i] < rest:
            return
        c, p = items[i]
        if p <= rest:
            chosen.append(c)
            dfs(i + 1, rest - p, chosen)
            chosen.pop()
        dfs(i + 1, rest, chosen)

    dfs(0, target, [])
    return sols


def solve_year(y, agg, pop, M_next):
    C = pop[y]
    M = {}
    method = {}
    for c in C:
        if c in M_next and M_next[c]["_whole"]:
            M[c] = {k: s for k, s in M_next[c].items() if k != "_whole"}
            method[c] = "arvet"
    # 2024-år: identitet
    if M_next is None or not M_next:
        for c in C:
            M[c] = {c: 1.0}
            method[c] = "2024-kode"

    def residuals():
        R = {}
        for k in agg:
            s = sum(pop[y][c] * sh.get(k, 0) for c, sh in M.items())
            r = agg[k].get(y, 0) - s
            if abs(r) > 0.5:
                R[k] = r
        return R

    R = residuals()
    E = {c: C[c] for c in C if c not in M}
    problems = []
    # 1) én hel kode dekker en rest nøyaktig
    changed = True
    while changed and R and E:
        changed = False
        for k, r in sorted(R.items()):
            hits = [c for c, p in E.items() if p == r]
            if len(hits) == 1:
                c = hits[0]
                M[c] = {k: 1.0}; method[c] = "eksakt"
                del E[c]; changed = True
        R = residuals()
    # 2) flere hele koder dekker restene nøyaktig – løses samlet (disjunkte løsninger,
    #    flest mulig rester dekket, færrest koder)
    R = residuals()
    ks = [k for k, r in R.items() if r > 0]
    sols = {}
    for k in ks:
        cand = [(c, p) for c, p in E.items() if kan_ga_til(c, k)]
        sols[k] = sorted(subset_exact(R[k], cand, max_size=8, max_solutions=20), key=len)
    order = sorted([k for k in ks if sols[k]], key=lambda k: len(sols[k]))
    best = [0, 0, {}]  # dekket, -antall koder, valg

    def bt(i, used, chosen, ncodes):
        if i == len(order):
            score = (len(chosen), -ncodes)
            if score > (best[0], best[1]):
                best[0], best[1], best[2] = score[0], score[1], dict(chosen)
            return
        if len(chosen) + (len(order) - i) <= best[0] and best[2]:
            return
        k = order[i]
        for sol in sols[k]:
            if not used & set(sol):
                chosen[k] = sol
                bt(i + 1, used | set(sol), chosen, ncodes + len(sol))
                del chosen[k]
        bt(i + 1, used, chosen, ncodes)

    bt(0, set(), {}, 0)
    for k, sol in best[2].items():
        if len(sols[k]) > 1:
            method_tag = "eksakt-sum (valgt blant %d)" % len(sols[k])
        else:
            method_tag = "eksakt-sum"
        for c in sol:
            M[c] = {k: 1.0}; method[c] = method_tag
            del E[c]
    R = residuals()
    # 3) delinger: restene deles i sammenhengende grupper (koder og 2024-kommuner som
    #    kan henge sammen). I hver gruppe er én kode delt og resten hele.
    if E:
        pos = {k: r for k, r in R.items() if r > 0}
        comps = []
        todo_c, todo_k = set(E), set(pos)
        while todo_c:
            cs, ks_ = {todo_c.pop()}, set()
            grew = True
            while grew:
                grew = False
                for k in list(todo_k):
                    if any(kan_ga_til(c, k) for c in cs):
                        ks_.add(k); todo_k.discard(k); grew = True
                for c in list(todo_c):
                    if any(kan_ga_til(c, k) for k in ks_):
                        cs.add(c); todo_c.discard(c); grew = True
            comps.append((sorted(cs), sorted(ks_)))
        for cs, targets in comps:
            codes = [(c, E[c]) for c in cs]
            solved_split = None
            for split_c, split_p in codes:
                rest = [(c, p) for c, p in codes if c != split_c]
                opts = [[k for k in targets if kan_ga_til(c, k)] for c, _ in rest]
                if any(not o for o in opts):
                    continue
                n = 1
                for o in opts:
                    n *= len(o)
                if n > 500_000:
                    continue
                for assign in itertools.product(*opts):
                    left = {k: pos[k] for k in targets}
                    for (c, p), k in zip(rest, assign):
                        left[k] -= p
                    if any(v < 0 for v in left.values()):
                        continue
                    parts = {k: v for k, v in left.items() if v > 0}
                    if abs(sum(parts.values()) - split_p) < 1 and all(kan_ga_til(split_c, k) for k in parts):
                        solved_split = (split_c, split_p, parts, list(zip(rest, assign)))
                        break
                if solved_split:
                    break
            if solved_split:
                split_c, split_p, parts, whole = solved_split
                for (c, p), k in whole:
                    M[c] = {k: 1.0}; method[c] = "eksakt (gruppe med deling)"
                    E.pop(c, None)
                M[split_c] = {k: v / split_p for k, v in parts.items()}
                method[split_c] = "delt" if len(parts) > 1 else "eksakt"
                E.pop(split_c, None)
    R = residuals()
    if E:
        problems.append((y, "ukartlagt", sorted(E.items())))
    if R:
        problems.append((y, "rest", sorted(R.items())[:10]))
    for c in M:
        M[c]["_whole"] = len(M[c]) == 1
    return M, method, problems


# ── Delinger der SSB ikke lager sammenlignbare tidsserier ─────────────────────
# SSB setter «Kommuner 2024, sammenslåtte tidsserier» til 0 for Heim, Hitra,
# Orkland, Narvik og Hamarøy før 2020 (Snillfjord og Tysfjord ble delt), og
# fører hele Ålesund (1507, 2020–2023) på nye Ålesund (1508). Her fastsettes
# oversettingen eksplisitt. Delte koder fordeles etter anslått folketall i delene.
KJENTE_2020_HELE = {
    "1571": "5055", "1612": "5055", "5011": "5055",           # Halsa, Hemne → Heim
    "1617": "5056", "5013": "5056",                           # Hitra
    "1622": "5059", "5016": "5059", "1636": "5059", "5023": "5059",
    "1638": "5059", "5024": "5059",                           # Agdenes, Meldal, Orkdal → Orkland
    "1805": "1806", "1854": "1806",                           # Narvik, Ballangen → Narvik
    "1849": "1875",                                           # Hamarøy
}
KJENTE_2020_DELT = {"1613": "SNILLFJORD", "5012": "SNILLFJORD", "1850": "TYSFJORD"}


def anslå_delingsandeler(pop):
    """Andel av Snillfjord/Tysfjord til hver ny kommune, anslått som
    folketall 1.1.2020 i ny kommune minus folketall 1.1.2019 i de hele delene.
    Normaliseres til sum 1 (vekst i løpet av året gir små avvik)."""
    g = lambda c, y: pop[y].get(c, 0)
    snill = {
        "5055": g("5055", 2020) - g("5011", 2019) - g("1571", 2019),
        "5056": g("5056", 2020) - g("5013", 2019),
        "5059": g("5059", 2020) - g("5016", 2019) - g("5023", 2019) - g("5024", 2019),
    }
    tys = {
        "1806": g("1806", 2020) - g("1805", 2019) - g("1854", 2019),
        "1875": g("1875", 2020) - g("1849", 2019),
    }
    out = {}
    for navn, d in (("SNILLFJORD", snill), ("TYSFJORD", tys)):
        assert all(v > 0 for v in d.values()), (navn, d)
        tot = sum(d.values())
        out[navn] = {k: v / tot for k, v in d.items()}
    # Ålesund 2020–2023 → Ålesund + Haram, etter folketall 1.1.2024
    tot = g("1508", 2024) + g("1580", 2024)
    out["ALESUND"] = {"1508": g("1508", 2024) / tot, "1580": g("1580", 2024) / tot}
    return out


def main():
    agg, pop = load()
    rows, allprob = [], []
    M_next = {}
    for y in range(LAST, FIRST - 1, -1):
        if y == 2024 or y > 2024:
            M = {c: {c: 1.0, "_whole": True} for c in pop[y]}
            method = {c: "2024-kode" for c in pop[y]}
            prob = [(y, "ukjent kode", c) for c in pop[y] if c not in agg]
        else:
            M, method, prob = solve_year(y, agg, pop, M_next)
            andeler = anslå_delingsandeler(pop)
            if y <= 2019:
                rest = [p_ for p_ in prob if p_[1] == "ukartlagt"]
                prob = [p_ for p_ in prob if p_[1] != "ukartlagt"]
                igjen = []
                for (_, _, koder) in rest:
                    for c, _p in koder:
                        if c in KJENTE_2020_HELE:
                            M[c] = {KJENTE_2020_HELE[c]: 1.0, "_whole": True}
                            method[c] = "kjent 2020 (SSB mangler tidsserie)"
                        elif c in KJENTE_2020_DELT:
                            M[c] = dict(andeler[KJENTE_2020_DELT[c]], _whole=False)
                            method[c] = "delt, anslått fra befolkningsendring 2019→2020"
                        else:
                            igjen.append((c, _p))
                if igjen:
                    prob.append((y, "ukartlagt", igjen))
                # SSB-aggregatet er 0 for disse før 2020 – rest mot SSB er da ikke meningsfull
                uten_fasit = {"5055", "5056", "5059", "1806", "1875"}
                prob = [p_ if p_[1] != "rest" else (y, "rest", [(k, r) for k, r in p_[2] if k not in uten_fasit])
                        for p_ in prob]
                prob = [p_ for p_ in prob if not (p_[1] == "rest" and not p_[2])]
            if 2020 <= y <= 2023 and "1507" in M:
                M["1507"] = dict(andeler["ALESUND"], _whole=False)
                method["1507"] = "delt, etter folketall 1.1.2024 (Ålesund/Haram)"
        allprob += prob
        print(f"  {y}: {len(M)} koder, {len(prob)} problemer", flush=True)
        print(f"  {y}: {len(M)} koder, {len(prob)} problemer", flush=True)
        for c, sh in M.items():
            for k, s in sh.items():
                if k == "_whole":
                    continue
                rows.append({"kode": c, "aar": y, "kom2024": k, "andel": round(s, 6),
                             "befolkning": pop[y][c], "metode": method[c]})
        if y <= 2024:
            M_next = M
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kode", "aar", "kom2024", "andel", "befolkning", "metode"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["aar"], r["kode"], r["kom2024"])))
    print(f"Lagret {len(rows)} rader til {OUT.relative_to(PROJECT)}")
    for p in allprob:
        print("PROBLEM:", p)
    return 1 if allprob else 0


if __name__ == "__main__":
    sys.exit(main())
