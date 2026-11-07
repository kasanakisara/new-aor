# -*- coding: utf-8 -*-
"""Post-process generated country files: drop empty if-blocks, fix CAN, report stray chars."""
import os, re, sys

CTRY = r"D:\new-aor\history\countries"


def read(p):
    return open(p, "rb").read().decode("utf-8-sig")


def write(p, s, bom=False):
    open(p, "wb").write((b"\xef\xbb\xbf" if bom else b"") + s.encode("utf-8"))


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


def body_empty(body):
    b = re.sub(r"#[^\n]*", "", body).strip()
    b = re.sub(r"^limit\s*=\s*\{[^{}]*\}", "", b, flags=re.S).strip()
    b = re.sub(r"^else\s*=\s*\{\s*\}", "", b).strip()
    return b == ""


def main():
    apply = "--apply" in sys.argv
    n_if = n_c = n_stray = 0
    for fn in sorted(os.listdir(CTRY)):
        if not fn.endswith(".txt"):
            continue
        p = os.path.join(CTRY, fn)
        s = read(p)
        orig = s
        # 1) remove empty if blocks
        out, pos, cnt = [], 0, 0
        for m in re.finditer(r"\bif\s*=\s*\{", s):
            if m.start() < pos:
                continue
            b = s.index("{", m.start())
            e = find_block(s, b)
            if e < 0:
                continue
            if body_empty(s[b + 1:e]):
                ls = s.rfind("\n", 0, m.start()) + 1
                end = e + 1
                while end < len(s) and s[end] in " \t":
                    end += 1
                if end < len(s) and s[end] == "\n":
                    end += 1
                out.append(s[pos:ls])
                pos = end
                cnt += 1
        out.append(s[pos:])
        s = "".join(out)
        if cnt:
            n_if += 1
        # 2) stray single-letter lines (artefact of earlier edits)
        lines = s.split("\n")
        kept = [ln for ln in lines if ln.strip() not in ("c",)]
        if len(kept) != len(lines):
            n_stray += 1
            s = "\n".join(kept)
        # 3) balance check
        if s.count("{") != s.count("}"):
            n_c += 1
            # drop trailing stray closing braces until balanced
            while s.count("{") < s.count("}") and s.rstrip().endswith("}"):
                s = s.rstrip()[:-1].rstrip("\n") + "\n"
        if s != orig:
            if apply:
                write(p, s)
    print("files with empty if cleaned:", n_if)
    print("files with stray 'c' removed:", n_stray)
    print("files brace-fixed:", n_c, "apply:", apply)


if __name__ == "__main__":
    main()
