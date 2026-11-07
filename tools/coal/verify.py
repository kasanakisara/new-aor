# -*- coding: utf-8 -*-
"""Verify the applied coal edits: syntax sanity + values + other fields untouched."""
import os, re, json, collections

AOR = r"D:\new-aor\history\states"
BK = r"D:\new-aor\tools\coal\backup"
plan = {p["id"]: p for p in json.load(open(r"D:\new-aor\tools\coal\plan.json", encoding="utf-8"))}

def read(p):
    return open(p, "rb").read().decode("utf-8-sig")

def braces_ok(t):
    return t.count("{") == t.count("}")

errors = []
tot = collections.Counter()
coal_total = 0
changed = 0
for sid, p in plan.items():
    path = os.path.join(AOR, p["file"])
    t = read(path)
    if not braces_ok(t):
        errors.append(("braces", p["file"]))
    # exactly one state block
    if len(re.findall(r"^\s*state\s*=\s*\{", t, re.M)) != 1:
        errors.append(("state-blocks", p["file"]))
    # coal inside resources block
    rm = re.search(r"^\s*resources\s*=\s*\{", t, re.M)
    val = None
    if rm:
        brace = t.index("{", rm.start())
        depth = 0
        end = None
        for i in range(brace, len(t)):
            if t[i] == "{": depth += 1
            elif t[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i; break
        inner = t[brace+1:end]
        cm = re.search(r"\bcoal\s*=\s*(-?[0-9.]+)", inner)
        val = float(cm.group(1)) if cm else None
    if val is None:
        val = 0
    if int(val) != p["coal"]:
        errors.append(("coal-mismatch", p["file"], val, p["coal"]))
    coal_total += val
    tot[p["coal"] > 0] += 1
    # compare with backup for untouched content
    bp = os.path.join(BK, p["file"])
    if os.path.exists(bp):
        changed += 1
        old = read(bp)
        # remove coal lines and resources blocks differences: normalize by stripping whitespace
        def norm(s):
            s = re.sub(r"\bcoal\s*=\s*-?[0-9.]+", "", s)
            s = re.sub(r"\bresources\s*=\s*\{\s*\}", "", s)
            return re.sub(r"\s+", "", s)
        if norm(old) != norm(t):
            errors.append(("other-content-changed", p["file"]))

print("errors:", len(errors), errors[:10])
print("states with coal:", tot[True], "without:", tot[False])
print("coal total:", coal_total)
print("files edited:", changed)
# untouched files identical?
print("backup files:", len(os.listdir(BK)) if os.path.isdir(BK) else "(none)")
