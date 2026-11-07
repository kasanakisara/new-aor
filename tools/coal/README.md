# AOR 煤炭分布工具（1919）

依据原版 `history/states` 的煤炭，按**省份**插值到 AOR 的州，再整体缩放。

## 结果

- 有煤州 216 / 1127，全球煤 2217（原版 1463，×1.52）
- 逐州清单：[coal_states.csv](coal_states.csv)；汇总：[coal_report.md](coal_report.md)
- 改动已提交（commit `煤炭`）；要回退用 git 即可

## 流程

```bash
PY="C:/Users/pc/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe"
$PY parse_both.py      # 解析原版+AOR 州，生成 data.json（含每省煤密度）
$PY build_plan.py      # 生成 plan.json（插值 + 缩放 + 取整）
$PY apply_coal.py      # 干跑看 diff；加 --apply 写入（先备份到 backup/）
$PY verify.py          # 校验：煤值、括号、其余内容未被改动
$PY make_report.py     # 重新生成 md/csv 报告
```

## 调参

- `build_plan.py` 顶部：`SCALE = 1.3`（1919 加成）、`MIN_BASE = 0.4`（有煤门槛，低于此记 0）
- 取整规则：`round(SCALE * Σ(原版州煤量 / 该州省份数))`；原文件已有手工煤值则取较大者（Saar 州 7、Perm 1 保留）
- 想重来：先 `git checkout -- history/states`，改 `SCALE` 后再 `build_plan.py` + `apply_coal.py --apply`
