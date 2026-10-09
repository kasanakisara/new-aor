# 终身护民党：SPD 报纸决议 GUI

## 游戏内查看

选择 GER（德意志共和国），打开决议列表，展开 **终身护民党**。
报纸使用原始的 480×720 底图，GUI 容器为 500×730，放在决议类别内部并随决议列表滚动。
不需要额外的 DLC。

新游戏初始值：左派 17%、中派 43%、右派 40%。旧存档最迟在下一个游戏日补齐初始化；已有支持度不会重置。
新增 GUI、GFX、脚本后建议完整重启游戏再载入存档。

## 布局与提示

- 四列，每列 25 行，共 100 行。按第一列从上到下，再向右逐列编号。
- 左派红色、中派使用 center2.png 的深棕色、右派蓝色；每行代表 1 个百分点。
- 第 1–17 行红色，第 18–60 行深棕色，第 61–100 行蓝色。
- 每一行只显示一个派系的图层，整行区域可以触发该派系的提示。
- 提示先显示支持度和派系介绍，再显示两位代表人物的头像、姓名及黄色职务标注。介绍正文直接位于 GER_SPD_*_tooltip 中，不依赖末尾的嵌套引用；头像顺序与下面的姓名顺序一致。
- 支持度为零的派系没有对应文字行，因此不会有该派系的行悬浮提示。

底图和标题直接引用用户素材。文字行从 left.png、center2.png、right.png 的透明通道中识别并切出原有 25 行，按同一横向比例缩放，保留每一行的长短和字块形状。
上一版误把预览中的 RGB 色块当成完整图像，只采色重画横条；现已改为直接使用原素材字形。

## 动态标题与音效

三派都不超过 60% 时显示 title.png；某派严格超过 60% 时显示对应标题。支持度回落到 60% 或以下时恢复默认标题。

| 状态 | 图片（gfx/interface/SPD_GUI/） | 悬浮翻译 |
| --- | --- | --- |
| 默认 | title.png | 总罢工！ |
| 左派 > 60% | title_left.png | 革命尚未结束！ |
| 中派 > 60% | title_center.png | 为了社会主义！ |
| 右派 > 60% | title_right.png | 保卫共和！ |

检查时 title_center.png 已存在并直接接入；title_right.png 暂时是默认标题的原样占位副本，避免引用缺失。美工完成后覆盖同名文件即可，生成脚本不会覆盖已有标题。
标题位置统一为 x=23、y=189，建议画布为 453×93；当前 title_left.png 为 465×88，也在报纸范围内。
标题中文翻译为 GER_SPD_headline_*_tooltip，派系介绍为 GER_SPD_*_description，位于报纸本地化文件。

报纸底图改为无动作的静音按钮，用于拦截原先透传到决议类别背景上的点击；最外层窗口也明确使用空点击音效。标题、文字行保留悬浮提示。

## 调整整个 GUI 的 X/Y

打开 interface/GER_SPD_newspaper.gui，找到最外层 GER_SPD_newspaper_window 下的第一条 position：

```text
name = "GER_SPD_newspaper_window"
position = { x = 20 y = 0 }
```

- x 增大向右，减小向左；y 增大向下，减小向上，单位为 GUI 像素。
- 例如改成 `position = { x = 10 y = -20 }`，整张报纸向右 10、向上 20。
- 只调整最外层 position，底图、标题、100 行文字和悬浮区域会一起移动。
- 各个 iconType 内的 position 只控制对应元素相对报纸容器的位置。
- size 控制容器大小及裁切范围，不会缩放图片；移动后需检查决议栏边界，以及报纸与下方决议的间距。

## 游戏内测试决议

common/decisions/GER_SPD_newspaper_test_decisions.txt 在本类别的报纸下方添加十个测试决议。
展开类别后向下滚动即可看到。

决议组横幅来自 gfx/interface/decisions/decision_GER_SPD.png（503×125）。
决议组使用原生 picture 显示横幅。interface/countrydecisionview.gui 的 short_text 设置为 x=14、y=134、宽 470，使带图片的决议组说明从图片下方按整栏宽度显示。
Build-Assets.ps1 从原图生成的 470×117 的 gfx/interface/decisions/decision_GER_SPD_inline.png 目前未被决议组使用；原图不被改动。
决议组说明固定显示 GER_SPD_lifelong_tribune_category_short_desc。长文保留在本地化文件的注释中；报纸底部不再重复显示短引言。

报纸左下角的石竹花显示 GER_SPD_unity 党内团结度，初始为 65%。0–29 使用 Landnelke_decay_1，30–59 使用 Landnelke_decay，60–100 使用 Landnelke_bloom。每 10 个百分点更新一次政治点数、指挥点数和每周稳定度修正；50% 为零点。其他事件或国策修改该变量后调用 GER_SPD_refresh_unity_effect = yes，直接改变量也会在每日检查中刷新。GER_SPD_unity_test_decisions.txt 提供 0、30、50、60、100 的测试决议。

