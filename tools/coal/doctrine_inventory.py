# -*- coding: utf-8 -*-
"""Inventory AOR doctrine system: grand doctrines, tracks, subdoctrines."""
import os, re, sys

ROOT = r"D:\new-aor\common\doctrines"


def read(p):
    return open(p, "rb").read().decode("utf-8-sig", errors="replace")


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


def top_blocks(path):
    s = read(path)
    out = []
    for m in re.finditer(r"^(\w+)\s*=\s*\{", s, re.M):
        b = s.index("{", m.start())
        e = find_block(s, b)
        out.append((m.group(1), s[b + 1:e]))
    return out


def main():
    lines = []
    # grand doctrines
    for fn in ["land_grand_doctrines.txt", "air_grand_doctrines.txt", "sea_grand_doctrines.txt",
               "special_forces_grand_doctrines.txt"]:
        p = os.path.join(ROOT, "grand_doctrines", fn)
        lines.append("##### " + fn)
        for name, body in top_blocks(p):
            nm = re.search(r"name\s*=\s*(\w+)", body)
            tracks = re.findall(r"^\s*(\w+)\s*=\s*\{", re.search(r"tracks\s*=\s*\{", body).group(0) and body, re.M)
            tb = re.search(r"tracks\s*=\s*\{", body)
            if tb:
                b = body.index("{", tb.start())
                e = find_block(body, b)
                tracks = re.findall(r"^\s*(\w+)\s*=\s*\{", body[b:e], re.M)
            lines.append("  %-28s %-40s tracks=%s" % (name, nm.group(1) if nm else "?", tracks))
        lines.append("")

    # tracks
    for fn in ["land_doctrine_tracks.txt", "future_land_doctrine_tracks.txt",
               "future_air_doctrine_tracks.txt", "future_sea_doctrine_tracks.txt"]:
        p = os.path.join(ROOT, "tracks", fn)
        lines.append("##### tracks/" + fn)
        for name, body in top_blocks(p):
            nm = re.search(r"name\s*=\s*(\w+)", body)
            subs = re.findall(r"sub_units\s*=\s*\{([^}]*)\}", body)
            cats = re.findall(r"categories\s*=\s*\{([^}]*)\}", body)
            lines.append("  %-24s %-36s sub_units=%s cats=%s" % (
                name, nm.group(1) if nm else "?",
                " ".join(" ".join(x.split()) for x in subs)[:70], " ".join(" ".join(x.split()) for x in cats)[:60]))
        lines.append("")

    # subdoctrines
    for sub in ["land", "air", "sea", "special_forces"]:
        d = os.path.join(ROOT, "subdoctrines", sub)
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".txt"):
                continue
            p = os.path.join(d, fn)
            lines.append("##### subdoctrines/%s/%s" % (sub, fn))
            for name, body in top_blocks(p):
                nm = re.search(r"name\s*=\s*(\w+)", body)
                # effect keys: lines like "unit_or_category = {" at top level of body (outside rewards)
                eff = []
                depth = 0
                i = 0
                while i < len(body):
                    c = body[i]
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                    elif depth == 0 and c.isalnum():
                        m = re.match(r"(\w+)\s*=\s*\{", body[i:])
                        if m and m.group(1) not in ("rewards", "available", "ai_will_do", "modifier", "effect", "custom_effect_tooltip"):
                            eff.append(m.group(1))
                            i += m.end()
                            depth += 1
                            continue
                    i += 1
                lines.append("  %-34s %-34s effects=%s" % (name, nm.group(1) if nm else "?", eff[:14]))
            lines.append("")
    out = r"D:\new-aor\tools\coal\doctrine_inventory.txt"
    open(out, "w", encoding="utf-8").write("\n".join(lines))
    print("written", out, len(lines), "lines")


if __name__ == "__main__":
    main()
