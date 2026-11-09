# AOR 三军学说重制 · 策划案 v1

> 目标：把 `common/doctrines/` 下的陆/海/空学说改造成 1919–1930 年代版本，删除一切机械化/现代化内容，只对 AOR 实际存在的兵种给加成。
> 范围：只改学说系统（大学说/轨道/子学说）与配套本地化；**特种部队学说只做适配校验**。
> 参考：原版本体文件（本机有）＋ 一战REDUX / 英式和平（若提供文件夹则对照，否则按原版结构 + 史实重写）。

---

## 1. 现状盘点

| 军种 | 大学说 | 轨道（每个大学说 8 条） | 子学说文件 |
|---|---|---|---|
| 陆军 | 4：机动战、优势火力、决战计划、人海突击 | infantry / combat_support / **armor** / operations + 4 条 future_* | armor(983行) infantry(844) combat_support(721) operations(883) + future 3 个(约1800行) |
| 海军 | 3：存在舰队、破交、**基地打击** | submarines / screens / **carriers** / capital_ships + 4 条 future_* | capital(445) screen(473) carrier(372) submarine(401) + future 4 个(约1000行) |
| 空军 | 3：战略破坏、战场支援、作战完整性 | fighter / strike / medium / heavy + 4 条 future_* | 4 条基础线(约1300行) + 4 条 advanced 线(约1270行) |
| 特种部队 | 2：数量、质量 | special_forces_first / second | 821 行，结构可保留 |

合计约 **11,400 行** 子学说脚本，去重后约 **30 个文件**需要重写/删除。

---

## 2. 陆军方案

### 2.1 大学说
- **删除**：`new_mobile_warfare`（机动战）
- **保留**：`superior_firepower`（优势火力）、`grand_battleplan`（决战计划）、`mass_assault`（人海突击）

### 2.2 轨道：8 → 3
删除：`armor`、`future_infantry`、`future_combat_support`、`future_armor`、`future_operations`
保留：`infantry`、`combat_support`、`operations`

### 2.3 子学说逐条处置

**步兵轨道**（8 → 7）
| 子学说 | 处置 |
|---|---|
| `mobile_infantry` 机动步兵 | **删除**（机械化） |
| `defensive_postures` 防御姿态 | 保留，把 `category_vehicle_infantry` 改为 AOR 步兵类 |
| `large_unit_tactics` 大兵团战术 | 保留 |
| `assault_infantry` 突击步兵 | 保留，**删掉喷火坦克连加成**，改为突击队/工兵 |
| `commandos` 突击队 | 保留，目标改 `commando_units`、`aor_sniper_observer`、`aor_flame_support` |
| `irregulars` 游击 | 保留 |
| `peoples_war` 人民战争 | 保留 |
| `great_war_infantry` 大战步兵 | 保留，作为 1919 主力步兵加成 |

**战斗支援轨道**（8 → 6，删 5 个改 3 个）
| 子学说 | 处置 |
|---|---|
| `anti_tank_frontline` 反坦克前线 | **删除**（AOR 无反坦克前线体系） |
| `mobile_recon_and_assault` 机动侦察 | **删除** |
| `self_propelled_support` 自行式支援 | **删除** |
| `flying_batteries` 空中骑兵 | **删除** |
| `fire_concentration` 火力集中 | 保留并重写：加农炮连、榴弹炮连、野战炮连、重火力连 |
| `siege_artillery` 攻城炮 | 保留，目标改 1919 重炮（榴弹炮/加农炮），去掉筑垒强攻的现代描述 |
| `field_engineering` 野战工程 | 保留：工兵、战斗工兵、喷火支援、狙击观察 |
| **新增** 毒气支援 | 新子学说，目标 `aor_chemical_support` |
| **新增** 装甲支援 | 新子学说，目标 `aor_tank_support`、`aor_car_support` |
| **新增** 勤务保障 | 新子学说，目标 `field_hospital`、`maintenance_company`、`logistics_company`、`signal_company`、`aor_integrated_support` |

**作战轨道**（9 → 8）
| 子学说 | 处置 |
|---|---|
| `deep_battle` / `deep_battle_no_lar` 纵深战斗 | **删除**（装甲纵深） |
| `mission_type_tactics` | 保留，改目标 |
| `last_stand` | 保留 |
| `infiltration_tactics` | 保留 |
| `grand_assault` | 保留 |
| `guerilla_war` | 保留 |
| `rapid_domination` | 保留（改成步兵/炮兵快速突破） |
| `expeditionary_warfare` | 保留 |

