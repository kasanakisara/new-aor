# AOR 煤炭分布（1919）

按原版 HOI4 `history/states` 的煤炭密度，用**省份插值**重算到 AOR 的州；再整体 ×1.3（1919 年煤炭仍是主要能源）。

## 总览

- 有煤州：**216** / 1127（原版 153 个）
- 全球煤总量：**1914**（原版 1463，×1.31）
- 单州最高：208（360-Pennsylvania.txt）
- 单州中位：3
- 计算方法：`state_coal = round(1.3 * Σ(原版所属州煤量 / 该州省份数))`，基础值 ≥0.4 的州至少 1 煤；原有手工煤值取较大者

## 分国家（按新煤量）

| 国家 | 煤 | 州数 |
| --- | ---: | ---: |
| USA | 581 | 27 |
| ENG | 292 | 14 |
| GER | 245 | 24 |
| CHI | 114 | 20 |
| FRA | 64 | 7 |
| JAP | 59 | 11 |
| ARU | 45 | 4 |
| CHT | 43 | 1 |
| ARR | 42 | 2 |
| RAJ | 39 | 5 |
| BNL | 33 | 3 |
| GML | 30 | 7 |
| CZE | 29 | 3 |
| RUS | 27 | 4 |
| AST | 26 | 3 |
| CAN | 23 | 5 |
| HUN | 22 | 6 |
| SPR | 22 | 5 |
| SAF | 22 | 2 |
| DON | 21 | 1 |
| BRA | 12 | 3 |
| MXS | 10 | 4 |
| GCL | 9 | 2 |
| AUS | 8 | 3 |
| TUR | 8 | 4 |

## 前 25 个煤州

| ID | 州 | 国家 | 煤 |
| ---: | --- | --- | ---: |
| 360 | 360-Pennsylvania.txt | USA | 208 |
| 816 | 816-West Virginia.txt | USA | 114 |
| 369 | 369-Kentucky.txt | USA | 73 |
| 122 | 122-Wales.txt | ENG | 72 |
| 130 | 130-Yorkshire.txt | ENG | 66 |
| 395 | 395-Illinois.txt | USA | 44 |
| 51 | 51-Moselland.txt | GER | 43 |
| 132 | 132-North-west England.txt | ENG | 43 |
| 200 | 200-Rivne.txt | CHT | 43 |
| 762 | 762-Katowice.txt | GER | 42 |
| 29 | 29-Pas de Calais.txt | FRA | 39 |
| 133 | 133-Strathclyde.txt | ENG | 38 |
| 850 | 850-Cologne.txt | GER | 36 |
| 67 | 67-Oberschlesien.txt | GER | 33 |
| 131 | 131-Northern England.txt | ENG | 30 |
| 622 | 622-Yulin.txt | CHI | 26 |
| 219 | 219-Moscow Area.txt | RUS | 21 |
| 227 | 227-Stalino.txt | ARR | 21 |
| 228 | 228-Taganrog.txt | ARR | 21 |
| 578 | 578-Siberia 5.txt | ARU | 21 |
| 1069 | 1069-truetaganrog.txt | DON | 21 |
| 435 | 435-Bihar.txt | RAJ | 20 |
| 1025 | 1025-Kitakyuushuu.txt | JAP | 20 |
| 621 | 621-Suiyuan.txt | CHI | 19 |
| 275 | 275-South Africa.txt | SAF | 18 |

## 各州分类

- rural: 65
- town: 51
- city: 37
- large_city: 18
- large_town: 14
- metropolis: 8
- pastoral: 8
- megalopolis: 5
- wasteland: 5
- enclave: 3
- (none): 1
- small_island: 1

完整逐州清单见 `coal_states.csv`。修改前的原始文件备份在 `backup/`。