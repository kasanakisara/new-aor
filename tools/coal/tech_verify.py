# -*- coding: utf-8 -*-
"""Verify the generated country tech blocks."""
import os, re, json, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tech_gen_common as G

CTRY = r"D:\new-aor\history\countries"
techs = G.techs
errs = []
stats = collections.Counter()

def read(p):
    return open(p, "rb").read().decode("utf-8-sig")

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

for fn in sorted(os.listdir(CTRY)):
    if not fn.endswith(".txt"):
        continue
    tag = G.tag_of(fn)
    if tag == "GER":
        continue
    s = read(os.path.join(CTRY, fn))
    if s.count("{") != s.count("}"):
        errs.append((fn, "unbalanced"))
    blocks = list(re.finditer(r"set_technology\s*=\s*\{", s))
    if len(blocks) != 1:
        errs.append((fn, "set_technology blocks: %d" % len(blocks)))
    got = set()
    for m in blocks:
        b = s.index("{", m.start())
        e = find_block(s, b)
        got |= set(re.findall(r"([A-Za-z0-9_]+)\s*=\s*1\b", s[b + 1:e]))
    bad = [t for t in got if t not in techs]
    if bad:
        errs.append((fn, "unknown techs", bad))
    info = G.build(tag, fn)
    missing = [t for t in info["techs"] if t not in got]
    extra = [t for t in got if t not in info["techs"]]
    if missing:
        errs.append((fn, "missing", missing[:5]))
    if extra:
        errs.append((fn, "extra", extra[:5]))
    # air variants consistent
    for m in re.finditer(r"create_equipment_variant\s*=\s*\{", s):
        b = s.index("{", m.start())
        e = find_block(s, b)
        body = s[b + 1:e]
        ty = re.search(r"\btype\s*=\s*([A-Za-z0-9_]+)", body)
        if ty and ty.group(1) in G.AIR_FRAME_EQUIP and ty.group(1) not in info["frames"]:
            errs.append((fn, "air variant without frame tech", ty.group(1)))
    stats[info["profile"]] += 1
    stats["techs_" + str(len(info["techs"]) // 20 * 20)] += 1

print("profiles:", {k: v for k, v in stats.items() if k.startswith("P")})
print("errors:", len(errs))
for e in errs[:15]:
    print("  ", e)
