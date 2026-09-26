#!/usr/bin/env python3
"""
bygg_kodemapping_1945.py – Oversetter kommunekoder 1945–1985 til 2024-kommuner.

Utvider bygg_kodemapping.py (1986–2026) bakover:
  1951–1985: SSB 06913 har befolkning per historisk kode og «Kommuner 2024, sammenslåtte
             tidsserier». Samme datadrevne løser som før (heltallslikhet mot SSB-aggregatet).
             Der SSB ikke har fasit (delte kommuner, «Rest»), brukes endringene fra SSB-rapport
             99/13 (utvidelse_1945/arbeid/P*.json, kontrollert av K*): en kode som opphører,
             fordeles på mottakerne etter folketallet i hvert område.
             Store overføringer (> 10 % av folketallet) fra kommuner som fortsetter, fordeles
             også etter rapporten.
  1945–1950: SSB har ikke befolkning per kode. Koder som finnes i 1951, får 1951-oversettingen;
             koder som opphørte 1945–1950, følger rapportens endringer fram til 1951.

Kodeidentitet: kommunenumre er gjenbrukt, og tabellene bruker ulike suffikser ('u', 'ut').
Grunnkoden (de fire sifrene) er nummeret kommunen hadde på det tidspunktet. En kode et gitt
år er den 06913-koden med samme grunnkode som har befolkning det året.

Utdata: data/processed/kodemapping_1945.csv (kode06913, aar, kom2024, andel, metode)
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import bygg_kodemapping as bk  # noqa: E402

SSB = PROJECT / "data" / "raw" / "ssb"
PROC = PROJECT / "data" / "processed"
ARB = PROJECT / "utvidelse_1945" / "arbeid"
OUT = PROC / "kodemapping_1945.csv"
LOGG = PROJECT / "utvidelse_1945" / "arbeid" / "mapping_logg.json"
TERSKEL_DELVIS = 0.10
TR_1986 = {"0716u": "0716", "0906": "0903", "2004": "2001"}  # 06913-kode -> 07459-kode


def grunnkode(k):
    return re.sub(r"[^0-9]", "", k)[:4]


def les():
    agg = defaultdict(dict)
    for r in csv.DictReader(open(SSB / "bef06913_agg2024.csv", encoding="utf-8")):
        k = r["kom2024"]
        if len(k) == 4 and k.isdigit():
            agg[k][int(r["aar"])] = int(r["befolkning"])
    pop = defaultdict(dict)
    for r in csv.DictReader(open(SSB / "bef06913_kommuner.csv", encoding="utf-8")):
        v = int(r["befolkning"])
        if v > 0:
            pop[int(r["aar"])][r["kode"]] = v
    hend = []
    for f in ("Pa.json", "Pb.json"):
        hend += json.load(open(ARB / f, encoding="utf-8"))["endringer"]
    # rettelser fra kontrollen (K*.json) legges inn av les_rettelser()
    return agg, pop, hend


def les_rettelser(hend):
    """Bruk kontrollørenes feltfeil og manglende rader, hvis kontrollfilene finnes."""
    byid = {h["id"]: h for h in hend}
    n_rett = n_ny = 0
    for f in ("Ka.json", "Kb.json"):
        p = PROJECT / "utvidelse_1945" / "kontroll" / f
        if not p.exists():
            continue
        k = json.load(open(p, encoding="utf-8"))
        for r in k.get("rader", []):
            if r.get("status") == "feil" and r.get("feltfeil") and r["id"] in byid:
                for felt, verdi in r["feltfeil"].items():
                    if felt in byid[r["id"]]:
                        byid[r["id"]][felt] = verdi
                        n_rett += 1
        for i, m in enumerate(k.get("mangler", [])):
            if m.get("fra_kode") and m.get("til_kode") and m.get("dato"):
                hend.append({"id": f"{f[:2]}-M{i:03d}", "kriterium": "K3", "dato": m["dato"],
                             "fra_kode": m["fra_kode"], "til_kode": m["til_kode"],
                             "folkemengde": m.get("folkemengde"), "hele_kommunen": False,
                             "omraade": m.get("beskrivelse", ""), "side": m.get("side")})
                n_ny += 1
    return n_rett, n_ny


def dato_aar(d):
    """Returner (år, er_1_januar). «1964» tolkes som 1.1.1964."""
    d = (d or "").strip().replace("..", ".")
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", d)
    if m:
        return int(m.group(3)), (m.group(1) == "1" and m.group(2) == "1")
    m = re.search(r"(\d{4})", d)
    return (int(m.group(1)), True) if m else (None, False)


ALIAS_06913 = {"0903": "0906", "2001": "2004"}  # 06913 fører Arendal og Hammerfest under senere nummer


def identitet(grunn, aar, pop):
    """06913-kode med gitt grunnkode som har befolkning i året (unik)."""
    kand = [k for k in pop.get(aar, {}) if grunnkode(k) == grunn]
    if not kand and grunn in ALIAS_06913:
        kand = [k for k in pop.get(aar, {}) if grunnkode(k) == ALIAS_06913[grunn]]
    return kand[0] if len(kand) == 1 else (kand if kand else None)


def hendelser_ved_overgang(grunn, y, hend):
    """Endringer fra grunnkode som skjer mellom 1.1.y (eksklusiv) og 1.1.(y+1) (inklusiv)."""
    ut = []
    for h in hend:
        if grunnkode(h.get("fra_kode") or "") != grunn:
            continue
        aar, jan1 = dato_aar(h.get("dato", ""))
        if aar is None:
            continue
        if (aar == y and not jan1) or (aar == y + 1 and jan1):
            ut.append(h)
    return ut


def navn_til_kode(navn, aar, pop, lab):
    """Finn kode i året med samme kommunenavn (uten periode og samisk navn)."""
    if not navn:
        return None
    rens = lambda t: re.sub(r"\s*\(.*?\)", "", t.split(" - ")[0]).strip().lower()
    kand = [k for k in pop.get(aar, {}) if rens(lab.get(k, "")) == rens(navn)]
    return kand[0] if len(kand) == 1 else None


def fordel(deler, y, pop, M_next, egen=None, lab=None):
    """deler: [(til_grunnkode, folketall, til_navn)] -> {kom2024: andel} via oversettingen året etter.
    egen = (kode, folketall år y): legg til en «resten»-del til kodens egen etterfølger når
    grunnkoden fortsatt finnes året etter, og la én del uten folketall få resten."""
    deler = [list(d) for d in deler]
    if egen:
        kode, p_y = egen
        g = grunnkode(kode)
        kjent = sum(max(d[1] or 0, 0) for d in deler if d[1] is not None)
        uten = [d for d in deler if d[1] is None]
        if len(uten) == 1:
            uten[0][1] = max(p_y - kjent, 0)
            kjent += uten[0][1]
        if not any(d[0] == g for d in deler) and isinstance(identitet(g, y + 1, pop), str):
            deler.append([g, max(p_y - kjent, 0), None])
    tot = sum(max(d[1] or 0, 0) for d in deler)
    res = defaultdict(float)
    feil = []
    for til, p, navn in deler:
        w = (max(p or 0, 0) / tot) if tot > 0 else 1 / len(deler)
        if w == 0:
            continue
        ident = identitet(til, y + 1, pop)
        if not isinstance(ident, str) or ident not in M_next:
            ident = navn_til_kode(navn, y + 1, pop, lab or {})
        if not isinstance(ident, str) or ident not in M_next:
            feil.append((til, navn))
            continue
        for k, sv in M_next[ident].items():
            if k != "_whole":
                res[k] += w * sv
    if feil and res:
        sm = sum(res.values())
        res = {k: v / sm for k, v in res.items()} if sm > 0 else {}
    return dict(res), feil, tot


def main():
    agg, pop, hend = les()
    lab = {r["kode"]: r["etikett"] for r in csv.DictReader(open(SSB / "koder_06913.csv", encoding="utf-8"))}
    n_rett, n_ny = les_rettelser(hend)
    # Start: 1986 fra eksisterende kodemapping_2024.csv, oversatt til 06913-koder
    m86 = defaultdict(dict)
    for r in csv.DictReader(open(PROC / "kodemapping_2024.csv", encoding="utf-8")):
        if r["aar"] == "1986":
            m86[r["kode"]][r["kom2024"]] = float(r["andel"])
    M_next = {}
    for k in pop[1986]:
        sh = m86[TR_1986.get(k, k)]
        M_next[k] = dict(sh, _whole=len(sh) == 1)
    rows, logg = [], {"rettelser_fra_kontroll": n_rett, "rader_lagt_til_fra_kontroll": n_ny, "år": {}}

    for y in range(1985, 1950, -1):
        # Koder som fortsetter, arver oversettingen fra året etter – også når den er delt
        for c in M_next:
            M_next[c]["_whole"] = True
        M, method, prob = bk.solve_year(y, agg, pop, M_next)
        uløst = sorted({c for p in prob if p[1] == "ukartlagt" for c, _ in p[2]})
        # Rapporten går foran løseren for ALLE koder som opphører: løserens delmengdesummer mot
        # et ufullstendig SSB-aggregat («Rest») kan gi falske treff.
        opphører = [c for c in pop[y] if c not in pop.get(y + 1, {})]
        uløst = sorted(set(uløst) | {c for c in opphører if hendelser_ved_overgang(grunnkode(c), y, hend)})
        # 1) koder som opphører: fordel etter rapporten
        pdf_brukt, fortsatt_uløst = [], []
        for c in uløst:
            if c in pop.get(y + 1, {}):
                fortsatt_uløst.append((c, "finnes året etter, men ikke kartlagt"))
                continue
            hs = hendelser_ved_overgang(grunnkode(c), y, hend)
            if not hs:
                fortsatt_uløst.append((c, "ingen hendelse i rapporten"))
                continue
            deler = [(grunnkode(h.get("til_kode") or ""), h.get("folkemengde"), h.get("til_navn")) for h in hs]
            res, feil, tot = fordel(deler, y, pop, M_next, egen=(c, pop[y][c]), lab=lab)
            if not res:
                fortsatt_uløst.append((c, f"mottakere ikke funnet: {feil}"))
                continue
            M[c] = dict(res, _whole=len(res) == 1)
            method[c] = "rapport 99/13" + (" (delt)" if len(res) > 1 else "") + \
                        (" – likt fordelt (folketall mangler)" if tot == 0 and len(deler) > 1 else "")
            pdf_brukt.append(c)
        # 2) store delvise overføringer fra kommuner som fortsetter
        delvis = []
        for c in list(M):
            if c not in pop.get(y + 1, {}):
                continue
            hs = [h for h in hendelser_ved_overgang(grunnkode(c), y, hend)
                  if grunnkode(h.get("til_kode") or "") != grunnkode(c) and (h.get("folkemengde") or 0) > 0]
            ut_sum = sum(h["folkemengde"] for h in hs)
            if hs and ut_sum / pop[y][c] > TERSKEL_DELVIS:
                deler = [(grunnkode(h.get("til_kode") or ""), h["folkemengde"], h.get("til_navn")) for h in hs]
                res, feil, _ = fordel(deler, y, pop, M_next, egen=(c, pop[y][c]), lab=lab)
                if res and not feil:
                    M[c] = dict(res, _whole=len(res) == 1)
                    method[c] = "rapport 99/13 (delvis overføring > 10 %)"
                    delvis.append((c, round(ut_sum / pop[y][c], 3)))
        # 3) kontroll mot SSB der SSB har fasit
        rest = []
        for k, a in agg.items():
            fas = a.get(y, 0)
            if fas <= 0:
                continue
            s = sum(pop[y][c] * sh.get(k, 0) for c, sh in M.items() if c in pop[y])
            if abs(s - fas) > max(1, 0.001 * fas):
                rest.append((k, fas, round(s)))
        logg["år"][y] = {"koder": len(pop[y]), "løst_med_rapport": len(pdf_brukt),
                         "delvise_overføringer": delvis, "uløst": fortsatt_uløst,
                         "avvik_mot_ssb": rest[:30], "n_avvik_mot_ssb": len(rest)}
        print(f"  {y}: {len(pop[y])} koder, rapport {len(pdf_brukt)}, delvis {len(delvis)}, "
              f"uløst {len(fortsatt_uløst)}, avvik mot SSB {len(rest)}", flush=True)
        for c, sh in M.items():
            for k, s in sh.items():
                if k != "_whole":
                    rows.append({"kode": c, "aar": y, "kom2024": k, "andel": round(s, 6),
                                 "metode": method.get(c, "arvet")})
        for c in M:
            M[c]["_whole"] = len([k for k in M[c] if k != "_whole"]) == 1
        M_next = M

    # 1945–1950: 1951-oversettingen + endringer 1946–1951 for koder som opphørte
    M51 = M_next
    koder_valg = set()
    for f in list(SSB.glob("st08092_194*.csv")) + list(SSB.glob("kv01180_194*.csv")) + \
            list(SSB.glob("kv01180_1951.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            koder_valg.add(grunnkode(r["Region"]))
    tidlig_uløst = []
    for y in range(1950, 1944, -1):
        for g in sorted(koder_valg):
            ident = identitet(g, 1951, pop)
            if isinstance(ident, str) and ident in M51:
                sh, met = M51[ident], "1951-oversetting"
            else:
                hs = [h for h in hend if grunnkode(h.get("fra_kode") or "") == g
                      and (dato_aar(h.get("dato", ""))[0] or 0) in range(y + 1, 1952)]
                if not hs:
                    if y == 1945:
                        tidlig_uløst.append(g)
                    continue
                res, feil, _ = fordel([(grunnkode(h.get("til_kode") or ""), h.get("folkemengde"), h.get("til_navn"))
                                       for h in hs], 1950, pop, M51, lab=lab)
                if not res:
                    if y == 1945:
                        tidlig_uløst.append((g, feil))
                    continue
                sh, met = res, "rapport 99/13 (1945–1950)"
            for k, s in sh.items():
                if k != "_whole":
                    rows.append({"kode": g, "aar": y, "kom2024": k, "andel": round(s, 6), "metode": met})
    logg["1945_1950_uløst"] = tidlig_uløst
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kode", "aar", "kom2024", "andel", "metode"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["aar"], r["kode"], r["kom2024"])))
    json.dump(logg, open(LOGG, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(f"Lagret {len(rows)} rader. 1945–1950 uløst: {tidlig_uløst[:20]}")


if __name__ == "__main__":
    main()
