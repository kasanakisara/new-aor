# -*- coding: utf-8 -*-
"""Build coal plan: interpolate vanilla coal onto AOR states, scale for 1919."""
import os, re, json, collections

VAN = r"D:\SteamLibrary\steamapps\common\Hearts of Iron IV\history\states"
AOR = r"D:\new-aor\history\states"
SCALE = 1.3
MIN_BASE = 0.4

d = json.load(open(r"D:\new-aor\tools\coal\data.json", encoding="utf-8"))
van, aor = d["van"], d["aor"]
pcoal = {int(k): v for k, v in d["pcoal"].items()}

def rnd(x):
    # round half up
    return int(x + 0.5)

plan = []
for sid_s, st in sorted(aor.items(), key=lambda kv: int(kv[0])):
    sid = int(sid_s)
    base = sum(pcoal.get(int(p), 0.0) for p in st["provinces"])
    val = rnd(base * SCALE) if base >= MIN_BASE else 0
    old = st["resources"].get("coal", 0)
    if old:
        val = max(val, int(old))
    # owner
    txt = open(os.path.join(AOR, st["file"]), "r", encoding="utf-8-sig", errors="replace").read()
    own = re.search(r"\bowner\s*=\s*([A-Za-z0-9_]+)", txt)
    plan.append({"id": sid, "file": st["file"], "nprov": len(st["provinces"]),
                 "base": round(base, 2), "old": old, "coal": val,
                 "owner": own.group(1) if own else ""})

json.dump(plan, open(r"D:\new-aor\tools\coal\plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

new_total = sum(p["coal"] for p in plan)
print("states with coal:", sum(1 for p in plan if p["coal"]), "of", len(plan))
print("total coal:", new_total, " vanilla:", 1463)
print("max:", max(p["coal"] for p in plan), "dist:", collections.Counter(p["coal"] for p in plan if p["coal"] < 6))
print()
own = collections.defaultdict(int)
for p in plan:
    own[p["owner"]] += p["coal"]
print("top 15 countries by new coal (owner tag):")
for k, v in sorted(own.items(), key=lambda kv: -kv[1])[:15]:
    print(f"  {k:6s} {v}")
print()
print("top 20 states:")
for p in sorted(plan, key=lambda p: -p["coal"])[:20]:
    print(f"  {p['id']:5d} {p['file'][:40]:40s} {p['coal']:4d} (base {p['base']})")
