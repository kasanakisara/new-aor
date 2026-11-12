# -*- coding: utf-8 -*-
"""Apply coal values from plan.json into AOR state files.

Usage:  python apply_coal.py [--apply]
Default is a dry run that prints a diff summary; --apply backs files up to
tools/coal/backup/ first, then writes the new coal values in place.
"""
import os, re, sys, json, shutil, difflib

AOR = r"D:\new-aor\history\states"
BK = r"D:\new-aor\tools\coal\backup"

plan = {p["id"]: p for p in json.load(open(r"D:\new-aor\tools\coal\plan.json", encoding="utf-8"))}

def find_block_end(s, brace):
    depth = 0
    for i in range(brace, len(s)):
        c = s[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1

def state_resources_span(s):
    m = re.search(r"^[ \t]*resources\s*=\s*\{", s, re.M)
    if not m:
        return None
    brace = s.index("{", m.start())
    end = find_block_end(s, brace)
    return (brace, end) if end >= 0 else None

COAL_RE = re.compile(r"^([ \t]*)coal([ \t]*=[ \t]*)(-?[0-9.]+)([ \t]*(?:#[^\r\n]*)?)\r?$", re.M)

def edit_text(txt, coal):
    """Return (new_text, mode)."""
    nl = "\r\n" if "\r\n" in txt else "\n"
    m = COAL_RE.search(txt)
    if m:
        cr = "\r" if m.group(0).endswith("\r") else ""
        new = (txt[:m.start()] + m.group(1) + "coal" + m.group(2) + str(coal)
               + m.group(4) + cr + txt[m.end():])
        return new, ("same" if new == txt else "replace")
    if coal <= 0:
        return txt, "skip-zero"
    span = state_resources_span(txt)
    if span:
        brace, end = span
        inner = txt[brace + 1:end]
        indent = "\t\t"
        for line in inner.split(nl):
            mm = re.match(r"^([ \t]+)\S", line)
            if mm:
                indent = mm.group(1)
                break
        line_start = txt.rfind(nl, 0, end) + len(nl)
        insert = f"{indent}coal={coal}{nl}"
        return txt[:line_start] + insert + txt[line_start:], "insert-in-block"
    mm = re.search(r"^([ \t]*)name\s*=\s*[\"'][^\"'\r\n]*[\"'][^\r\n]*" + nl, txt, re.M)
    if not mm:
        mm = re.search(r"^([ \t]*)id\s*=\s*\d+[^\r\n]*" + nl, txt, re.M)
    if not mm:
        return txt, "NO-ANCHOR"
    indent = mm.group(1)
    block = f"{indent}resources={{{nl}{indent}\tcoal={coal}{nl}{indent}}}{nl}"
    return txt[:mm.end()] + block + txt[mm.end():], "new-block"

def main():
    apply = "--apply" in sys.argv
    if apply:
        os.makedirs(BK, exist_ok=True)
    counts = {}
    changed = 0
    samples = {}
    for sid, p in sorted(plan.items()):
        path = os.path.join(AOR, p["file"])
        txt = open(path, "rb").read().decode("utf-8-sig")
        new, how = edit_text(txt, p["coal"])
        counts[how] = counts.get(how, 0) + 1
        if how == "NO-ANCHOR":
            print("!! anchor missing:", p["file"], sid)
        if new == txt:
            continue
        changed += 1
        if not apply:
            if how not in samples:
                samples[how] = (p["file"], p["coal"], txt, new)
            continue
        shutil.copy2(path, os.path.join(BK, p["file"]))
        open(path, "wb").write(new.encode("utf-8"))
    if not apply:
        for how, (f, coal, old, new) in samples.items():
            print(f"--- sample {how}: {f} (coal={coal})")
            sys.stdout.write("".join(list(difflib.unified_diff(old.splitlines(True), new.splitlines(True), n=2))[:30]))
    print("modes:", counts, "changed:", changed, "apply:", apply)
    if apply:
        print("backup dir:", BK)

if __name__ == "__main__":
    main()
