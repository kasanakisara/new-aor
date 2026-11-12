# -*- coding: utf-8 -*-
"""Parse vanilla + AOR state files, report province/coal mapping."""
import os, re, json, sys, collections

VAN = r"D:\SteamLibrary\steamapps\common\Hearts of Iron IV\history\states"
AOR = r"D:\new-aor\history\states"

COMMENT = re.compile(r"#[^\n]*")

def read(p):
    with open(p, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read()

def strip_comments(s):
    return COMMENT.sub("", s)

STATE_RE = re.compile(r"^\s*state\s*=\s*\{", re.M)

def find_block_end(s, start):
    """start points at the '{' index; return index of matching '}'."""
    depth = 0
    for i in range(start, len(s)):
        c = s[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1

def parse_states(path):
    raw = read(path)
    s = strip_comments(raw)
    out = []
    for m in STATE_RE.finditer(s):
        brace = s.index("{", m.start())
        end = find_block_end(s, brace)
        if end < 0:
            continue
        body = s[brace+1:end]
        idm = re.search(r"\bid\s*=\s*(\d+)", body)
        if not idm:
            continue
        sid = int(idm.group(1))
        provs = []
        pm = re.search(r"\bprovinces\s*=\s*\{([^}]*)\}", body)
        if pm:
            provs = [int(x) for x in re.findall(r"-?\d+", pm.group(1))]
        res = {}
        rm = re.search(r"\bresources\s*=\s*\{([^}]*)\}", body)
        if rm:
            for k, v in re.findall(r"([A-Za-z_]+)\s*=\s*(-?[\d.]+)", rm.group(1)):
                res[k] = float(v)
        # state name (localisation key) + trailing comment on name line
        nm = re.search(r'\bname\s*=\s*"([^"]+)"', body)
        nameline = ""
        for line in raw.splitlines():
            if 'name="' in line or 'name = "' in line.replace(" = ", " = "):
                if "state=" not in line:
                    nameline = line
                    break
        out.append({"id": sid, "file": os.path.basename(path), "provinces": provs, "resources": res})
    return out

def load_dir(d):
    states = {}
    dupes = []
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith(".txt"):
            continue
        for st in parse_states(os.path.join(d, fn)):
            if st["id"] in states:
                dupes.append((st["id"], states[st["id"]]["file"], fn))
            states[st["id"]] = st
    return states, dupes

van, vdup = load_dir(VAN)
aor, adup = load_dir(AOR)

print("vanilla states:", len(van), "dupes:", len(vdup))
print("aor states:", len(aor), "dupes:", len(adup))
if vdup: print("  van dupes sample:", vdup[:5])
if adup: print("  aor dupes sample:", adup[:5])

vprovs = collections.Counter()
for st in van.values():
    vprovs.update(st["provinces"])
aprovs = collections.Counter()
for st in aor.values():
    aprovs.update(st["provinces"])

print("vanilla provinces total:", len(vprovs), "dup-provinces-in-multiple-states:",
      sum(1 for c in vprovs.values() if c > 1))
print("aor provinces total:", len(aprovs), "dup:", sum(1 for c in aprovs.values() if c > 1))

vset, aset = set(vprovs), set(aprovs)
print("aor provs not in vanilla:", len(aset - vset), sorted(list(aset - vset))[:20])
print("vanilla provs not in aor:", len(vset - aset), sorted(list(vset - aset))[:20])

# coal totals
vcoal = sum(st["resources"].get("coal", 0) for st in van.values())
acoal = sum(st["resources"].get("coal", 0) for st in aor.values())
print("vanilla coal total:", vcoal, "states with coal:", sum(1 for st in van.values() if st["resources"].get("coal")))
print("aor coal total:", acoal, "states with coal:", sum(1 for st in aor.values() if st["resources"].get("coal")))
vc = [st["resources"]["coal"] for st in van.values() if st["resources"].get("coal")]
print("vanilla coal per-state min/max/mean:", min(vc), max(vc), round(sum(vc)/len(vc), 2))

# per-province coal from vanilla
pcoal = {}
for st in van.values():
    n = len(st["provinces"])
    c = st["resources"].get("coal", 0)
    if n and c:
        for p in st["provinces"]:
            pcoal[p] = pcoal.get(p, 0) + c / n

json.dump({"van": {k: {"provinces": v["provinces"], "resources": v["resources"], "file": v["file"]} for k, v in van.items()},
           "aor": {k: {"provinces": v["provinces"], "resources": v["resources"], "file": v["file"]} for k, v in aor.items()},
           "pcoal": pcoal, "vprovs": vprovs, "aprovs": aprovs},
          open(r"D:\new-aor\tools\coal\data.json", "w", encoding="utf-8"), ensure_ascii=False)

# how many aor states are exact copies of vanilla province sets
vexact = {tuple(sorted(st["provinces"])): st for st in van.values() if st["provinces"]}
match = sum(1 for st in aor.values() if tuple(sorted(st["provinces"])) in vexact)
print("aor states with exact vanilla province-set match:", match, "/", len(aor))
same_id = sum(1 for st in aor.values() if st["id"] in van and sorted(van[st["id"]]["provinces"]) == sorted(st["provinces"]))
print("aor states with same id AND same provinces:", same_id)
