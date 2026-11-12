# -*- coding: utf-8 -*-
"""Summarize European country OOB references and their OOB file contents."""
import os, re, json, collections

CTRY = r"D:\new-aor\history\countries"
UNITS = r"D:\new-aor\history\units"

EURO = {"ENG", "FRA", "GER", "ITA", "AUS", "HUN", "CZE", "POL", "ROM", "BUL", "GRE",
        "SER", "YUG", "ALB", "BEL", "HOL", "LUX", "SWI", "SWE", "NOR", "DEN", "FIN",
        "POR", "SPR", "IRE", "EST", "LAT", "LIT", "UKR", "BLR", "RUS", "ARU", "DON",
        "KUB", "SBC", "ARR", "URS", "TUR", "GEO", "ARM", "AZR", "BAV", "SAX", "HAN",
        "SHL", "MEK", "RHI", "PRE", "WUR", "NAU", "HAM", "BRI", "COR", "CAT", "OCC",
        "SLO", "CRO", "BOS", "MNT", "MAC", "KOS", "DAL", "HRZ", "SIL", "NSH", "DNZ",
        "FIC", "RPS", "PSR", "SRK", "SCR", "NAA", "GLC", "GDL", "ALT", "ABK", "KAR",
        "BSK", "TAT", "CHU", "UDM", "MEL", "KOM", "KAL", "NOA", "CIN", "DAG", "KBK",
        "BYA", "YAK", "TAY", "NEN", "YAM", "CSU", "CAU", "VGE", "GNR", "OIC", "SFM",
        "SPE", "WUG", "XCD", "TRZ", "RFR", "IDE", "BAG", "GLC"}

def read(p):
    return open(p, "rb").read().decode("utf-8-sig", errors="replace")

def oob_summary(fn):
    s = read(os.path.join(UNITS, fn))
    return {
        "templates": len(re.findall(r"^division_template\s*=", s, re.M)),
        "divisions": len(re.findall(r"^\s*division\s*=\s*\{", s, re.M)),
        "ships": len(re.findall(r"^\s*ship\s*=\s*\{", s, re.M)),
        "air": len(re.findall(r"air_wing", s)),
        "equip": sorted(set(re.findall(r"^\s*([a-z_0-9]+_equipment_?[0-9]*)\s*=\s*\{", s, re.M)))[:4],
        "size": len(s),
    }

rows = []
for fn in sorted(os.listdir(CTRY)):
    if not fn.endswith(".txt"):
        continue
    tag = re.match(r"([A-Za-z0-9]{2,3})", fn).group(1).upper()
    if tag not in EURO:
        continue
    s = read(os.path.join(CTRY, fn))
    refs = {}
    for key in ("oob", "set_oob", "load_oob", "land_oob"):
        m = re.findall(key + r'\s*=\s*"?([A-Za-z0-9_]+)"?', s)
        if m:
            refs[key] = m
    active = refs.get("oob", [])
    info = []
    for o in active:
        f = o + ".txt"
        if os.path.exists(os.path.join(UNITS, f)):
            info.append((o, oob_summary(f)))
        else:
            info.append((o, "MISSING"))
    rows.append({"tag": tag, "file": fn, "refs": refs, "oob": info})

for r in rows:
    print(f"{r['tag']:4s} keys={list(r['refs'].keys())!s:40s}", end=" ")
    if r["oob"]:
        for name, summ in r["oob"]:
            if summ == "MISSING":
                print(f"{name}:MISSING", end=" ")
            else:
                print(f"{name}: div={summ['divisions']} tpl={summ['templates']} ships={summ['ships']}", end=" ")
    print()

print()
print("=== files 1936-derived used by europe ===")
for r in rows:
    for name, summ in r["oob"]:
        if summ != "MISSING" and "1936" in name:
            print(r["tag"], name, summ["divisions"], "divs")
json.dump(rows, open(r"D:\new-aor\tools\coal\eu_oob.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
