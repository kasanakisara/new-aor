# -*- coding: utf-8 -*-
"""Create AOR generic + German division name groups and bind templates."""
import os, re, sys

ROOT = r"D:\new-aor"
NAMES = os.path.join(ROOT, "common", "units", "names_divisions")
UNITS = os.path.join(ROOT, "history", "units")

DIG = "零一二三四五六七八九"


def cn(n):
    if n < 10:
        return DIG[n]
    if n < 20:
        return "十" + (DIG[n % 10] if n % 10 else "")
    if n < 100:
        return DIG[n // 10] + "十" + (DIG[n % 10] if n % 10 else "")
    if n < 110:
        return "一百" + (DIG[n % 10] if n % 10 else "")
    if n < 1000:
        return "一百" + DIG[n // 10 % 10] + "十" + (DIG[n % 10] if n % 10 else "")
    return str(n)


def group(key, gname, unit_word, dtype, count=123, countries=None, words=None):
    lines = ["%s = {" % key, '\tname = "%s"' % gname]
    if countries:
        lines.append("\tfor_countries = { %s }" % " ".join(countries))
    lines.append("\tcan_use = { always = yes }")
    lines.append('\tdivision_types = { "%s" }' % dtype)
    lines.append('\tfallback_name = "%%d%s"' % unit_word)
    lines.append("\tordered = {")
    if words:
        for i, w in enumerate(words, 1):
            lines.append('\t\t%d = { "%s" }' % (i, w))
    else:
        for i in range(1, count + 1):
            lines.append('\t\t%d = { "第%s%s" }' % (i, cn(i), unit_word))
    lines.append("\t}")
    lines.append("}")
    return "\n".join(lines)


def main():
    apply = "--apply" in sys.argv
    words_file = os.path.join(ROOT, "tools", "coal", "ger_names.txt")
    words = []
    for line in open(words_file, encoding="utf-8").read().splitlines():
        line = line.strip()
        if not line or line.startswith("（"):
            continue
        if re.fullmatch(r"[0-9 ]+", line):   # pure numbers row: skip
            continue
        words.extend(line.split())

    parts = []
    parts.append(group("AOR_GEN_INF", "步兵师", "步兵师", "infantry"))
    parts.append(group("AOR_GEN_CAV", "骑兵师", "骑兵师", "cavalry"))
    parts.append(group("AOR_GEN_MTN", "山地师", "山地师", "mountaineers"))
    parts.append(group("AOR_GEN_ASL", "突击部队", "突击部队", "assault_team"))
    parts.append(group("AOR_GEN_MAR", "海军陆战队", "海军陆战队", "marine"))
    ger_words = ["第%s“%s”步兵师" % ("", w) for w in words]
    # 第一“革命”步兵师 …
    ger_names = []
    for i, w in enumerate(words, 1):
        ger_names.append("第%s“%s”步兵师" % (cn(i), w))
    parts.append(group("AOR_GER_INF", "国防军步兵师", "步兵师", "infantry",
                       countries=["GER"], words=ger_names))

    text = "# AOR 通用番号组 + 德国特色番号组\n" + "\n\n".join(parts) + "\n"
    path = os.path.join(NAMES, "AOR_generic_names_divisions.txt")
    if apply:
        open(path, "wb").write(b"\xef\xbb\xbf" + text.encode("utf-8"))
    print("groups:", 6, "ger words:", len(words), "->", path)

    # bind templates
    if apply:
        # 1) generated European OOBs -> generic infantry group
        for fn in os.listdir(UNITS):
            if not fn.startswith("AOR_EU_"):
                continue
            p = os.path.join(UNITS, fn)
            raw = open(p, "rb").read()
            s = raw.decode("utf-8-sig")
            if "division_names_group" in s:
                continue
            s2 = re.sub(r'(division_template\s*=\s*\{\s*\n\s*name\s*=\s*"[^"]*")',
                        r'\1\n\tdivision_names_group = AOR_GEN_INF', s, count=1)
            if s2 != s:
                open(p, "wb").write((b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"") + s2.encode("utf-8"))
        # 2) Germany: fix wrong SPAN groups
        p = os.path.join(UNITS, "GER_AOR.txt")
        raw = open(p, "rb").read()
        s = raw.decode("utf-8-sig")
        s = s.replace("division_names_group = SPAN_INF_02", "division_names_group = AOR_GER_INF")
        s = s.replace("division_names_group = SPAN_INF_03", "division_names_group = AOR_GEN_INF")
        s = re.sub(r'name = "骑兵旅"(\s*#[^\n]*)?\n(\s*)division_names_group = AOR_GEN_INF',
                   lambda m: 'name = "骑兵旅"%s\n%sdivision_names_group = AOR_GEN_CAV' % (m.group(1) or "", m.group(2)), s)
        open(p, "wb").write((b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"") + s.encode("utf-8"))
    print("bound templates")


if __name__ == "__main__":
    main()
