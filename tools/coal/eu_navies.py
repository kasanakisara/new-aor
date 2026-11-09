# -*- coding: utf-8 -*-
"""European 1919 navies: downgrade major fleets to 1914-era hulls and create small fleets."""
import os, re, sys, math
import numpy as np
from PIL import Image

ROOT = r"D:\new-aor"
UNITS = os.path.join(ROOT, "history", "units")
CTRY = os.path.join(ROOT, "history", "countries")
STATES = os.path.join(ROOT, "history", "states")

# ---------- map data ----------
col2id = {}
land = set()
sea = set()
for line in open(os.path.join(ROOT, "map", "definition.csv"), "rb").read().decode("utf-8-sig", errors="replace").splitlines():
    p = line.split(";")
    if len(p) < 5:
        continue
    try:
        pid, r, g, b = int(p[0]), int(p[1]), int(p[2]), int(p[3])
    except ValueError:
        continue
    col2id[(r << 16) | (g << 8) | b] = pid
    typ = p[4].lower()
    if typ == "land":
        land.add(pid)
    elif typ == "sea":
        sea.add(pid)

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
    vpm = re.search(r"victory_points\s*=\s*\{([^}]*)\}", s)
    provs = [int(x) for x in re.findall(r"\d+", prov.group(1))] if prov else []
    state_provs[sid] = provs
    state_vp[sid] = {int(a): int(b) for a, b in re.findall(r"(\d+)\s+(\d+)", vpm.group(1))} if vpm else {}
    if own:
        for p in provs:
            if p in land:
                prov_owner[p] = own.group(1)