### 2.4 加成覆盖原则（重要）
1. **只允许**给 AOR 里存在的兵种/支援连加加成（白名单来自 `common/units/` 扫描）。
2. 黑名单（出现即删）：`light_armor`、`medium_armor`、`heavy_armor`、`modern_armor`、`mechanized`、`rocket_artillery`、`sp_*`、`self_propelled`、`motorized`（保留少量骑兵/自行车）、`category_tanks`、`carrier`、`submarine`、`missile`、`strat_bomber_intercontinental`、`heavy_fighter` 等 1919 不存在的。
3. **覆盖面要求**：以下 AOR 兵种/连队必须至少出现在 2–3 个子学说里，不能只堆重火力连：
   - 步兵类：`infantry`、`assault_team`、`Stormtroopers`、`commando_units`、`Elite_infantry`、`marine`、`mountaineers`、`penal_battalion`、`irregular_infantry`、`militia`、`bicycle_battalion`
   - 骑兵类：`cavalry`、`camelry`
   - 炮兵类：`artillery`、`artillery_brigade`、`howitzer_brigade`、`anti_air_brigade`、`anti_tank_brigade`
   - 支援连：`engineer`、`recon`、`military_police`、`Machine_gun`、`field_hospital`、`maintenance_company`、`logistics_company`、`signal_company`、`aor_integrated_support`、`aor_tank_support`、`aor_car_support`、`aor_chemical_support`、`aor_sniper_observer`、`aor_flame_support`、`aor_armored_assault`
4. 每个子学说的加成数值参考原版同位置节点，按 1919 的小规模下调（一般 5%–10%，关键节点 15%）。

---

## 3. 海军方案

### 3.1 大学说
- **删除** `new_base_strike`（基地打击）
- **保留** `new_fleet_in_being`（存在舰队）、`new_convoy_raiding`（破交）

### 3.2 轨道：8 → 2
删除：`carriers`、`submarines`、`future_carriers`、`future_submarines`、`future_screens`、`future_capital_ships`
保留：`capital_ships`、`screens`

### 3.3 子学说重写（1919–1930）
**主力舰轨道**：战列线、战列巡洋、重炮校射、装甲与损管、夜战与探照灯、舰队决战
**屏卫舰轨道**：护航、驱逐雷击、轻巡侦察、水雷战、反潜（1919 有潜艇，作为屏卫的反潜任务保留，但**不再有潜艇自身分支**）、海岸防御

目标单位全部用 1919 船型（battleship / battle_cruiser / heavy_cruiser / light_cruiser / destroyer / 水雷），删除航母、雷达、导弹、现代舰体相关效果。

---

## 4. 空军方案（重设计）

### 4.1 大学说
保留 3 个：战略破坏、战场支援、作战完整性。

### 4.2 轨道：8 → 4（2 飞机 + 2 飞艇）
| 轨道 | 内容 |
|---|---|
| `fighter_aircraft` | 飞机·战斗机线（战斗机、侦察机） |
| `bomber_aircraft` | 飞机·轰炸线（CAS、战术、战略、海攻合并） |
| `blimp` | 软式飞艇线 |
| `rigid_airship` | 硬式飞艇线 |

删除全部 `future_*` 轨道与 advanced_* 文件中的现代内容。

### 4.3 子学说草案（每轨道 4–5 个）
- **战斗机**：本土防空、护航、制空争夺、王牌战术、截击
- **轰炸机**：战场支援（CAS）、战术轰炸、战略轰炸、海上攻击、夜间轰炸
- **软式飞艇**：前线侦察、海上巡逻、反潜巡逻、夜间袭扰
- **硬式飞艇**：远程侦察、战略轰炸、舰队伴随、运输补给

### 4.4 目标单位
- 飞机：`category_fighter`、`category_cas`、`category_tac_bomber`、`category_strat_bomber`、`category_nav_bomber`、`category_scout_plane`
- 飞艇（用**具体单位 id**，避免和飞机串味）：`airship`、`aor_blimp_naval_bomber`、`aor_blimp_maritime_patrol_plane`；`rigid_airship`、`aor_rigid_naval_bomber`、`aor_rigid_maritime_patrol_plane`、`airship_bomber`

### 4.5 平衡
飞艇在 AOR 是早期单位（1914–1921），两条飞艇线给侦察/巡逻/轰炸的**低成本、中等收益**，避免出现「飞艇吊打战斗机」；数值沿用原版百分比但压低 30% 左右。

---

