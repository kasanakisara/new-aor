# -*- coding: utf-8 -*-
"""Rewrite starting technologies of all AOR country history files (GER skipped)."""
import os, re, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tech_gen_common as G

CTRY = r"D:\new-aor\history\countries"
techs = G.techs

HEADER = ("# AOR 1919 tech baseline (generated): historically appropriate starting technologies.\n")
GROUP_TITLES = [
    ("Industry", {"basic_machine_tools", "construction1", "excavation1", "fuel_refining",
                  "aor_railway_engineering", "aor_shipbuilding", "aor_fortification1"}),
    ("Science", {"aor_basic_science_1900", "Modern_electronics", "Classic_optics",
                 "Hot_air_balloon", "Gas_Preparation", "Gas_mask"}),
    ("Infantry and support", {"aor_inf_r01", "aor_inf_r02", "aor_inf_b01", "aor_inf_l00",
                              "aor_inf_l01", "aor_inf_g01", "aor_inf_u01", "aor_inf_u02",
                              "aor_inf_m01", "aor_inf_t01", "aor_inf_e01", "tech_support",
                              "tech_engineers", "tech_recon", "tech_military_police",
                              "aor_inf_mg1", "tech_field_hospital", "basic_train",
                              "aor_tank_support", "bicycle_infantry", "paratroopers",
                              "infantry_at"}),
    ("Artillery", {"Old_howitzers", "aor_field_gun_1", "aor_howitzer_1", "interwar_antitank"}),
    ("Aviation", None),
    ("Navy", None),
    ("Doctrine", {"mobile_warfare", "superior_firepower", "trench_warfare", "mass_assault",
                  "fleet_in_being", "trade_interdiction", "base_strike", "air_superiority",
                  "formation_flying", "force_rotation"}),
]


BOM = b"\xef\xbb\xbf"


def read(p):
    return open(p, "rb").read().decode("utf-8-sig")


def write(p, s):
    raw = open(p, "rb").read()
    open(p, "wb").write((BOM if raw.startswith(BOM) else b"") + s.encode("utf-8"))


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


AI_COMMENTS = {
    "# AOR industry 1919 baseline; later tiers remain research choices.",
    "# AOR modular aviation startup: tech prerequisites and modules precede variants and stockpiles.",
    "# AOR 1919 tech baseline (generated): historically appropriate starting technologies.",
}


def strip_ai_comments(s):
    nl = "\r\n" if "\r\n" in s else "\n"
    out = []
    for line in s.split(nl):
        if line.strip() in AI_COMMENTS:
            continue
        out.append(line)
    return nl.join(out)


def strip_all_set_technology(s):
    out, pos = [], 0
    for m in re.finditer(r"set_technology\s*=\s*\{", s):
        if m.start() < pos:
            continue
        b = s.index("{", m.start())
        e = find_block(s, b)
        if e < 0:
            continue
        # eat trailing whitespace up to end of line
        end = e + 1
        while end < len(s) and s[end] in " \t":
            end += 1
        if end < len(s) and s[end] == "\r":
            end += 1
        if end < len(s) and s[end] == "\n":
            end += 1
        out.append(s[pos:m.start()])
        pos = end
    out.append(s[pos:])
    return "".join(out)


def remove_air_variants(s, granted_frames):
    """Delete create_equipment_variant blocks whose plane frame is not granted."""
    nl = "\r\n" if "\r\n" in s else "\n"
    out, pos = [], 0
    removed = 0
    for m in re.finditer(r"create_equipment_variant\s*=\s*\{", s):
        if m.start() < pos:
            continue
        b = s.index("{", m.start())
        e = find_block(s, b)
        if e < 0:
            continue
        body = s[b + 1:e]
        ty = re.search(r"\btype\s*=\s*([A-Za-z0-9_]+)", body)
        tname = ty.group(1) if ty else None
        if tname in G.AIR_FRAME_EQUIP and tname not in granted_frames:
            # remove from start of line to end of block (+ eol)
            line_start = s.rfind(nl, 0, m.start()) + len(nl)
            end = e + 1
            while end < len(s) and s[end] in " \t":
                end += 1
            if end < len(s) and s[end] == "\r":
                end += 1
            if end < len(s) and s[end] == "\n":
                end += 1
            out.append(s[pos:line_start])
            pos = end
            removed += 1
    out.append(s[pos:])
    return "".join(out), removed


