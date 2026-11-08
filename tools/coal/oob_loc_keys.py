# -*- coding: utf-8 -*-
"""Turn Chinese division/template names in generated European OOBs into localisation keys."""
import os, re, sys

ROOT = r"D:\new-aor"
UNITS = os.path.join(ROOT, "history", "units")
LOC_CN = os.path.join(ROOT, "localisation", "simp_chinese", "AOR_EU_armies_l_simp_chinese.yml")
LOC_EN = os.path.join(ROOT, "localisation", "english", "AOR_EU_armies_l_english.yml")


def ordinal(n):
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return "%d%s" % (n, suf)


def read(p):
    return open(p, "rb").read().decode("utf-8-sig")


def write(p, s, crlf=True):
    s = s.replace("\r\n", "\n")
    if crlf:
        s = s.replace("\n", "\r\n")
    open(p, "wb").write(b"\xef\xbb\xbf" + s.encode("utf-8"))


def process(path, tag):
    s = read(path)
    nl = "\r\n" if "\r\n" in s else "\n"
    # template
    tm = re.search(r"division_template\s*=\s*\{", s)
    if not tm:
        return s, []
    tb = s.index("{", tm.start())
    depth = 0
    te = None
    for i in range(tb, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                te = i
                break
    tpl_body = s[tb:te]
    nm = re.search(r'name\s*=\s*"([^"]+)"', tpl_body)
    if not nm:
        return s, []
    tpl_cn = nm.group(1)
    tpl_key = "AOR_EU_%s_TPL" % tag
    entries = [(tpl_key, tpl_cn, "Royal Guard" if "卫队" in tpl_cn else ("Militia Division" if "民兵" in tpl_cn else "Infantry Division"))]
    s = s[:tb] + tpl_body.replace('name = "%s"' % tpl_cn, 'name = "%s"' % tpl_key, 1) + s[te:]
    s = s.replace('division_template = "%s"' % tpl_cn, 'division_template = "%s"' % tpl_key)

    # divisions
    out = []
    pos = 0
    idx = 0
    for m in re.finditer(r"^\s*division\s*=\s*\{", s, re.M):
        if m.start() < pos:
            continue
        b = s.index("{", m.start())
        depth = 0
        e = None
        for i in range(b, len(s)):
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                depth -= 1
                if depth == 0:
                    e = i
                    break
        body = s[b:e]
        dn = re.search(r'name\s*=\s*"([^"]+)"', body)
        if not dn:
            continue
        cn = dn.group(1)
        idx += 1
        key = "AOR_EU_%s_DIV_%d" % (tag, idx)
        en = "%s Infantry Division" % ordinal(idx) if "步兵" in cn else "%s Division" % ordinal(idx)
        entries.append((key, cn, en))
        newbody = body.replace('name = "%s"' % cn, 'name = "%s"' % key, 1)
        out.append((b, e, newbody))
        pos = e
    # apply from the end
    for b, e, newbody in reversed(out):
        s = s[:b] + newbody + s[e:]
    return s, entries


def main():
    apply = "--apply" in sys.argv
    all_entries = []
    for fn in sorted(os.listdir(UNITS)):
        if fn.startswith("AOR_EU_"):
            tag = fn[7:-4]
        elif fn == "BEL_1919.txt":
            tag = "BEL"
        else:
            continue
        path = os.path.join(UNITS, fn)
        s, entries = process(path, tag)
        if apply and entries:
            write(path, s, crlf=("\r\n" in s))
        all_entries.extend(entries)
        print(fn, "->", len(entries), "keys" if apply else "(dry)")

    if apply:
        cn = ["l_simp_chinese:"] + [" %s:0 \"%s\"" % (k, c) for k, c, e in all_entries]
        en = ["l_english:"] + [" %s:0 \"%s\"" % (k, e) for k, c, e in all_entries]
        write(LOC_CN, "\n".join(cn))
        write(LOC_EN, "\n".join(en))
        print("loc entries:", len(all_entries))


if __name__ == "__main__":
    main()
