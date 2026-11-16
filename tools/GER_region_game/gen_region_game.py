# -*- coding: utf-8 -*-
"""
地区博弈地图 GUI 生成脚本（AOR / GER）

读取美术素材文件夹里的 14_素材清单.json、16_区块素材清单.json、区块_12帧/region_fill_frames.json、
右侧面板素材/素材清单.json：
  1. 把素材原样（逐字节）复制到 gfx/interface/GER_region_game/（面板素材在 panel/），文件名改成英文；
     地区照片从 gfx/interface/GER_region_game/photos/<区块id>.png 读，拼成 panel/region_photos_16f.png；
  2. 生成 interface/GER_region_game.gfx、interface/GER_region_game.gui、
     common/scripted_guis/GER_region_game.txt 里的重复部分；
  3. 生成 common/scripted_effects/GER_region_game_effects.txt、
     测试决议和本地化。

.gfx / .gui / scripted_gui 三个文件：只有在文件不存在时才按模板整份写出；
文件已存在时，只替换「# >>> GENERATED: xxx」与「# <<< GENERATED: xxx」之间的内容，
标记外面手写的部分（右侧面板等）不会被覆盖。
其余文件（scripted_effects、测试决议、本地化）整份由脚本生成。

用法：
    python tools/GER_region_game/gen_region_game.py [素材文件夹]
需要 Pillow（把 2 帧点击条拼成 3 帧、拼照片条带）：python -m pip install pillow
其余素材逐字节复制。
"""
import json
import os
import re
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", ".."))
SRC = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\DONG\Desktop\AOR资料\地区博弈_美术素材"

GFX_DIR_REL = "gfx/interface/GER_region_game"
GFX_DIR = os.path.join(MOD, *GFX_DIR_REL.split("/"))

CANVAS_W, CANVAS_H = 1248, 813

# ---------------------------------------------------------------- 窗口布局
WIN_W, WIN_H = 1616, 893
MAP_X, MAP_Y = 16, 64

# 区块帧号（12 帧，见 区块_12帧/region_fill_frames.json）。state 就是帧号，sync 原样拷贝。
#   1 斜线  2 中立/摇摆  3 左派核心  4 右派核心  5 魏玛联盟核心  6 特殊(绿)  7 备用(紫)
#   8 左派控制  9 右派控制  10 魏玛联盟控制  11 特殊控制(绿)  12 备用控制(紫)
REGION_FRAMES = 12
CORE_FRAMES = {3: "left", 4: "right", 5: "weimar", 6: "green"}        # 面板上显示核心区方块的帧
TYPE_NAMES = {2: "摇摆区", 3: "左派核心区", 4: "右派核心区", 5: "魏玛联盟核心区", 6: "特殊区",
              8: "左派控制区", 9: "右派控制区", 10: "魏玛联盟控制区", 11: "特殊控制区"}   # 名称框右侧的地区类型（修改说明第 3、12 节）

# 右侧面板素材（修改说明_右侧面板.md）
PANEL_SRC = "右侧面板素材"
REGION12_SRC = "区块_12帧"
PANEL_DIR_REL = GFX_DIR_REL + "/panel"
PANEL_DIR = os.path.join(MOD, *PANEL_DIR_REL.split("/"))
PHOTO_DIR_REL = GFX_DIR_REL + "/photos"     # 用户交的地区照片：photos/<区块id>.png，425x157（放中文地区名如 大柏林.png 也行，运行时自动改成区块id名）
PHOTO_IDLE = "idle"                         # 待机照片 photos/idle.png（放 待机.png 也行，自动改名）：没选中地区时显示
PHOTO_IDLE_CN = "待机"
PHOTO_BG = (25, 27, 25, 255)                # 没交照片的地区：与照片框内底同色的深色占位

# 领导人（策划案第 8 页）。portrait = 模组里现成的 156x210 头像，没有就写 None（只显示名字）。
# 名字和悬停介绍写在 HAND_PANEL_LOC 里，这里的中文名只用来第一次补占位。
# 顺序 = GER_region_Rxx_leader 的取值（1 起），以后只往后加，不要插队。
LEADERS = [
    ("daeumig", "恩斯特·多伊米希", "gfx/leaders/GER/Ernst_Daeumig.png"),
    ("dissmann", "罗伯特·迪斯曼", "gfx/leaders/GER/Robert_Dissmann.png"),
    ("henke", "阿尔弗雷德·亨克", None),
    ("koenen", "威廉·科嫩", "gfx/leaders/GER/Wilhelm_Koenen.png"),
    ("lipinski", "罗伯特·利平斯基", None),
    ("committee_nine", "九人委员会", None),
    ("paul_dittmann", "保罗·迪特曼", None),
    ("otto_braun", "奥托·布劳恩", "gfx/leaders/GER/Otto_Braun.png"),
    ("paul_hirsch", "保罗·希尔施", None),
    ("weimar_coalition", "魏玛联盟", None),
    ("bitta", "约瑟夫·比塔", None),
    ("bebel", "奥古斯特·倍倍尔", "gfx/leaders/GER/August_Bebel.png"),   # 待机（没选中地区）时显示
    # 巴伐利亚危机阶段的巴伐利亚领导人（无效果）。头像还没做：做好后放到下面的路径（156x210），重跑脚本就会显示
    ("hoffmann", "约翰内斯·霍夫曼", "gfx/leaders/GER/Johannes_Hoffmann.png"),
]
IDLE_LEADER = "bebel"
# 领导人效果（用户给的清单；「武装力量」一律改成控制度）。只在该领导人所在的区块已开放时生效。
# 地区本地的（该地区控制度 / 支持度、该地区的州修正）按地区各算一份；
# 全国的（SPD 派别支持度、稳定度、党内团结度、议会协商惯性、全国修正）每位领导人只算一份，带几个地区都一样。
#   local_bw  [(control/support, 值)]      每两周（全国统一的两周结算日）
#   state     [(州修正, 值, 名字)]          该地区里归德国所有的州
#   country   [(国家修正, 值, 名字)]
#   daily     [(种类, 值)]  left/center/right/all = SPD 派别党内支持度；stability = 稳定度（0.0005 = 0.05%）
#   bw        [(种类, 值)]  unity = 党内团结度（%）；inertia = 议会协商惯性
#   soc       社会化点数每日获取（社会化还没有每日点数：只把系数写进 GER_region_soc_points_factor，接入时读它）
#   cond_daily [(国家旗标, 种类, 值)]  有旗标时才生效
# 威廉·科嫩、奥托·布劳恩是以后替换用的领导人：效果写好了，换上去就生效（set_variable = { GER_region_Rxx_leader = 序号 }）。
LEADER_FX = {
    "daeumig": dict(country=[("political_power_factor", 0.05, "政治点数获取")], state=[("local_manpower", 0.20, "当地人力")],
                    local_bw=[("control", 0.05)], daily=[("left", 1)]),
    "dissmann": dict(local_bw=[("control", 0.05)], daily=[("center", 1)]),
    "henke": dict(local_bw=[("support", 0.05)], daily=[("center", 1)]),
    "lipinski": dict(daily=[("stability", 0.0005), ("center", 1)]),
    "koenen": dict(soc=0.10, daily=[("left", 1)]),
    "committee_nine": dict(bw=[("unity", 3)], state=[("local_resources_factor", 0.20, "当地资源获取")]),
    "paul_dittmann": dict(local_bw=[("control", 0.1)], state=[("local_manpower", 0.10, "当地人力")]),
    "otto_braun": dict(local_bw=[("control", 0.1)], daily=[("right", 1)],
                       country=[("drift_defence_factor", 0.20, "意识形态抵制力度")]),
    "paul_hirsch": dict(local_bw=[("control", -0.2)], daily=[("all", -1)], bw=[("unity", -5)]),
    "weimar_coalition": dict(daily=[("right", 1), ("stability", 0.0002)]),
    "bitta": dict(bw=[("inertia", 5)], cond_daily=[("GER_silesia_autonomy", "stability", 0.0005)]),
}
SPD_FACTION = {"left": ("GER_SPD_left_support", "左派支持度"), "center": ("GER_SPD_center_support", "中派支持度"),
               "right": ("GER_SPD_right_support", "右派支持度")}
# 州修正图标（先用原版的；AOR 地区界面的「地区修正」格子 40x47、左下对齐，原版 32x30 的图标放得下）
TIER_ICONS = {100: "GFX_modifiers_ETH_state_development", 75: "GFX_modifiers_ETH_state_development",
              50: "GFX_modifiers_ETH_state_development", 0: "GFX_modifiers_generic_resistance"}
LEADER_STATE_ICON = "GFX_modifiers_SOV_factory_worker_militias"
LEADER_COUNTRY_ICON = "GFX_modifiers_generic_military_plans"
# 行动方针（决议）。右侧面板里是一个可滚动的列表，列表内容每次刷新时按下面的数据 + 手写的 _visible 条件生成，
# 加一条新决议 = 在 ACTIONS 里加一行（n 用新号）、放进 ACTION_ORDER，重跑脚本；
# 脚本会在手写文件里补上它的效果钩子和条件（占位），再去手写文件里填。
#   n      固定编号：变量、钩子、本地化键都用它。只往后加，不要改旧号。
#   kind   "daily" 日常决议：每条按地区各自计时，可以同时生效好几条
#          "garrison" 驻区方针：每个地区同时只有一条生效，点另一条 = 切换，一直生效到切换为止
#   days   日常决议点击后保持选中（暗黄）的天数：耗时 N 天写 N（结束时给效果），持续 24 周写 168（期间每两周给效果）；
#          0 = 点了立刻生效，不进入生效中状态
#   max    每个地区最多执行几次（0 = 不限）；界面自动加条件、悬停提示里写「已执行次数」
#   region 只在这个区块出现（区块 key，如 "R03"）；None = 所有地区
ACTIONS = [
    dict(n=1, cname="扩大宣传投入", kind="daily", cost=10, days=7),
    dict(n=2, cname="扩张防卫组织", kind="daily", cost=10, days=7),
    dict(n=3, cname="组织网络的扩展", kind="daily", cost=20, days=168),
    dict(n=4, cname="推动公共事业", kind="daily", cost=25, days=168),
    dict(n=5, cname="组织重心向工厂转移", kind="daily", cost=15, days=14, max=2),
    dict(n=6, cname="发起罢工", kind="daily", cost=70, days=14, cooldown=120),   # 长冷却：从点击起 120 天
    dict(n=7, cname="工厂委员会的扩张", kind="daily", cost=15, days=7),
    dict(n=8, cname="影子苏维埃", kind="daily", cost=60, days=0),
    dict(n=9, cname="扩充安全部队", kind="garrison", cost=25),
    dict(n=10, cname="总结政权经验", kind="garrison", cost=25),
    dict(n=11, cname="培训根据地干部", kind="garrison", cost=25),
    dict(n=12, cname="支援邻近地区", kind="garrison", cost=25),
    dict(n=13, cname="红色海军网络", kind="garrison", cost=25, region="R03"),
    dict(n=14, cname="与基督教社会主义者交好", kind="garrison", cost=25, region="R14"),
    # 巴伐利亚危机（阶段博弈，见 PHASES）：只在阶段进行中出现，每条只能执行一次；
    # 随危机进度（GER_region_bavaria_stage）逐步出现，条件写在手写的 _visible / _allowed 里
    dict(n=15, cname="调停SPD内部冲突", kind="daily", cost=100, days=0, max=1, region="R09", phase="bavaria"),
    dict(n=16, cname="对巴伐利亚施压", kind="daily", cost=25, days=0, max=1, region="R09", phase="bavaria"),
    dict(n=17, cname="向协约国提交巴伐利亚报告", kind="daily", cost=5, days=0, max=1, region="R09", phase="bavaria"),
    dict(n=18, cname="采取保守态势", kind="daily", cost=25, days=0, max=1, region="R09", phase="bavaria"),
    dict(n=19, cname="宣布抵制恐怖袭击", kind="daily", cost=5, days=0, max=1, region="R09", phase="bavaria"),
    dict(n=20, cname="撤出SPD优秀分子", kind="daily", cost=50, days=7, max=1, region="R09", phase="bavaria"),
    dict(n=21, cname="向巴伐利亚发动最后通牒", kind="daily", cost=5, days=0, max=1, region="R09", phase="bavaria"),
    dict(n=22, cname="依靠协约国施压", kind="daily", cost=25, days=0, max=1, region="R09", phase="bavaria"),
]
ACTION_ORDER = [1, 2, 7, 3, 4, 5, 6, 8,      # 行动方针（显示顺序）
                9, 10, 11, 12, 13, 14,       # 驻区方针
                15, 16, 17, 18, 19, 20, 21, 22]   # 巴伐利亚危机（阶段决议，放在最后）
# ---- 阶段博弈：地图全开之前，先只开放一个地区，右侧列表只显示该阶段的特色决议（普通决议全部隐藏），结束后全部关掉。
# 每个阶段生成（<key> = 下面的键）：
#   GER_region_game_<key>_start       开始：设旗标、只开放该地区、选中它、进度归 0、清掉该阶段决议的执行记录
#   GER_region_game_<key>_next_stage  进度 +1（事件里调用；也可以直接 set_variable 进度变量再跑 GER_region_game_sync_selected）
#   GER_region_game_<key>_end         结束：清旗标，该阶段的决议全部隐藏（决议的执行次数保留，结束后的事件还能查）；
#                                     keep_open = True 时地块保留显示，否则关闭该地区、面板回到待机
# 手写钩子（common/scripted_effects/GER_region_game_actions.txt）：GER_region_<key>_on_start / _on_end
#   flag    阶段进行中的国家旗标；决议的 phase 写这里的键
#   region  开放的地区；state = 地区类型帧号；values = 背地里的 (支持度, 控制度)，(25, 25) = 地区效益无效果
#   leader  地区领导人（LEADERS 的键，None = 无）
#   stage   进度变量：0 = 刚开始（还没有决议），之后由事件推进；stages = 最大进度
#   keep_open  结束后地块是否保留显示
# 巴伐利亚危机的事件链在 events/AOR_GER_events.txt（AOR_GER_bavaria_crisis）。正式流程里巴伐利亚要到 1920.4.5 的事件点击后才显示
# （手写的 GER_region_bavaria_reveal 调用 _start），在那之前界面一直待机，类型 / 领导人只在背地里记着：1.12 魏玛联盟控制区、霍夫曼，
# 2.21 霍夫曼遇刺后领导人清空，2.23 转换为右派控制区。所以显示出来时是右派控制区、无领导人；下面的 state / leader 是 1.12 的初始值。
PHASES = {
    "bavaria": dict(cname="巴伐利亚危机", flag="GER_region_bavaria_phase", region="R09", state=10, values=(25, 25),
                    leader="hoffmann", stage="GER_region_bavaria_stage", stages=4, keep_open=True),
}
BIWEEKLY = 14   # 「每两周」效果的间隔天数
#   cooldown 每个地区点击后多少天内不能再点（含生效期间；0 = 没有冷却）

# ---- 地区效益（用户图「我修改过后的版本」）：控制度 / 支持度到档后给该地区的州加修正
# 档位看控制度：100 / 75 / 50 / 25 / 0。75、50 档还要支持度 >= 控制度的一半；100 档只要支持度 >= 25（控制度的四分之一）；
# 支持度不够就落到 25 档（无效果）。修正只加在该地区里、目前归德国所有的州上（割让出去的州自动去掉）。
TIER_MODS = {
    100: [("local_resources_factor", 0.15, "当地资源获取"), ("state_production_speed_buildings_factor", 0.20, "地区建造速度"),
          ("local_manpower", 0.30, "当地人力")],
    75: [("state_production_speed_buildings_factor", 0.10, "地区建造速度"), ("local_manpower", 0.20, "当地人力")],
    50: [("local_manpower", 0.10, "当地人力")],
    25: [],
    0: [("local_resources_factor", -0.10, "当地资源获取"), ("state_production_speed_buildings_factor", -0.20, "地区建造速度"),
        ("local_manpower", -0.30, "当地人力")],
}
TIERS = [100, 75, 50, 25, 0]
# 不显示数值的地区（核心区方块盖住数值框）背地里的 (支持度, 控制度)，开局时设，用来触发地区效益
HIDDEN_VALUES = {3: (100, 100), 4: (0, 0), 5: (25, 25), 6: (25, 25)}
# 摇摆区：左派核心区 / 左派控制区里支持度 < 50 且控制度 < 60 时变成摇摆区；回升后再维持 35 天，随后恢复原类型
SWING_SUPPORT, SWING_CONTROL, SWING_DAYS = 50, 60, 35
SWING_FROM = (3, 8)
# 支持度、控制度不会增长的地区（只能靠国策与焦点博弈：那边先 set_temp_variable = { GER_region_force = 1 } 再调用小工具）
FROZEN = ["R07"]
# 地区 -> 州（格尔利茨归萨克森、右岸莱茵兰和科隆归鲁尔是用户指定；其余用各州在地图上的位置经美术素材的配准落到区块里求得；但泽 / 波森 / 西普鲁士只在割让盖板下，不属于任何地区）
REGION_STATES = {
    "R01": [56, 853, 866], "R02": [59, 1108, 1112, 1116, 1117, 1132],
    "R03": [58, 838, 839, 855, 862, 1043, 1113, 1125], "R04": [61, 1110], "R05": [62, 63], "R06": [64, 68],
    "R07": [66, 67, 762, 1134], "R08": [60, 65, 842, 870, 871, 1111, 1114, 1129, 1130],
    "R09": [52, 53, 54, 857, 861, 863], "R10": [50, 837, 841, 860], "R11": [55, 856, 858, 1109, 1121, 1131],
    "R12": [42, 836, 850, 1101, 1118, 1119], "R13": [5, 188, 763, 849, 864, 865], "R14": [57, 51, 859],
    "R15": [854, 1115], "R16": [840],
}

GEN_TAG = "tools/GER_region_game/gen_region_game.py"

# 正式悬浮介绍直接手写在这个本地化文件里，脚本只读不写；
# 这里已有的键，生成的本地化文件就不再输出【待定】占位，避免重复键。
HAND_TT_LOC = "localisation/simp_chinese/gui/GER_region_game_tt_l_simp_chinese.yml"
# 右侧面板上要用户定的文字（决议名/花费/提示、核心区说明、领导人名字/提示、照片说明），同样只补缺不改
HAND_PANEL_LOC = "localisation/simp_chinese/gui/GER_region_game_panel_l_simp_chinese.yml"


def hand_written_keys(rel=HAND_TT_LOC):
    path = os.path.join(MOD, *rel.split("/"))
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8-sig") as f:
        return set(re.findall(r"^\s*([A-Za-z0-9_.]+):\d*\s*\"", f.read(), flags=re.M))


def append_missing(rel, entries, header=None):
    """手写本地化文件里缺哪个键就在末尾补一行；已有的行一律不碰。entries = [(键, 值)]"""
    have = hand_written_keys(rel)
    missing = [(k, v) for k, v in entries if k not in have]
    if not missing:
        return 0
    p = os.path.join(MOD, *rel.split("/"))
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            f.write("l_simp_chinese:\r\n")
            for h in header or []:
                f.write(" # %s\r\n" % h)
    with open(p, "rb") as f:
        ends_nl = f.read().endswith(b"\n")
    with open(p, "a", encoding="utf-8", newline="") as f:
        if not ends_nl:
            f.write("\r\n")       # 最后一行没换行时先补换行，免得接到手写行末尾
        for k, v in missing:
            f.write(' %s: "%s"\r\n' % (k, v))
    print("%s 补了 %d 条占位" % (rel, len(missing)))
    return len(missing)


# ---------------------------------------------------------------- 工具函数
def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("不是 PNG：" + path)
    return struct.unpack(">II", head[16:24])


def copy_if_changed(src, dst):
    """内容相同就不写（游戏开着时贴图文件是锁住的）"""
    with open(src, "rb") as f:
        data = f.read()
    if os.path.exists(dst):
        with open(dst, "rb") as f:
            if f.read() == data:
                return
    with open(dst, "wb") as f:
        f.write(data)


def save_png_if_changed(img, dst):
    import io
    buf = io.BytesIO()
    img.save(buf, "PNG")
    data = buf.getvalue()
    if os.path.exists(dst):
        with open(dst, "rb") as f:
            if f.read() == data:
                return
    with open(dst, "wb") as f:
        f.write(data)


