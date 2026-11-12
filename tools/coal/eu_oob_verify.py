# -*- coding: utf-8 -*-
"""Verify European starting armies."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eu_oob as E

CTRY = E.CTRY
UNITS = E.UNITS

def read(p):
    return open(p, "rb").read().decode("utf-8-sig")

def find_block(s, start):
    d = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            d += 1
        elif s[i] == "}":
            d -= 1
            if d == 0:
                return i
    return -1

bad = []
rows = []
seen = set()
for fn in sorted(os.listdir(CTRY)):
    if not fn.endswith(".txt"):
        continue
    tag = re.match(r"([A-Za-z0-9]{2,3})", fn).group(1).upper()
    if tag not in E.KEEP and tag not in E.TARGET:
        continue
    s = read(os.path.join(CTRY, fn))
    active = re.findall(r'^\s*oob\s*=\s*"?([A-Za-z0-9_]+)"?', s, re.M)
    broken = re.findall(r'^\s*(?:set_oob|load_oob|land_oob)\s*=', s, re.M)
    if broken:
        bad.append((tag, "broken oob key left", fn))
    if len(active) != 1:
        bad.append((tag, "oob lines=%d" % len(active), fn))
        continue
    name = active[0]
    p = os.path.join(UNITS, name + ".txt")
    if not os.path.exists(p):
        bad.append((tag, "missing file " + name, fn))
        continue
    o = read(p)
    if o.count("{") != o.count("}"):
        bad.append((tag, "unbalanced " + name, fn))
    divs = len(re.findall(r"^\s*division\s*=\s*\{", o, re.M))
    tpls = re.findall(r'^\s*name\s*=\s*"([^"]+)"', o, re.M)[:10]
    used = set(re.findall(r'division_template\s*=\s*"([^"]+)"', o))
    defined = set()
    for m in re.finditer(r"^division_template\s*=\s*\{", o, re.M):
        b = o.index("{", m.start()); e = find_block(o, b)
        nm = re.search(r'name\s*=\s*"([^"]+)"', o[b:e])
        if nm:
            defined.add(nm.group(1))
    if used - defined:
        bad.append((tag, "template not defined %s" % (used - defined), name))
    target = E.TARGET.get(tag)
    rows.append((tag, name, divs, target))

print("%-5s %-22s %6s %6s" % ("tag", "oob", "divs", "target"))
for r in rows:
    print("%-5s %-22s %6s %6s" % r)
print()
print("errors:", len(bad))
for b in bad:
    print("  ", b)
