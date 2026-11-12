# -*- coding: utf-8 -*-
"""Fix unit locations of generated European OOBs: capital state -> its main province."""
import re, os, sys, json

CTRY = r"D:\new-aor\history\countries"
UNITS = r"D:\new-aor\history\units"

# map: land/sea
land = set()
for line in open(r"D:\new-aor\map\definition.csv", "rb").read().decode("utf-8-sig", errors="replace").splitlines():
    p = line.split(";")
    if len(p) < 5:
        continue
    try:
        pid = int(p[0])
    except ValueError:
        continue
    if p[4].lower() == "land":
        land.add(pid)

# states: id -> provinces + victory points
states = {}
for fn in os.listdir(r"D:\new-aor\history\states"):
    if not fn.endswith(".txt"):
        continue
    s = open(os.path.join(r"D:\new-aor\history\states", fn), "rb").read().decode("utf-8-sig", errors="replace")
    m = re.search(r"\bid\s*=\s*(\d+)", s)
    if not m:
        continue
    sid = int(m.group(1))
    prov = re.search(r"\bprovinces\s*=\s*\{([^}]*)\}", s)
    vpm = re.search(r"victory_points\s*=\s*\{([^}]*)\}", s)
    vps = {int(a): int(b) for a, b in re.findall(r"(\d+)\s+(\d+)", vpm.group(1))} if vpm else {}
    states[sid] = {
        "provs": [int(x) for x in re.findall(r"\d+", prov.group(1))] if prov else [],
        "vp": vps,
    }


def capital_province(state_id):
    st = states.get(state_id)
    if not st:
        return None
    cands = [p for p in st["provs"] if p in land]
    if not cands:
        return None
    cands.sort(key=lambda p: (-st["vp"].get(p, 0), p))
    return cands[0]


def read(p):
    return open(p, "rb").read().decode("utf-8-sig")


def write(p, s):
    raw = open(p, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    open(p, "wb").write((b"\xef\xbb\xbf" if bom else b"") + s.encode("utf-8"))


def main():
    apply = "--apply" in sys.argv
    report = []
    targets = [(fn, fn[7:-4]) for fn in os.listdir(UNITS) if fn.startswith("AOR_EU_")]
    targets.append(("BEL_1919.txt", "BEL"))
    for fn, tag in sorted(targets):
        # country file
        cfiles = [f for f in os.listdir(CTRY)
                  if re.match(r"^" + re.escape(tag) + r"(?![A-Z0-9])", f)]
        cap = None
        for f in cfiles:
            m = re.search(r"^\s*capital\s*=\s*(\d+)", read(os.path.join(CTRY, f)), re.M)
            if m:
                cap = int(m.group(1))
                break
        prov = capital_province(cap) if cap else None
        if prov is None:
            report.append((tag, cap, None, "NO PROVINCE"))
            continue
        p = os.path.join(UNITS, fn)
        s = read(p)
        n = s.count("location = ")
        new = re.sub(r"location\s*=\s*\d+", "location = %d" % prov, s)
        if apply and new != s:
            write(p, new)
        report.append((tag, cap, prov, n))
    for r in report:
        print(r)
    bad = [r for r in report if r[3] == "NO PROVINCE"]
    print("files:", len(report), "unresolved:", len(bad))


if __name__ == "__main__":
    main()
