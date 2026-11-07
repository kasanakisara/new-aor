# -*- coding: utf-8 -*-
"""Generate coal report (MD + CSV) from the current state files."""
import os, re, json, collections

AOR = r"D:\new-aor\history\states"
OUT = r"D:\new-aor\tools\coal"
VAN_TOTAL = 1463
VAN_STATES = 153
SCALE = 1.5

def read(p):
    return open(p, "rb").read().decode("utf-8-sig")

def grab(t, pat):
    m = re.search(pat, t, re.M)
    return m

def block_inner(t, key):
    m = re.search(r"^\s*" + key + r"\s*=\s*\{", t, re.M)
    if not m:
        return None
    brace = t.index("{", m.start())
    depth = 0
    for i in range(brace, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                return t[brace + 1:i]
    return None

rows = []
for fn in sorted(os.listdir(AOR)):
    if not fn.endswith(".txt"):
        continue
    t = read(os.path.join(AOR, fn))
    sid = int(grab(t, r"^\s*id\s*=\s*(\d+)").group(1))
    res = block_inner(t, "resources") or ""
    coal = 0
    m = re.search(r"\bcoal\s*=\s*([0-9.]+)", res)
    if m:
        coal = int(float(m.group(1)))
    own = grab(t, r"^\s*owner\s*=\s*([A-Za-z0-9_]+)")
    prov = block_inner(t, "provinces") or ""
    nprov = len(re.findall(r"\d+", prov))
    cat = grab(t, r"^\s*state_category\s*=\s*([a-z_]+)")
    name_c = re.search(r'name\s*=\s*"([^"]+)"[ \t]*(?:#\s*(.*))?', t)
    rows.append({"id": sid, "file": fn, "owner": own.group(1) if own else "",
                 "coal": coal, "nprov": nprov,
                 "category": cat.group(1) if cat else "",
                 "comment": (name_c.group(2) or "").strip() if name_c else ""})

rows.sort(key=lambda r: r["id"])
with open(os.path.join(OUT, "coal_states.csv"), "w", encoding="utf-8-sig", newline="") as f:
    f.write("state_id;file;owner;coal;provinces;category;note\n")
    for r in rows:
        if r["coal"]:
            f.write(f'{r["id"]};{r["file"]};{r["owner"]};{r["coal"]};{r["nprov"]};{r["category"]};{r["comment"]}\n')

coal_rows = [r for r in rows if r["coal"]]
total = sum(r["coal"] for r in coal_rows)
own = collections.defaultdict(lambda: [0, 0])
for r in coal_rows:
    own[r["owner"]][0] += r["coal"]
    own[r["owner"]][1] += 1
own_sorted = sorted(own.items(), key=lambda kv: -kv[1][0])

by_cat = collections.Counter()
for r in coal_rows:
    by_cat[r["category"]] += 1

lines = []
lines.append("# AOR 煤炭分布（1919）\n")
lines.append("按原版 HOI4 `history/states` 的煤炭密度，用**省份插值**重算到 AOR 的州；再整体 ×1.5（1919 年煤炭仍是主要能源）。\n")
lines.append("## 总览\n")
lines.append(f"- 有煤州：**{len(coal_rows)}** / {len(rows)}（原版 {VAN_STATES} 个）")
lines.append(f"- 全球煤总量：**{total}**（原版 {VAN_TOTAL}，×{total/VAN_TOTAL:.2f}）")
lines.append(f"- 单州最高：{max(r['coal'] for r in coal_rows)}（{max(coal_rows, key=lambda r: r['coal'])['file']}）")
lines.append(f"- 单州中位：{sorted(r['coal'] for r in coal_rows)[len(coal_rows)//2]}")
lines.append(f"- 计算方法：`state_coal = round(1.5 * Σ(原版所属州煤量 / 该州省份数))`，基础值 ≥0.4 的州至少 1 煤；原有手工煤值取较大者")
lines.append("")
lines.append("## 分国家（按新煤量）\n")
lines.append("| 国家 | 煤 | 州数 |")
lines.append("| --- | ---: | ---: |")
for tag, (v, c) in own_sorted[:25]:
    lines.append(f"| {tag} | {v} | {c} |")
lines.append("")
lines.append("## 前 25 个煤州\n")
lines.append("| ID | 州 | 国家 | 煤 |")
lines.append("| ---: | --- | --- | ---: |")
for r in sorted(coal_rows, key=lambda r: -r["coal"])[:25]:
    lines.append(f"| {r['id']} | {r['file']} | {r['owner']} | {r['coal']} |")
lines.append("")
lines.append("## 各州分类\n")
for k, v in by_cat.most_common():
    lines.append(f"- {k or '(none)'}: {v}")
lines.append("")
lines.append("完整逐州清单见 `coal_states.csv`。修改前的原始文件备份在 `backup/`。")
open(os.path.join(OUT, "coal_report.md"), "w", encoding="utf-8").write("\n".join(lines))
print("coal states:", len(coal_rows), "total:", total)
print("top countries:", own_sorted[:8])
