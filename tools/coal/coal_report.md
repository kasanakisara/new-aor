# AOR 煤炭分布（1919）

按原版 HOI4 `history/states` 的煤炭密度，用**省份插值**重算到 AOR 的州；再整体 ×1.5（1919 年煤炭仍是主要能源）。

## 总览

- 有煤州：**216** / 1127（原版 153 个）
- 全球煤总量：**2217**（原版 1463，×1.52）
- 单州最高：240（360-Pennsylvania.txt）
- 单州中位：3
- 计算方法：`state_coal = round(1.5 * Σ(原版所属州煤量 / 该州省份数))`，基础值 ≥0.4 的州至少 1 煤；原有手工煤值取较大者

## 分国家（按新煤量）

| 国家 | 煤 | 州数 |
| --- | ---: | ---: |
| USA | 671 | 27 |
| ENG | 340 | 14 |
| GER | 280 | 24 |
| CHI | 130 | 20 |
| FRA | 72 | 7 |
| JAP | 71 | 11 |
| ARU | 51 | 4 |
| ARR | 50 | 2 |
| CHT | 49 | 1 |
| RAJ | 44 | 5 |
| BNL | 37 | 3 |
| GML | 34 | 7 |
| CZE | 32 | 3 |
| RUS | 31 | 4 |
| AST | 29 | 3 |
| CAN | 28 | 5 |
| SAF | 26 | 2 |
| SPR | 25 | 5 |
| DON | 25 | 1 |
| HUN | 23 | 6 |
| BRA | 15 | 3 |
| MXS | 13 | 4 |
| TUR | 11 | 4 |
| GCL | 11 | 2 |
| AUS | 10 | 3 |

## 前 25 个煤州

| ID | 州 | 国家 | 煤 |
| ---: | --- | --- | ---: |
| 360 | 360-Pennsylvania.txt | USA | 240 |
| 816 | 816-West Virginia.txt | USA | 132 |
| 369 | 369-Kentucky.txt | USA | 84 |
| 122 | 122-Wales.txt | ENG | 83 |
| 130 | 130-Yorkshire.txt | ENG | 77 |
| 395 | 395-Illinois.txt | USA | 51 |
| 51 | 51-Moselland.txt | GER | 50 |
| 132 | 132-North-west England.txt | ENG | 50 |
| 200 | 200-Rivne.txt | CHT | 49 |
| 762 | 762-Katowice.txt | GER | 48 |
| 29 | 29-Pas de Calais.txt | FRA | 45 |
| 133 | 133-Strathclyde.txt | ENG | 44 |
| 850 | 850-Cologne.txt | GER | 42 |
| 67 | 67-Oberschlesien.txt | GER | 38 |
| 131 | 131-Northern England.txt | ENG | 35 |
| 622 | 622-Yulin.txt | CHI | 30 |
| 227 | 227-Stalino.txt | ARR | 25 |
| 228 | 228-Taganrog.txt | ARR | 25 |
| 1069 | 1069-truetaganrog.txt | DON | 25 |
| 219 | 219-Moscow Area.txt | RUS | 24 |
| 578 | 578-Siberia 5.txt | ARU | 24 |
| 435 | 435-Bihar.txt | RAJ | 23 |
| 1025 | 1025-Kitakyuushuu.txt | JAP | 23 |
| 621 | 621-Suiyuan.txt | CHI | 22 |
| 275 | 275-South Africa.txt | SAF | 21 |

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