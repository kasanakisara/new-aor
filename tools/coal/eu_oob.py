# -*- coding: utf-8 -*-
"""European 1919 starting armies.

- keep_tags:  hand-written OOB files that stay as they are.
- trim_tags:  hand-written files whose division count is cut (or raised) to the target.
- gen_tags:   no usable 1919 OOB -> a fresh, simple OOB is generated.
"""
import os, re, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tech_gen_common as G
TIER_KIND = {"P0": 1, "P1": 1, "P2": 2, "P3": 3, "P4": 4}

CTRY = r"D:\new-aor\history\countries"
UNITS = r"D:\new-aor\history\units"

# tag: (divisions, template kind)  kind: 1 = 9inf+2art, 2 = 9inf, 3 = 6inf, 4 = 3inf
TARGET = {
    # ---- generated (divisions only; template style follows the country's tech tier)
    "ALB": 2, "ARM": 2, "AZR": 2, "BLR": 3, "BOS": 2, "CRO": 3, "CZE": 8,
    "EST": 2, "FIN": 4, "FIC": 2, "GEO": 2, "HOL": 4, "HUN": 6, "IRE": 2,
    "KOS": 1, "LAT": 2, "LUX": 1, "MAC": 2, "MNT": 2, "NOR": 4, "POR": 5,
    "SER": 12, "SLO": 2, "SPR": 12, "SWI": 4, "TUR": 12, "HRZ": 1, "DAL": 2,
    "NSH": 1, "DNZ": 1, "DON": 8, "KUB": 5, "SBC": 6, "URS": 3, "NAA": 1,
    "PSR": 1, "RPS": 3, "SCR": 1, "SRK": 1, "XCD": 1, "WUG": 1, "TRZ": 1,
    "RFR": 1, "IDE": 1, "OIC": 1, "SFM": 1, "VGE": 1, "GNR": 1, "CAT": 3,
    "OCC": 2, "BRI": 2, "COR": 1, "SIL": 3, "GLC": 3, "MNT": 2,
    # ---- hand-written files: trim / grow to target
    "SWE": 8, "NAU": 2, "BEL": 6,
    "AUS": 4,
}

# hand-written files kept untouched (already written and reasonable)
KEEP = {"FRA", "ENG", "GER", "ITA", "ARU", "ARR", "POL", "BUL", "ROM", "GRE",
        "YUG", "DEN", "UKR", "BAV", "SAX", "HAN", "SHL", "MEK", "WUR",
        "PRE", "SPE", "UZH", "RUS", "LIT", "CAU"}

TEMPLATE_KINDS = {
    1: ("步兵师", 9, 2),
    2: ("步兵师", 9, 0),
    3: ("步兵师", 6, 0),
    4: ("民兵师", 3, 0),
}


def read(p):
    return open(p, "rb").read().decode("utf-8-sig")


BOM = b"\xef\xbb\xbf"


def write(p, s, bom=False):
    try:
        raw = open(p, "rb").read()
        has_bom = raw.startswith(BOM)
    except OSError:
        has_bom = bom
    open(p, "wb").write((BOM if has_bom else b"") + s.encode("utf-8"))


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


