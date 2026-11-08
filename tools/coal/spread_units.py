# -*- coding: utf-8 -*-
"""Spread starting divisions: capital + border provinces (colour-decoded province map)."""
import os, re, sys, math
import numpy as np
from PIL import Image

ROOT = r"D:\new-aor"
UNITS = os.path.join(ROOT, "history", "units")
CTRY = os.path.join(ROOT, "history", "countries")
STATES = os.path.join(ROOT, "history", "states")

# definition: colour -> id, land set
col2id = {}
land = set()
for line in open(os.path.join(ROOT, "map", "definition.csv"), "rb").read().decode("utf-8-sig", errors="replace").splitlines():
    p = line.split(";")
    if len(p) < 5:
        continue
    try:
        pid, r, g, b = int(p[0]), int(p[1]), int(p[2]), int(p[3])
    except ValueError:
        continue
    col2id[(r << 16) | (g << 8) | b] = pid
    if p[4].lower() == "land":
        land.add(pid)

# states
state_provs, prov_owner, state_vp = {}, {}, {}
for fn in os.listdir(STATES):
    if not fn.endswith(".txt"):
        continue
    s = open(os.path.join(STATES, fn), "rb").read().decode("utf-8-sig", errors="replace")
    m = re.search(r"\bid\s*=\s*(\d+)", s)
    if not m:
        continue
    sid = int(m.group(1))
    own = re.search(r"\bowner\s*=\s*([A-Za-z0-9_]+)", s)
    prov = re.search(r"\bprovinces\s*=\s*\{([^}]*)\}", s)
    provs = [int(x) for x in re.findall(r"\d+", prov.group(1))] if prov else []
    vpm = re.search(r"victory_points\s*=\s*\{([^}]*)\}", s)
    state_vp[sid] = {int(a): int(b) for a, b in re.findall(r"(\d+)\s+(\d+)", vpm.group(1))} if vpm else {}
    state_provs[sid] = provs
    if own:
        for p in provs:
            if p in land:
                prov_owner[p] = own.group(1)

# bitmap -> ids
im = Image.open(os.path.join(ROOT, "map", "provinces.bmp")).convert("RGB")
a = np.array(im, dtype=np.uint32)
key = (a[:, :, 0] << 16) | (a[:, :, 1] << 8) | a[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
lut = np.array([col2id.get(int(k), 0) for k in uniq], dtype=np.int32)
ids = lut[inv].reshape(key.shape).astype(np.int64)

pairs = []
for x, y in ((ids[:, :-1], ids[:, 1:]), (ids[:-1, :], ids[1:, :])):
    mask = (x != y) & (x > 0) & (y > 0)
    lo = np.minimum(x[mask], y[mask])
    hi = np.maximum(x[mask], y[mask])
    pairs.append(np.stack([lo, hi], axis=1))
pairs = np.unique(np.concatenate(pairs), axis=0)
adj = {}
for lo, hi in pairs:
    lo, hi = int(lo), int(hi)
    adj.setdefault(lo, set()).add(hi)
    adj.setdefault(hi, set()).add(lo)
print("adjacency pairs:", len(pairs))


def capital_of(tag):
    for f in sorted(os.listdir(CTRY)):
        if not re.match(r"^" + re.escape(tag) + r"(?![A-Z0-9])", f):
            continue
        s = open(os.path.join(CTRY, f), "rb").read().decode("utf-8-sig", errors="replace")
        m = re.search(r"^\s*capital\s*=\s*(\d+)", s, re.M)
        if m:
            return int(m.group(1))
    return None


def plan(tag, n):
    cap_state = capital_of(tag)
    cap_prov = None
    if cap_state:
        ps = [p for p in state_provs.get(cap_state, []) if p in land]
        if ps:
            vps = state_vp.get(cap_state, {})
            ps.sort(key=lambda p: (-vps.get(p, 0), p))
            cap_prov = ps[0]
    owned = sorted(p for p, o in prov_owner.items() if o == tag)
    home = owned if owned else [p for p in state_provs.get(cap_state, []) if p in land]
    if not home:
        return None
    home_set = set(home)
    border = [p for p in home if any(q not in home_set for q in adj.get(p, ()))]
    if not border:
        border = list(home)
    border.sort()
    if cap_prov is None or cap_prov not in home_set:
        cap_prov = border[0]

    cap_n = max(1, int(math.ceil(n * 0.3)))
    cap_n = min(cap_n, n)
    seq = [cap_prov] * cap_n
    rest = n - cap_n
    for i in range(rest):
        idx = (i * len(border)) // rest
        seq.append(border[idx])
    return seq


def read(p):
    return open(p, "rb").read().decode("utf-8-sig")


def write(p, s):
    raw = open(p, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    open(p, "wb").write((b"\xef\xbb\xbf" if bom else b"") + s.encode("utf-8"))


def main():
    apply = "--apply" in sys.argv
    todo = [(f, f[7:-4]) for f in sorted(os.listdir(UNITS)) if f.startswith("AOR_EU_")]
    todo.append(("BEL_1919.txt", "BEL"))
    for fn, tag in todo:
        path = os.path.join(UNITS, fn)
        s = read(path)
        n = len(re.findall(r"^\s*division\s*=\s*\{", s, re.M))
        locs = plan(tag, n)
        if not locs:
            print("SKIP", tag)
            continue
        it = iter(locs)
        new = re.sub(r"location\s*=\s*\d+", lambda m: "location = %d" % next(it), s)
        if apply:
            write(path, new)
        print(tag, n, "->", locs)
    print("apply:", apply)


if __name__ == "__main__":
    main()