def copy_asset(src_rel, dst_name, expect_w, expect_h):
    src = os.path.join(SRC, *src_rel.split("/"))
    w, h = png_size(src)
    if (w, h) != (expect_w, expect_h):
        raise ValueError("尺寸不符 %s：实际 %dx%d，清单推算 %dx%d" % (src_rel, w, h, expect_w, expect_h))
    dst = os.path.join(GFX_DIR, dst_name)
    copy_if_changed(src, dst)          # 逐字节复制，不做任何处理
    return GFX_DIR_REL + "/" + dst_name


def copy_hit2_as_3(src_rel, dst_name, frame_w, h):
    """2 帧点击条 [普通|悬浮] -> 3 帧 [普通|悬浮|悬浮]。

    实测：HOI4 按钮 2 帧时，帧 2 只在「按下」时出现，悬浮停在帧 1；
    3 帧时帧 2 = 悬浮、帧 3 = 按下。所以把帧 2 原样再贴一份当帧 3。
    只做整块像素复制（crop/paste），不缩放、不重采样、不改像素。需要 Pillow。
    """
    from PIL import Image
    src = os.path.join(SRC, *src_rel.split("/"))
    w, hh = png_size(src)
    if (w, hh) != (frame_w * 2, h):
        raise ValueError("尺寸不符 %s：实际 %dx%d，清单推算 %dx%d" % (src_rel, w, hh, frame_w * 2, h))
    im = Image.open(src)
    im.load()
    f1 = im.crop((0, 0, frame_w, h))
    f2 = im.crop((frame_w, 0, frame_w * 2, h))
    out = Image.new(im.mode, (frame_w * 3, h))
    out.paste(f1, (0, 0))
    out.paste(f2, (frame_w, 0))
    out.paste(f2, (frame_w * 2, 0))
    dst = os.path.join(GFX_DIR, dst_name)
    save_png_if_changed(out, dst)
    # 校验：三帧分别与源帧逐像素相同
    chk = Image.open(dst)
    for i, ref in enumerate((f1, f2, f2)):
        if chk.crop((i * frame_w, 0, (i + 1) * frame_w, h)).tobytes() != ref.tobytes():
            raise ValueError("像素校验失败：" + dst_name)
    return GFX_DIR_REL + "/" + dst_name


def write(path_rel, text, bom=False, crlf=False):
    path = os.path.join(MOD, *path_rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if crlf:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    enc = "utf-8-sig" if bom else "utf-8"
    if os.path.exists(path):   # 内容没变就不写（游戏开着时会锁住 .gfx 等文件）
        with open(path, encoding=enc, newline="") as f:
            if f.read() == text:
                return
    with open(path, "w", encoding=enc, newline="") as f:
        f.write(text)
    print("写出", path_rel)


def indent(block, n):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else "" for line in block.splitlines())


def splice(path_rel, template, blocks):
    """模板首次写出；之后只替换标记之间的内容。"""
    path = os.path.join(MOD, *path_rel.split("/"))
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            text = f.read()
    else:
        text = template
        for name in blocks:
            text = re.sub(r"^([ \t]*)\{\{GEN:%s\}\}[ \t]*$" % name,
                          lambda m, n=name: "%s# >>> GENERATED: %s (%s) 不要手改，重跑脚本\n%s# <<< GENERATED: %s"
                          % (m.group(1), n, GEN_TAG, m.group(1), n),
                          text, flags=re.M)
    for name, body in blocks.items():
        pat = re.compile(r"^([ \t]*)# >>> GENERATED: %s\b[^\n]*\n.*?^[ \t]*# <<< GENERATED: %s[ \t]*$"
                         % (re.escape(name), re.escape(name)), re.M | re.S)
        m = pat.search(text)
        if not m:
            raise ValueError("%s 里找不到生成标记 %s" % (path_rel, name))
        pad = len(m.group(1).replace("\t", "    "))
        new = "%s# >>> GENERATED: %s (%s) 不要手改，重跑脚本\n%s\n%s# <<< GENERATED: %s" % (
            m.group(1), name, GEN_TAG, indent(body, pad), m.group(1), name)
        text = text[:m.start()] + new + text[m.end():]
    write(path_rel, text)


# ---------------------------------------------------------------- 读清单
with open(os.path.join(SRC, "14_素材清单.json"), encoding="utf-8") as f:
    M14 = {it["id"]: it for it in json.load(f)["items"]}
with open(os.path.join(SRC, "16_区块素材清单.json"), encoding="utf-8") as f:
    M16 = json.load(f)
assert M16["frame_index_base"] == 1
with open(os.path.join(SRC, REGION12_SRC, "region_fill_frames.json"), encoding="utf-8") as f:
    M12 = json.load(f)
assert M12["frame_index_base"] == 1 and len(M12["frames"]) == REGION_FRAMES
M12_by_id = {r["id"]: r for r in M12["regions"]}
with open(os.path.join(SRC, PANEL_SRC, "素材清单.json"), encoding="utf-8") as f:
    PJ = json.load(f)

regions = []    # 16 个区块
by_id = {r["id"]: r for r in M16["regions"]}
for r in M16["regions"]:
    if r["frames"] != 7:          # 16 号清单里的填充条（7 帧）；点击条另有 _hit 条目
        continue
    hit = by_id[r["id"] + "_hit"]
    assert (hit["x"], hit["y"], hit["w"], hit["h"]) == (r["x"], r["y"], r["w"], r["h"])
    r12 = M12_by_id[r["id"]]      # 填充条改用 区块_12帧 里的同名文件，位置尺寸必须一致
    assert (r12["x"], r12["y"], r12["w"], r12["h"], r12["frames"]) == (r["x"], r["y"], r["w"], r["h"], REGION_FRAMES), r["id"]
    regions.append({
        "id": r["id"],                       # R01_WeserEms
        "key": r["id"].split("_")[0],        # R01  （变量用）
        "name": r["name"],
        "x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"],
        "file": REGION12_SRC + "/" + r12["file"], "hit_file": "区块/" + hit["file"],
    })
assert len(regions) == 16 and len(M12["regions"]) == 16
overlays = []   # 11 张割让盖板
for o in M16["overlays"]:
    overlays.append({
        "id": o["id"], "name": o["name"],
        "x": o["x"], "y": o["y"], "w": o["w"], "h": o["h"],
        "file": "割让盖板/" + o["file"], "hit_file": "割让盖板/" + o["hit_file"],
    })

# ---------------------------------------------------------------- 复制素材
os.makedirs(GFX_DIR, exist_ok=True)
sprites = []   # (sprite_name, texturefile, frames, transparencecheck)


def add_sprite(name, path, frames=1, tcheck=False):
    sprites.append((name, path, frames, tcheck))
    return name


# 层 1 / 6 不在 14 号清单里，固定铺满画布
SP_BASE = add_sprite("GFX_GER_region_base",
                     copy_asset("02_最底层_羊皮纸_海洋_海岸水纹.png", "base_parchment_sea.png", CANVAS_W, CANVAS_H))
SP_OUTLINE = add_sprite("GFX_GER_region_outline",
                        copy_asset("03_德国轮廓线_透明层.png", "germany_outline.png", CANVAS_W, CANVAS_H))

STATIC = {   # 14 号清单里的条目 -> (英文文件名, 精灵名)
    "GER_map_locked_all": ("locked_all.png", "GFX_GER_region_locked_all"),
    "GER_map_locked_all_hit": ("locked_all_hit.png", "GFX_GER_region_locked_all_hit"),
    "GER_reg_alsace_lorraine": ("alsace_lorraine_fill.png", "GFX_GER_region_alsace_lorraine_fill"),
    "GER_reg_alsace_lorraine_hit": ("alsace_lorraine_hit.png", "GFX_GER_region_alsace_lorraine_hit"),
    "GER_reg_bav_corner": ("bav_corner_fill.png", "GFX_GER_region_bav_corner_fill"),
    "GER_reg_bav_corner_hit": ("bav_corner_hit.png", "GFX_GER_region_bav_corner_hit"),
}
for sid, (fname, sp) in STATIC.items():
    it = M14[sid]
    fr = it["frames"]
    if fr == 2:   # 2 帧点击条改成 3 帧，见 copy_hit2_as_3
        add_sprite(sp, copy_hit2_as_3(it["file"], fname, it["w"], it["h"]), 3, True)
    else:
        add_sprite(sp, copy_asset(it["file"], fname, it["w"] * fr, it["h"]), fr, sid.endswith("_hit"))

for r in regions:
    r["sp_fill"] = add_sprite("GFX_GER_region_%s_fill" % r["id"],
                              copy_asset(r["file"], "%s_fill.png" % r["id"], r["w"] * REGION_FRAMES, r["h"]),
                              REGION_FRAMES)
    r["sp_hit"] = add_sprite("GFX_GER_region_%s_hit" % r["id"],
                             copy_asset(r["hit_file"], "%s_hit.png" % r["id"], r["w"] * 3, r["h"]), 3, True)
for o in overlays:
    o["sp_fill"] = add_sprite("GFX_GER_region_OV_%s" % o["id"],
                              copy_asset(o["file"], "OV_%s.png" % o["id"], o["w"], o["h"]), 1)
    o["sp_hit"] = add_sprite("GFX_GER_region_OV_%s_hit" % o["id"],
                             copy_hit2_as_3(o["hit_file"], "OV_%s_hit.png" % o["id"], o["w"], o["h"]), 3, True)

# ---------------------------------------------------------------- 右侧面板素材
# 静态素材逐字节复制到 panel/；它们的 spriteType 是 .gfx 里手写的（GENERATED 标记外）。
os.makedirs(PANEL_DIR, exist_ok=True)
PANEL_FILES = {   # 文件名 -> (宽, 高)；宽是整条（多帧时 = 每帧宽 x 帧数）
    "support_bar_full.png": (158, 22), "support_bar_empty.png": (158, 22),
    "control_bar_full.png": (158, 22), "control_bar_empty.png": (158, 22),
    "core_left.png": (312, 84), "core_right.png": (312, 84), "core_weimar.png": (312, 84),
    "core_green.png": (312, 84),
    "decision_row_3f.png": (292 * 3, 42),
    "region_photo_frame.png": tuple(PJ["region_photo"]["sprite_size"]),
    "leader_photo_frame.png": tuple(PJ["leader_photo"]["sprite_size"]),
    "region_photo_vignette.png": tuple(PJ["region_photo"]["photo_size"]),
    "leader_photo_vignette.png": tuple(PJ["leader_photo"]["photo_size"]),
    "map_corner_shade.png": tuple(PJ["map_corner_shade"]["size"]),
}
for _f, (_w, _h) in PANEL_FILES.items():
    _src = os.path.join(SRC, PANEL_SRC, _f)
    if png_size(_src) != (_w, _h):
        raise ValueError("尺寸不符 %s：实际 %dx%d，应为 %dx%d" % ((_f,) + png_size(_src) + (_w, _h)))
    copy_if_changed(_src, os.path.join(PANEL_DIR, _f))

# 地区照片：16 帧条带，帧号 = GER_region_selected（区块序号）。没交照片的地区用深色占位。
PHOTO_W, PHOTO_H = PJ["region_photo"]["photo_size"]
PHOTO_STRIP = "region_photos_16f.png"


def build_photo_strip():
    from PIL import Image
    strip = Image.new("RGBA", (PHOTO_W * len(regions), PHOTO_H), PHOTO_BG)
    have, adjusted = [], []
    photo_dir = os.path.join(MOD, *PHOTO_DIR_REL.split("/"))
    rename_photos(photo_dir)
    for r in regions:
        src = find_photo(photo_dir, r["id"])
        if not src:
            continue
        im, note = fit_photo(src)
        if note:
            adjusted.append(note)
        strip.paste(im, ((r["idx"] - 1) * PHOTO_W, 0))
        have.append(r["id"])
    save_png_if_changed(strip, os.path.join(PANEL_DIR, PHOTO_STRIP))
    print("地区照片：已交 %d 张 %s，其余用深色占位" % (len(have), have))
    idle = find_photo(photo_dir, PHOTO_IDLE)
    if idle:
        im, note = fit_photo(idle)
        if note:
            adjusted.append(note)
        print("待机照片：", os.path.basename(idle))
    else:
        im = Image.new("RGBA", (PHOTO_W, PHOTO_H), PHOTO_BG)
        print("待机照片：没交（photos/%s.png），用深色占位" % PHOTO_IDLE)
    save_png_if_changed(im, os.path.join(PANEL_DIR, PHOTO_IDLE_FILE))
    for n in adjusted:
        print("  照片尺寸不对，已处理：", n)


PHOTO_EXTS = (".png", ".jpg", ".jpeg")
PHOTO_IDLE_FILE = "region_photo_idle.png"


def find_photo(photo_dir, stem):
    for ext in PHOTO_EXTS:
        p = os.path.join(photo_dir, stem + ext)
        if os.path.exists(p):
            return p
    return None


def _norm(s):
    return re.sub(r"[\s\-—–－‐·・_]", "", s)


def rename_photos(photo_dir):
    """中文名的照片改成区块id名（大柏林.png -> R16_GreatBerlin.png，待机.png -> idle.png）。
    比对时去掉连字符、破折号、空格；文件名是某个地区名的一部分（符腾堡 -> 巴登-符腾堡）且只对上一个地区也算。
    对不上 / 对上多个 / 英文名已存在的，不动，只报告。"""
    targets = [(r["id"], r["name"]) for r in regions] + [(PHOTO_IDLE, PHOTO_IDLE_CN)]
    ids = {i for i, _ in targets}
    for f in sorted(os.listdir(photo_dir)):
        stem, ext = os.path.splitext(f)
        if ext.lower() not in PHOTO_EXTS or stem in ids:
            continue
        s = _norm(stem)
        hits = [i for i, n in targets if s and _norm(n) == s] or [i for i, n in targets if s and s in _norm(n)]
        if len(hits) != 1:
            print("  照片没改名：%s 对不上地区名%s" % (f, "（可能是 %s）" % "/".join(hits) if hits else ""))
            continue
        if find_photo(photo_dir, hits[0]):
            print("  照片没改名：%s 和 %s 都在，请删掉一个" % (f, os.path.basename(find_photo(photo_dir, hits[0]))))
            continue
        os.rename(os.path.join(photo_dir, f), os.path.join(photo_dir, hits[0] + ext.lower()))
        print("  照片改名：%s -> %s%s" % (f, hits[0], ext.lower()))


def fit_photo(src):
    """读入照片，不是 425x157 就居中裁切到 425:157，还不对再等比缩放（不拉伸）；返回 (图, 说明或 None)"""
    from PIL import Image
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    note = None
    if (w, h) != (PHOTO_W, PHOTO_H):
        # 只做居中裁切到 425:157；裁完尺寸仍不对时等比缩放（不拉伸），并报告
        if w * PHOTO_H > h * PHOTO_W:
            nw = round(h * PHOTO_W / PHOTO_H)
            im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:
            nh = round(w * PHOTO_H / PHOTO_W)
            im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
        note = "%s %dx%d -> 居中裁切 %dx%d" % (os.path.basename(src), w, h, im.size[0], im.size[1])
        if im.size != (PHOTO_W, PHOTO_H):
            im = im.resize((PHOTO_W, PHOTO_H), Image.LANCZOS)
            note += " -> 等比缩放到 %dx%d" % (PHOTO_W, PHOTO_H)
    return im, note


for i, r in enumerate(regions, 1):
    r["idx"] = i                                      # GER_region_selected 的取值（也是照片帧号）
build_photo_strip()

panel_sprites = [("GFX_GER_region_panel_photos", PANEL_DIR_REL + "/" + PHOTO_STRIP, len(regions), False),
                 ("GFX_GER_region_panel_photo_idle", PANEL_DIR_REL + "/" + PHOTO_IDLE_FILE, 1, False)]
# 核心区 / 特殊区方块（按 CORE_FRAMES 生成；手写区只在 .gfx 不存在时写一次，所以放在生成块里）
panel_sprites += [("GFX_GER_region_panel_core_%s" % side, PANEL_DIR_REL + "/core_%s.png" % side, 1, False)
                  for _f, side in sorted(CORE_FRAMES.items())]
leaders = []
for i, (key, cname, portrait) in enumerate(LEADERS, 1):
    ld = {"idx": i, "key": key, "cname": cname, "portrait": portrait,
          "name_key": "GER_region_leader_%s_name" % key, "tt": "GER_region_leader_%s_tt" % key}
    if portrait and not os.path.exists(os.path.join(MOD, *portrait.split("/"))):
        print("  头像还没放进来，先只显示名字：" + portrait)
        ld["portrait"] = portrait = None
    if portrait:
        if png_size(os.path.join(MOD, *portrait.split("/"))) != (156, 210):
            raise ValueError("头像不是 156x210：" + portrait)
        ld["sp"] = "GFX_GER_region_leader_%s" % key
        ld["el"] = "GER_region_panel_leader_%s" % key
        panel_sprites.append((ld["sp"], portrait, 1, False))
    leaders.append(ld)

LD_BY_KEY0 = {ld["key"]: ld for ld in leaders}

# ---------------------------------------------------------------- 命名约定
for r in regions:
    r["el_fill"] = "GER_region_%s_fill" % r["id"]
    r["el_btn"] = "GER_region_%s_button" % r["id"]
    r["v_open"] = "GER_region_%s_open" % r["key"]      # =1 显示（已开放）
    r["v_state"] = "GER_region_%s_state" % r["key"]    # 1-12 地区类型 = 帧号（见 REGION_FRAMES 注释）
    r["v_frame"] = "GER_region_%s_frame" % r["key"]    # 1-12 实际显示帧（sync 时从 state 拷贝）
    r["v_support"] = "GER_region_%s_support" % r["key"]  # 0-100 支持度
    r["v_control"] = "GER_region_%s_control" % r["key"]  # 0-100 控制度
    r["v_leader"] = "GER_region_%s_leader" % r["key"]    # 领导人序号（LEADERS，1 起；0 = 无）
    r["tt"] = "GER_region_%s_tt" % r["id"]
    r["tooltip"] = "GER_region_%s_tooltip" % r["id"]
    r["head"] = "GER_region_%s_head" % r["id"]
    r["body"] = "GER_region_%s_body" % r["id"]         # scripted loc：= 手写介绍 GER_region_<id>_tt          # scripted loc：地区名：类型
    r["name_key"] = "GER_region_%s_name" % r["id"]
    r["caption_key"] = "GER_region_%s_photo_caption" % r["id"]

# 驻区方针能不能点：左派核心区，或支持度、控制度双满
GARRISON_OPEN = ("OR = { check_variable = { GER_region_sel_frame = 3 } AND = { check_variable = { GER_region_sel_support > 99.99 }"
                 " check_variable = { GER_region_sel_control > 99.99 } } }")
# 行动方针 = 决议。效果、条件、悬停介绍是手写文件；脚本只在里面补缺的钩子（占位），已有内容一律不碰
ACTIONS_EFFECTS = "common/scripted_effects/GER_region_game_actions.txt"
ACTIONS_TRIGGERS = "common/scripted_triggers/GER_region_game_actions.txt"

_by_n = {a["n"]: a for a in ACTIONS}
assert len(_by_n) == len(ACTIONS) and sorted(ACTION_ORDER) == sorted(_by_n), "ACTIONS 编号重复或 ACTION_ORDER 不全"
ROWS = []
for n in ACTION_ORDER:
    row = dict(dict(days=0, max=0, region=None, cooldown=0, phase=None), **_by_n[n])
    row["garrison"] = row["kind"] == "garrison"
    assert row["kind"] in ("daily", "garrison") and not (row["garrison"] and row["days"])
    if row["phase"]:   # 阶段决议：只在该阶段的地区出现，不能是驻区方针
        assert not row["garrison"] and row["region"] == PHASES[row["phase"]]["region"], "阶段决议的 region 要等于阶段的地区"
    ROWS.append(row)
for row in ROWS:
    n = row["n"]
    row["name"] = "GER_region_panel_row_%d_name" % n
    row["tt"] = "GER_region_panel_row_%d_tt" % n
    row["sel_days"] = "GER_region_sel_row_%d_days" % n         # 选中地区这条还剩几天（面板读）
    row["sel_count"] = "GER_region_sel_row_%d_count" % n       # 选中地区这条已执行几次（有 max 的才有）
    row["sel_cd"] = "GER_region_sel_row_%d_cd" % n             # 选中地区这条冷却还剩几天（有 cooldown 的才有）
    row["pp_ok"] = "has_political_power > %s" % (row["cost"] - 0.01)
    # 「生效中」：日常决议 = 选中地区剩余天数 > 0；驻区方针 = 选中地区当前方针是这一条
    row["active"] = ("check_variable = { GER_region_sel_policy = %d }" % n if row["garrison"]
                     else "check_variable = { %s > 0 }" % row["sel_days"])
    # 钩子：点击时 / 结束时 / 每两周 / 每天（都在手写的效果文件里）
    row["hooks"] = [""]
    if not row["garrison"] and row["days"]:
        row["hooks"].append("_complete")
    if row["garrison"] or row["days"] >= BIWEEKLY:
        row["hooks"].append("_biweekly")
    if row["garrison"]:
        row["hooks"].append("_daily")
