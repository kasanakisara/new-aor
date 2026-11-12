# AOR 工具：煤炭分布 + 1919 开局科技

## 1. 煤炭分布（1919）

依据原版 `history/states` 的煤炭，按**省份**插值到 AOR 的州，再整体 ×1.3。

- 有煤州 216 / 1127，全球煤 1914（原版 1463）
- 逐州清单：[coal_states.csv](coal_states.csv)；汇总：[coal_report.md](coal_report.md)

```bash
PY="C:/Users/pc/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe"
$PY parse_both.py      # 解析原版+AOR 州，生成 data.json
$PY build_plan.py      # 生成 plan.json（SCALE/MIN_BASE 在文件顶部）
$PY apply_coal.py      # 干跑；--apply 写入
$PY make_report.py     # 重新生成报告
```

## 2. 1919 开局科技（除德国）

按 1919 年各国水平分五档，给 363 个国家文件写入统一格式的 `set_technology`：

- 分档表与统计：[tech_report.md](tech_report.md)；逐国清单：[tech_report.csv](tech_report.csv)
- 档位与科技组在 `tech_profiles.py`，档位归属在 `tech_gen_common.py`（P0/P1/P2/P4 集合 + 陆/海/空学说表）

```bash
$PY tech_inventory.py   # 解析科技树 + 现有国家科技 → techs.json
$PY country_analysis.py # 国家文件结构 → countries.json
$PY oob_needs.py        # OOB/型号 → 必需科技 → oob_req.json
$PY tech_write.py       # 干跑看 diff；--apply 写入
$PY tech_verify.py      # 校验：唯一 set_technology、科技 id 合法、括号、机型一致
$PY tech_report.py      # 生成 md/csv 报告
```

规则要点：

- 陆军按档给，不再人人一战全套：P0/P1 才有 1919 栓动步枪+机枪+支援连+野炮+工兵；P2 步枪/机枪/工兵/野炮；P3 老步枪+少量野炮；P4 只有 1900 步枪（无炮/工兵/支援连/学说）
- 空军分 0/1914 小型/1914+1919 小型/中小型/全套（含飞艇）；无空军国家的 1919 机型的 `create_equipment_variant` 会被删掉，避免悬空引用
- 海军分无/1914 舰体/1919 舰体；少数国家因开局舰船型号需要额外保留 1923/1925 舰体科技
- OOB 里用到的兵种（山地、陆战、伞兵等）和装备会强制补上对应科技，避免开局部队造不出来
- 已顺手修复 `CAN - Canada.txt` 多出的一个 `}`（原文件括号不配对）

## 4. 欧洲开局部队（1919）

按 1919 年各国实际兵力配置欧洲各国 OOB，生成器 `eu_oob.py`：

- `KEEP`：手写且规模合理，保留不动（英、法、意、德、波、罗、保、希、南、巴伐利亚……）
- `KEEP` 另含俄国 148、立陶宛 28、高加索 30（按用户要求不削）
- `TARGET`：手写但超模的按目标师数删/补（瑞典 13→8、拿骚 9→2、比利时 0→6）
- 其余 53 个欧洲国家生成新 OOB `AOR_EU_<TAG>`，编制按科技档位：
  P0/P1 = 9 步兵+2 炮兵，P2 = 9 步兵，P3 = 6 步兵，P4 = 3 步兵（民兵师）
- 同时修掉了 `set_oob` / `load_oob` / `land_oob` 这类无效写法（法、意、丹、瑞典、南斯拉夫、乌克兰、奥地利原来因此**根本没有部队**）

```bash
$PY eu_oob.py          # 干跑
$PY eu_oob.py --apply  # 写入
$PY eu_oob_verify.py   # 校验引用/师数/模板
```
