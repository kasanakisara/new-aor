# -*- coding: utf-8 -*-
"""Compute, per country file, the techs needed by its OOB units and equipment variants."""
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

equip2tech = {}
for tid, t in techs.items():
    for e in t["equip"]:
        equip2tech.setdefault(e, set()).add(tid)
sub2tech = {}
for tid, t in techs.items():
    for s in t["subunits"]:
        sub2tech.setdefault(s, set()).add(tid)

# parse OOB files -> equipment names + subunits
oob_equip = {}
oob_sub = {}
for fn in os.listdir(UNITS):
    if not fn.endswith(".txt"):
        continue
    s = strip_comments(read(os.path.join(UNITS, fn)))
    eq = set(re.findall(r"equipment\s*=\s*\{\s*([A-Za-z0-9_]+)\s*=\s*\{", s))
    subs = set(re.findall(r"^\s*([a-z_]+)\s*=\s*\{\s*x\s*=", s, re.M))
    oob_equip[fn] = eq
    oob_sub[fn] = subs

all_eq = collections.Counter()
for v in oob_equip.values():
    all_eq.update(v)
print("distinct equipment in OOBs:", len(all_eq))
mapped = [e for e in all_eq if e in equip2tech]
print("mapped to tech:", len(mapped), "| unmapped:", sorted(e for e in all_eq if e not in equip2tech)[:20])
print("equipment sample:", sorted(all_eq)[:20])

all_sub = collections.Counter()
for v in oob_sub.values():
    all_sub.update(v)
print("subunits in OOBs:", dict(all_sub))

# country -> required
req = {}
for fn in sorted(os.listdir(CTRY)):
    if not fn.endswith(".txt"):
        continue
    s = strip_comments(read(os.path.join(CTRY, fn)))
    oobs = re.findall(r'(?:oob|set_naval_oob|set_oob)\s*=\s*"([^"]+)"', s)
    variants = []
    for m in re.finditer(r"create_equipment_variant\s*=\s*\{", s):
        b = s.index("{", m.start())
        e = find_block(s, b)
        body = s[b + 1:e]
        ty = re.search(r"type\s*=\s*([A-Za-z0-9_]+)", body)
        nm = re.search(r'name\s*=\s*"([^"]*)"', body)
        mods = re.findall(r"=\s*([aorA-Za-z0-9_]+)", body)
        variants.append({"type": ty.group(1) if ty else None, "name": nm.group(1) if nm else "", "body": body})
    need = set()
    missing_oob = []
    for o in oobs:
        f = o + ".txt"
        if f in oob_equip:
            for e in oob_equip[f]:
                need |= equip2tech.get(e, set())
            for sb in oob_sub[f]:
                need |= sub2tech.get(sb, set())
        else:
            missing_oob.append(o)
    req[fn] = {"oobs": oobs, "missing_oob": missing_oob,
               "need": sorted(need),
               "variants": [{"type": v["type"], "name": v["name"]} for v in variants]}
    # variant frame -> tech (frame equipment name -> tech)
    for v in variants:
        for t in equip2tech.get(v["type"] or "", set()):
            req[fn]["need"].append(t)

json.dump(req, open(r"D:\new-aor\tools\coal\oob_req.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)

print("countries with missing oob files:", sum(1 for v in req.values() if v["missing_oob"]))
print("files with variants:", sum(1 for v in req.values() if v["variants"]))
vn = collections.Counter(v["type"] for r in req.values() for v in r["variants"])
print("variant types:", vn.most_common(15))
needs = collections.Counter()
for v in req.values():
    needs.update(v["need"])
print("most needed by OOB/variants:", needs.most_common(12))
