# -*- coding: utf-8 -*-
"""Analyze country files: tag, oob, current techs, air variants; map OOB needs."""
import os, re, json, collections

CTRY = r"D:\new-aor\history\countries"
UNITS = r"D:\new-aor\history\units"
techs = json.load(open(r"D:\new-aor\tools\coal\techs.json", encoding="utf-8"))

def read(p):
    return open(p, "rb").read().decode("utf-8-sig", errors="replace")

def strip_comments(s):
    return re.sub(r"#[^\n]*", "", s)

def find_block(s, start):
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1

# tech -> subunits enabled
tech_sub = {}
for tid, t in techs.items():
    for su in t["subunits"]:
        tech_sub.setdefault(su, set()).add(tid)
print("subunits unlockable:", {k: sorted(v) for k, v in tech_sub.items()})

# OOB analysis
oob_sub = {}
oob_equip = {}
for fn in os.listdir(UNITS):
    if not fn.endswith(".txt"):
        continue
    s = strip_comments(read(os.path.join(UNITS, fn)))
    subs = set(re.findall(r"\b(infantry|marine|mountaineers|assault_team|aor_armored_assault|artillery|anti_tank|anti_air|motorized|mechanized|armored|armored_car|cavalry|bicycle|paratrooper|engineer[s]?|tank_destroyer|artillery_brigade|rocket_artillery|airborne)\b", s))
    oob_sub[fn] = subs

print("OOB files:", len(oob_sub))

# country files
rows = []
for fn in sorted(os.listdir(CTRY)):
    if not fn.endswith(".txt"):
        continue
    s = strip_comments(read(os.path.join(CTRY, fn)))
    tm = re.search(r"^\s*([A-Z][A-Z0-9]{1,2})\s*=\s*\{", s, re.M)
    tag = tm.group(1) if tm else None
    oob = re.search(r'\boob\s*=\s*"([^"]+)"', s)
    tech_ids = []
    for m in re.finditer(r"set_technology\s*=\s*\{", s):
        b = s.index("{", m.start())
        e = find_block(s, b)
        tech_ids += re.findall(r"([A-Za-z0-9_]+)\s*=\s*1\b", s[b + 1:e])
    variants = re.findall(r'create_equipment_variant\s*=\s*\{[^}]*?name\s*=\s*"([^"]*)"', s, re.S)
    rows.append({"file": fn, "tag": tag, "oob": oob.group(1) if oob else None,
                 "techs": tech_ids, "variants": variants})

print("country files:", len(rows), "without tag block:", sum(1 for r in rows if not r["tag"]))
print("without oob:", sum(1 for r in rows if not r["oob"]))
print("files with variants:", sum(1 for r in rows if r["variants"]))
print("variant names sample:", rows[0]["variants"][:3] if rows else None)
print("tags:", len(set(r["tag"] for r in rows if r["tag"])))

# duplicates
dup = collections.Counter(r["tag"] for r in rows if r["tag"])
print("dup tags:", [k for k, v in dup.items() if v > 1])

oobs = set(r["oob"] for r in rows if r["oob"])
print("oob refs without file:", len([o for o in oobs if o + ".txt" not in os.listdir(UNITS)]), sorted(o for o in oobs if o + ".txt" not in os.listdir(UNITS))[:10])

json.dump(rows, open(r"D:\new-aor\tools\coal\countries.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
