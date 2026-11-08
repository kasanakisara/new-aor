# -*- coding: utf-8 -*-
"""Build a report of the generated 1919 tech sets."""
import os, re, json, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tech_gen_common as G

CTRY = r"D:\new-aor\history\countries"
rows = []
post = collections.Counter()
post_country = collections.defaultdict(list)

for fn in sorted(os.listdir(CTRY)):
    if not fn.endswith(".txt"):
        continue
    tag = G.tag_of(fn)
    if tag == "GER":
        continue
    info = G.build(tag, fn)
    name = fn.replace(".txt", "")
    name = name.split(" - ", 1)[1] if " - " in name else name
    rows.append({"tag": tag, "file": fn, "name": name, "profile": info["profile"],
                 "air": info["air"], "navy": info["navy"], "techs": len(info["techs"])})
    for t in info["techs"]:
        y = G.techs[t]["year"]
        if y is not None and y > 1919:
            post[t] += 1
            post_country[tag].append(t)

with open(r"D:\new-aor\tools\coal\tech_report.csv", "w", encoding="utf-8-sig", newline="") as f:
    f.write("tag;file;country;profile;air_navy_level;navy_level;techs\n")
    for r in sorted(rows, key=lambda r: (r["profile"], r["tag"])):
        f.write(f'{r["tag"]};{r["file"]};{r["name"]};{r["profile"]};{r["air"]};{r["navy"]};{r["techs"]}\n')

prof_count = collections.Counter(r["profile"] for r in rows)
prof_range = {}
for r in rows:
    prof_range.setdefault(r["profile"], []).append(r["techs"])
tc = [r["techs"] for r in rows]
lines = []
lines.append("# AOR 1919 开局科技设置（除德国）\n")
lines.append("按 1919 年各国实际军事/工业水平分档，为每个国家文件写入一个 `set_technology`。\n")
lines.append("## 分档\n")
lines.append("| 档位 | 含义 | 国家数 | 科技数 | 内容 |")
lines.append("| --- | --- | ---: | ---: | --- |")
lines.append(f"| P0 | 一战列强 | {prof_count['P0']} | {min(prof_range['P0'])}-{max(prof_range['P0'])} | 工业（采矿/铁路/炼油/要塞/造船）+科学全套+航空 1914/1919 中小型+海军 1919 舰体+全部步兵/支援/炮兵+陆海空学说 |")
lines.append(f"| P1 | 主要强国 | {prof_count['P1']} | {min(prof_range['P1'])}-{max(prof_range['P1'])} | 工业只剩采矿/铁路+基础科学+航空 1914/1919 小型+海军 1914 舰体+步兵/支援/炮兵+学说 |")
lines.append(f"| P1B | 二线强国 | {prof_count['P1B']} | {min(prof_range['P1B'])}-{max(prof_range['P1B'])} | 有像样军队但工业薄弱：步枪/机枪/工兵/1900 野炮+仅 1914 小型机+1914 舰体；只给采矿/铁路 |")
lines.append(f"| P2 | 地区国家 | {prof_count['P2']} | {min(prof_range['P2'])}-{max(prof_range['P2'])} | 只给采矿/铁路+科学基础+仅 1914 小型机+海军 1914+步枪1919/机枪/工兵/1900 野炮 |")
lines.append(f"| P3 | 小国 | {prof_count['P3']} | {min(prof_range['P3'])}-{max(prof_range['P3'])} | 基础科学+仅 1914 小型机+1900步枪/1900野炮，无工业科技/无工兵/支援连 |")
lines.append(f"| P4 | 殖民地/部落 | {prof_count['P4']} | {min(prof_range['P4'])}-{max(prof_range['P4'])} | 1900步枪+基础科学，无工业科技/炮兵/工兵/支援连/航空/海军/学说 |")
lines.append("")
lines.append("陆军不再给「人人一战全套」：P0/P1 才是 1919 栓动步枪+机枪+支援连+野战炮+工兵；P2 只有步枪/机枪/工兵/野炮；P3 只有老式步枪+少量野炮；P4 只有最基础的 1900 步枪，没有炮兵、工兵、支援连。\n")
lines.append("## 陆/海/空学说\n")
lines.append("- 陆军：`mobile_warfare`（英、日、美式机动作战）/ `trench_warfare`（法、意、东欧壕堑）/ `mass_assault`（俄、中、巴尔干、拉美人海）")
lines.append("- 海军：`fleet_in_being`（英美日法意等主力舰队）/ `trade_interdiction`（北欧、荷兰、南美等袭击战）/ `base_strike`（日本）")
lines.append("- 空军：`air_superiority`（英美）/ `formation_flying`（法、意、日、俄）")
lines.append("")
lines.append("## 空军等级\n")
lines.append("| 等级 | 国家数 | 内容 |")
lines.append("| ---: | ---: | --- |")
for lvl, desc in [(4, "全套（小型/中型/重型/运输/飞艇）"), (3, "小型+中型 1914/1919"),
                  (2, "仅小型 1914/1919"), (1, "仅小型 1914"), (0, "无空军")]:
    lines.append(f"| {lvl} | {sum(1 for r in rows if r['air']==lvl)} | {desc} |")
lines.append("")
lines.append("无空军的国家（阿富汗、埃塞俄比亚、利比里亚、不丹、尼泊尔、西藏、蒙古、各非洲殖民地、中亚汗国等）其 1919 年机型的 `create_equipment_variant` 也已一并删除，避免出现「有飞机型号却没科技」的悬空引用。\n")
lines.append("## 备注\n")
lines.append("- 少数国家因开局舰船型号需要，额外保留了 1923/1925 的海军舰体科技（如英国的战列舰 3、美国的战巡 2），否则开局舰队会缺型号。")
lines.append("- 修正了 `CAN - Canada.txt` 多出来的一个右花括号（原文件括号不配对，会中断加拿大历史加载）。")
lines.append("- 详细逐国清单见 `tech_report.csv`。")
open(r"D:\new-aor\tools\coal\tech_report.md", "w", encoding="utf-8").write("\n".join(lines))
print("rows:", len(rows), "profiles:", dict(prof_count), "tech range:", min(tc), max(tc))
print("post-1919 carry-overs:", post.most_common())
