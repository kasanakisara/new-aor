# -*- coding: utf-8 -*-
"""Inventory AOR tech tree + current country tech sets."""
import os, re, json, collections

TECH = r"D:\new-aor\common\technologies"
CTRY = r"D:\new-aor\history\countries"

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

techs = {}
for fn in sorted(os.listdir(TECH)):
    if not fn.endswith(".txt"):
        continue
    s = strip_comments(read(os.path.join(TECH, fn)))
    # find "technologies = {" top-level
    for m in re.finditer(r"^(?:[ \t]*technologies[ \t]*=\s*\{)", s, re.M):
        b = s.index("{", m.start())
        e = find_block(s, b)
        body = s[b + 1:e]
        # iterate direct children: id = { ... }
        pos = 0
        for cm in re.finditer(r"^[ \t]*([A-Za-z0-9_]+)\s*=\s*\{", body, re.M):
            if cm.start() < pos:
                continue
            b2 = body.index("{", cm.start())
            e2 = find_block(body, b2)
            inner = body[b2 + 1:e2]
            tid = cm.group(1)
            y = re.search(r"start_year\s*=\s*(-?\d+)", inner)
            eq = re.findall(r"enable_equipments\s*=\s*\{([^}]*)\}", inner)
            su = re.findall(r"enable_subunits\s*=\s*\{([^}]*)\}", inner)
            cats = re.findall(r"categories\s*=\s*\{([^}]*)\}", inner)
            folder = re.search(r"folder\s*=\s*\{\s*name\s*=\s*([A-Za-z0-9_]+)", inner)
            xor = "xor" if re.search(r"XOR\s*=\s*\{", inner) else ""
            leads = re.findall(r"leads_to_tech\s*=\s*([A-Za-z0-9_]+)", inner)
            techs[tid] = {
                "file": fn,
                "year": int(y.group(1)) if y else None,
                "cats": [c.strip() for c in (cats[0].split() if cats else [])],
                "equip": sum([x.split() for x in eq], []),
                "subunits": sum([x.split() for x in su], []),
                "folder": folder.group(1) if folder else "",
                "xor": xor,
                "leads": leads,
                "raw": inner,
            }
            pos = e2

print("techs parsed:", len(techs))
print("by file:", collections.Counter(t["file"] for t in techs.values()))
print("year dist:", sorted(collections.Counter(t["year"] for t in techs.values()).items(), key=lambda kv: (kv[0] is None, kv[0]))[:14])
print("xor techs:", sum(1 for t in techs.values() if t["xor"]))

json.dump({k: {kk: vv for kk, vv in v.items() if kk != "raw"} for k, v in techs.items()},
          open(r"D:\new-aor\tools\coal\techs.json", "w", encoding="utf-8"), ensure_ascii=False)

# current country sets
country_techs = {}
for fn in sorted(os.listdir(CTRY)):
    if not fn.endswith(".txt"):
        continue
    s = strip_comments(read(os.path.join(CTRY, fn)))
    tags = re.findall(r"^\s*([A-Za-z0-9_]+)\s*=\s*[A-Za-z0-9_]+", s[:200])  # crude, ignored
    ids = []
    for m in re.finditer(r"set_technology\s*=\s*\{", s):
        b = s.index("{", m.start())
        e = find_block(s, b)
        inner = s[b + 1:e]
        for tm in re.finditer(r"([A-Za-z0-9_]+)\s*=\s*1\b", inner):
            ids.append(tm.group(1))
    country_techs[fn] = ids

json.dump(country_techs, open(r"D:\new-aor\tools\coal\country_techs.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)

unknown = collections.Counter()
for fn, ids in country_techs.items():
    for i in ids:
        if i not in techs:
            unknown[i] += 1
print("unknown tech ids referenced by countries:", len(unknown))
print(sorted(unknown.items(), key=lambda kv: -kv[1])[:40])

lens = collections.Counter(len(v) for v in country_techs.values())
print("techs per country (sorted):", sorted(lens.items())[:15], "...")
print("files with 0 techs:", sum(1 for v in country_techs.values() if not v))