def make_block(tl, tier, profile, air, navy):
    nl = "\r\n" if True else "\n"
    lines = [HEADER.rstrip("\n")]
    lines.append("set_technology = {")
    used = set()
    for title, group in GROUP_TITLES:
        if group is None:
            if title == "Aviation":
                items = [t for t in tl if t.startswith("aor_air_")]
            else:
                items = [t for t in tl if t.startswith(("early_ship_hull", "tech_1919_ship_hull",
                                                        "tech_1919_crusier", "aor_engine_19",
                                                        "aor_engine_1914", "aor_fcs",
                                                        "basic_fire_control", "damage_control",
                                                        "fire_control_methods", "basic_battery",
                                                        "basic_torpedo", "basic_naval_mines",
                                                        "aor_lightgun", "aor_mediumgun",
                                                        "aor_heavygun", "aor_secondary",
                                                        "aor_aa_1919", "aor_torpedo_1919",
                                                        "aor_mines_1919", "aor_depth_1919",
                                                        "aor_sonar_1919", "aor_armorheavy",
                                                        "aor_armorcr", "aor_airscout",
                                                        "aor_dd_", "aor_ss_", "aor_bb_",
                                                        "aor_cr_", "aor_bc_", "aor_cv_",
                                                        "mtg_transport"))]
        else:
            items = [t for t in tl if t in group]
        items = [t for t in items if t not in used]
        if not items:
            continue
        used.update(items)
        lines.append("\t# " + title)
        for t in sorted(items):
            lines.append("\t%s = 1" % t)
    rest = [t for t in tl if t not in used]
    if rest:
        lines.append("\t# Other (required by starting OOB)")
        for t in sorted(rest):
            lines.append("\t%s = 1" % t)
    lines.append("}")
    return "\r\n".join(lines) + "\r\n"


def main():
    apply = "--apply" in sys.argv
    rows = []
    counts = collections.Counter()
    samples = []
    for fn in sorted(os.listdir(CTRY)):
        if not fn.endswith(".txt"):
            continue
        tag = G.tag_of(fn)
        if tag == "GER":
            continue
        info = G.build(tag, fn)
        path = os.path.join(CTRY, fn)
        txt = read(path)
        new = strip_ai_comments(txt)
        new = strip_all_set_technology(new)
        new, removed = remove_air_variants(new, info["frames"])
        # insert block at top after leading comment/bom lines
        block = make_block(info["techs"], None, info["profile"], info["air"], info["navy"])
        nl = "\r\n" if "\r\n" in new else "\n"
        block = block.replace("\r\n", nl)
        new = block + new
        rows.append({"tag": tag, "file": fn, "profile": info["profile"], "air": info["air"],
                     "navy": info["navy"], "techs": len(info["techs"]),
                     "removed_variants": removed})
        counts[(info["profile"], info["air"], info["navy"])] += 1
        if not apply:
            if len(samples) < 2 and fn in ("SWI - Switzerland.txt", "CHI - China.txt"):
                samples.append((fn, txt, new))
            continue
        write(path, new)
    print("counts (profile, air, navy):", counts.most_common(10))
    print("countries:", len(rows), "apply:", apply)
    json.dump(rows, open(r"D:\new-aor\tools\coal\tech_plan_report.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    if not apply:
        import difflib
        for fn, old, new in samples:
            print("=" * 20, fn)
            d = list(difflib.unified_diff(old.splitlines(True), new.splitlines(True), n=1))
            sys.stdout.write("".join(d[:50]))
            print("... diff lines:", len(d))


if __name__ == "__main__":
    main()