def make_oob(tag, divisions, kind, capital, country_name):
    tpl_name, inf, art = TEMPLATE_KINDS[kind]
    nl = "\r\n"
    out = []
    out.append("# AOR 1919 starting army for %s" % tag)
    out.append("division_template = {")
    out.append('\tname = "%s"' % tpl_name)
    out.append("\tregiments = {")
    for i in range(inf):
        out.append("\t\tinfantry = { x = %d y = %d }" % (i % 3, i // 3))
    for i in range(art):
        out.append("\t\tartillery_brigade = { x = %d y = %d }" % ((inf + i) % 3, (inf + i) // 3))
    out.append("\t}")
    out.append("\tsupport = {")
    out.append("\t}")
    out.append("}")
    out.append("")
    out.append("units = {")
    for i in range(1, divisions + 1):
        out.append("\tdivision = {")
        out.append('\t\tname = "第%d%s"' % (i, "民兵师" if kind == 4 else "步兵师"))
        out.append("\t\tlocation = %d" % capital)
        out.append('\t\tdivision_template = "%s"' % tpl_name)
        out.append("\t\tstart_experience_factor = 0.35")
        out.append("\t\tstart_equipment_factor = 0.8")
        out.append("\t}")
    out.append("}")
    return nl.join(out) + nl


def count_divisions(text):
    return len(re.findall(r"^\s*division\s*=\s*\{", text, re.M))


def trim_divisions(text, target):
    """Delete surplus division blocks from the units block (keeps first `target`)."""
    nl = "\r\n" if "\r\n" in text else "\n"
    um = re.search(r"^units\s*=\s*\{", text, re.M)
    if not um:
        return text, 0
    ub = text.index("{", um.start())
    ue = find_block(text, ub)
    body = text[ub + 1:ue]
    blocks = list(re.finditer(r"^\s*division\s*=\s*\{", body, re.M))
    if len(blocks) <= target:
        return text, 0
    cut_from = blocks[target].start()
    newbody = body[:cut_from].rstrip() + nl
    new = text[:ub + 1] + newbody + text[ue:]
    return new, len(blocks) - target


def grow_divisions(text, target, tag):
    """Append simple divisions cloned from the last one, up to `target`."""
    nl = "\r\n" if "\r\n" in text else "\n"
    um = re.search(r"^units\s*=\s*\{", text, re.M)
    count = count_divisions(text)
    if count >= target:
        return text, 0
    if not um:
        return text, 0
    ub = text.index("{", um.start())
    ue = find_block(text, ub)
    body = text[ub + 1:ue]
    blocks = list(re.finditer(r"^(\s*)division\s*=\s*\{", body, re.M))
    if not blocks:
        return text, 0
    last = blocks[-1]
    bstart = last.start()
    bend = find_block(body, body.index("{", last.start()))
    block = body[bstart:bend + 1]
    added = []
    for i in range(count + 1, target + 1):
        clone = re.sub(r'name\s*=\s*"[^"]*"', 'name = "第%d步兵师"' % i, block, count=1)
        added.append(clone.rstrip())
    newbody = body.rstrip() + nl + nl.join(added) + nl
    return text[:ub + 1] + newbody + text[ue:], target - count


OOBDEF_RE = re.compile(r"^(\s*)#?\s*(oob|set_oob|load_oob|land_oob)\s*=\s*\"?([A-Za-z0-9_]+)\"?[^\r\n]*(?:\r?\n|$)", re.M)


def rewrite_country_oob_line(text, newfile):
    """Remove every oob-ish line and insert `oob = "newfile"` after the capital line."""
    nl = "\r\n" if "\r\n" in text else "\n"
    text2 = OOBDEF_RE.sub("", text)
    anchor = re.search(r"^\s*capital\s*=\s*\d+[^\r\n]*" + re.escape(nl), text2, re.M)
    line = 'oob = "%s"%s' % (newfile, nl)
    if anchor:
        return text2[:anchor.end()] + line + text2[anchor.end():]
    return line + text2


def normalise_refs(apply):
    """Give every European country exactly one valid `oob =` line."""
    changed = []
    for fn in sorted(os.listdir(CTRY)):
        if not fn.endswith(".txt"):
            continue
        tag = re.match(r"([A-Za-z0-9]{2,3})", fn).group(1).upper()
        if tag not in KEEP and tag not in TARGET:
            continue
        path = os.path.join(CTRY, fn)
        text = read(path)
        refs = re.findall(r'^[ \t]*#?[ \t]*(?:oob|set_oob|load_oob|land_oob)\s*=\s*"?([A-Za-z0-9_]+)"?', text, re.M)
        refs = [r for r in refs if r and r != "set_naval_oob"]
        chosen = None
        for r in refs:
            if os.path.exists(os.path.join(UNITS, r + ".txt")) and "1936" not in r:
                chosen = r
                break
        if chosen is None:
            continue
        if not apply:
            changed.append((tag, fn, refs, chosen))
            continue
        new = rewrite_country_oob_line(text, chosen)
        write(path, new, bom=text.startswith("\ufeff"))
        changed.append((tag, fn, refs, chosen))
    return changed


def main():
    apply = "--apply" in sys.argv
    report = []
    for fn in sorted(os.listdir(CTRY)):
        if not fn.endswith(".txt"):
            continue
        tag = re.match(r"([A-Za-z0-9]{2,3})", fn).group(1).upper()
        if tag in KEEP or tag not in TARGET:
            continue
        path = os.path.join(CTRY, fn)
        text = read(path)
        cap = re.search(r"^\s*capital\s*=\s*(\d+)", text, re.M)
        capital = int(cap.group(1)) if cap else None
        if capital is None:
            report.append((tag, "NO CAPITAL", 0))
            continue

        cur = re.search(r'^\s*#?\s*(?:oob|set_oob|load_oob|land_oob)\s*=\s*"?([A-Za-z0-9_]+)"?', text, re.M)
        curfile = cur.group(1) if cur else None
        target = TARGET[tag]
        kind = TIER_KIND.get(G.profile_of(tag), 3)

        if tag in ("RUS", "LIT", "SWE", "NAU", "CAU", "BEL") and curfile and os.path.exists(os.path.join(UNITS, curfile + ".txt")):
            # hand-written file: adjust division count only
            oob_path = os.path.join(UNITS, curfile + ".txt")
            oob = read(oob_path)
            n = count_divisions(oob)
            if tag == "BEL" and n == 0:
                # append units block using its existing template name
                tm = re.search(r'^\s*name\s*=\s*"([^"]+)"', oob, re.M)
                tpl = tm.group(1) if tm else "步兵师"
                nl = "\r\n" if "\r\n" in oob else "\n"
                parts = ["units = {"]
                for i in range(1, target + 1):
                    parts += ["\tdivision = {", '\t\tname = "第%d步兵师"' % i,
                              "\t\tlocation = %d" % capital,
                              '\t\tdivision_template = "%s"' % tpl,
                              "\t\tstart_experience_factor = 0.35",
                              "\t\tstart_equipment_factor = 0.8", "\t}"]
                parts.append("}")
                new_oob = oob.rstrip() + nl + nl.join(parts) + nl
                if apply:
                    write(oob_path, new_oob, bom=oob.startswith("\ufeff"))
                report.append((tag, "grew " + curfile, target))
            elif n > target:
                new_oob, removed = trim_divisions(oob, target)
                if apply:
                    write(oob_path, new_oob, bom=oob.startswith("\ufeff"))
                report.append((tag, "trimmed " + curfile, "%d->%d" % (n, target)))
            elif n < target:
                new_oob, added = grow_divisions(oob, target, tag)
                if apply:
                    write(oob_path, new_oob, bom=oob.startswith("\ufeff"))
                report.append((tag, "grew " + curfile, "%d->%d" % (n, target)))
            else:
                report.append((tag, "kept " + curfile, n))
            continue

        # generated
        newname = "AOR_EU_%s" % tag
        new_oob = make_oob(tag, target, kind, capital, fn)
        if apply:
            write(os.path.join(UNITS, newname + ".txt"), new_oob)
            new_text = rewrite_country_oob_line(text, newname)
            write(path, new_text, bom=text.startswith("\ufeff"))
        report.append((tag, "generated " + newname, target))

    refs = normalise_refs(apply)
    print("--- reference normalisation ---")
    for r in refs:
        print(r)
    print("--- files ---")
    for r in report:
        print(r)


if __name__ == "__main__":
    main()