im = Image.open(os.path.join(ROOT, "map", "provinces.bmp")).convert("RGB")
a = np.array(im, dtype=np.uint32)
key = (a[:, :, 0] << 16) | (a[:, :, 1] << 8) | a[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
lut = np.array([col2id.get(int(k), 0) for k in uniq], dtype=np.int32)
ids = lut[inv].reshape(key.shape).astype(np.int64)
coastal = set()
for x, y in ((ids[:, :-1], ids[:, 1:]), (ids[:-1, :], ids[1:, :])):
    m = (x != y) & (x > 0) & (y > 0)
    lo = np.minimum(x[m], y[m]).astype(np.int64)
    hi = np.maximum(x[m], y[m]).astype(np.int64)
    for l, h in zip(lo, hi):
        if l in land and h in sea:
            coastal.add(int(l))
        if h in land and l in sea:
            coastal.add(int(h))
print("coastal provinces:", len(coastal))


def capital_of(tag):
    for f in sorted(os.listdir(CTRY)):
        if not re.match(r"^" + re.escape(tag) + r"(?![A-Z0-9])", f):
            continue
        s = open(os.path.join(CTRY, f), "rb").read().decode("utf-8-sig", errors="replace")
        m = re.search(r"^\s*capital\s*=\s*(\d+)", s, re.M)
        if m:
            return int(m.group(1)), f
    return None, None


def naval_base(tag):
    cap, _ = capital_of(tag)
    def best(provs):
        provs = [p for p in provs if p in coastal]
        if not provs:
            return None
        vps = state_vp.get(cap, {})
        provs.sort(key=lambda p: (-vps.get(p, 0), p))
        return provs[0]
    if cap:
        b = best(state_provs.get(cap, []))
        if b:
            return b
    owned = [p for p, o in prov_owner.items() if o == tag and p in coastal]
    if owned:
        # use victory points of the owning state for the main port
        def vp_of(p):
            for sid, ps in state_provs.items():
                if p in ps:
                    return state_vp.get(sid, {}).get(p, 0)
            return 0
        owned.sort(key=lambda p: (-vp_of(p), p))
        return owned[0]
    return None


# ---------- fleet composition ----------
FLEETS = {
    "ITA": {"battleship": 6, "heavy_cruiser": 3, "light_cruiser": 4, "destroyer": 12, "submarine": 10},
    "SPR": {"battleship": 3, "light_cruiser": 3, "destroyer": 8, "submarine": 4},
    "HOL": {"light_cruiser": 2, "destroyer": 6, "submarine": 4},
    "SWE": {"battleship": 2, "destroyer": 4, "submarine": 3},
    "NOR": {"battleship": 2, "destroyer": 3, "submarine": 2},
    "POR": {"light_cruiser": 1, "destroyer": 3, "submarine": 1},
    "GRE": {"light_cruiser": 1, "destroyer": 5, "submarine": 1},
    "TUR": {"battleship": 1, "light_cruiser": 1, "destroyer": 3, "submarine": 1},
    "BEL": {"destroyer": 2},
    "ARU": {"battleship": 1, "destroyer": 2},
    "RUS": {"light_cruiser": 1, "destroyer": 3, "submarine": 2},
}

EQUIP = {
    "battleship": ("battleship", "battleship_1"),
    "heavy_cruiser": ("heavy_cruiser", "heavy_cruiser_1"),
    "light_cruiser": ("light_cruiser", "light_cruiser_1"),
    "destroyer": ("destroyer", "destroyer_1"),
    "submarine": ("submarine", "submarine_1"),
}

LABEL = {"battleship": "BB", "heavy_cruiser": "CA", "light_cruiser": "CL", "destroyer": "DD", "submarine": "SS"}

UPGRADE = {
    "battleship_2": "battleship_1", "battleship_3": "battleship_1",
    "battle_cruiser_1": "battleship_1", "battle_cruiser_2": "battleship_1",
    "light_cruiser_2": "light_cruiser_1", "light_cruiser_3": "light_cruiser_1",
    "heavy_cruiser_2": "heavy_cruiser_1",
    "submarine_2": "submarine_1", "submarine_3": "submarine_1",
}


def main():
    apply = "--apply" in sys.argv
    # 1) downgrade major fleets
    for fn in ["AOR_ENG_naval.txt", "AOR_FRA_naval.txt", "AOR_JAP_naval.txt", "AOR_USA_naval.txt"]:
        p = os.path.join(UNITS, fn)
        s = open(p, "rb").read().decode("utf-8-sig")
        for old, new in UPGRADE.items():
            s = re.sub(r"^\s*%s\s*=\s*\{" % old, lambda m: m.group(0).replace(old, new), s, flags=re.M)
        # drop version_name (classes refer to old hulls)
        s = re.sub(r"^\s*version_name\s*=\s*\"[^\"]*\"\s*$\n?", "", s, flags=re.M)
        if apply:
            open(p, "wb").write(b"\xef\xbb\xbf" + s.encode("utf-8"))
        print(fn, "downgraded")

    # 2) new small fleets
    for tag, comp in FLEETS.items():
        base = naval_base(tag)
        cap, cfile = capital_of(tag)
        if base is None:
            print("SKIP", tag, "no coastal base")
            continue
        lines = ["units = {", "\tfleet = {", '\t\tname = "%s Navy"' % tag, "\t\tnaval_base = %d" % base,
                 "\t\ttask_force = {", '\t\t\tname = "%s Navy"' % tag, "\t\t\tlocation = %d" % base]
        idx = {}
        for kind, n in comp.items():
            definition, equip = EQUIP[kind]
            for i in range(1, n + 1):
                lines.append('\t\t\tship = { name = "%s %s %02d" definition = %s equipment = { %s = { amount = 1 owner = %s } } }'
                             % (tag, LABEL[kind], i, definition, equip, tag))
        lines += ["\t\t}", "\t}", "}"]
        out = "\n".join(lines) + "\n"
        name = "AOR_NAV_%s" % tag
        if apply:
            open(os.path.join(UNITS, name + ".txt"), "wb").write(out.encode("utf-8"))
            # update country file
            p = os.path.join(CTRY, cfile)
            s = open(p, "rb").read().decode("utf-8-sig")
            s = re.sub(r"^\s*set_naval_oob\s*=\s*\"?[A-Za-z0-9_]+\"?[^\r\n]*\r?\n?", "", s, flags=re.M)
            anchor = re.search(r"^\s*oob\s*=\s*\"?[A-Za-z0-9_]+\"?[^\r\n]*\r?\n", s, re.M)
            line = 'set_naval_oob = "%s"\n' % name
            if anchor:
                s = s[:anchor.end()] + line + s[anchor.end():]
            else:
                s = line + s
            open(p, "wb").write(b"\xef\xbb\xbf" + s.encode("utf-8"))
        print(tag, "fleet at", base, comp)


if __name__ == "__main__":
    main()