TIMED_ROWS = [row for row in ROWS if not row["garrison"] and row["days"] > 0]
GARRISON = [row for row in ROWS if row["garrison"]]
COUNTED = [row for row in ROWS if row["max"]]
COOLED = [row for row in ROWS if row["cooldown"]]
DAILY_LIST = [row for row in ROWS if not row["garrison"]]
# 有任何阶段博弈在进行
PHASE_ANY = " ".join("has_country_flag = %s" % ph["flag"] for ph in PHASES.values())
# 地图全开（GER_region_game_open_map）时设的国家旗标：之前普通的行动方针 / 驻区方针整个不显示
MAP_OPENED_FLAG = "GER_region_map_opened"
MAP_OPENED = "has_country_flag = %s" % MAP_OPENED_FLAG
# 待机（没选中地区）时罩住数值框的核心区方块（CORE_FRAMES 的值），上面的字 = 手写的 GER_region_panel_idle_cover
IDLE_COVER = "green"
for r in regions:
    r["v_policy"] = "GER_region_%s_policy" % r["key"]            # 当前驻区方针编号，0 = 无
    r["v_policy_days"] = "GER_region_%s_policy_days" % r["key"]  # 当前方针已生效天数
    r["v_count"] = {row["n"]: "GER_region_%s_count_%d" % (r["key"], row["n"]) for row in COUNTED}  # 已执行次数
    r["v_growth"] = "GER_region_%s_control_growth" % r["key"]    # 永久每两周控制度增长
    r["v_floor"] = "GER_region_%s_control_floor" % r["key"]      # 控制度下限（影子苏维埃后 80）
    r["v_cd"] = {row["n"]: "GER_region_%s_cd_%d" % (r["key"], row["n"]) for row in COOLED}  # 冷却剩余天数
    r["v_tier"] = "GER_region_%s_tier" % r["key"]                # 地区效益档位 100/75/50/25/0
    r["v_swing_return"] = "GER_region_%s_swing_return" % r["key"]  # 掉成摇摆区之前的类型（0 = 不是临时摇摆区）
    r["v_swing_days"] = "GER_region_%s_swing_days" % r["key"]    # 回升后还要维持摇摆区几天
    assert r["key"] in REGION_STATES
    r["v_act"] = {row["n"]: "GER_region_%s_act_%d" % (r["key"], row["n"]) for row in TIMED_ROWS}  # 剩余天数

# 盖板互斥：键的盖板在值的盖板显示时不画（A 方案范围包含 B 方案）
OVERLAY_HIDDEN_BY = {"SIL_planB_762": "SIL_planA_1134_762"}
for _b, _a in OVERLAY_HIDDEN_BY.items():
    assert _b in {o["id"] for o in overlays} and _a in {o["id"] for o in overlays}, "清单里缺西里西亚盖板"

for o in overlays:
    o["el_fill"] = "GER_region_OV_%s" % o["id"]
    o["el_btn"] = "GER_region_OV_%s_button" % o["id"]
    o["v_shown"] = "GER_region_OV_%s_shown" % o["id"]  # =1 显示
    o["tt"] = "GER_region_OV_%s_tt" % o["id"]

# ---------------------------------------------------------------- .gfx
def sprite_lines(lst):
    out = []
    for name, path, frames, tcheck in lst:
        out.append("spriteType = {")
        out.append('    name = "%s"' % name)
        out.append('    texturefile = "%s"' % path)
        if frames > 1:
            out.append("    noOfFrames = %d" % frames)
        if tcheck:
            out.append("    transparencecheck = yes")
        out.append("}")
    return out


gfx_lines = sprite_lines(sprites)
GFX_TEMPLATE = """spriteTypes = {
    # 名称框、数值框、决议总框：tiled_plain_bg_lined，金线在框边界往里 4px，
    # 小框用 8px 的 borderSize，避免默认 64px 边角在矮框里叠在一起。
    corneredTileSpriteType = {
        name = "GFX_GER_region_game_frame"
        size = { x = 190 y = 190 }
        textureFile = "gfx/interface/tiles/tiled_plain_bg_lined.dds"
        borderSize = { x = 8 y = 8 }
        tilingCenter = yes
        effectFile = "gfx/FX/buttonstate_nodowneffect.lua"
    }

    # ---- 右侧面板素材（gfx/interface/GER_region_game/panel/，1:1 显示，不要缩放）----
    # 进度条：写法同 GER_socialization 的组织度条；frame = 0-100
    progressbartype = {
        name = "GFX_GER_region_panel_support_bar"
        textureFile1 = "gfx/interface/GER_region_game/panel/support_bar_full.png"
        textureFile2 = "gfx/interface/GER_region_game/panel/support_bar_empty.png"
        size = { x = 158 y = 22 }
        effectFile = "gfx/FX/progress.lua"
        horizontal = yes
    }
    progressbartype = {
        name = "GFX_GER_region_panel_control_bar"
        textureFile1 = "gfx/interface/GER_region_game/panel/control_bar_full.png"
        textureFile2 = "gfx/interface/GER_region_game/panel/control_bar_empty.png"
        size = { x = 158 y = 22 }
        effectFile = "gfx/FX/progress.lua"
        horizontal = yes
    }
    # 决议条底板：帧1 普通、帧2 悬停、帧3 选中（暗黄）
    spriteType = {
        name = "GFX_GER_region_panel_decision_row"
        texturefile = "gfx/interface/GER_region_game/panel/decision_row_3f.png"
        noOfFrames = 3
    }
    spriteType = {
        name = "GFX_GER_region_panel_region_photo_frame"
        texturefile = "gfx/interface/GER_region_game/panel/region_photo_frame.png"
    }
    spriteType = {
        name = "GFX_GER_region_panel_leader_photo_frame"
        texturefile = "gfx/interface/GER_region_game/panel/leader_photo_frame.png"
    }
    spriteType = {
        name = "GFX_GER_region_panel_region_photo_vignette"
        texturefile = "gfx/interface/GER_region_game/panel/region_photo_vignette.png"
    }
    spriteType = {
        name = "GFX_GER_region_panel_leader_photo_vignette"
        texturefile = "gfx/interface/GER_region_game/panel/leader_photo_vignette.png"
    }
    spriteType = {
        name = "GFX_GER_region_panel_map_corner_shade"
        texturefile = "gfx/interface/GER_region_game/panel/map_corner_shade.png"
    }

    # 地区照片条带（16 帧，脚本拼）、领导人头像（引用模组现成的 156x210 头像）
    {{GEN:panel_sprites}}

    # 地图素材：像素对齐，GUI 里一律 scale = 1，不要缩放。
    {{GEN:sprites}}
}
"""

# ---------------------------------------------------------------- .gui 地图层
def icon(name, sprite, x, y, frame=None, transparent=True, extra=()):
    s = ["iconType = {",
         '    name = "%s"' % name,
         '    spriteType = "%s"' % sprite,
         "    position = { x = %d y = %d }" % (x, y)]
    if frame:
        s.append("    frame = %d" % frame)
    s += ["    " + e for e in extra]
    if transparent:
        s.append("    alwaystransparent = yes")
    s.append("}")
    return s


SILENT_CLICK = "GER_region_silent_click"   # sound/GER_region_game.asset：click_default 的音量 0 版本


def button(name, sprite, x, y, tt=None, sound=True):
    s = ["buttonType = {",
         '    name = "%s"' % name,
         '    quadTextureSprite = "%s"' % sprite,
         "    position = { x = %d y = %d }" % (x, y)]
    if tt:
        s.append('    pdx_tooltip = "%s"' % tt)
    s.append("    clicksound = %s" % ("click_default" if sound else SILENT_CLICK))
    s.append("}")
    return s


AL, AL_H = M14["GER_reg_alsace_lorraine"], M14["GER_reg_alsace_lorraine_hit"]
BC, BC_H = M14["GER_reg_bav_corner"], M14["GER_reg_bav_corner_hit"]
LK, LK_H = M14["GER_map_locked_all"], M14["GER_map_locked_all_hit"]

L = []
L.append("# 层 1：最底层 羊皮纸 / 海 / 水纹（一直显示）")
L += icon("GER_region_base", SP_BASE, 0, 0)
L.append("# 层 2：阿尔萨斯-洛林、巴伐利亚缺角斜线块（一直显示）")
L += icon("GER_region_alsace_lorraine", "GFX_GER_region_alsace_lorraine_fill", AL["x"], AL["y"])
L += icon("GER_region_bav_corner", "GFX_GER_region_bav_corner_fill", BC["x"], BC["y"])
L.append("# 层 3：整块斜线层（一直显示，永不隐藏）")
L += icon("GER_region_locked_all", "GFX_GER_region_locked_all", LK["x"], LK["y"])
L.append("# 层 4：16 个区块精灵（%d 帧）。默认隐藏；帧号 = var:GER_region_Rxx_frame" % REGION_FRAMES)
for r in regions:
    L += icon(r["el_fill"], r["sp_fill"], r["x"], r["y"], frame=2)
L.append("# 层 5：割让盖板（默认全部隐藏）")
for o in overlays:
    L += icon(o["el_fill"], o["sp_fill"], o["x"], o["y"])
L.append("# 层 6：德国外轮廓线（透明底，不接收鼠标）")
L += icon("GER_region_outline", SP_OUTLINE, 0, 0)
L.append("# 层 7：点击层。后写的先接收鼠标：整块德国 -> 区块 -> 盖板 -> 阿洛 / 巴伐利亚缺角")
L += button("GER_region_locked_all_button", "GFX_GER_region_locked_all_hit", LK_H["x"], LK_H["y"],
            "GER_region_locked_all_tt", sound=False)     # 斜线 / 割让盖板 / 阿洛 / 缺角：只有悬停黄线和提示，没有点击音
for r in regions:
    L += button(r["el_btn"], r["sp_hit"], r["x"], r["y"], r["tooltip"])   # 第一行「地区名：类型」+ 手写介绍
for o in overlays:
    L += button(o["el_btn"], o["sp_hit"], o["x"], o["y"], o["tt"], sound=False)
L += button("GER_region_alsace_lorraine_button", "GFX_GER_region_alsace_lorraine_hit", AL_H["x"], AL_H["y"],
            "GER_region_alsace_lorraine_tt", sound=False)
L += button("GER_region_bav_corner_button", "GFX_GER_region_bav_corner_hit", BC_H["x"], BC_H["y"],
            "GER_region_bav_corner_tt", sound=False)
GUI_MAP = "\n".join(L)


def tbox(name, x, y, text, w, h=24, font="hoi_16mbs", fmt="left", tt=None):
    # 没有悬停提示的文字框一律 alwaystransparent：实测文字框会挡住下面按钮的悬停帧和悬停提示
    s = ["instantTextboxType = {",
         '    name = "%s"' % name,
         "    position = { x = %d y = %d }" % (x, y),
         '    font = "%s"' % font,
         '    text = "%s"' % text,
         "    maxWidth = %d" % w,
         "    maxHeight = %d" % h,
         "    format = %s" % fmt]
    s.append('    pdx_tooltip = "%s"' % tt if tt else "    alwaystransparent = yes")
    return s + ["}"]


def box(name, x, y, w, h, children):
    return (["containerWindowType = {",
             '    name = "%s"' % name,
             "    position = { x = %d y = %d }" % (x, y),
             "    size = { width = %d height = %d }" % (w, h),
             '    background = { name = "%s_bg" quadTextureSprite = "GFX_GER_region_game_frame" }' % name]
            + ["    " + c for c in children] + ["}"])


# 右侧面板（窗口坐标，修改说明_右侧面板.md 第 3 节；照片/头像/压暗坐标取自 右侧面板素材/素材清单.json）
# 绘制顺序 = 写的顺序，后写的盖在上面。装饰层都 alwaystransparent，不挡地图点击。
RPH, LPH = PJ["region_photo"], PJ["leader_photo"]
P = []
P.append("# 1 地图右下角轻微压暗（装饰）")
P += icon("GER_region_panel_map_shade", "GFX_GER_region_panel_map_corner_shade", *PJ["map_corner_shade"]["pos"])
P.append("# 2-5 地区照片：框（带阴影，框内是深色底）→ 照片（%d 帧，帧号 = GER_region_selected）→ 暗角 → 说明" % len(regions))
P += icon("GER_region_panel_photo_frame", "GFX_GER_region_panel_region_photo_frame", *RPH["sprite_pos_window"])
P += icon("GER_region_panel_photo", "GFX_GER_region_panel_photos", *RPH["photo_pos_window"])
P += icon("GER_region_panel_photo_idle", "GFX_GER_region_panel_photo_idle", *RPH["photo_pos_window"])
# 暗角接收鼠标：悬停提示 = 选中地区在地图上的提示，没选中时 = 待机提示
P += icon("GER_region_panel_photo_vignette", "GFX_GER_region_panel_region_photo_vignette", *RPH["photo_pos_window"],
          transparent=False, extra=['pdx_tooltip = "GER_region_panel_photo_tooltip"'])
_cx, _cy, _cw, _ch = RPH["caption_rect_window"]
CAPTION_DY = 3     # 说明条文字比条顶下移几像素（用户看图要求「稍微降一点」）
_NAME_W = 160      # 左：地区名；右：地区类型 / 待机时的一句话（右边更长，给宽一些）
P += tbox("GER_region_panel_photo_name", _cx + 4, _cy + CAPTION_DY, "GER_region_panel_photo_name", _NAME_W, _ch)
P += tbox("GER_region_panel_photo_status", _cx + 4 + _NAME_W, _cy + CAPTION_DY, "GER_region_panel_photo_status",
          _cw - 8 - _NAME_W, _ch, fmt="right")
P.append("# 6-9 领导人：框（带阴影）→ 头像（每人一个，scale %s，按 GER_region_sel_leader 切换）→ 暗角（带悬停提示）→ 名字"
         % PJ["leader_portrait_scale"])
# 领导人整组右移，让领导人框的右边与地区照片框的右边对齐（两框都按 frame_pos + frame_size 算）
LEADER_DX = (RPH["frame_pos_window"][0] + RPH["frame_size"][0]) - (LPH["frame_pos_window"][0] + LPH["frame_size"][0])


def _ld(pos):
    return pos[0] + LEADER_DX, pos[1]


P += icon("GER_region_panel_leader_frame", "GFX_GER_region_panel_leader_photo_frame", *_ld(LPH["sprite_pos_window"]))
for ld in leaders:
    if ld.get("sp"):
        P += icon(ld["el"], ld["sp"], *_ld(LPH["photo_pos_window"]), extra=["scale = %s" % PJ["leader_portrait_scale"]])
P += icon("GER_region_panel_leader_vignette", "GFX_GER_region_panel_leader_photo_vignette", *_ld(LPH["photo_pos_window"]),
          transparent=False, extra=['pdx_tooltip = "GER_region_panel_leader_tt"'])
_lx, _ly, _lw, _lh = LPH["caption_rect_window"]
P += tbox("GER_region_panel_leader_name", _lx + LEADER_DX, _ly + CAPTION_DY, "GER_region_panel_leader_name", _lw, _lh,
          fmt="centre")