石竹花右侧的 SPD_history.png 按钮切换党的过往焦点窗口。该窗口是独立的 player_context 窗口，不设置 parent_window_name；屏幕坐标为 x=544、y=121，紧贴决议窗口右边。窗口使用独立滚动容器；每个事件在 interface/GER_SPD_history.gui 中有独立的 entry 容器，标题、引文和正文分别使用 localisation/simp_chinese/GER_SPD_newspaper_l_simp_chinese.yml 中的三个本地化键。增加事件时复制一组 entry，修改年份与 y 坐标，并补齐三个本地化键。

- 三派两两互相转移，共六个方向，每次转移 5 个百分点。
- 转出方不足 5% 时按钮不可用，第三派保持不变。
- 一键恢复初始的左 17%、中 43%、右 40%。
- 左、中、右派各有一个“影响力设为 100%”按钮，另外两派同时归零，并立即刷新文字及标题；可直接用于检查三种派系标题和全色版面。
- 免费、可重复点击，无冷却；仅玩家 GER 可见，AI 不会执行。
- 点击后立即调用支持度刷新效果，合计始终为 100%。

## 调整支持度

在 **GER 国家作用域**中修改以下三个国家变量：

| 变量 | 含义 |
| --- | --- |
| GER_SPD_left_support | SPD 左派支持度 |
| GER_SPD_center_support | SPD 中派支持度 |
| GER_SPD_right_support | SPD 右派支持度 |

示例（事件、国策或决议效果）：

```text
GER = {
    set_variable = { GER_SPD_left_support = 52 }
    set_variable = { GER_SPD_center_support = 23 }
    set_variable = { GER_SPD_right_support = 25 }
    GER_SPD_refresh_support_effect = yes
}
```

示例：从右派向左派转移 5 个百分点，先确保右派至少有 5 点：

```text
GER = {
    if = {
        limit = { NOT = { check_variable = { GER_SPD_right_support < 5 } } }
        add_to_variable = { GER_SPD_left_support = 5 }
        add_to_variable = { GER_SPD_right_support = -5 }
        GER_SPD_refresh_support_effect = yes
    }
}
```

刷新效果将负数归零，再按三派比例分配 100 个整数百分点。
小数采用最大余数分配，相同余数时依次优先左、中、右；三个输入均为零时恢复 17/43/40。
已是合计 100 的非负整数不会改变。提示数值和行数读取同一组整数。
刷新后更新 GUI 的 dirty 变量，暂停时由事件调用也可刷新。
直接修改变量而漏掉刷新调用时，每日检查会补做一次刷新。

不要把农业系统的 GER_SPD_support 接到这里：它代表 SPD 整党的支持度，不是党内三派比例。
测试决议与现有事件、国策效果独立。

## 后续替换人物信息

提示本地化：
localisation/simp_chinese/GER_SPD_newspaper_l_simp_chinese.yml

三派分别有 GER_SPD_left_tooltip、GER_SPD_center_tooltip、GER_SPD_right_tooltip。
左派：罗莎·卢森堡（斯巴达克斯派）、格奥尔格·雷德布尔（雷德布尔集团）。
中派：奥古斯特·倍倍尔（党主席）、胡戈·哈泽（代理党主席，代理倍倍尔）。
右派：菲利普·谢德曼（执行委员会秘书）、弗里德里希·艾伯特（党主席）。
所有职务/派别后缀使用 §Y 黄色文字；三派介绍根据《德意志共和国情况简报，2026.6.13，浅光》编写，分别使用 GER_SPD_left_description、GER_SPD_center_description、GER_SPD_right_description。
六张头像精灵在 interface/GER_SPD_newspaper.gfx 中直接引用 gfx/leaders/GER 的原图。
倍倍尔使用当前国家领袖配置中的 August_Bebel_2.png。

## 素材与离线预览

```powershell
powershell -ExecutionPolicy Bypass -File tools/ger_spd_newspaper/Build-Assets.ps1
```

这个脚本读取原始 PNG，生成文字图集与预览（缺少中/右派标题时另建立占位副本）：
- gfx/interface/SPD_GUI/generated/rows_left.png
- gfx/interface/SPD_GUI/generated/rows_center.png
- gfx/interface/SPD_GUI/generated/rows_right.png
- gfx/interface/SPD_GUI/generated/leader_placeholder.png
- tools/ger_spd_newspaper/preview.png

每张文字图集有 25 个横向帧，每帧 110×12 像素。
预览读取实际 GUI 中的位置、帧号、GFX 引用及脚本初始值进行排版，不是游戏截图。

## 已完成的检查

- 解析本次六个 GUI/GFX/游戏脚本文件，检查括号、元素名、图片引用和本地化引用。
- 对全部 5,151 组非负整数、合计 100 的分布检查 100 行：无缺行、无叠色，三派行数与支持度相等。
- 执行脚本效果的离线解释检查：初始 17/43/40、保留已有 52/23/25、零值、单派 100%、负数和小数分配。
- 按实际布局生成并查看预览。

尚未运行游戏引擎验证。进游戏重点确认类别高度、滚动裁切和头像悬浮框排版。