## 5. 特种部队
- 结构不动（2 大学说 × 2 轨道）
- 只做适配：校验效果引用的 `ranger_battalion`、`mountaineers`、`marine`、`paratrooper`、`pioneer_support`、`marines_commandoes` 是否都在 AOR 存在，不存在的删掉；补上 AOR 特有的 `aor_sniper_observer`、`aor_flame_support` 等。

---

## 6. 实施步骤

1. 建分支 + 备份 `common/doctrines/`
2. 用脚本生成「AOR 兵种/分类白名单」（`common/units/` 扫描）
3. 按 陆 → 海 → 空 → 特战 顺序重写文件（保留 doc 与目录结构）
4. 写校验脚本：
   - 所有效果键 ⊆ 白名单
   - 无黑名单关键词（装甲/机械化/航母/潜艇/导弹/未来）
   - 每个大学说的 tracks 引用存在
   - 每个轨道至少 3 个子学说可选
5. 补本地化：新子学说/大学说的中英文 key（`SUBDOCTRINE_*`、`GRAND_DOCTRINE_*`）
6. 游戏内测试：开局学说面板、XP 购买、AI 是否正常、特种部队不报错
7. 提交（分类：学说）

**预计改动**：重写/新建约 20 个文件、删除约 14 个文件、新增本地化约 60 条 key。

---

## 7. 风险

- **删大学说** → 老存档兼容性（读档可能报缺学说）
- AI 的 `ai_will_do` 需要重新配平，否则 AI 乱点
- 飞艇线若飞艇科技不给力，玩家会觉得鸡肋 → 可考虑给飞艇线少量「解锁飞艇单位」的联动（另议）
- 删掉装甲/机械化后陆军整体变弱，需要靠步兵/炮兵加成补回来
- 原版/参考模组的数值不能直接照搬（时代不同），要统一缩放

---

## 8. 需要你确认的 4 件事

1. **旧科技树里的学说科技**：`common/technologies/land_doctrine.txt` 里还有 `mobile_warfare`、`trench_warfare` 等 64 个旧学说科技，而且国家历史里还在 `set_technology` 给它们。这次要不要一并删掉/替换？（现在游戏里的学说界面用的是新系统，旧科技可能是摆设）
2. **参考模组**：已收到路径并调研（见文末第 9 节）。
3. **飞艇两条线的定位**：软式=侦察/巡逻、硬式=轰炸/远程，这样分行不行？
4. **数值尺度**：沿用原版百分比（5-15%）还是整体再压低/提高？


---

## 9. 参考模组调研（一战 3365515312 / PB 3780154583）

### 9.1 一战模组（The Great War）
- **陆军多一个大学说：`industrial_warfare`（工业战）**，轨道正好是 3 条：`ww1_infantry` / `ww1_combat_support` / `ww1_operations`（无装甲轨道）——和这次要的「无机械化」形状完全一致。
- 它的 7 个时代专属子学说（可直接借鉴/改写）：
  - 战斗支援：`methodical_fire`（有计划的火力）、`integrated_firepower`（整合火力）、`hurricane_bombardment`（飓风炮击）
  - 步兵：`bite_and_hold`（咬住并坚守）、`defense_in_depth`（纵深防御）
  - 作战：`methodical_battle`（有条不紊的战斗）、`attack_in_position_warfare`（阵地进攻）
- 海军仍是 3 大学说 × 4 轨道（潜艇/屏卫/航母/主力舰），只是子学说内容改成了战列巡洋舰/海岸防御口径；空军仍是原版 4 轨（无飞艇分支）。
- 有独立本地化文件 `ww1_doctrines_l_english.yml`，可参照命名与描述风格。

### 9.2 PB 模组
- 4 个陆军大学说只是改名（Supremacy of Steel / Fire and Fury / Architecture of War / Supremacy of Flesh），轨道仍是原版 4 条（含装甲），没有时代专属内容；空军/海军也基本是原版结构。
- 结论：PB 主要可借鉴**大学说命名与风味**，机制上参考价值不大。

### 9.3 对策划案的调整建议
1. **强烈建议**把一战的 `industrial_warfare`（工业战）作为第 4 个大学说保留（3 轨道、无装甲），比「只有 3 个大学说」更贴 1919；若坚持 3 个，则把它的 7 个子学说并入优势火力/决战计划/人海突击的共享池。
2. 陆军子学说优先抄一战的 7 个时代节点，再补 AOR 特色（毒气连/装甲连/重火力连/狙击/喷火等）。
3. 空军飞艇双轨、海军删航母/潜艇：参考模组都没有现成方案，按本策划案自行设计。