P.append("# 10 名称框：区名居中（地区类型写在地图悬停提示的第一行）")
P += box("GER_region_game_name_box", 1281, 13, 282, 42, [
    *tbox("GER_region_game_name_box_text", 0, 42 // 2 - 9, "GER_region_game_selected_name", 282, 26, "hoi_18mbs", "centre"),
])
P.append("# 11-15 数值框：支持度 / 控制度（只在非核心区显示）。字样、进度条、百分比都带悬停提示")
P += box("GER_region_panel_values", 1281, 57, 320, 92, [
    *tbox("GER_region_panel_support_label", 1297 - 1281, 75 - 57, "GER_region_game_support_label", 70,
          tt="GER_region_panel_support_tooltip"),
    *icon("GER_region_panel_support_bar", "GFX_GER_region_panel_support_bar", 1371 - 1281, 74 - 57,
          transparent=False, extra=['pdx_tooltip = "GER_region_panel_support_tooltip"']),
    *tbox("GER_region_panel_support_value", 1585 - 1281 - 60, 75 - 57, "GER_region_panel_support_value", 60,
          fmt="right", tt="GER_region_panel_support_tooltip"),
    *tbox("GER_region_panel_control_label", 1297 - 1281, 107 - 57, "GER_region_game_control_label", 70,
          tt="GER_region_panel_control_tooltip"),
    *icon("GER_region_panel_control_bar", "GFX_GER_region_panel_control_bar", 1371 - 1281, 106 - 57,
          transparent=False, extra=['pdx_tooltip = "GER_region_panel_control_tooltip"']),
    *tbox("GER_region_panel_control_value", 1585 - 1281 - 60, 107 - 57, "GER_region_panel_control_value", 60,
          fmt="right", tt="GER_region_panel_control_tooltip"),
])
P.append("# 16-17 核心区方块（只在左派 / 右派 / 魏玛联盟核心区显示，和数值框互换）。标题居中，说明在悬停提示里")
for f, side in sorted(CORE_FRAMES.items()):
    P += icon("GER_region_panel_core_%s" % side, "GFX_GER_region_panel_core_%s" % side, 1285, 61,
              transparent=False, extra=['pdx_tooltip = "GER_region_panel_core_tooltip"'])
P += tbox("GER_region_panel_core_title", 1285, 61 + 84 // 2 - 9, "GER_region_panel_core_title", 312, 26,
          "hoi_18mbs", "centre")

P.append("# 18-22 决议总框：标题「行动方针」+ 可滚动列表。列表每条 = 一个 GER_region_panel_entry（见 GUI_ENTRY），")
P.append("# 内容来自数组 GER_region_panel_list（GER_region_game_sync_selected 按 ACTION_ORDER 和各条 _visible 条件重建）")
_AX, _AY = 1281, 150
ROW_W, ROW_H = 292, 48
LIST_X, LIST_Y = 1295 - _AX, 200 - _AY          # 第一条的位置（与原来固定排布相同）
TITLE_X, TITLE_Y = 1297 - _AX, 166 - _AY        # 「行动方针」标题
_act = tbox("GER_region_panel_actions_title", TITLE_X, TITLE_Y, "GER_region_game_policy_label", 200, 26, "hoi_18mbs")
_act += ["containerWindowType = {",
         '    name = "GER_region_panel_list_area"',
         "    position = { x = %d y = %d }" % (LIST_X, LIST_Y),
         "    size = { width = %d height = %d }" % (320 - LIST_X, 731 - LIST_Y - 8),
         '    verticalScrollbar = "right_vertical_slider"',
         "    scroll_wheel_factor = %d" % ROW_H,
         "    smooth_scrolling = yes",
         "    gridboxType = {",
         '        name = "GER_region_panel_list"',
         "        position = { x = 0 y = 0 }",
         "        size = { width = %d height = 100%%%% }" % ROW_W,
         "        slotsize = { width = %d height = %d }" % (ROW_W, ROW_H),
         '        format = "UPPER_LEFT"',
         "        max_slots_horizontal = 1",
         "    }",
         "}"]
P += box("GER_region_panel_actions", _AX, _AY, 320, 731, _act)

# 列表的一条（v = 决议编号；v = 0 是「驻区方针」小标题）。
# 实测：scripted_gui 用 properties 给按钮设 frame 后，引擎不再自动切悬停帧 2。
# 所以按钮本身不设 frame（帧1 普通 / 帧2 悬停 交给引擎），生效中时在上面盖一张帧 3 的图标（不挡鼠标）。
# 小标题与下一条的距离 = 「行动方针」标题与第一条的距离（LIST_Y - TITLE_Y），字体相同。
_E = ["containerWindowType = {",
      '    name = "GER_region_panel_entry"',
      "    position = { x = 0 y = 0 }",
      "    size = { width = %d height = %d }" % (ROW_W, ROW_H)]
_E += ["    " + s for s in button("GER_region_panel_entry_button", "GFX_GER_region_panel_decision_row", 0, 0,
                                  "GER_region_panel_entry_tooltip")]
_E += ["    " + s for s in icon("GER_region_panel_entry_selected", "GFX_GER_region_panel_decision_row", 0, 0, frame=3)]
_E += ["    " + s for s in tbox("GER_region_panel_entry_name", 14, 11, "GER_region_panel_entry_name", 180, 22)]
_E += ["    " + s for s in tbox("GER_region_panel_entry_status", ROW_W - 14 - 120, 11, "GER_region_panel_entry_status",
                                120, 22, fmt="right")]
_E += ["    " + s for s in tbox("GER_region_panel_entry_header", TITLE_X - LIST_X, ROW_H - (LIST_Y - TITLE_Y),
                                "GER_region_panel_garrison_label", 200, 26, "hoi_18mbs", tt="GER_region_panel_garrison_tt")]
_E.append("}")
GUI_ENTRY = "\n".join(_E)
GUI_PANEL = "\n".join(P)

GUI_TEMPLATE = """guiTypes = {
    # 决议列表的一条（scripted_gui 的 dynamic_lists 用）
    {{GEN:list_entries}}

    # 入口按钮：右下角，议会按钮（GER_yihui_entry_bg，y = -360，100x100）正上方
    containerWindowType = {
        name = "GER_region_game_entry_bg"
        position = { x = 0 y = -470 }
        Orientation = LOWER_RIGHT
        Origo = LOWER_RIGHT
        size = { width = 148 height = 34 }
        buttonType = {
            name = "GER_region_game_button"
            quadTextureSprite = "GFX_button_148x34"
            position = { x = 0 y = 0 }
            buttonText = "GER_region_game_entry_text"
            buttonFont = "hoi_18mbs"
            pdx_tooltip = "GER_region_game_entry_tt"
            clicksound = click_default
        }
    }

    containerWindowType = {
        name = "GER_region_game_window"
        position = { x = 0 y = -1100 }
        Orientation = center
        Origo = center
        size = { width = %(W)d height = %(H)d }
        moveable = yes
        # 打开时从屏幕上方慢慢滑下来（写法同 AOR_supernews.gui）
        show_position = { x = 0 y = 0 }
        hide_position = { x = 0 y = -1100 }
        animation_time = 500
        show_animation_type = decelerated
        hide_animation_type = accelerated

        background = {
            name = "GER_region_game_bg"
            quadTextureSprite = "GFX_tiled_plain_bg"
        }
        # 内缩 1 像素的 lined 层；alwaystransparent 让鼠标穿透到窗口本身，拖动照常
        buttonType = {
            name = "GER_region_game_lined_overlay"
            position = { x = 1 y = 1 }
            size = { x = %(W2)d y = %(H2)d }
            quadTextureSprite = "GFX_tiled_plain_bg_lined"
            alwaystransparent = yes
        }

        # 顶部引言框
        containerWindowType = {
            name = "GER_region_game_quote_box"
            position = { x = %(MX)d y = 12 }
            size = { width = %(CW)d height = 44 }
            background = { name = "GER_region_game_quote_box_bg" quadTextureSprite = "GFX_GER_region_game_frame" }
            instantTextboxType = {
                name = "GER_region_game_quote_text"
                position = { x = 10 y = 14 }
                font = "hoi_16mbs"
                text = "GER_region_game_quote"
                maxWidth = %(CW10)d
                maxHeight = 22
                format = centre
            }
        }

        # 地图画布 1248 x 813：所有图层位置都相对画布左上角，取自素材清单
        containerWindowType = {
            name = "GER_region_game_map"
            position = { x = %(MX)d y = %(MY)d }
            size = { width = %(CW)d height = %(CH)d }
            {{GEN:map_layers}}
        }

        # 右侧面板 + 盖在地图右下角的照片、领导人（坐标是窗口坐标）
        {{GEN:right_panel}}

        buttonType = {
            name = "close_button"
            position = { x = -40 y = 8 }
            quadTextureSprite = "GFX_profile_button_close"
            shortcut = "ESCAPE"
            Orientation = "UPPER_RIGHT"
            pdx_tooltip = "CLOSE"
        }
    }
}
""" % {"W": WIN_W, "H": WIN_H, "W2": WIN_W - 2, "H2": WIN_H - 2, "MX": MAP_X, "MY": MAP_Y,
       "CW": CANVAS_W, "CH": CANVAS_H, "CW10": CANVAS_W - 20}

# ---------------------------------------------------------------- scripted_gui
props = ["%s = { frame = var:%s }" % (r["el_fill"], r["v_frame"]) for r in regions]
trig = ["# 区块：显示 = 已开放（GER_region_Rxx_open = 1）；隐藏时不画、不挡鼠标"]
for r in regions:
    trig.append("%s_visible = { check_variable = { %s = 1 } }" % (r["el_fill"], r["v_open"]))
    trig.append("%s_visible = { check_variable = { %s = 1 } }" % (r["el_btn"], r["v_open"]))
trig.append("# 割让盖板：显示 = GER_region_OV_xxx_shown = 1；盖板点击图只出提示，不写 click 效果")
trig.append("# 互斥：西里西亚 A 方案（1134+762）包含 B 方案（762），A 显示时 B 一律不画")
ov_by_id = {o["id"]: o for o in overlays}
for o in overlays:
    cond = "check_variable = { %s = 1 }" % o["v_shown"]
    hider = OVERLAY_HIDDEN_BY.get(o["id"])
    if hider:
        cond += " NOT = { check_variable = { %s = 1 } }" % ov_by_id[hider]["v_shown"]
    trig.append("%s_visible = { %s }" % (o["el_fill"], cond))
    trig.append("%s_visible = { %s }" % (o["el_btn"], cond))

# ---- 右侧面板：显示的都是「选中地区」的镜像变量 GER_region_sel_*，由 GER_region_game_sync_selected 拷贝
props += ["GER_region_panel_photo = { frame = var:GER_region_selected }",
          "GER_region_panel_support_bar = { frame = var:GER_region_sel_support }",
          "GER_region_panel_control_bar = { frame = var:GER_region_sel_control }"]
SEL ="check_variable = { GER_region_selected > 0 }"
CORE_ANY = " ".join("check_variable = { GER_region_sel_frame = %d }" % f for f in sorted(CORE_FRAMES))
trig.append("# 右侧面板：照片、照片说明只在选中地区后显示；没选中（含整块斜线时）显示待机照片")
trig.append("GER_region_panel_photo_visible = { %s }" % SEL)
trig.append("GER_region_panel_photo_idle_visible = { NOT = { %s } }" % SEL)
trig.append("# 领导人头像：按选中地区的领导人序号（GER_region_sel_leader）切换；没头像的领导人只显示名字")
for ld in leaders:
    if ld.get("sp"):
        trig.append("%s_visible = { check_variable = { GER_region_sel_leader = %d } }" % (ld["el"], ld["idx"]))
trig.append("GER_region_panel_leader_vignette_visible = { check_variable = { GER_region_sel_leader > 0 } }")
trig.append("# 数值框 <-> 核心区方块：帧 %s = 核心区，显示方块；其余显示支持度 / 控制度"
            % "/".join(str(f) for f in sorted(CORE_FRAMES)))
trig.append("# 待机（没选中地区）：数值框不显示，用 %s 方块罩住，上面写 GER_region_panel_idle_cover" % IDLE_COVER)
trig.append("GER_region_panel_values_visible = { %s NOT = { %s } }" % (SEL, CORE_ANY))
assert IDLE_COVER in CORE_FRAMES.values()
for f, side in sorted(CORE_FRAMES.items()):
    if side == IDLE_COVER:
        trig.append("GER_region_panel_core_%s_visible = { OR = { check_variable = { GER_region_sel_frame = %d } NOT = { %s } } }"
                    % (side, f, SEL))
    else:
        trig.append("GER_region_panel_core_%s_visible = { check_variable = { GER_region_sel_frame = %d } }" % (side, f))
trig.append("GER_region_panel_core_title_visible = { OR = { %s NOT = { %s } } }" % (CORE_ANY, SEL))
trig.append("# 「行动方针」标题：地图全开之后，或阶段博弈进行中才显示（列表内容同理，见 GER_region_game_sync_selected）")
trig.append("GER_region_panel_actions_title_visible = { OR = { %s %s } }" % (MAP_OPENED, PHASE_ANY))
trig.append("# 决议列表（dynamic_lists）：每条的 v = 决议编号；v = 0 是「驻区方针」小标题")
trig.append("GER_region_panel_entry_header_visible = { check_variable = { v = 0 } }")
for _el in ("GER_region_panel_entry_button", "GER_region_panel_entry_name", "GER_region_panel_entry_status"):
    trig.append("%s_visible = { check_variable = { v > 0 } }" % _el)
trig.append("# 生效中的条盖上帧 3（每条各自计时，可以同时好几条）")
trig.append("GER_region_panel_entry_selected_visible = {\n    OR = {")
for row in ROWS:
    trig.append("        AND = { check_variable = { v = %d } %s }" % (row["n"], row["active"]))
trig.append("    }\n}")
trig.append("# 能否点击：选中了地区、不在生效中、政治点数够、该地区次数没满；驻区方针还要左派核心区或双满；")
trig.append("# 再加上 %s 里的 GER_region_action_N_allowed（冷却、解锁条件等）" % ACTIONS_TRIGGERS)
trig.append("GER_region_panel_entry_button_click_enabled = {\n    check_variable = { GER_region_selected > 0 }\n    OR = {")
for row in ROWS:
    c = "check_variable = { v = %d } NOT = { %s } %s" % (row["n"], row["active"], row["pp_ok"])
    if row["max"]:
        c += " check_variable = { %s < %d }" % (row["sel_count"], row["max"])
    if row["cooldown"]:
        c += " NOT = { check_variable = { %s > 0 } }" % row["sel_cd"]
    if row["garrison"]:
        c += " " + GARRISON_OPEN
    trig.append("        AND = { %s GER_region_action_%d_allowed = yes }" % (c, row["n"]))
trig.append("    }\n}")
DYN_LISTS = """dynamic_lists = {
    GER_region_panel_list = {
        array = GER_region_panel_list
        entry_container = GER_region_panel_entry
        index = i
        value = v
        change_scope = no   # 不加的话引擎把 v 当作国家 / 省份去切换作用域，点击效果会在错误的作用域里执行
    }
}"""

SGUI_TEMPLATE = """scripted_gui = {
    # 右下角入口按钮：打开 / 关闭地区博弈界面
    GER_region_game_button = {
        context_type = player_context
        window_name = "GER_region_game_entry_bg"
        visible = { original_tag = GER }
        effects = {
            GER_region_game_button_click = {
                if = {
                    limit = { has_country_flag = GER_region_game_open }
                    clr_country_flag = GER_region_game_open
                }
                else = {
                    set_country_flag = GER_region_game_open
                    GER_region_game_sync_selected = yes
                }
            }
        }
    }

    # 地区博弈主界面
    # 接口（全部存在本国变量里，没设过 = 开局状态）：
    #   GER_region_Rxx_open    = 1      区块已开放（显示精灵 + 点击条）
    #   GER_region_Rxx_state   = 1..12  地区类型 = 帧号：1 斜线 2 摇摆 3 左核 4 右核 5 魏玛核 6 特殊 7 备用
    #                                   8 左控 9 右控 10 魏玛控 11 特殊控 12 备用控
    #   GER_region_Rxx_frame            实际显示帧，GER_region_game_sync_frames 从 state 拷贝
    #   GER_region_Rxx_support / _control = 0..100   支持度 / 控制度
    #   GER_region_Rxx_leader  = 1..N   领导人序号（见 gen_region_game.py 的 LEADERS），0 = 无
    #   GER_region_OV_<id>_shown = 1    显示对应割让盖板
    #   GER_region_selected = 1..16     最后点击的区块；右侧面板显示它
    #   GER_region_Rxx_act_N   = 天数   日常决议 N 在该地区还剩几天（>0 = 生效中，条显示帧 3）
    #   GER_region_Rxx_policy  = 9..12  该地区当前驻区方针，0 = 无
    # 改了上面任何变量后跑一次 GER_region_game_sync_frames = yes，地图和右侧面板才会刷新。
    GER_region_game_gui = {
        context_type = player_context
        window_name = "GER_region_game_window"
        visible = {
            original_tag = GER
            has_country_flag = GER_region_game_open
        }
        {{GEN:dynamic_lists}}
        properties = {
            {{GEN:properties}}
        }
        triggers = {
            {{GEN:triggers}}
        }
        effects = {
            close_button_click = {
                clr_country_flag = GER_region_game_open
            }
            {{GEN:effects}}
        }
    }
}
"""

clicks = ["# 点击区块：记下选中的区块，右侧面板随之显示该区块"]
for r in regions:
    clicks.append("%s_click = { set_variable = { GER_region_selected = %d } GER_region_game_sync_selected = yes }"
                  % (r["el_btn"], r["idx"]))
clicks.append("# 斜线 / 割让盖板 / 阿洛 / 缺角：只悬停（黄线 + 提示）。点击什么都不做、没有声音，也不落到下面的区块")
NOOP = "set_temp_variable = { GER_region_noop = 1 }"
for el in ["GER_region_locked_all_button", "GER_region_alsace_lorraine_button", "GER_region_bav_corner_button"] + \
          [o["el_btn"] for o in overlays]:
    clicks.append("%s_click = { %s }" % (el, NOOP))
clicks.append("# 行动方针条 = 决议：点击扣政治点数、开始计时、执行 GER_region_action_N（效果写在 %s）。" % ACTIONS_EFFECTS)
clicks.append("# 能不能点见 triggers 里的 _click_enabled。")
clicks.append("GER_region_panel_entry_button_click = {")
for row in ROWS:
    clicks.append("    if = { limit = { check_variable = { v = %d } } GER_region_game_take_action_%d = yes }" % (row["n"], row["n"]))
clicks.append("}")


# 条件勾叉：名字 -> 触发器（选中地区的镜像变量 GER_region_sel_*）
CHECKS = {
    "GER_region_check_garrison_open": GARRISON_OPEN,
    "GER_region_check_party_reform": "GER_region_party_reform_done = yes",
    "GER_region_check_shipbuilding": "GER_region_shipbuilding_socialized = yes",
    "GER_region_check_swing": "check_variable = { GER_region_sel_frame = 2 }",
    "GER_region_check_support_50": "check_variable = { GER_region_sel_support > 49.99 }",
    "GER_region_check_control_80": "check_variable = { GER_region_sel_control > 79.99 }",
}
CHECKS["GER_region_check_left_core"] = "check_variable = { GER_region_sel_frame = 3 }"
CHECKS["GER_region_check_support_100"] = "check_variable = { GER_region_sel_support > 99.99 }"
CHECKS["GER_region_check_control_100"] = "check_variable = { GER_region_sel_control > 99.99 }"
CHECKS["GER_region_check_double_full"] = ("check_variable = { GER_region_sel_support > 99.99 } "
                                          "check_variable = { GER_region_sel_control > 99.99 }")
for _row in ROWS:
    if _row["cooldown"]:
        CHECKS["GER_region_check_cd_%d" % _row["n"]] = "NOT = { check_variable = { %s > 0 } }" % _row["sel_cd"]
for _row in COUNTED:
    CHECKS["GER_region_check_count_%d" % _row["n"]] = "check_variable = { %s < %d }" % (_row["sel_count"], _row["max"])
for _row in ROWS:   # 阶段决议：「已执行过第 N 条」（读该阶段地区自己的执行次数）
    if _row["phase"]:
        CHECKS["GER_region_check_did_%d" % _row["n"]] = ("check_variable = { GER_region_%s_count_%d > 0 }"
                                                         % (_row["region"], _row["n"]))


def defined_text(name, cases, default):
    """cases = [(触发器, 本地化键)]"""
    out = ["defined_text = {", "    name = %s" % name]
    for trg, key in cases:
        out.append("    text = { trigger = { %s } localization_key = %s }" % (trg, key))
    out += ["    text = { localization_key = %s }" % default, "}"]
    return out


def is_sel(i):
    return "check_variable = { GER_region_selected = %d }" % i


sl =["# 由 %s 生成，不要手改。" % GEN_TAG, "",
      "# 名称框 / 照片说明：选中区块名，没选时显示占位"]
sl += defined_text("GER_region_selected_name", [(is_sel(r["idx"]), r["name_key"]) for r in regions],
                   "GER_region_game_selected_none")
sl.append("# 地图悬停提示第一行：「地区名：类型」（按该区块自己的帧号；没有类型名的帧只写地区名）")
for r in regions:
    sl += defined_text(r["head"], [("check_variable = { %s = %d }" % (r["v_frame"], f), "%s_%d" % (r["head"], f))
                                   for f in sorted(TYPE_NAMES)], r["head"] + "_none")
sl.append("# 悬停提示里引用手写文字用的别名（悬停提示不认 $键$，只认 [scripted loc]）")
for r in regions:
    sl += defined_text(r["body"], [], r["tt"])
sl += defined_text("GER_region_panel_support_body", [], "GER_region_panel_support_tt")
sl += defined_text("GER_region_panel_control_body", [], "GER_region_panel_control_tt")
sl.append("# 核心区方块的标题：地区类型（按选中区块的帧号）")
sl += defined_text("GER_region_sel_type",
                   [("check_variable = { GER_region_sel_frame = %d }" % f, "GER_region_type_%d" % f)
                    for f in sorted(TYPE_NAMES)], "GER_region_panel_empty")
sl.append("# 核心区方块上的字 / 悬停提示：待机（没选中地区）时 = 手写的 GER_region_panel_idle_cover / GER_region_panel_idle_tt")
sl += defined_text("GER_region_panel_core_title_text", [("NOT = { %s }" % SEL, "GER_region_panel_idle_cover")],
                   "GER_region_panel_core_title_type")
sl += defined_text("GER_region_panel_core_tt", [("NOT = { %s }" % SEL, "GER_region_panel_idle_tt")],
                   "GER_region_panel_core_tooltip_sel")
sl.append("# 核心区方块的说明")
sl += defined_text("GER_region_sel_core_desc",
                   [("check_variable = { GER_region_sel_frame = %d }" % f, "GER_region_panel_core_%d_desc" % f)
                    for f in sorted(CORE_FRAMES)], "GER_region_panel_empty")
sl.append("# 照片说明条：选中地区时 = 地区名 / 地区类型；待机时 = 手写的两句（GER_region_panel_idle_name / _status）")
sl += defined_text("GER_region_panel_photo_name_text", [(is_sel(r["idx"]), r["name_key"]) for r in regions],
                   "GER_region_panel_idle_name")
sl += defined_text("GER_region_panel_photo_status_text", [(SEL, "GER_region_panel_photo_type")],
                   "GER_region_panel_idle_status")
sl.append("# 地区照片的悬停提示：与地图上该区块的提示相同；没选中时用待机提示（手写）")
sl += defined_text("GER_region_panel_photo_tt", [(is_sel(r["idx"]), r["tooltip"]) for r in regions],
                   "GER_region_panel_idle_tt")
sl.append("# 领导人名字 / 悬停提示")
sl += defined_text("GER_region_sel_leader_name",
                   [("check_variable = { GER_region_sel_leader = %d }" % ld["idx"], ld["name_key"]) for ld in leaders],
                   "GER_region_panel_empty")
sl += defined_text("GER_region_sel_leader_tt",
                   [("check_variable = { GER_region_sel_leader = %d }" % ld["idx"], ld["tt"]) for ld in leaders],
                   "GER_region_panel_empty")
sl.append("# 行动方针条：名字（驻区方针双满之前灰色）和右侧状态")
sl.append("# 状态优先级：生效中(绿) > 未满足双满(灰) > 条件不满足(灰) > 政治点数不够(红) > 可点(金)")
for row in ROWS:
    n = row["n"]
    allowed = "GER_region_action_%d_allowed = yes" % n
    if row["garrison"]:
        sl += defined_text("GER_region_row_%d_label" % n, [(GARRISON_OPEN, row["name"])], row["name"] + "_locked")
    cases = []
    if row["garrison"]:
        cases.append((row["active"], "GER_region_panel_status_policy_on"))
        cases.append(("NOT = { AND = { %s } }" % GARRISON_OPEN, "GER_region_panel_row_%d_status_grey" % n))
    elif row["days"]:
        cases.append((row["active"], "GER_region_panel_row_%d_status_days" % n))
    if row["cooldown"]:
        cases.append(("check_variable = { %s > 0 }" % row["sel_cd"], "GER_region_panel_row_%d_status_cd" % n))
    if row["max"]:
        cases.append(("check_variable = { %s > %d }" % (row["sel_count"], row["max"] - 1),
                      "GER_region_panel_row_%d_status_grey" % n))
    cases.append(("NOT = { %s }" % allowed, "GER_region_panel_row_%d_status_grey" % n))
    cases.append(("NOT = { %s }" % row["pp_ok"], "GER_region_panel_row_%d_status_red" % n))
    sl += defined_text("GER_region_row_%d_status" % n, cases, "GER_region_panel_row_%d_status_gold" % n)
sl.append("# 决议列表条目（v = 决议编号）：名字、右侧状态、悬停提示（手写 GER_region_panel_row_N_tt）")
sl += defined_text("GER_region_entry_name", [("check_variable = { v = %d }" % row["n"],
                                             "GER_region_panel_row_%d_label" % row["n"]) for row in ROWS],
                   "GER_region_panel_empty")
sl += defined_text("GER_region_entry_status", [("check_variable = { v = %d }" % row["n"],
                                               "GER_region_panel_row_%d_status" % row["n"]) for row in ROWS],
                   "GER_region_panel_empty")
sl += defined_text("GER_region_entry_tt", [("check_variable = { v = %d }" % row["n"], row["tt"]) for row in ROWS],
                   "GER_region_panel_empty")
sl.append("# 决议悬停提示里的条件勾叉（仿原版：£trigger_yes / £trigger_no）。手写提示里用 [名字] 引用")
for _name, _trg in sorted(CHECKS.items()):
    sl += defined_text(_name, [(_trg, "GER_region_check_yes")], "GER_region_check_no")
SCRIPTED_LOC = "\n".join(sl) + "\n"
_SL2_PENDING = True

# ---------------------------------------------------------------- 开局设定（用户给定：地图全开后的 GUI 开局）
# 左翼核心：汉堡-石荷、图林根-萨克森、鲁尔；右翼核心：巴伐利亚、东普鲁士、波美拉尼亚、汉诺威；
# 特殊区：莱茵兰；共和（魏玛联盟）核心：巴登-符腾堡；其余 7 个是摇摆区。
OPENING_TYPES = {"R03": 3, "R08": 3, "R14": 3, "R09": 4, "R13": 4, "R05": 4, "R02": 4, "R12": 6, "R10": 5,
                 "R16": 2, "R15": 2, "R01": 2, "R07": 2, "R06": 2, "R04": 2, "R11": 2}
OPENING_VALUES = {"R06": (51, 30), "R11": (46, 35), "R15": (39, 35), "R04": (45, 20), "R07": (15, 5),
                  "R01": (43, 60), "R16": (60, 75)}     # 摇摆区 (支持度, 控制度)
# 开局领导人（用户给定；巴伐利亚、东普鲁士、莱茵兰暂无）。没有头像的只显示名字。
OPENING_LEADERS = {"R16": "daeumig", "R11": "dissmann",
                   "R06": "paul_hirsch", "R05": "paul_hirsch", "R04": "paul_hirsch",
                   "R10": "weimar_coalition", "R03": "paul_dittmann", "R14": "committee_nine",
                   "R08": "lipinski", "R02": "lipinski", "R15": "lipinski",
                   "R01": "henke", "R07": "bitta"}
# 地图全开时一并显示的割让盖板：萨尔（两小块）、欧本-马尔梅迪、波森-西普鲁士-但泽走廊、梅梅尔
OPENING_OVERLAYS = ["SAAR_bump_A", "SAAR_bump_B", "EUPEN_MALMEDY", "POSEN_WPRUSSIA", "MEMEL"]
assert sorted(OPENING_TYPES) == sorted(r["key"] for r in regions)
assert all(OPENING_TYPES[k] == 2 for k in OPENING_VALUES) and sum(v == 2 for v in OPENING_TYPES.values()) == len(OPENING_VALUES)

R_BY_KEY0 = {r["key"]: r for r in regions}
OV_BY_ID0 = {o["id"]: o for o in overlays}
assert all(k in R_BY_KEY0 for k in OPENING_LEADERS) and all(v in LD_BY_KEY0 for v in OPENING_LEADERS.values())
assert all(o in OV_BY_ID0 for o in OPENING_OVERLAYS)

ADJ = {  # 由区块精灵的不透明像素外扩 2px 求得的相邻关系（只用于「相邻不同色」测试）
    "R01": ["R02", "R15"], "R02": ["R01", "R03", "R04", "R06", "R08", "R11", "R15"],
    "R03": ["R02", "R04"], "R04": ["R02", "R03", "R05", "R06"], "R05": ["R04", "R06", "R13"],
    "R06": ["R02", "R04", "R05", "R07", "R08", "R13", "R16"], "R07": ["R06", "R08"],
    "R08": ["R02", "R06", "R07", "R09", "R11"], "R09": ["R08", "R10", "R11"],
    "R10": ["R09", "R11", "R12"], "R11": ["R02", "R08", "R09", "R10", "R12", "R15"],
    "R12": ["R10", "R11", "R14", "R15"], "R13": ["R05", "R06"], "R14": ["R12", "R15"],
    "R15": ["R01", "R02", "R11", "R12", "R14"], "R16": ["R06"],
}
for _k, _ns in ADJ.items():
    assert all(_k in ADJ[_n] for _n in _ns), "ADJ 不对称：" + _k

# 每两周变化的来源（悬停提示里逐条列出）：(键, support/control, 数值或变量, 条件（选中地区）, 名字)
_R = R_BY_KEY0
BW_SOURCES = [
    ("bw3", "control", "0.4", "check_variable = { GER_region_sel_row_3_days > 0 }", "组织网络的扩展"),
    ("bw4", "support", "0.4", "check_variable = { GER_region_sel_row_4_days > 0 }", "推动公共事业"),
    ("bw9", "control", "0.2", "check_variable = { GER_region_sel_policy = 9 }", "扩充安全部队"),
    ("bw13a", "control", "0.1", "check_variable = { GER_region_sel_policy = 13 }", "红色海军网络"),
    ("bw13b", "control", "0.9", "%s check_variable = { GER_region_R03_policy = 13 }" % is_sel(_R["R01"]["idx"]),
     "红色海军网络（§Y汉堡-石荷§!）"),
    ("bw14s", "support", "0.5", "%s check_variable = { GER_region_R14_policy = 14 }" % is_sel(_R["R15"]["idx"]),
     "与基督教社会主义者交好（§Y鲁尔§!）"),
    ("bw14c", "control", "0.5", "%s check_variable = { GER_region_R14_policy = 14 }" % is_sel(_R["R15"]["idx"]),
     "与基督教社会主义者交好（§Y鲁尔§!）"),
    ("bw12", "control", "GER_region_sel_nb12", "check_variable = { GER_region_sel_nb12 > 0 }", "§Y相邻地区§!的支援邻近地区"),
    ("bwg", "control", "GER_region_sel_growth", "check_variable = { GER_region_sel_growth > 0 }", "组织重心向工厂转移（永久）"),
]
for _ld in leaders:
    for _what, _v in LEADER_FX.get(_ld["key"], {}).get("local_bw", []):
        BW_SOURCES.append(("ld_%s_%s" % (_ld["key"], _what), _what, "%g" % _v,
                           "check_variable = { GER_region_sel_leader = %d }" % _ld["idx"], "领导人：§Y%s§!" % _ld["cname"]))
FROZEN_SEL = "OR = { %s }" % " ".join(is_sel(_R[k]["idx"]) for k in FROZEN)


def _is_num(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# ---------------------------------------------------------------- scripted_effects
eff = ["# 由 %s 生成，不要手改。" % GEN_TAG, ""]
eff.append("# 刷新地图和右侧面板：state（= 帧号 1-%d）拷到 frame，再刷新选中地区和行动方针条。" % REGION_FRAMES)
eff.append("# 改了任何 GER_region_* 变量后都跑一次。")
eff.append("GER_region_game_sync_frames = {")
for r in regions:
    eff.append("    set_variable = { %s = %s }" % (r["v_frame"], r["v_state"]))
eff.append("    GER_region_game_update_tiers = yes")
eff.append("    GER_region_game_sync_selected = yes")
eff.append("}")
eff.append("")
eff.append("# 把选中区块（GER_region_selected）的帧号、支持度、控制度、领导人、决议计时、驻区方针拷到 GER_region_sel_*，右侧面板读这些")
eff.append("GER_region_game_sync_selected = {")
eff.append("    # 选中的区块没开放（例如整块斜线时）就当没选，面板显示待机")
for r in regions:
    eff.append("    if = { limit = { %s NOT = { check_variable = { %s = 1 } } } set_variable = { GER_region_selected = 0 } }"
               % (is_sel(r["idx"]), r["v_open"]))
for v in ("frame", "support", "control", "leader", "policy"):
    eff.append("    set_variable = { GER_region_sel_%s = 0 }" % v)
for row in TIMED_ROWS:
    eff.append("    set_variable = { %s = 0 }" % row["sel_days"])
for row in COUNTED:
    eff.append("    set_variable = { %s = 0 }" % row["sel_count"])
for row in COOLED:
    eff.append("    set_variable = { %s = 0 }" % row["sel_cd"])
for v in ("tier", "swing_days", "growth", "nb12"):
    eff.append("    set_variable = { GER_region_sel_%s = 0 }" % v)
for i, r in enumerate(regions):
    eff.append("    %s = {" % ("if" if i == 0 else "else_if"))
    eff.append("        limit = { %s }" % is_sel(r["idx"]))
    eff.append("        set_variable = { GER_region_sel_frame = %s }" % r["v_frame"])
    eff.append("        set_variable = { GER_region_sel_support = %s }" % r["v_support"])
    eff.append("        set_variable = { GER_region_sel_control = %s }" % r["v_control"])
    eff.append("        set_variable = { GER_region_sel_leader = %s }" % r["v_leader"])
    eff.append("        set_variable = { GER_region_sel_policy = %s }" % r["v_policy"])
    for row in TIMED_ROWS:
        eff.append("        set_variable = { %s = %s }" % (row["sel_days"], r["v_act"][row["n"]]))
    for row in COUNTED:
        eff.append("        set_variable = { %s = %s }" % (row["sel_count"], r["v_count"][row["n"]]))
    for row in COOLED:
        eff.append("        set_variable = { %s = %s }" % (row["sel_cd"], r["v_cd"][row["n"]]))
    eff.append("        set_variable = { GER_region_sel_tier = %s }" % r["v_tier"])
    eff.append("        set_variable = { GER_region_sel_swing_days = %s }" % r["v_swing_days"])
    eff.append("        set_variable = { GER_region_sel_growth = %s }" % r["v_growth"])
    for k in ADJ[r["key"]]:
        eff.append("        if = { limit = { check_variable = { GER_region_%s_policy = 12 } } add_to_variable = { GER_region_sel_nb12 = 1 } }" % k)
    eff.append("    }")
eff.append("    else = { set_variable = { GER_region_sel_leader = %d } }   # 待机：%s"
           % (LD_BY_KEY0[IDLE_LEADER]["idx"], LD_BY_KEY0[IDLE_LEADER]["cname"]))
eff.append("    clamp_variable = { var = GER_region_sel_support min = 0 max = 100 }")
eff.append("    clamp_variable = { var = GER_region_sel_control min = 0 max = 100 }")
eff.append("    # 每两周变化合计（悬停提示用；来源见 gen_region_game.py 的 BW_SOURCES，要和手写效果一致）")
eff.append("    set_variable = { GER_region_sel_bw_support = 0 }")
eff.append("    set_variable = { GER_region_sel_bw_control = 0 }")
for _k, _what, _amt, _cond, _label in BW_SOURCES:
    eff.append("    if = { limit = { %s } add_to_variable = { GER_region_sel_bw_%s = %s } }   # %s" % (_cond, _what, _amt, _label))
eff.append("    if = { limit = { %s } set_variable = { GER_region_sel_bw_support = 0 } set_variable = { GER_region_sel_bw_control = 0 } }"
           % FROZEN_SEL)
eff.append("    # 重建决议列表：行动方针 → 0（「驻区方针」小标题）→ 驻区方针；每条按 region 和手写的 _visible 决定是否出现")
eff.append("    # 地图全开（旗标 %s）之前：普通决议和小标题都不出现" % MAP_OPENED_FLAG)
eff.append("    # 阶段博弈（PHASES）进行中：普通决议和小标题都不出现，只出现该阶段的决议")
eff.append("    clear_array = GER_region_panel_list")
for row in ROWS:
    if row is GARRISON[0]:
        eff.append("    if = { limit = { %s NOT = { %s } } add_to_array = { array = GER_region_panel_list value = 0 } }"
                   % (MAP_OPENED, PHASE_ANY))
    cond = "GER_region_action_%d_visible = yes" % row["n"]
    if row["region"]:
        cond = is_sel(R_BY_KEY0[row["region"]]["idx"]) + " " + cond
    if row["phase"]:
        cond = "has_country_flag = %s %s" % (PHASES[row["phase"]]["flag"], cond)
    else:
        cond = "%s NOT = { %s } %s" % (MAP_OPENED, PHASE_ANY, cond)
    eff.append("    if = { limit = { %s } add_to_array = { array = GER_region_panel_list value = %d } }   # %s"
               % (cond, row["n"], row["cname"]))
eff.append("}")
eff.append("")


def on_target(stmts):
    """对 GER_region_target 指向的区块执行 stmts（{key} {support} {control} {state} {floor} {growth} 指代该区块）"""
    out = []
    for i, r in enumerate(regions):
        body = " ".join(s.format(key=r["key"], support=r["v_support"], control=r["v_control"], state=r["v_state"],
                                 floor=r["v_floor"], growth=r["v_growth"]) for s in stmts)
        out.append("    %s = {{ limit = {{ check_variable = {{ GER_region_target = %d }} }} %s }}".replace("{{", "{").replace("}}", "}")
                   % ("if" if i == 0 else "else_if", r["idx"], body))
    return out


eff.append("# ---- 给手写决议效果用的小工具。先 set_temp_variable = { GER_region_delta = 3 }（或 GER_region_value），再调用。")
eff.append("# 支持度、控制度结果夹在 0-100；控制度不低于该地区的下限（影子苏维埃后为 80）。")
eff.append("# 指定地区：GER_region_Rxx_add_support / _add_control（Rxx 见区块 key）")
eff.append("# %s：支持度、控制度不会增长（GER_region_delta > 0 时不加），国策 / 焦点博弈先设 GER_region_force = 1 再调用"
           % "、".join(R_BY_KEY0[k]["name"] for k in FROZEN))
for r in regions:
    lim = ("    if = { limit = { OR = { check_variable = { GER_region_delta < 0.0001 } check_variable = { GER_region_force = 1 } } }"
           if r["key"] in FROZEN else None)
    for what, var in (("support", r["v_support"]), ("control", r["v_control"])):
        body = ["add_to_variable = { %s = GER_region_delta }" % var, "clamp_variable = { var = %s min = 0 max = 100 }" % var]
        if what == "control":
            body.append("if = { limit = { check_variable = { %s < %s } } set_variable = { %s = %s } }"
                        % (r["v_control"], r["v_floor"], r["v_control"], r["v_floor"]))
        eff.append("GER_region_%s_add_%s = {   # %s" % (r["key"], what, r["name"]))
        if lim:
            eff.append(lim)
            eff += ["        " + s for s in body]
            eff.append("    }")
        else:
            eff += ["    " + s for s in body]
        eff.append("}")
eff.append("# 作用于 GER_region_target 指向的地区（决议效果执行时已经设好）")
eff.append("GER_region_target_add_support = {")
eff += on_target(["GER_region_{key}_add_support = yes"])
eff.append("}")
eff.append("GER_region_target_add_control = {")
eff += on_target(["GER_region_{key}_add_control = yes"])
eff.append("}")
eff.append("# 目标地区的相邻地区控制度 + GER_region_delta（相邻关系见 gen_region_game.py 的 ADJ）")
eff.append("GER_region_target_neighbors_add_control = {")
for i, r in enumerate(regions):
    calls = " ".join("GER_region_%s_add_control = yes" % k for k in ADJ[r["key"]])
    eff.append("    %s = { limit = { check_variable = { GER_region_target = %d } } %s }   # %s"
               % ("if" if i == 0 else "else_if", r["idx"], calls, r["name"]))
eff.append("}")
eff.append("# 目标地区类型 = GER_region_value（帧号：2 摇摆 3 左核 8 左控 ……）")
eff.append("GER_region_target_set_state = {")
eff += on_target(["set_variable = {{ {state} = GER_region_value }}"])
eff.append("}")
eff.append("# 目标地区控制度下限 = GER_region_value（之后控制度不会低于它）")
eff.append("GER_region_target_set_control_floor = {")
eff += on_target(["set_variable = {{ {floor} = GER_region_value }}",
                  "if = {{ limit = {{ check_variable = {{ {control} < {floor} }} }} set_variable = {{ {control} = {floor} }} }}"])
eff.append("}")
eff.append("# 目标地区永久「每两周控制度」+ GER_region_delta（全国统一每 %d 天结算一次）" % BIWEEKLY)
eff.append("# 目标地区领导人 = GER_region_value（领导人序号，见 gen_region_game.py 的 LEADERS；0 = 无）。换完跑 GER_region_game_sync_frames")
eff.append("GER_region_target_set_leader = {")
eff += on_target(["set_variable = {{ %s = GER_region_value }}" % "GER_region_{key}_leader"])
eff.append("}")
eff.append("GER_region_target_add_control_growth = {")
eff += on_target(["add_to_variable = {{ {growth} = GER_region_delta }}"])
eff.append("}")
eff.append("")
eff.append("# ---- 点击行动方针：扣政治点数 → 记下目标地区 → 开始计时 / 切换方针 → 执行手写效果 → 刷新")
for row in ROWS:
    n = row["n"]
    eff.append("GER_region_game_take_action_%d = {" % n)
    eff.append("    add_political_power = -%d" % row["cost"])
    eff.append("    set_variable = { GER_region_target = GER_region_selected }")
    for i, r in enumerate(regions):
        body = []
        if row["garrison"]:
            body.append("set_variable = { %s = %d } set_variable = { %s = 0 }" % (r["v_policy"], n, r["v_policy_days"]))
        elif row["days"]:
            body.append("set_variable = { %s = %d }" % (r["v_act"][n], row["days"]))
        if row["max"]:
            body.append("add_to_variable = { %s = 1 }" % r["v_count"][n])
        if row["cooldown"]:
            body.append("set_variable = { %s = %d }" % (r["v_cd"][n], row["cooldown"]))
        if not body:
            break
        eff.append("    %s = { limit = { %s } %s }" % ("if" if i == 0 else "else_if", is_sel(r["idx"]), " ".join(body)))
    eff.append("    GER_region_action_%d = yes" % n)
    eff.append("    GER_region_game_sync_frames = yes")
    eff.append("}")
eff.append("")
eff.append("# ---- 每天（on_daily_GER）：日常决议倒计时，每满 %d 天调用 _biweekly，到 0 调用 _complete；" % BIWEEKLY)
eff.append("# 驻区方针累计天数，每满 %d 天调用当前方针的 _biweekly。" % BIWEEKLY)
eff.append("# 另外：驻区方针每天调用 _daily；全国每满 %d 天结算各地区的永久每两周控制度；控制度不低于下限。" % BIWEEKLY)
eff.append("GER_region_game_daily_tick = {")
eff.append("    add_to_variable = { GER_region_day = 1 }")
eff.append("    set_temp_variable = { GER_region_day_mod = GER_region_day }")
eff.append("    modulo_temp_variable = { GER_region_day_mod = %d }" % BIWEEKLY)
for r in regions:
    eff.append("    # %s" % r["name"])
    for row in TIMED_ROWS:
        n, v = row["n"], r["v_act"][row["n"]]
        eff.append("    if = {")
        eff.append("        limit = { check_variable = { %s > 0 } }" % v)
        eff.append("        subtract_from_variable = { %s = 1 }" % v)
        eff.append("        set_variable = { GER_region_target = %d }" % r["idx"])
        if row["days"] >= BIWEEKLY:
            eff.append("        set_temp_variable = { GER_region_elapsed = %d }" % row["days"])
            eff.append("        subtract_from_temp_variable = { GER_region_elapsed = %s }" % v)
            eff.append("        modulo_temp_variable = { GER_region_elapsed = %d }" % BIWEEKLY)
            eff.append("        if = { limit = { check_variable = { GER_region_elapsed = 0 } } GER_region_action_%d_biweekly = yes }" % n)
        eff.append("        if = { limit = { check_variable = { %s = 0 } } GER_region_action_%d_complete = yes }" % (v, n))
        eff.append("    }")
    eff.append("    if = {")
    eff.append("        limit = { check_variable = { %s > 0 } }" % r["v_policy"])
    eff.append("        add_to_variable = { %s = 1 }" % r["v_policy_days"])
    eff.append("        set_variable = { GER_region_target = %d }" % r["idx"])
    for row in GARRISON:
        eff.append("        if = { limit = { check_variable = { %s = %d } } GER_region_action_%d_daily = yes }"
                   % (r["v_policy"], row["n"], row["n"]))
    eff.append("        set_temp_variable = { GER_region_elapsed = %s }" % r["v_policy_days"])
    eff.append("        modulo_temp_variable = { GER_region_elapsed = %d }" % BIWEEKLY)
    eff.append("        if = {")
    eff.append("            limit = { check_variable = { GER_region_elapsed = 0 } }")
    for row in GARRISON:
        eff.append("            if = { limit = { check_variable = { %s = %d } } GER_region_action_%d_biweekly = yes }"
                   % (r["v_policy"], row["n"], row["n"]))
    eff.append("        }")
    eff.append("    }")
    eff.append("    if = { limit = { check_variable = { GER_region_day_mod = 0 } check_variable = { %s > 0 } } "
               "set_temp_variable = { GER_region_delta = %s } GER_region_%s_add_control = yes }"
               % (r["v_growth"], r["v_growth"], r["key"]))
    eff.append("    if = { limit = { check_variable = { %s < %s } } set_variable = { %s = %s } }"
               % (r["v_control"], r["v_floor"], r["v_control"], r["v_floor"]))
    for row in COOLED:
        v = r["v_cd"][row["n"]]
        eff.append("    if = { limit = { check_variable = { %s > 0 } } subtract_from_variable = { %s = 1 } }" % (v, v))
    for ld in leaders:
        for what, v in LEADER_FX.get(ld["key"], {}).get("local_bw", []):
            eff.append("    if = { limit = { check_variable = { GER_region_day_mod = 0 } check_variable = { %s = 1 } check_variable = { %s = %d } } "
                       "set_temp_variable = { GER_region_delta = %g } GER_region_%s_add_%s = yes }   # 领导人 %s"
                       % (r["v_open"], r["v_leader"], ld["idx"], v, r["key"], what, ld["cname"]))
    # 摇摆区规则
    low = "check_variable = { %s < %d } check_variable = { %s < %d }" % (r["v_support"], SWING_SUPPORT, r["v_control"], SWING_CONTROL)
    eff.append("    if = { limit = { check_variable = { %s > 0 } NOT = { check_variable = { %s = 2 } } } "
               "set_variable = { %s = 0 } set_variable = { %s = 0 } }   # 临时摇摆区被别的效果改了类型：不再恢复"
               % (r["v_swing_return"], r["v_state"], r["v_swing_return"], r["v_swing_days"]))
    eff.append("    if = { limit = { check_variable = { %s = 1 } OR = { %s } %s } set_variable = { %s = %s } set_variable = { %s = 2 } }"
               % (r["v_open"], " ".join("check_variable = { %s = %d }" % (r["v_state"], f) for f in SWING_FROM), low,
                  r["v_swing_return"], r["v_state"], r["v_state"]))
    eff.append("    if = {")
    eff.append("        limit = { check_variable = { %s > 0 } }" % r["v_swing_return"])
    eff.append("        if = { limit = { %s } set_variable = { %s = %d } }" % (low, r["v_swing_days"], SWING_DAYS))
    eff.append("        else = {")
    eff.append("            subtract_from_variable = { %s = 1 }" % r["v_swing_days"])
    eff.append("            if = { limit = { check_variable = { %s < 1 } } set_variable = { %s = %s } set_variable = { %s = 0 } set_variable = { %s = 0 } }"
               % (r["v_swing_days"], r["v_state"], r["v_swing_return"], r["v_swing_return"], r["v_swing_days"]))
    eff.append("        }")
    eff.append("    }")
eff.append("    # ---- 领导人（全国）：每位领导人只算一份，所在区块开放时生效")
eff.append("    set_temp_variable = { GER_region_spd_changed = 0 }")
eff.append("    set_variable = { GER_region_soc_points_factor = 0 }")
for ld in leaders:
    fx = LEADER_FX.get(ld["key"])
    if not fx:
        continue
    anyr = "OR = { %s }" % " ".join("AND = { check_variable = { %s = 1 } check_variable = { %s = %d } }"
                                    % (r["v_open"], r["v_leader"], ld["idx"]) for r in regions)
    body = []
    for kind, v in fx.get("daily", []):
        if kind == "stability":
            body.append("add_stability = %g" % v)
        else:
            for k in (["left", "center", "right"] if kind == "all" else [kind]):
                body.append("add_to_variable = { %s = %g }" % (SPD_FACTION[k][0], v))
            body.append("set_temp_variable = { GER_region_spd_changed = 1 }")
    if fx.get("soc"):
        body.append("add_to_variable = { GER_region_soc_points_factor = %g }" % fx["soc"])
    for flag, kind, v in fx.get("cond_daily", []):
        body.append("if = { limit = { has_country_flag = %s } add_stability = %g }" % (flag, v))
    bw = []
    for kind, v in fx.get("bw", []):
        if kind == "unity":
            bw.append("add_to_variable = { GER_region_unity_acc = %g }" % v)
        elif kind == "inertia":
            bw.append("add_to_variable = { GER_yihui_inertia = %g }" % v)
    if bw:
        body.append("if = { limit = { check_variable = { GER_region_day_mod = 0 } } %s }" % " ".join(bw))
    eff.append("    # %s" % ld["cname"])
    if body:
        eff.append("    if = { limit = { %s } %s }" % (anyr, " ".join(body)))
    if fx.get("country"):
        m = "GER_region_leader_%s_country" % ld["key"]
        eff.append("    if = { limit = { %s NOT = { has_dynamic_modifier = { modifier = %s } } } add_dynamic_modifier = { modifier = %s } }"
                   % (anyr, m, m))
        eff.append("    if = { limit = { NOT = { %s } has_dynamic_modifier = { modifier = %s } } remove_dynamic_modifier = { modifier = %s } }"
                   % (anyr, m, m))
eff.append("    if = { limit = { check_variable = { GER_region_spd_changed = 1 } } GER_SPD_refresh_support_effect = yes }")
eff.append("    # 党内团结度会被取整：零头先攒在 GER_region_unity_acc，满 1 点再加进去")
eff.append("    set_temp_variable = { GER_region_unity_changed = 0 }")
for _i in range(8):
    eff.append("    if = { limit = { check_variable = { GER_region_unity_acc > 0.999 } } add_to_variable = { GER_SPD_unity = 1 } "
               "subtract_from_variable = { GER_region_unity_acc = 1 } set_temp_variable = { GER_region_unity_changed = 1 } }")
    eff.append("    if = { limit = { check_variable = { GER_region_unity_acc < -0.999 } } add_to_variable = { GER_SPD_unity = -1 } "
               "add_to_variable = { GER_region_unity_acc = 1 } set_temp_variable = { GER_region_unity_changed = 1 } }")
eff.append("    if = { limit = { check_variable = { GER_region_unity_changed = 1 } } GER_SPD_refresh_unity_effect = yes }")
eff.append("    GER_region_game_sync_frames = yes")
eff.append("}")
eff.append("")
eff.append("# 地图全开后的开局：16 个区块全部开放，按 OPENING_TYPES 设类型、按 OPENING_VALUES 设摇摆区支持度/控制度，")
eff.append("# 清掉选中（面板显示待机）。地图全开的那一刻（事件 / 决议 / 国策里）调用 GER_region_game_open_map = yes。")
eff.append("GER_region_game_open_map = {")
for _pk in sorted(PHASES):
    eff.append("    GER_region_game_%s_end = yes   # 阶段博弈还没结束的话先结束（里面自己判断旗标）" % _pk)
for r in regions:
    s, c = OPENING_VALUES.get(r["key"], HIDDEN_VALUES.get(OPENING_TYPES[r["key"]], (0, 0)))
    eff.append("    set_variable = { %s = 1 } set_variable = { %s = %d } set_variable = { %s = %d } set_variable = { %s = %d }   # %s %s"
               % (r["v_open"], r["v_state"], OPENING_TYPES[r["key"]], r["v_support"], s, r["v_control"], c,
                  r["name"], TYPE_NAMES[OPENING_TYPES[r["key"]]]))
for k, lk in sorted(OPENING_LEADERS.items()):
    eff.append("    set_variable = { %s = %d }   # %s" % (R_BY_KEY0[k]["v_leader"], LD_BY_KEY0[lk]["idx"], LD_BY_KEY0[lk]["cname"]))
for oid in OPENING_OVERLAYS:
    eff.append("    set_variable = { %s = 1 }   # 割让：%s" % (OV_BY_ID0[oid]["v_shown"], OV_BY_ID0[oid]["name"]))
eff.append("    set_country_flag = %s   # 解锁右侧的行动方针 / 驻区方针" % MAP_OPENED_FLAG)
eff.append("    GER_region_on_open_map = yes   # 手写钩子：各地区的开局数值设好之后（例如补上巴伐利亚危机结局对周边地区的影响）")
eff.append("    set_variable = { GER_region_selected = 0 }")
eff.append("    GER_region_game_sync_frames = yes")
eff.append("}")
eff.append("")
eff.append("# ---- 地区效益：按支持度 / 控制度算各地区档位（未开放 = 25 无效果），再给该地区里归德国所有的州加对应修正")
eff.append("GER_region_game_update_tiers = {")
for r in regions:
    s, c, tv = r["v_support"], r["v_control"], r["v_tier"]
    eff.append("    # %s" % r["name"])
    eff.append("    if = { limit = { NOT = { check_variable = { %s = 1 } } } set_variable = { %s = 25 } }" % (r["v_open"], tv))
    eff.append("    else_if = { limit = { check_variable = { %s > 99.99 } check_variable = { %s > 24.99 } } set_variable = { %s = 100 } }" % (c, s, tv))
    eff.append("    else = {")
    eff.append("        set_temp_variable = { GER_region_half = %s }" % s)
    eff.append("        multiply_temp_variable = { GER_region_half = 2 }")
    eff.append("        subtract_from_temp_variable = { GER_region_half = %s }   # 2 x 支持度 - 控制度 >= 0 即支持度够一半" % c)
    eff.append("        if = { limit = { check_variable = { %s > 74.99 } check_variable = { GER_region_half > -0.001 } } set_variable = { %s = 75 } }" % (c, tv))
    eff.append("        else_if = { limit = { check_variable = { %s > 49.99 } check_variable = { GER_region_half > -0.001 } } set_variable = { %s = 50 } }" % (c, tv))
    eff.append("        else_if = { limit = { check_variable = { %s > 24.99 } } set_variable = { %s = 25 } }" % (c, tv))
    eff.append("        else = { set_variable = { %s = 0 } }" % tv)
    eff.append("    }")
    for sid in REGION_STATES[r["key"]]:
        eff.append("    %d = { set_temp_variable = { GER_region_tier_now = GER.%s } "
                   "if = { limit = { NOT = { is_owned_by = GER } } set_temp_variable = { GER_region_tier_now = 25 } } "
                   "GER_region_state_set_tier = yes "
                   "set_temp_variable = { GER_region_leader_now = GER.%s } "
                   "if = { limit = { OR = { NOT = { is_owned_by = GER } NOT = { check_variable = { GER.%s = 1 } } } } "
                   "set_temp_variable = { GER_region_leader_now = 0 } } "
                   "GER_region_state_set_leader = yes }" % (sid, tv, r["v_leader"], r["v_open"]))
eff.append("}")
eff.append("# 州作用域：只保留 GER_region_tier_now 对应的那个修正（25 = 全部去掉）")
eff.append("GER_region_state_clear_tiers = {")
for tt in TIERS:
    if TIER_MODS[tt]:
        eff.append("    if = { limit = { has_dynamic_modifier = { modifier = GER_region_tier_%d } } remove_dynamic_modifier = { modifier = GER_region_tier_%d } }" % (tt, tt))
eff.append("}")
eff.append("GER_region_state_set_tier = {")
for tt in TIERS:
    if TIER_MODS[tt]:
        eff.append("    if = { limit = { check_variable = { GER_region_tier_now = %d } NOT = { has_dynamic_modifier = { modifier = GER_region_tier_%d } } } "
                   "GER_region_state_clear_tiers = yes add_dynamic_modifier = { modifier = GER_region_tier_%d } }" % (tt, tt, tt))
eff.append("    if = { limit = { check_variable = { GER_region_tier_now = 25 } } GER_region_state_clear_tiers = yes }")
eff.append("}")
_LSTATE = [ld for ld in leaders if LEADER_FX.get(ld["key"], {}).get("state")]
eff.append("# 州作用域：只保留 GER_region_leader_now（领导人序号）对应的领导人州修正")
eff.append("GER_region_state_clear_leader_mods = {")
for ld in _LSTATE:
    m = "GER_region_leader_%s_state" % ld["key"]
    eff.append("    if = { limit = { has_dynamic_modifier = { modifier = %s } } remove_dynamic_modifier = { modifier = %s } }" % (m, m))
eff.append("}")
eff.append("GER_region_state_set_leader = {")
for ld in _LSTATE:
    m = "GER_region_leader_%s_state" % ld["key"]
    eff.append("    if = { limit = { check_variable = { GER_region_leader_now = %d } NOT = { has_dynamic_modifier = { modifier = %s } } } "
               "GER_region_state_clear_leader_mods = yes add_dynamic_modifier = { modifier = %s } }" % (ld["idx"], m, m))
eff.append("    if = { limit = { NOT = { %s } } GER_region_state_clear_leader_mods = yes }"
           % " ".join("check_variable = { GER_region_leader_now = %d }" % ld["idx"] for ld in _LSTATE))
eff.append("}")
eff.append("")
eff.append("# 隐藏全部割让盖板")
eff.append("GER_region_game_hide_all_overlays = {")
for o in overlays:
    eff.append("    clear_variable = %s" % o["v_shown"])
eff.append("}")
eff.append("")
eff.append("# 回到开局画面：全部区块隐藏、全部盖板隐藏、面板数据清空")
eff.append("GER_region_game_reset_to_opening = {")
for r in regions:
    for v in ("v_open", "v_state", "v_frame", "v_support", "v_control", "v_leader", "v_policy", "v_policy_days"):
        eff.append("    clear_variable = %s" % r[v])
    for v in (list(r["v_act"].values()) + list(r["v_count"].values()) + list(r["v_cd"].values())
              + [r["v_growth"], r["v_floor"], r["v_tier"], r["v_swing_return"], r["v_swing_days"]]):
        eff.append("    clear_variable = %s" % v)
eff.append("    clear_variable = GER_region_selected")
eff.append("    clr_country_flag = %s" % MAP_OPENED_FLAG)
for _pk, _ph in sorted(PHASES.items()):
    eff.append("    clr_country_flag = %s" % _ph["flag"])
    eff.append("    clear_variable = %s" % _ph["stage"])
eff.append("    GER_region_actions_on_reset = yes   # 手写：决议自己的全国状态（例如罢工的建造减速）")
eff.append("    GER_region_game_hide_all_overlays = yes")
eff.append("}")
# ---- 阶段博弈（PHASES）
for _pk, _ph in sorted(PHASES.items()):
    _r = R_BY_KEY0[_ph["region"]]
    _prow = [row for row in ROWS if row["phase"] == _pk]
    _ptimed = [row for row in _prow if row in TIMED_ROWS]
    eff.append("")
    eff.append("# ==== 阶段博弈：%s（只开放 %s；右侧列表只显示该阶段的决议 %s）"
               % (_ph["cname"], _r["name"], "、".join(str(row["n"]) for row in _prow)))
    eff.append("# 开始。设计上在地图全开（GER_region_game_open_map）之前用；进度从 0 开始，这时列表是空的")
    eff.append("GER_region_game_%s_start = {" % _pk)
    eff.append("    set_country_flag = %s" % _ph["flag"])
    eff.append("    set_variable = { %s = 0 }" % _ph["stage"])
    eff.append("    set_variable = { %s = 1 } set_variable = { %s = %d } set_variable = { %s = %d } set_variable = { %s = %d }   # %s"
               % (_r["v_open"], _r["v_state"], _ph["state"], _r["v_support"], _ph["values"][0], _r["v_control"], _ph["values"][1],
                  TYPE_NAMES[_ph["state"]]))
    if _ph["leader"]:
        eff.append("    set_variable = { %s = %d }   # %s" % (_r["v_leader"], LD_BY_KEY0[_ph["leader"]]["idx"],
                                                          LD_BY_KEY0[_ph["leader"]]["cname"]))
    for row in _prow:
        if row["max"]:
            eff.append("    clear_variable = %s" % _r["v_count"][row["n"]])
        if row in _ptimed:
            eff.append("    clear_variable = %s" % _r["v_act"][row["n"]])
    eff.append("    GER_region_%s_on_start = yes   # 手写钩子" % _pk)
    eff.append("    set_variable = { GER_region_selected = %d }" % _r["idx"])
    eff.append("    GER_region_game_sync_frames = yes")
    eff.append("}")
    eff.append("# 进度 +1（最大 %d），右侧列表随之刷新" % _ph["stages"])
    eff.append("GER_region_game_%s_next_stage = {" % _pk)
    eff.append("    if = { limit = { check_variable = { %s < %d } } add_to_variable = { %s = 1 } }" % (_ph["stage"], _ph["stages"], _ph["stage"]))
    eff.append("    GER_region_game_sync_selected = yes")
    eff.append("}")
    eff.append("# 结束：该阶段的决议全部隐藏%s。阶段没在进行时什么都不做"
               % ("，%s地块保留显示" % _r["name"] if _ph.get("keep_open") else "，关闭%s" % _r["name"]))
    eff.append("GER_region_game_%s_end = {" % _pk)
    eff.append("    if = {")
    eff.append("        limit = { has_country_flag = %s }" % _ph["flag"])
    eff.append("        GER_region_%s_on_end = yes   # 手写钩子（例如去掉还在生效的修正）" % _pk)
    eff.append("        clr_country_flag = %s" % _ph["flag"])
    if not _ph.get("keep_open"):
        for v in ("v_open", "v_state", "v_frame", "v_support", "v_control", "v_leader"):
            eff.append("        clear_variable = %s" % _r[v])
    for row in _ptimed:
        eff.append("        clear_variable = %s" % _r["v_act"][row["n"]])
    if not _ph.get("keep_open"):
        eff.append("        set_variable = { GER_region_selected = 0 }")
    eff.append("        GER_region_game_sync_frames = yes")
    eff.append("    }")
    eff.append("}")
EFFECTS = "\n".join(eff) + "\n"

# 悬停提示里的动态行（要用 BW_SOURCES，所以放在这里补进 SCRIPTED_LOC）
_sl2 = ["", "# 支持度 / 控制度悬停：每两周变化来源（选中地区）、合计、地区效益、摇摆区、冻结地区说明"]
for _k, _what, _amt, _cond, _label in BW_SOURCES:
    _sl2 += defined_text("GER_region_src_%s" % _k, [("%s NOT = { %s }" % (_cond, FROZEN_SEL), "GER_region_src_%s_line" % _k)],
                         "GER_region_panel_empty")
for _what in ("support", "control"):
    _sl2 += defined_text("GER_region_bw_%s_sum" % _what, [("check_variable = { GER_region_sel_bw_%s > 0 }" % _what,
                                                          "GER_region_bw_%s_pos" % _what),
                                                         ("check_variable = { GER_region_sel_bw_%s < 0 }" % _what,
                                                          "GER_region_bw_%s_neg" % _what)], "GER_region_bw_zero")
_sl2 += defined_text("GER_region_tier_text", [("NOT = { %s }" % SEL, "GER_region_panel_empty")] +   # 没选中地区：不显示
                     [("check_variable = { GER_region_sel_tier = %d }" % tt, "GER_region_tier_text_%d" % tt) for tt in TIERS],
                     "GER_region_tier_text_25")
_sl2 += defined_text("GER_region_swing_note",
                     [("check_variable = { GER_region_sel_frame = 2 } check_variable = { GER_region_sel_swing_days > 0 }",
                       "GER_region_swing_note_lock"),
                      ("check_variable = { GER_region_sel_frame = 2 }", "GER_region_swing_note_on")], "GER_region_panel_empty")
_sl2 += defined_text("GER_region_frozen_note", [(FROZEN_SEL, "GER_region_frozen_note_text")], "GER_region_panel_empty")
for _row in COOLED:   # 决议悬停提示：冷却中时显示「（还剩X日）」
    _sl2 += defined_text("GER_region_cd_%d_left" % _row["n"], [("check_variable = { %s > 0 } " % _row["sel_cd"],
                                                              "GER_region_cd_%d_left_text" % _row["n"])], "GER_region_panel_empty")
SCRIPTED_LOC += "\n".join(_sl2) + "\n"

# 地区效益的州修正（生成）
_dm = ["# 由 %s 生成，不要手改。地区效益（州修正），见 TIER_MODS" % GEN_TAG]
for tt in TIERS:
    if TIER_MODS[tt]:
        _dm.append("GER_region_tier_%d = {" % tt)
        _dm.append("    icon = %s" % TIER_ICONS[tt])
        _dm += ["    %s = %.2f" % (m, v) for m, v, _n in TIER_MODS[tt]]
        _dm.append("}")
_dm.append("# 领导人：州修正（该地区里归德国所有的州）、全国修正")
for _ld in leaders:
    _fx = LEADER_FX.get(_ld["key"], {})
    for _kind, _icon in (("state", LEADER_STATE_ICON), ("country", None)):   # 全国修正不写 icon：不显示成民族精神
        if _fx.get(_kind):
            _dm.append("GER_region_leader_%s_%s = {" % (_ld["key"], _kind))
            if _icon:
                _dm.append("    icon = %s" % _icon)
            _dm += ["    %s = %.2f" % (m, v) for m, v, _n in _fx[_kind]]
            _dm.append("}")
DYN_MODIFIERS = "\n".join(_dm) + "\n"
_sl2 = ["", "# 约瑟夫·比塔：西里西亚自治后多一条（旗标 GER_silesia_autonomy）"]
_sl2 += defined_text("GER_region_bitta_autonomy_line", [("has_country_flag = GER_silesia_autonomy", "GER_region_bitta_autonomy_text")],
                     "GER_region_panel_empty")
SCRIPTED_LOC += "\n".join(_sl2) + "\n"

# ---------------------------------------------------------------- 测试决议
CHECKER_COLORS = [3, 4, 6, 2]   # 红、蓝、绿、中立
checker = {}
for k in sorted(ADJ, key=lambda k: -len(ADJ[k])):
    used = {checker.get(n) for n in ADJ[k]}
    checker[k] = next(c for c in CHECKER_COLORS if c not in used)


def dec(name, body, desc_extra=None, unlock=True):
    if unlock:   # 测试用：当作地图已经全开，右侧列表才会出现
        body = list(body) + ["set_country_flag = %s" % MAP_OPENED_FLAG]
    return ["    %s = {" % name,
            "        allowed = { original_tag = GER }",
            "        visible = { original_tag = GER }",
            "        cost = 0",
            "        fire_only_once = no",
            "        ai_will_do = { factor = 0 }",
            "        complete_effect = {",
            "            set_country_flag = GER_region_game_open",
            "            hidden_effect = {"] + ["                " + b for b in body] + [
            "                GER_region_game_sync_frames = yes",
            "            }",
            "        }",
            "    }"]


def open_all(state):
    out = []
    for r in regions:
        out.append("set_variable = { %s = 1 }" % r["v_open"])
        out.append("set_variable = { %s = %s }" % (r["v_state"], state))
    return out


D = ["# 由 %s 生成，不要手改。地区博弈地图的测试决议，测完整个文件和分类一起删掉即可。" % GEN_TAG,
     "GER_region_game_test_category = {"]
TEST_VARS = ["GER_region_test_color", "GER_region_test_next", "GER_region_test_ov_next",
             "GER_region_test_type_idx", "GER_region_test_type", "GER_region_test_bar_idx", "GER_region_test_bar",
             "GER_region_test_leader"]
D += dec("GER_region_test_reset", ["GER_region_game_reset_to_opening = yes"]
         + ["clear_variable = %s" % v for v in TEST_VARS], unlock=False)
D += dec("GER_region_test_opening", ["GER_region_game_hide_all_overlays = yes", "GER_region_game_open_map = yes"])
D += dec("GER_region_test_open_all", open_all(2))
D += dec("GER_region_test_checker", sum((["set_variable = { %s = 1 }" % r["v_open"],
                                          "set_variable = { %s = %d }" % (r["v_state"], checker[r["key"]])]
                                         for r in regions), []))
cyc = ["add_to_variable = { GER_region_test_color = 1 }",
       "if = { limit = { check_variable = { GER_region_test_color > %d } } set_variable = { GER_region_test_color = 1 } }"
       % REGION_FRAMES]
D += dec("GER_region_test_cycle_color", cyc + open_all("GER_region_test_color"))
# 修改说明第 12 节给的配色示例，对照 区块_12帧/预览_地图_核心区与控制区.png
MAP_EXAMPLE = {"R08": 3, "R16": 3, "R06": 8, "R14": 8, "R09": 4, "R05": 9, "R10": 5, "R11": 10,
               "R13": 6, "R07": 11, "R02": 12}
D += dec("GER_region_test_map_example", sum((["set_variable = { %s = 1 }" % r["v_open"],
                                              "set_variable = { %s = %d }" % (r["v_state"], MAP_EXAMPLE.get(r["key"], 2))]
                                             for r in regions), []))
nxt = ["add_to_variable = { GER_region_test_next = 1 }",
       "if = {",
       "    limit = { check_variable = { GER_region_test_next > %d } }" % len(regions),
       "    set_variable = { GER_region_test_next = 1 }",
       "    GER_region_game_reset_to_opening = yes",
       "}"]
for i, r in enumerate(regions, 1):
    nxt.append("if = { limit = { check_variable = { GER_region_test_next = %d } } set_variable = { %s = 1 } set_variable = { %s = 3 } }"
               % (i, r["v_open"], r["v_state"]))
D += dec("GER_region_test_next_region", nxt)
D += dec("GER_region_test_silesia_A", open_all(2) + ["GER_region_game_hide_all_overlays = yes",
                                                     "set_variable = { GER_region_OV_SIL_planA_1134_762_shown = 1 }",
                                                     "set_variable = { GER_region_OV_SIL_planB_762_shown = 1 }"])
D += dec("GER_region_test_silesia_B", open_all(2) + ["GER_region_game_hide_all_overlays = yes",
                                                     "set_variable = { GER_region_OV_SIL_planB_762_shown = 1 }"])
D += dec("GER_region_test_all_overlays", open_all(2) + ["set_variable = { %s = 1 }" % o["v_shown"] for o in overlays])
D += dec("GER_region_test_denmark_1", ["GER_region_game_hide_all_overlays = yes",
                                       "set_variable = { GER_region_OV_SHL_trust_all_shown = 1 }"])
D += dec("GER_region_test_denmark_2", ["GER_region_game_hide_all_overlays = yes",
                                       "set_variable = { GER_region_OV_SHL_north_Denmark_shown = 1 }",
                                       "set_variable = { GER_region_R03_open = 1 }",
                                       "set_variable = { GER_region_R03_state = 2 }"])
onx = ["add_to_variable = { GER_region_test_ov_next = 1 }",
       "if = { limit = { check_variable = { GER_region_test_ov_next > %d } } set_variable = { GER_region_test_ov_next = 1 } }"
       % len(overlays),
       "GER_region_game_hide_all_overlays = yes"]
for i, o in enumerate(overlays, 1):
    onx.append("if = { limit = { check_variable = { GER_region_test_ov_next = %d } } set_variable = { %s = 1 } }"
               % (i, o["v_shown"]))
D += dec("GER_region_test_next_overlay", onx)

# ---- 右侧面板测试
R_BY_KEY = {r["key"]: r for r in regions}
LD_BY_KEY = {ld["key"]: ld for ld in leaders}
HESSE = R_BY_KEY["R11"]


def hesse_sample(state):
    """对照预览图：黑森，支持度 46、控制度 35、领导人罗伯特·迪斯曼，其余区块中立"""
    return open_all(2) + ["GER_region_game_hide_all_overlays = yes",
                          "set_variable = { %s = %d }" % (HESSE["v_state"], state),
                          "set_variable = { %s = 46 }" % HESSE["v_support"],
                          "set_variable = { %s = 35 }" % HESSE["v_control"],
                          "set_variable = { %s = %d }" % (HESSE["v_leader"], LD_BY_KEY["dissmann"]["idx"]),
                          "set_variable = { GER_region_selected = %d }" % HESSE["idx"]]


D += dec("GER_region_test_panel_swing", hesse_sample(2))
D += dec("GER_region_test_panel_left_core", hesse_sample(3))

# 下面几个都作用在「当前选中的区块」上；还没选过就先选黑森
ENSURE_SEL = ["if = {",
              "    limit = { NOT = { %s } }" % SEL,
              "    set_variable = { GER_region_selected = %d }" % HESSE["idx"],
              "}"]


def on_selected(stmts):
    """对选中区块执行 stmts（里面用 {open} {state} {support} {control} {leader} 指代该区块的变量）"""
    out = []
    for r in regions:
        body = " ".join(s.format(open=r["v_open"], state=r["v_state"], support=r["v_support"],
                                 control=r["v_control"], leader=r["v_leader"]) for s in stmts)
        out.append("if = { limit = { %s } %s }" % (is_sel(r["idx"]), body))
    return out


TYPE_CYCLE = [2, 8, 9, 10, 3, 4, 5]
tc = ENSURE_SEL + ["add_to_variable = { GER_region_test_type_idx = 1 }",
                   "if = { limit = { check_variable = { GER_region_test_type_idx > %d } } set_variable = { GER_region_test_type_idx = 1 } }"
                   % len(TYPE_CYCLE)]
for i, f in enumerate(TYPE_CYCLE, 1):
    tc.append("if = { limit = { check_variable = { GER_region_test_type_idx = %d } } set_variable = { GER_region_test_type = %d } }"
              % (i, f))
tc += on_selected(["set_variable = {{ {open} = 1 }}", "set_variable = {{ {state} = GER_region_test_type }}"])
D += dec("GER_region_test_panel_type_cycle", tc)

BAR_STEPS = [0, 10, 46, 50, 100]
bc = ENSURE_SEL + ["add_to_variable = { GER_region_test_bar_idx = 1 }",
                   "if = { limit = { check_variable = { GER_region_test_bar_idx > %d } } set_variable = { GER_region_test_bar_idx = 1 } }"
                   % len(BAR_STEPS)]
for i, v in enumerate(BAR_STEPS, 1):
    bc.append("if = { limit = { check_variable = { GER_region_test_bar_idx = %d } } set_variable = { GER_region_test_bar = %d } }"
              % (i, v))
bc += on_selected(["set_variable = {{ {open} = 1 }}", "set_variable = {{ {support} = GER_region_test_bar }}",
                   "set_variable = {{ {control} = GER_region_test_bar }}"])
D += dec("GER_region_test_panel_bars", bc)

lc = ENSURE_SEL + ["add_to_variable = { GER_region_test_leader = 1 }",
                   "if = { limit = { check_variable = { GER_region_test_leader > %d } } set_variable = { GER_region_test_leader = 0 } }"
                   % len(leaders)]
lc += on_selected(["set_variable = {{ {open} = 1 }}", "set_variable = {{ {leader} = GER_region_test_leader }}"])
D += dec("GER_region_test_panel_leader_cycle", lc)

# 策划案第 4 页的初始支持度 / 控制度 + 第 8 页的领导人（只填对得上区块的；只是测试数据，不是正式开局设定）
PLAN_VALUES = {"R01": (43, 60), "R06": (51, 30), "R11": (46, 35), "R15": (39, 35), "R04": (45, 20), "R07": (15, 5)}
PLAN_LEADERS = {"R16": "daeumig", "R11": "dissmann", "R01": "henke", "R03": "paul_dittmann",
                "R06": "paul_hirsch", "R05": "paul_hirsch", "R04": "paul_hirsch", "R08": "lipinski",
                "R10": "weimar_coalition", "R07": "bitta", "R14": "committee_nine"}
pv = open_all(2)
for k, (s, c) in sorted(PLAN_VALUES.items()):
    pv += ["set_variable = { %s = %d }" % (R_BY_KEY[k]["v_support"], s),
           "set_variable = { %s = %d }" % (R_BY_KEY[k]["v_control"], c)]
for k, lk in sorted(PLAN_LEADERS.items()):
    pv.append("set_variable = { %s = %d }" % (R_BY_KEY[k]["v_leader"], LD_BY_KEY[lk]["idx"]))
D += dec("GER_region_test_panel_plan_values", pv)
# 行动方针测试：加政治点数；把选中地区生效中的决议快进到只剩 1 天（再过一天就结束），驻区方针快进到下一天触发「每两周」
D += dec("GER_region_test_pp", ["add_political_power = 100"])
ff = ENSURE_SEL[:]
for r in regions:
    body = []
    for row in TIMED_ROWS:
        v = r["v_act"][row["n"]]
        body.append("if = { limit = { check_variable = { %s > 1 } } set_variable = { %s = 1 } }" % (v, v))
    body.append("if = { limit = { check_variable = { %s > 0 } } set_variable = { %s = %d } }"
                % (r["v_policy"], r["v_policy_days"], BIWEEKLY - 1))
    ff.append("if = { limit = { %s } %s }" % (is_sel(r["idx"]), " ".join(body)))
D += dec("GER_region_test_panel_fast_forward", ff)
# 阶段博弈测试：开始 / 推进进度 / 结算并关闭
D += dec("GER_region_test_bavaria_start", ["GER_region_game_bavaria_start = yes"], unlock=False)
D += dec("GER_region_test_bavaria_next_stage", ["GER_region_game_bavaria_next_stage = yes"], unlock=False)
D += dec("GER_region_test_bavaria_settle", ["GER_region_bavaria_settle = yes"], unlock=False)
D.append("}")
DECISIONS = "\n".join(D) + "\n"

CATEGORY = """# 由 %s 生成，不要手改。地区博弈地图测试用，测完删掉。
GER_region_game_test_category = {
    icon = generic
    priority = 5
    allowed = { original_tag = GER }
    visible = { original_tag = GER }
}
""" % GEN_TAG

# ---------------------------------------------------------------- 本地化
ov_order = " → ".join(o["name"] for o in overlays)
reg_order = " → ".join(r["name"] for r in regions)
loc = ["l_simp_chinese:",
       " # 由 %s 生成，不要手改" % GEN_TAG,
       ' GER_region_game_entry_text: "地区博弈"',
       ' GER_region_game_entry_tt: "打开/关闭§Y地区博弈§!"',
       ' GER_region_game_quote: "“我的故事并不让人愉快。它不像虚构的故事那般甜美和谐。它有荒诞和迷惘的味道，疯狂和梦境的味道。它的味道，就像那些不再想自我欺骗之人的生活的味道。” ——赫尔曼·黑塞"',
       ' GER_region_game_selected_name: "[GER_region_selected_name]"',
       ' GER_region_game_selected_none: "（选中地区名称）"',
       ' GER_region_game_support_label: "支持度"',
       ' GER_region_game_control_label: "控制度"',
       ' GER_region_game_policy_label: "行动方针"',
       ' GER_region_panel_garrison_label: "驻区方针"',
       ' GER_region_panel_empty: ""',
       ' GER_region_panel_support_value: "[?GER_region_sel_support|1]%"',
       ' GER_region_panel_control_value: "[?GER_region_sel_control|1]%"',
       ' GER_region_panel_support_tooltip: "§Y支持度§!：§Y[?GER_region_sel_support|1]%%§!\\n§Y每两周§!变化：[GER_region_bw_support_sum]%s\\n\\n[GER_region_frozen_note][GER_region_panel_support_body]\\n\\n[GER_region_tier_text][GER_region_swing_note]"'
       % "".join("[GER_region_src_%s]" % s[0] for s in BW_SOURCES if s[1] == "support"),
       ' GER_region_panel_control_tooltip: "§Y控制度§!：§Y[?GER_region_sel_control|1]%%§!\\n§Y每两周§!变化：[GER_region_bw_control_sum]%s\\n\\n[GER_region_frozen_note][GER_region_panel_control_body]\\n\\n[GER_region_tier_text][GER_region_swing_note]"'
       % "".join("[GER_region_src_%s]" % s[0] for s in BW_SOURCES if s[1] == "control"),
       ' GER_region_panel_photo_name: "[GER_region_panel_photo_name_text]"',
       ' GER_region_panel_photo_status: "[GER_region_panel_photo_status_text]"',
       ' GER_region_panel_photo_type: "[GER_region_sel_type]"',
       ' GER_region_panel_photo_tooltip: "[GER_region_panel_photo_tt]"',
       ' GER_region_panel_leader_name: "[GER_region_sel_leader_name]"',
       ' GER_region_panel_leader_tt: "[GER_region_sel_leader_tt]"',
       ' GER_region_panel_core_title: "[GER_region_panel_core_title_text]"',
       ' GER_region_panel_core_title_type: "[GER_region_sel_type]"',
       ' GER_region_panel_core_tooltip: "[GER_region_panel_core_tt]"',
       ' GER_region_panel_core_tooltip_sel: "§Y[GER_region_sel_type]§!\\n\\n[GER_region_sel_core_desc]\\n\\n[GER_region_tier_text]"',
       ' GER_region_panel_status_policy_on: ""',
       ' GER_region_panel_entry_name: "[GER_region_entry_name]"',
       ' GER_region_panel_entry_status: "[GER_region_entry_status]"',
       ' GER_region_panel_entry_tooltip: "[GER_region_entry_tt]"',
       ' GER_region_check_yes: "£trigger_yes"',
       ' GER_region_check_no: "£trigger_no"',
       ]
loc += [' GER_region_type_%d: "%s"' % (f, n) for f, n in sorted(TYPE_NAMES.items())]
loc.append(" # 地图悬停提示：第一行「地区名：类型」，下面接手写介绍（%s）" % HAND_TT_LOC)
for r in regions:
    loc.append(' %s: "[%s]\\n\\n[%s]"' % (r["tooltip"], r["head"], r["body"]))
    loc.append(' %s_none: "§Y%s§!"' % (r["head"], r["name"]))
    for f, tn in sorted(TYPE_NAMES.items()):
        loc.append(' %s_%d: "§Y%s：%s§!"' % (r["head"], f, r["name"], tn))
loc.append(" # 行动方针条：名字、悬停提示写在 %s；花费、天数在 gen_region_game.py 的 ACTIONS" % HAND_PANEL_LOC)
for row in ROWS:
    n = row["n"]
    if row["garrison"]:
        loc.append(' GER_region_panel_row_%d_label: "[GER_region_row_%d_label]"' % (n, n))
        loc.append(' %s_locked: "§g$%s$§!"' % (row["name"], row["name"]))
    else:
        loc.append(' GER_region_panel_row_%d_label: "$%s$"' % (n, row["name"]))
    loc.append(' GER_region_panel_row_%d_status: "[GER_region_row_%d_status]"' % (n, n))
    for col, c in (("gold", "Y"), ("red", "R"), ("grey", "g")):
        loc.append(' GER_region_panel_row_%d_status_%s: "§%s%dpp§!"' % (n, col, c, row["cost"]))
    if row["days"]:
        loc.append(' GER_region_panel_row_%d_status_days: "§G[?%s|0]天§!"' % (n, row["sel_days"]))
    if row["cooldown"]:
        loc.append(' GER_region_panel_row_%d_status_cd: "§g冷却[?%s|0]天§!"' % (n, row["sel_cd"]))
loc += [' %s: "%s"' % (r["name_key"], r["name"]) for r in regions]
HAND = hand_written_keys()
tt_all = [("GER_region_locked_all_tt", "整个德国"),
          ("GER_region_alsace_lorraine_tt", "阿尔萨斯-洛林"),
          ("GER_region_bav_corner_tt", "巴伐利亚缺角")]
tt_all += [(r["tt"], r["name"]) for r in regions] + [(o["tt"], o["name"]) for o in overlays]
loc.append(" # 悬浮介绍（*_tt）不在这个文件里，全部在 %s" % HAND_TT_LOC)
# 手写文件里缺哪个键，就在文件末尾补一行占位；已有的行一律不碰。
append_missing(HAND_TT_LOC, [(k, "【待定】" + n) for k, n in tt_all])
panel_entries = []
for row in ROWS:
    panel_entries.append((row["name"], row["cname"]))
    panel_entries.append((row["tt"], "【待定】" + row["cname"]))
panel_entries.append(("GER_region_panel_garrison_tt", "§Y需支持度、控制度双满§!"))
panel_entries.append(("GER_region_panel_support_tt", "【待定】支持度说明"))
panel_entries.append(("GER_region_panel_control_tt", "【待定】控制度说明"))
for f in sorted(CORE_FRAMES):
    panel_entries.append(("GER_region_panel_core_%d_desc" % f, "【待定】%s说明" % TYPE_NAMES[f]))
for ld in leaders:
    panel_entries.append((ld["name_key"], ld["cname"]))
    panel_entries.append((ld["tt"], ld["cname"] if ld["key"] == IDLE_LEADER else "【待定】" + ld["cname"]))
panel_entries.append(("GER_region_panel_idle_tt", "【待定】待机说明"))
panel_entries.append(("GER_region_panel_idle_name", "德意志共和国"))
panel_entries.append(("GER_region_panel_idle_status", "我们暂时无暇顾及“国中之国”......"))
panel_entries.append(("GER_region_panel_idle_cover", "我们暂时无暇顾及“国中之国”......"))   # 待机时罩住数值框的方块上的字
append_missing(HAND_PANEL_LOC, panel_entries, header=[
    "地区博弈 · 右侧面板文字（手写，脚本只在末尾补缺的键，不改已有行）",
    "行动方针：GER_region_panel_row_N_name = 名字，_tt = 悬停介绍（N 见 gen_region_game.py 的 ACTIONS）；花费和天数在 ACTIONS 里。",
    "GER_region_panel_support_tt / _control_tt = 支持度、控制度的悬停说明（上面会自动加一行当前数值）。",
    "GER_region_panel_core_N_desc = 核心区方块的悬停说明。",
    "GER_region_panel_idle_tt = 没选中地区时，鼠标放在待机照片上的说明。",
    "GER_region_panel_idle_name / _status = 没选中地区时，照片下面左边 / 右边的字。",
    "领导人序号见 tools/GER_region_game/gen_region_game.py 的 LEADERS。"])
loc.append(" # 支持度 / 控制度悬停：每两周变化来源、地区效益、摇摆区、西里西亚说明")
loc.append(' GER_region_bw_zero: "0.00"')
for _what in ("support", "control"):
    loc.append(' GER_region_bw_%s_pos: "§G+[?GER_region_sel_bw_%s|2]§!"' % (_what, _what))
    loc.append(' GER_region_bw_%s_neg: "§R[?GER_region_sel_bw_%s|2]§!"' % (_what, _what))
for _k, _what, _amt, _cond, _label in BW_SOURCES:
    if _is_num(_amt):
        _val = ("§G+%.2f§!" if float(_amt) > 0 else "§R%.2f§!") % float(_amt)
    else:
        _val = "§G+[?%s|2]§!" % _amt
    loc.append(' GER_region_src_%s_line: "\\n  %s：%s"' % (_k, _label, _val))
# 悬停提示里 $键$ 不会被替换，规则说明直接写进每一条
_TIER_RULE = ("地区效益按§Y控制度§!分档（100%、75%、50%、25%、0%），且§Y支持度§!需不低于§Y控制度§!的一半才能生效"
              "（§Y控制度§!达到100%时，§Y支持度§!为其四分之一即可）；不满足时按25%（无效果）计。"
              "效果只作用于该地区目前在德国境内的州。")
_SWING_RULE = ("当社民党在一个地区的§Y支持度§!低于§Y{0}%§!、§Y控制度§!低于§Y{1}%§!时，该地区将会被视为§Y摇摆区§!；"
               "即使之后数值回升，该地区也将在§Y{2}§!日内被视为§Y摇摆区§!，随后恢复正常。").format(SWING_SUPPORT, SWING_CONTROL, SWING_DAYS)
for tt in TIERS:
    lines = ["§Y地区效益：%d%%§!" % tt]
    lines += ["%s：%s%+.2f%%§!" % (nm, "§G" if v > 0 else "§R", v * 100) for _m, v, nm in TIER_MODS[tt]] or ["无效果"]
    loc.append(' GER_region_tier_text_%d: "%s"' % (tt, "\\n".join(lines)))
    loc.append(' GER_region_tier_%d: "地区效益：%d%%"' % (tt, tt))
loc.append(' GER_region_swing_note_on: ""')
loc.append(' GER_region_swing_note_lock: "\\n\\n该地区还将维持§Y摇摆区§!§Y[?GER_region_sel_swing_days|0]§!日。"')
for _row in COOLED:
    loc.append(' GER_region_cd_%d_left_text: "（还剩§Y[?%s|0]§!日）"' % (_row["n"], _row["sel_cd"]))
loc.append(' GER_region_bitta_autonomy_text: "\\n§Y西里西亚自治后§!：\\n每日§Y稳定度§!：§G+0.05%§!"')
for _ld in leaders:
    for _kind in ("state", "country"):
        if LEADER_FX.get(_ld["key"], {}).get(_kind):
            loc.append(' GER_region_leader_%s_%s: "领导人：%s"' % (_ld["key"], _kind, _ld["cname"]))
loc.append(' GER_region_frozen_note_text: "受限于社会民主党对§Y西里西亚§!的影响之孱弱，此地的§Y支持度§!和§Y控制度§!不会有任何增长。'
           '我们只有通过§Y国策§!与§Y焦点博弈§!对此展开行动。\\n\\n"')
LOC_GUI = "\n".join(loc) + "\n"

dl = ["l_simp_chinese:",
      " # 由 %s 生成，不要手改" % GEN_TAG,
      ' GER_region_game_test_category: "【测试】地区博弈地图"',
      ' GER_region_game_test_category_desc: "地区博弈地图的素材和接口测试。每个决议执行后会自动打开地区博弈界面。"',
      ' GER_region_test_reset: "重置为开局画面"',
      ' GER_region_test_reset_desc: "隐藏全部区块和割让盖板，只剩无缝整块斜线 + 阿尔萨斯-洛林、巴伐利亚缺角两块。右侧回到地图全开之前的样子：数值框被绿色方块罩住，行动方针、驻区方针不显示（其余测试决议会顺手解锁列表）。"',
      ' GER_region_test_opening: "地图全开开局"',
      ' GER_region_test_opening_desc: "调用 GER_region_game_open_map（同时显示萨尔、欧本-马尔梅迪、波森-西普鲁士-但泽走廊、梅梅尔的割让，并填好各地区领导人）：左翼核心 汉堡-石荷、图林根-萨克森、鲁尔；右翼核心 巴伐利亚、东普鲁士、波美拉尼亚、汉诺威；特殊区 莱茵兰；共和核心 巴登-符腾堡；摇摆区 大柏林 60/75、威斯特法伦 39/35、威悉-埃姆斯 43/60、西里西亚 15/5、勃兰登堡 51/30、梅克伦堡 45/20、黑森 46/35。不选中任何地区，右下角显示待机照片和倍倍尔。"',
      ' GER_region_test_open_all: "开放全部区块（中立）"',
      ' GER_region_test_open_all_desc: "16 个区块全部显示为帧 2（中立）。"',
      ' GER_region_test_checker: "区块划分：相邻不同色"',
      ' GER_region_test_checker_desc: "16 个区块全部显示，相邻区块分别用红 / 蓝 / 绿 / 中立，检查分界和位置。"',
      ' GER_region_test_cycle_color: "全部区块换下一帧（1-12）"',
      ' GER_region_test_cycle_color_desc: "全部区块一起 帧1 → 帧12 循环：1 斜线 2 中立 3 左核(红) 4 右核(蓝) 5 魏玛核(黄) 6 绿 7 紫 8 左控 9 右控 10 魏玛控 11 绿控 12 紫控（8-12 带斜线）。当前：帧[?GER_region_test_color|0]。对照 区块_12帧/预览_色板12帧_图林根萨克森为例.png，位置不应跳动。"',
      ' GER_region_test_map_example: "地图配色示例（核心区与控制区）"',
      ' GER_region_test_map_example_desc: "图林根-萨克森、柏林=3，勃兰登堡、鲁尔=8，巴伐利亚=4，波美拉尼亚=9，巴登-符腾堡=5，黑森=10，东普鲁士=6，西里西亚=11，汉诺威=12，其余中立。对照 区块_12帧/预览_地图_核心区与控制区.png。"',
      ' GER_region_test_next_region: "逐个开放下一个区块（红）"',
      ' GER_region_test_next_region_desc: "每点一次多开放一个区块（帧 3），顺序：%s。已开放到第 [?GER_region_test_next] 个，16 个之后重来。"' % reg_order,
      ' GER_region_test_panel_swing: "面板：黑森·摇摆区"',
      ' GER_region_test_panel_swing_desc: "全部区块中立，选中黑森：支持度 46、控制度 35、领导人罗伯特·迪斯曼。对照 右侧面板素材/预览_摇摆区.png。"',
      ' GER_region_test_panel_left_core: "面板：黑森·左派核心区"',
      ' GER_region_test_panel_left_core_desc: "同上，但黑森设为帧 3（左派核心区）：数值框应换成红色核心区方块。对照 右侧面板素材/预览_左派核心区.png。"',
      ' GER_region_test_panel_type_cycle: "面板：选中地区换下一种类型"',
      ' GER_region_test_panel_type_cycle_desc: "对当前选中的区块（没选就用黑森）按 摇摆2 → 左控8 → 右控9 → 魏玛控10 → 左核3 → 右核4 → 魏玛核5 循环。当前：帧[?GER_region_test_type|0]。核心区时数值框和核心区方块应互换，不重叠、不残留。"',
      ' GER_region_test_panel_bars: "面板：选中地区的进度条换下一档"',
      ' GER_region_test_panel_bars_desc: "支持度、控制度一起按 0 → 10 → 46 → 50 → 100 循环。当前：[?GER_region_test_bar|0]。100 时下面四条驻区方针应从灰色变成可用。"',
      ' GER_region_test_panel_leader_cycle: "面板：选中地区换下一位领导人"',
      ' GER_region_test_panel_leader_cycle_desc: "按 无 → %s 循环。当前序号：[?GER_region_test_leader|0]。有头像的检查头像是否正好填满框；没头像的只显示名字。"' % " → ".join(ld["cname"] + ("" if ld["portrait"] else "（无头像）") for ld in leaders),
      ' GER_region_test_panel_plan_values: "面板：填入策划案初始数值"',
      ' GER_region_test_pp: "政治点数 +100"',
      ' GER_region_test_pp_desc: "测试行动方针的花费用。"',
      ' GER_region_test_panel_fast_forward: "面板：选中地区的决议快进到剩 1 天"',
      ' GER_region_test_panel_fast_forward_desc: "把选中地区所有生效中的日常决议改成只剩 1 天，再过一天应结束（暗黄消失、可以再点）；驻区方针改成明天触发一次「每两周」效果。"',
      ' GER_region_test_panel_plan_values_desc: "全部区块中立；按策划案第 4 页填支持度/控制度（威悉-埃姆斯(不来梅) 43/60、勃兰登堡 51/30、黑森 46/35、威斯特法伦 39/35、梅克伦堡 45/20、西里西亚 15/5），按第 8 页填领导人。之后逐个点地区看右侧面板。只是测试数据，不是正式开局设定。"',
      ' GER_region_test_bavaria_start: "巴伐利亚危机：开始（只开放巴伐利亚）"',
      ' GER_region_test_bavaria_start_desc: "调用 GER_region_game_bavaria_start：只开放巴伐利亚（魏玛联盟控制区、领导人霍夫曼）并选中它，右侧普通决议全部隐藏。进度从 0 开始，这时列表是空的，点「推进进度」后巴伐利亚决议才逐步出现。建议先点「重置为开局画面」再点这个。正式流程由事件链驱动（控制台：event AOR_GER_bavaria_crisis.1），巴伐利亚要到 4 月 5 日的事件点击后才显示，那时已是右派控制区、无领导人。"',
      ' GER_region_test_bavaria_next_stage: "巴伐利亚危机：推进进度"',
      ' GER_region_test_bavaria_next_stage_desc: "进度 +1（最大 4）。1 = 艾舍里希组织成立后（调停SPD内部冲突、对巴伐利亚施压）；2 = 协约国第一次抗议后（提交巴伐利亚报告、采取保守态势）；3 = 6 月 2 日「又一起凶杀案」后（宣布抵制恐怖袭击、撤出SPD优秀分子）；4 = 协约国第二次抗议后（最后通牒、依靠协约国施压）。当前进度：[?GER_region_bavaria_stage|0]。"',
      ' GER_region_test_bavaria_settle: "巴伐利亚危机：结算"',
      ' GER_region_test_bavaria_settle_desc: "调用 GER_region_bavaria_settle：按已执行的决议算出结局（1 完美 2 冲突和平落幕 3 苦涩的和平 4 全面溃败）并弹出对应的结局事件；巴伐利亚决议全部隐藏，巴伐利亚地块保留显示。只结算一次，要再测先点「巴伐利亚危机：开始」。上次结局：[?GER_region_bavaria_result|0]。"',
      ' GER_region_test_silesia_A: "西里西亚 A 方案（1134+762）"',
      ' GER_region_test_silesia_A_desc: "全部区块中立；A、B 两个盖板变量都设为 1，应只显示 A 的一整块斜线（互斥：A 显示时 B 不画）。"',
      ' GER_region_test_silesia_B: "西里西亚 B 方案（762）"',
      ' GER_region_test_silesia_B_desc: "全部区块中立；只显示 B 盖板，应是 A 范围里靠东南的那一块。"',
      ' GER_region_test_all_overlays: "显示全部区块和全部割让盖板"',
      ' GER_region_test_all_overlays_desc: "16 个区块 + %d 张盖板全部打开，检查叠放和性能（西里西亚 A、B 互斥，只会看到 A）。"' % len(overlays),
      ' GER_region_test_denmark_1: "丹麦阶段一：石勒苏益格托管"',
      ' GER_region_test_denmark_1_desc: "只显示 SHL_trust_all 盖板。"',
      ' GER_region_test_denmark_2: "丹麦阶段二：北石勒苏益格归丹麦"',
      ' GER_region_test_denmark_2_desc: "隐藏 SHL_trust_all，显示 SHL_north_Denmark，同时开放汉堡-石荷区块（中立）露出中部。"',
      ' GER_region_test_next_overlay: "逐张显示下一张割让盖板"',
      ' GER_region_test_next_overlay_desc: "每次只显示一张盖板，顺序：%s。当前第 [?GER_region_test_ov_next] 张。"' % ov_order]
LOC_DEC = "\n".join(dl) + "\n"

# ---------------------------------------------------------------- 行动方针（决议）的手写文件：只补缺的定义
def append_missing_defs(path_rel, header, defs):
    """手写脚本文件：缺哪个顶层定义（name = {）就在末尾补一段占位；已有的一律不碰"""
    path = os.path.join(MOD, *path_rel.split("/"))
    text = open(path, encoding="utf-8-sig").read() if os.path.exists(path) else "\n".join(header) + "\n"
    have = set(re.findall(r"^([A-Za-z0-9_]+)\s*=\s*\{", text, re.M))
    add = [block for name, block in defs if name not in have]
    if add:
        write(path_rel, text.rstrip("\n") + "\n\n" + "\n\n".join(add) + "\n")
        print("%s 补了 %d 段占位" % (path_rel, len(add)))


NOOP = "    set_temp_variable = { GER_region_noop = 1 }   # 占位（空的 scripted_effect 引擎不认），写了效果后可删"
HOOK_DESC = {"": "点击时（政治点数已扣）", "_complete": "计时结束那天", "_biweekly": "生效期间每满 %d 天" % BIWEEKLY,
             "_daily": "生效期间每天"}
_ae, _at = [], []
for row in ROWS:
    n = row["n"]
    for h in row["hooks"]:
        _ae.append(("GER_region_action_%d%s" % (n, h),
                    "# %d %s：%s\nGER_region_action_%d%s = {\n%s\n}" % (n, row["cname"], HOOK_DESC[h], n, h, NOOP)))
    _at.append(("GER_region_action_%d_allowed" % n,
                "# %d %s：能否点击的额外条件\nGER_region_action_%d_allowed = {\n    always = yes\n}" % (n, row["cname"], n)))
    _at.append(("GER_region_action_%d_visible" % n,
                "# %d %s：是否出现在列表里\nGER_region_action_%d_visible = {\n    always = yes\n}" % (n, row["cname"], n)))
for _pk, _ph in sorted(PHASES.items()):
    for _h, _d in (("on_start", "开始时"), ("on_end", "结束时（关闭地区之前）")):
        _ae.append(("GER_region_%s_%s" % (_pk, _h), "# 阶段博弈 %s：%s\nGER_region_%s_%s = {\n%s\n}"
                    % (_ph["cname"], _d, _pk, _h, NOOP)))
_ae.append(("GER_region_on_open_map", "# 地图全开（GER_region_game_open_map）时，各地区开局数值设好之后调用\n"
            "GER_region_on_open_map = {\n%s\n}" % NOOP))
_ae.append(("GER_region_actions_on_reset", "# 测试决议「重置」时调用：清掉决议自己的全国状态\n"
            "GER_region_actions_on_reset = {\n%s\n}" % NOOP))
_at.append(("GER_region_party_reform_done", "# 党改革国策完成\nGER_region_party_reform_done = {\n    always = no\n}"))
_at.append(("GER_region_shipbuilding_socialized", "# 造船业社会化完成\nGER_region_shipbuilding_socialized = {\n"
            "    has_country_flag = GER_socialization_reward_shipbuilding\n}"))
append_missing_defs(ACTIONS_EFFECTS, ["# 地区博弈 · 行动方针（决议）的效果（手写；脚本只在末尾补缺的钩子）"], _ae)
append_missing_defs(ACTIONS_TRIGGERS, ["# 地区博弈 · 行动方针（决议）的条件（手写；脚本只在末尾补缺的定义）"], _at)
write("sound/GER_region_game.asset",
      "# 由 %s 生成，不要手改。\n"
      "# 地区博弈里只悬停、不该有点击音的点击条（斜线、割让盖板）用这个：原版点击音，音量 0\n"
      "soundeffect = {\n\tname = %s\n\tvolume = 0\n\tsounds = {\n\t\tsound = click_default\n\t}\n}\n"
      % (GEN_TAG, SILENT_CLICK))
write("common/on_actions/GER_region_game_on_actions.txt",
      "# 由 %s 生成，不要手改。地区博弈：行动方针每日计时\non_actions = {\n    on_daily_GER = {\n"
      "        effect = { GER_region_game_daily_tick = yes }\n    }\n}\n" % GEN_TAG)

# ---------------------------------------------------------------- 写文件
splice("interface/GER_region_game.gfx", GFX_TEMPLATE,
       {"panel_sprites": "\n".join(sprite_lines(panel_sprites)), "sprites": "\n".join(gfx_lines)})
splice("interface/GER_region_game.gui", GUI_TEMPLATE,
       {"map_layers": GUI_MAP, "right_panel": GUI_PANEL, "list_entries": GUI_ENTRY})
splice("common/scripted_guis/GER_region_game.txt", SGUI_TEMPLATE,
       {"properties": "\n".join(props), "triggers": "\n".join(trig), "effects": "\n".join(clicks),
        "dynamic_lists": DYN_LISTS})
write("common/scripted_localisation/GER_region_game.txt", SCRIPTED_LOC)
write("common/dynamic_modifiers/GER_region_game_tiers.txt", DYN_MODIFIERS)
write("common/scripted_effects/GER_region_game_effects.txt", EFFECTS)
write("common/decisions/GER_region_game_test.txt", DECISIONS)
write("common/decisions/categories/GER_region_game_test.txt", CATEGORY)
write("localisation/simp_chinese/gui/GER_region_game_l_simp_chinese.yml", LOC_GUI, bom=True, crlf=True)
write("localisation/simp_chinese/decision/GER_region_game_test_l_simp_chinese.yml", LOC_DEC, bom=True, crlf=True)
# 清理：素材目录里不再被清单引用的旧图（例如删掉的盖板）
_used = {os.path.basename(path) for _, path, _, _ in sprites}
for _f in sorted(os.listdir(GFX_DIR)):
    if _f.lower().endswith(".png") and _f not in _used:
        os.remove(os.path.join(GFX_DIR, _f))
        print("删除不再使用的素材", _f)
_panel_used = set(PANEL_FILES) | {PHOTO_STRIP, PHOTO_IDLE_FILE}
for _f in sorted(os.listdir(PANEL_DIR)):
    if _f.lower().endswith(".png") and _f not in _panel_used:
        os.remove(os.path.join(PANEL_DIR, _f))
        print("删除不再使用的面板素材", _f)
print("素材 %d 张 -> %s" % (len(sprites), GFX_DIR_REL))
print("相邻不同色配色：", checker)
