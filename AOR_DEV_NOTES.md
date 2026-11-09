# AOR 开发笔记（给 AI 和人类看的记忆文件）

> 位置：仓库根目录。每次接手任务先读这个文件；做完事记得回来更新。
> 项目：D:\new-aor（HOI4 1919 年模组，游戏本体在 D:\SteamLibrary\steamapps\common\Hearts of Iron IV）

## 0. 工作约定

- 用 Python：`C:/Users/pc/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe`
- 脚本都在 `tools/coal/`，报告也在那里（coal_report.md / tech_report.md 等）
- git：仓库 blob 是 LF、工作区是 CRLF，提交前先把要提交的文件转成 LF，否则 diff 会整文件重写
- 用户自己的工作区改动（interface/*.gfx、descriptor.mod 等）不要动
- 提交按分类：科技 / 部队 / 海军 / 番号 / 内容 / 工具

## 1. 已完成

### 1.1 煤炭分布（1919）
- 按原版州煤炭密度插值到省份，再 ×1.3：216 个州有煤，总量 1914（原版 1463）
- 脚本：parse_both.py → build_plan.py → apply_coal.py → verify.py → make_report.py
- 调参：build_plan.py 顶部 `SCALE`

### 1.2 1919 开局科技（除德国）
- 五档 + 二线档：P0 列强 / P1 工业国 / P1B 二线 / P2 地区 / P3 小国 / P4 殖民地
- 规则（当前版本）：
  - 只有 P0/P1 有：基础机床、建筑技术、速射野战加农炮、支援连科技（支援装备/工兵/侦察/宪兵/机枪/野战医院/列车）
  - P1B/P2：只有铁路工程（`aor_railway_engineering`），无支援连、无 1919 火炮
  - P3/P4：无工业科技；P3 有 1900 野战炮，P4 只有步枪
  - 海军：**所有人 0 项海军科技**
  - 空军：P0 只给 1914+1919 小型/中型；P1 小型；P1B/P2/P3 仅 1914 小型；P4 无
  - 学说：陆/海/空各给根节点（海军学说已随海军科技取消）
- 当前科技数：英 48 / 美 47 / 日 46 / 法 46 / 意 45 / 俄 43；波 38；土 23；中 19；阿 7；埃塞 2
- 脚本：tech_inventory.py → country_analysis.py → oob_needs.py → tech_write.py → tech_finalize.py → tech_verify.py → tech_report.py
- 档位定义：tools/coal/tech_profiles.py（科技组）+ tech_gen_common.py（国家分档、LAND_BY_TIER、DEFAULT_AIR/NAVY）

### 1.3 欧洲开局部队
- 手写保留：英、法、意、德、波、罗、保、希、南、俄 148、立陶宛 28、高加索 30
- 调整：瑞典 13→8、拿骚 9→2、比利时 0→6
- 53 国生成 AOR_EU_<TAG> 编制（30% 首都 + 边境省份，边境用 provinces.bmp 颜色解码求邻接）
- 脚本：eu_oob.py、spread_units.py、fix_unit_locations.py、eu_oob_verify.py
- **坑**：country history 的 `capital = N` 是**州 ID**，不是省 ID！落点要取「首都州里 VP 最高的省」

### 1.4 欧洲海军
- 英/法/日/美：舰队保留，装备全部降级到 1914 一级（battleship_2/3→battleship_1 等），去掉旧舰级名
- 意大利原来挂空的 1936 海军文件 → 生成 1919 舰队（6 战列/3 重巡/4 轻巡/12 驱逐/10 潜艇）
- 新增：西班牙、荷兰、瑞典、挪威、葡萄牙、希腊、土耳其、比利时、全俄政府、苏俄
- 脚本：tools/coal/eu_navies.py

### 1.5 兵种分组（编成界面）
- `artillery_brigade`：group=combat_support + 补回 `is_artillery_brigade = yes`（AOR 删掉了这个字段，导致改组后 OOB 报 Invalid subunit）
- `howitzer_brigade`：group=combat_support + 同样补 is_artillery_brigade
- `anti-air_brigade` / `anti_tank_brigade`：group=combat_support
- `cavalry`：`aor_inf_r01` 里 `enable_subunits = { infantry cavalry }` 解锁（active 保持 no，直接 active=yes 会刷 229 条错误）

### 1.6 删除陆地巡洋舰支援连
- 覆盖 `common/units/land_cruiser.txt`（active=no）
- 覆盖 `common/special_projects/projects/land_projects.txt`（sp_land_land_cruiser 的 allowed = always = no）

### 1.7 部队番号组
- 新文件 `common/units/names_divisions/AOR_generic_names_divisions.txt`
  - 通用：AOR_GEN_INF 步兵师 / AOR_GEN_CAV 骑兵师 / AOR_GEN_MTN 山地师 / AOR_GEN_ASL 突击部队 / AOR_GEN_MAR 海军陆战队，各 123 个（第一步兵师…第一百二十三步兵师）
  - 德国：AOR_GER_INF，80 个词（第一“革命”步兵师…），仅 GER
- 模板绑定：德国 OOB 修正错用的 SPAN_INF_02/03；127 个没番号组的模板按兵种绑定通用组（79 个文件）
- 脚本：tools/coal/aor_name_groups.py（词库在 tools/coal/ger_names.txt，来自桌面 docx）

## 2. HOI4 踩坑记录

- 部队实例名（OOB `name =`）**不走本地化**，写 key 会直接显示 key；编制模板名（division_template 的 name）**走本地化**（已验证）
- 番号组（names_divisions）里的名字也不走本地化 → 直接写中文
- 本地化 key 不能带空格（`Infantry Division:0` 会报 Expected colon）
- 改 `common/units` 里兵种的 `group` 时，注意原版字段（is_artillery_brigade 等）是否被 AOR 删了
- 地图 provinces.bmp 是**颜色编码**：id 从 map/definition.csv 的 r/g/b 列反查，不是直接 RGB 数值
- 改完 OOB 记得检查落点是否为 land province（definition.csv 第 5 列）

## 3. 待办 / 可继续

- 法国特色番号组（需要词库，格式同德国）
- 其他大陆的部队/海军（目前只做了欧洲）
- 剩余未提交：用户自己的 interface gfx 等改动
- 若用户要求继续削：可考虑空军 1914 小型机、学说根节点

## 4. 常用命令

```bash
PY="C:/Users/pc/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe"
$PY tools/coal/tech_write.py --apply      # 重写全部国家科技
$PY tools/coal/tech_finalize.py --apply   # 清理空 if / 杂字符
$PY tools/coal/tech_verify.py             # 校验
$PY tools/coal/eu_oob.py --apply          # 欧洲部队
$PY tools/coal/spread_units.py --apply    # 部队分散
$PY tools/coal/eu_navies.py --apply       # 欧洲海军
$PY tools/coal/aor_name_groups.py --apply # 番号组
```
