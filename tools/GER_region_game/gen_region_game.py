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
CORE_FRAMES = {3: "left", 4: "right", 5: "weimar"}        # 面板上显示核心区方块的帧
TYPE_NAMES = {2: "摇摆区", 3: "左派核心区", 4: "右派核心区", 5: "魏玛联盟核心区",
              8: "左派控制区", 9: "右派控制区", 10: "魏玛联盟控制区"}   # 名称框右侧的地区类型（修改说明第 3、12 节）

# 右侧面板素材（修改说明_右侧面板.md）
PANEL_SRC = "右侧面板素材"
REGION12_SRC = "区块_12帧"
PANEL_DIR_REL = GFX_DIR_REL + "/panel"
PANEL_DIR = os.path.join(MOD, *PANEL_DIR_REL.split("/"))
PHOTO_DIR_REL = GFX_DIR_REL + "/photos"     # 用户交的地区照片：photos/<区块id>.png，425x157
PHOTO_BG = (25, 27, 25, 255)                # 没交照片的地区：与照片框内底同色的深色占位

# 领导人（策划案第 8 页）。portrait = 模组里现成的 156x210 头像，没有就写 None（只显示名字）。
# 名字和悬停介绍写在 HAND_PANEL_LOC 里，这里的中文名只用来第一次补占位。
# 顺序 = GER_region_Rxx_leader 的取值（1 起），以后只往后加，不要插队。
LEADERS = [
    ("daeumig", "恩斯特·多伊米希", "gfx/leaders/GER/Ernst_Daeumig.png"),
    ("dissmann", "罗伯特·迪斯曼", "gfx/leaders/GER/Robert_Dissmann.png"),
    ("henke", "阿尔弗雷德·亨克", None),
    ("koenen", "威廉·科嫩", "gfx/leaders/GER/Wilhelm_Koenen.png"),
    ("lipinski", "利平斯基", None),
    ("committee_nine", "九人委员会", None),
    ("paul_dittmann", "保罗·迪特曼", None),
    ("otto_braun", "奥托·布劳恩", "gfx/leaders/GER/Otto_Braun.png"),
    ("paul_hirsch", "保罗·希尔施", None),
    ("weimar_coalition", "魏玛联盟", None),
    ("bitta", "约瑟夫·比塔", None),
]
# 行动方针（策划案第 5、6 页）。日常决议：(名称, 政治点数花费, 生效天数)，按地区各自计时，可同时生效多条。
#   生效天数 = 点击后保持选中（暗黄）的天数：「耗时 N 天」的写 N（结束时给效果），「持续 24 周」的写 168（期间每两周给效果）；
#   0 = 点了立刻生效，不进入生效中状态。
DAILY_ROWS = [("扩大宣传投入", 15, 7), ("扩张防卫组织", 15, 7), ("组织网络的扩展", 25, 168),
              ("推动公共事业", 30, 168), ("组织重心向工厂转移", 20, 14), ("发起罢工", 100, 14),
              ("工厂委员会的扩张", 20, 7), ("影子苏维埃", 65, 0)]
# 驻区方针：每个地区同时只有一条生效，点另一条 = 切换（花 25pp），一直生效到切换为止
GARRISON_ROWS = ["扩充安全部队", "总结政权经验", "培训根据地干部", "支援邻近地区"]
GARRISON_COST = 25
BIWEEKLY = 14   # 「每两周」效果的间隔天数

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
    for r in regions:
        src = None
        for ext in (".png", ".jpg", ".jpeg"):
            p = os.path.join(MOD, *PHOTO_DIR_REL.split("/"), r["id"] + ext)
            if os.path.exists(p):
                src = p
                break
        if not src:
            continue
        im = Image.open(src).convert("RGBA")
        w, h = im.size
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
            adjusted.append(note)
        strip.paste(im, ((r["idx"] - 1) * PHOTO_W, 0))
        have.append(r["id"])
    save_png_if_changed(strip, os.path.join(PANEL_DIR, PHOTO_STRIP))
    print("地区照片：已交 %d 张 %s，其余用深色占位" % (len(have), have))
    for n in adjusted:
        print("  照片尺寸不对，已处理：", n)


for i, r in enumerate(regions, 1):
    r["idx"] = i                                      # GER_region_selected 的取值（也是照片帧号）
build_photo_strip()

panel_sprites = [("GFX_GER_region_panel_photos", PANEL_DIR_REL + "/" + PHOTO_STRIP, len(regions), False)]
leaders = []
for i, (key, cname, portrait) in enumerate(LEADERS, 1):
    ld = {"idx": i, "key": key, "cname": cname, "portrait": portrait,
          "name_key": "GER_region_leader_%s_name" % key, "tt": "GER_region_leader_%s_tt" % key}
    if portrait:
        if png_size(os.path.join(MOD, *portrait.split("/"))) != (156, 210):
            raise ValueError("头像不是 156x210：" + portrait)
        ld["sp"] = "GFX_GER_region_leader_%s" % key
        ld["el"] = "GER_region_panel_leader_%s" % key
        panel_sprites.append((ld["sp"], portrait, 1, False))
    leaders.append(ld)

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

GARRISON_OPEN = "check_variable = { GER_region_sel_support > 99.99 } check_variable = { GER_region_sel_control > 99.99 }"
# 行动方针 = 决议。效果和额外条件是手写文件，只在不存在时生成一次，之后脚本不再碰
ACTIONS_EFFECTS = "common/scripted_effects/GER_region_game_actions.txt"
ACTIONS_TRIGGERS = "common/scripted_triggers/GER_region_game_actions.txt"
# 策划案第 5、6 页的原话，只写进上面两个文件的注释里，方便以后写效果
ACTION_NOTES = [
    "15pp 支持度+3（耗时7天）",
    "15pp 控制度+3（耗时7天）",
    "25pp 每两周控制度增长+0.4（持续时间24周）",
    "30pp 每两周支持度+0.4（持续时间24周），spd随机一个派别政党支持度+0.5",
    "20pp 该地区永久每两周控制度增长+0.02（党改革国策解锁，每个地区可以点两次）（耗时14天）",
    "100pp 控制度+5，支持度+5（耗时14天，持续时间内建造速度-80%）（效果好，长cd）",
    "20pp（耗时7天）控制度+5",
    "65pp（支持度50大于等于控制度大于等于80）点了之后该地区转换为控制区，控制度不再能够下降到百分之八十以下",
    "每两周+0.2武装力量",
    "每两周+2%的无产阶级组织度",
    "每日+0.3pp",
    "相邻地区每两周控制度+1",
]

ROWS = []   # 12 条行动方针：1-8 日常决议，9-12 驻区方针
for i, (nm, cost, days) in enumerate(DAILY_ROWS, 1):
    ROWS.append({"n": i, "cname": nm, "cost": cost, "days": days, "garrison": False})
for j, nm in enumerate(GARRISON_ROWS, len(DAILY_ROWS) + 1):
    ROWS.append({"n": j, "cname": nm, "cost": GARRISON_COST, "days": 0, "garrison": True})
for row in ROWS:
    n = row["n"]
    row["el"] = "GER_region_panel_row_%d" % n
    row["el_sel"] = "GER_region_panel_row_%d_selected" % n   # 生效中时盖上的帧 3
    row["name"] = "GER_region_panel_row_%d_name" % n
    row["tt"] = "GER_region_panel_row_%d_tt" % n
    row["sel_days"] = "GER_region_sel_row_%d_days" % n         # 选中地区这条还剩几天（面板读）
    row["sel_weeks"] = "GER_region_sel_row_%d_weeks" % n
    row["pp_ok"] = "has_political_power > %s" % (row["cost"] - 0.01)
    # 「生效中」：日常决议 = 选中地区剩余天数 > 0；驻区方针 = 选中地区当前方针是这一条
    row["active"] = ("check_variable = { GER_region_sel_policy = %d }" % n if row["garrison"]
                     else "check_variable = { %s > 0 }" % row["sel_days"])
TIMED_ROWS = [row for row in ROWS if not row["garrison"] and row["days"] > 0]
GARRISON = [row for row in ROWS if row["garrison"]]
for r in regions:
    r["v_policy"] = "GER_region_%s_policy" % r["key"]            # 当前驻区方针 9-12，0 = 无
    r["v_policy_days"] = "GER_region_%s_policy_days" % r["key"]  # 当前方针已生效天数
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
        name = "GFX_GER_region_panel_core_left"
        texturefile = "gfx/interface/GER_region_game/panel/core_left.png"
    }
    spriteType = {
        name = "GFX_GER_region_panel_core_right"
        texturefile = "gfx/interface/GER_region_game/panel/core_right.png"
    }
    spriteType = {
        name = "GFX_GER_region_panel_core_weimar"
        texturefile = "gfx/interface/GER_region_game/panel/core_weimar.png"
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


def button(name, sprite, x, y, tt=None):
    s = ["buttonType = {",
         '    name = "%s"' % name,
         '    quadTextureSprite = "%s"' % sprite,
         "    position = { x = %d y = %d }" % (x, y)]
    if tt:
        s.append('    pdx_tooltip = "%s"' % tt)
    s.append("    clicksound = click_default")
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
            "GER_region_locked_all_tt")
for r in regions:
    L += button(r["el_btn"], r["sp_hit"], r["x"], r["y"], r["tooltip"])   # 第一行「地区名：类型」+ 手写介绍
for o in overlays:
    L += button(o["el_btn"], o["sp_hit"], o["x"], o["y"], o["tt"])
L += button("GER_region_alsace_lorraine_button", "GFX_GER_region_alsace_lorraine_hit", AL_H["x"], AL_H["y"],
            "GER_region_alsace_lorraine_tt")
L += button("GER_region_bav_corner_button", "GFX_GER_region_bav_corner_hit", BC_H["x"], BC_H["y"],
            "GER_region_bav_corner_tt")
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
P += icon("GER_region_panel_photo_vignette", "GFX_GER_region_panel_region_photo_vignette", *RPH["photo_pos_window"])
_cx, _cy, _cw, _ch = RPH["caption_rect_window"]
P += tbox("GER_region_panel_photo_name", _cx + 4, _cy, "GER_region_game_selected_name", 220, _ch)
P += tbox("GER_region_panel_photo_caption", _cx + _cw - 4 - 200, _cy, "GER_region_panel_photo_caption", 200, _ch,
          fmt="right")
P.append("# 6-9 领导人：框（带阴影）→ 头像（每人一个，scale %s，按 GER_region_sel_leader 切换）→ 暗角（带悬停提示）→ 名字"
         % PJ["leader_portrait_scale"])
P += icon("GER_region_panel_leader_frame", "GFX_GER_region_panel_leader_photo_frame", *LPH["sprite_pos_window"])
for ld in leaders:
    if ld.get("sp"):
        P += icon(ld["el"], ld["sp"], *LPH["photo_pos_window"], extra=["scale = %s" % PJ["leader_portrait_scale"]])
P += icon("GER_region_panel_leader_vignette", "GFX_GER_region_panel_leader_photo_vignette", *LPH["photo_pos_window"],
          transparent=False, extra=['pdx_tooltip = "GER_region_panel_leader_tt"'])
_lx, _ly, _lw, _lh = LPH["caption_rect_window"]
P += tbox("GER_region_panel_leader_name", _lx, _ly, "GER_region_panel_leader_name", _lw, _lh, fmt="centre")

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

P.append("# 18-22 决议总框：行动方针 8 条 + 驻区方针 4 条。条：帧1 普通 / 帧2 悬停 / 帧3 生效中")
_act = []
_AX, _AY = 1281, 150
_act += tbox("GER_region_panel_actions_title", 1297 - _AX, 166 - _AY, "GER_region_game_policy_label", 200, 26, "hoi_18mbs")


def row_els(row, y):
    # 实测：scripted_gui 用 properties 给按钮设 frame 后，引擎不再自动切悬停帧 2。
    # 所以按钮本身不设 frame（帧1 普通 / 帧2 悬停 交给引擎），生效中时在上面盖一张帧 3 的图标（不挡鼠标）。
    rx = 1295 - _AX
    return (button(row["el"], "GFX_GER_region_panel_decision_row", rx, y, row["tt"])
            + icon(row["el_sel"], "GFX_GER_region_panel_decision_row", rx, y, frame=3)
            + tbox(row["el"] + "_name", rx + 14, y + 11, "GER_region_panel_row_%d_label" % row["n"], 180, 22)
            + tbox(row["el"] + "_status", rx + 292 - 14 - 120, y + 11, "GER_region_panel_row_%d_status" % row["n"],
                   120, 22, fmt="right"))


for k, row in enumerate(r for r in ROWS if not r["garrison"]):
    _act += row_els(row, 200 + 48 * k - _AY)
_act += tbox("GER_region_panel_garrison_label", 1299 - _AX, 593 - _AY, "GER_region_panel_garrison_label", 100, 22,
             tt="GER_region_panel_garrison_tt")
for k, row in enumerate(r for r in ROWS if r["garrison"]):
    _act += row_els(row, 622 + 48 * k - _AY)
P += box("GER_region_panel_actions", _AX, _AY, 320, 731, _act)
GUI_PANEL = "\n".join(P)

GUI_TEMPLATE = """guiTypes = {
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
        position = { x = 0 y = 0 }
        Orientation = center
        Origo = center
        size = { width = %(W)d height = %(H)d }
        moveable = yes

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
                position = { x = 10 y = 12 }
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
trig.append("# 右侧面板：照片、照片说明只在选中地区后显示")
for el in ("GER_region_panel_photo", "GER_region_panel_photo_name", "GER_region_panel_photo_caption"):
    trig.append("%s_visible = { %s }" % (el, SEL))
trig.append("# 领导人头像：按选中地区的领导人序号（GER_region_sel_leader）切换；没头像的领导人只显示名字")
for ld in leaders:
    if ld.get("sp"):
        trig.append("%s_visible = { check_variable = { GER_region_sel_leader = %d } }" % (ld["el"], ld["idx"]))
trig.append("GER_region_panel_leader_vignette_visible = { check_variable = { GER_region_sel_leader > 0 } }")
trig.append("# 数值框 <-> 核心区方块：帧 %s = 核心区，显示方块；其余显示支持度 / 控制度"
            % "/".join(str(f) for f in sorted(CORE_FRAMES)))
trig.append("GER_region_panel_values_visible = { NOT = { %s } }" % CORE_ANY)
for f, side in sorted(CORE_FRAMES.items()):
    trig.append("GER_region_panel_core_%s_visible = { check_variable = { GER_region_sel_frame = %d } }" % (side, f))
trig.append("GER_region_panel_core_title_visible = { OR = { %s } }" % CORE_ANY)
trig.append("# 行动方针条：选中地区里生效中的条盖上帧 3（每条各自计时，可以同时好几条）")
for row in ROWS:
    trig.append("%s_visible = { %s }" % (row["el_sel"], row["active"]))
trig.append("# 决议能否点击：选中了地区、不在生效中、政治点数够；驻区方针还要支持度、控制度双满；")
trig.append("# 再加上 %s 里的 GER_region_action_N_allowed（冷却、解锁条件等）" % ACTIONS_TRIGGERS)
for row in ROWS:
    cond = "check_variable = { GER_region_selected > 0 } NOT = { %s } %s" % (row["active"], row["pp_ok"])
    if row["garrison"]:
        cond += " " + GARRISON_OPEN
    trig.append("%s_click_enabled = { %s GER_region_action_%d_allowed = yes }" % (row["el"], cond, row["n"]))

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
clicks.append("# 行动方针条 = 决议：点击扣政治点数、开始计时、执行 GER_region_action_N（效果写在 %s）。" % ACTIONS_EFFECTS)
clicks.append("# 能不能点见 triggers 里的 _click_enabled。")
for row in ROWS:
    clicks.append("%s_click = { GER_region_game_take_action_%d = yes }" % (row["el"], row["n"]))


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
sl.append("# 核心区方块的说明")
sl += defined_text("GER_region_sel_core_desc",
                   [("check_variable = { GER_region_sel_frame = %d }" % f, "GER_region_panel_core_%d_desc" % f)
                    for f in sorted(CORE_FRAMES)], "GER_region_panel_empty")
sl.append("# 照片右下角小字（拍摄地 / 年份）")
sl += defined_text("GER_region_sel_photo_caption", [(is_sel(r["idx"]), r["caption_key"]) for r in regions],
                   "GER_region_panel_empty")
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
        cases.append(("check_variable = { %s > %d }" % (row["sel_days"], BIWEEKLY - 1),
                      "GER_region_panel_row_%d_status_weeks" % n))
        cases.append((row["active"], "GER_region_panel_row_%d_status_days" % n))
    cases.append(("NOT = { %s }" % allowed, "GER_region_panel_row_%d_status_grey" % n))
    cases.append(("NOT = { %s }" % row["pp_ok"], "GER_region_panel_row_%d_status_red" % n))
    sl += defined_text("GER_region_row_%d_status" % n, cases, "GER_region_panel_row_%d_status_gold" % n)
SCRIPTED_LOC = "\n".join(sl) + "\n"

# ---------------------------------------------------------------- scripted_effects
eff = ["# 由 %s 生成，不要手改。" % GEN_TAG, ""]
eff.append("# 刷新地图和右侧面板：state（= 帧号 1-%d）拷到 frame，再刷新选中地区和行动方针条。" % REGION_FRAMES)
eff.append("# 改了任何 GER_region_* 变量后都跑一次。")
eff.append("GER_region_game_sync_frames = {")
for r in regions:
    eff.append("    set_variable = { %s = %s }" % (r["v_frame"], r["v_state"]))
eff.append("    GER_region_game_sync_selected = yes")
eff.append("}")
eff.append("")
eff.append("# 把选中区块（GER_region_selected）的帧号、支持度、控制度、领导人、决议计时、驻区方针拷到 GER_region_sel_*，右侧面板读这些")
eff.append("GER_region_game_sync_selected = {")
for v in ("frame", "support", "control", "leader", "policy"):
    eff.append("    set_variable = { GER_region_sel_%s = 0 }" % v)
for row in TIMED_ROWS:
    eff.append("    set_variable = { %s = 0 }" % row["sel_days"])
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
    eff.append("    }")
eff.append("    clamp_variable = { var = GER_region_sel_support min = 0 max = 100 }")
eff.append("    clamp_variable = { var = GER_region_sel_control min = 0 max = 100 }")
for row in TIMED_ROWS:
    eff.append("    set_variable = { %s = %s }" % (row["sel_weeks"], row["sel_days"]))
    eff.append("    divide_variable = { %s = 7 }" % row["sel_weeks"])
eff.append("}")
eff.append("")


def on_target(stmts):
    """对 GER_region_target 指向的区块执行 stmts（{support} {control} 等指代该区块的变量）"""
    out = []
    for i, r in enumerate(regions):
        body = " ".join(s.format(support=r["v_support"], control=r["v_control"]) for s in stmts)
        out.append("    %s = { limit = { check_variable = { GER_region_target = %d } } %s }"
                   % ("if" if i == 0 else "else_if", r["idx"], body))
    return out


eff.append("# ---- 给手写决议效果用的小工具：先 set_temp_variable = { GER_region_delta = 3 }，再调用。")
eff.append("# 作用于 GER_region_target 指向的地区（决议效果执行时已经设好），结果夹在 0-100。")
eff.append("GER_region_target_add_support = {")
eff += on_target(["add_to_variable = {{ {support} = GER_region_delta }}",
                  "clamp_variable = {{ var = {support} min = 0 max = 100 }}"])
eff.append("}")
eff.append("GER_region_target_add_control = {")
eff += on_target(["add_to_variable = {{ {control} = GER_region_delta }}",
                  "clamp_variable = {{ var = {control} min = 0 max = 100 }}"])
eff.append("}")
eff.append("")
eff.append("# ---- 点击行动方针：扣政治点数 → 记下目标地区 → 开始计时 / 切换方针 → 执行手写效果 → 刷新")
for row in ROWS:
    n = row["n"]
    eff.append("GER_region_game_take_action_%d = {" % n)
    eff.append("    add_political_power = -%d" % row["cost"])
    eff.append("    set_variable = { GER_region_target = GER_region_selected }")
    for i, r in enumerate(regions):
        if row["garrison"]:
            body = "set_variable = { %s = %d } set_variable = { %s = 0 }" % (r["v_policy"], n, r["v_policy_days"])
        elif row["days"]:
            body = "set_variable = { %s = %d }" % (r["v_act"][n], row["days"])
        else:
            break
        eff.append("    %s = { limit = { %s } %s }" % ("if" if i == 0 else "else_if", is_sel(r["idx"]), body))
    eff.append("    GER_region_action_%d = yes" % n)
    eff.append("    GER_region_game_sync_frames = yes")
    eff.append("}")
eff.append("")
eff.append("# ---- 每天（on_daily_GER）：日常决议倒计时，每满 %d 天调用 _biweekly，到 0 调用 _complete；" % BIWEEKLY)
eff.append("# 驻区方针累计天数，每满 %d 天调用当前方针的 _biweekly。" % BIWEEKLY)
eff.append("GER_region_game_daily_tick = {")
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
    eff.append("        set_temp_variable = { GER_region_elapsed = %s }" % r["v_policy_days"])
    eff.append("        modulo_temp_variable = { GER_region_elapsed = %d }" % BIWEEKLY)
    eff.append("        if = {")
    eff.append("            limit = { check_variable = { GER_region_elapsed = 0 } }")
    eff.append("            set_variable = { GER_region_target = %d }" % r["idx"])
    for row in GARRISON:
        eff.append("            if = { limit = { check_variable = { %s = %d } } GER_region_action_%d_biweekly = yes }"
                   % (r["v_policy"], row["n"], row["n"]))
    eff.append("        }")
    eff.append("    }")
eff.append("    GER_region_game_sync_frames = yes")
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
    for v in r["v_act"].values():
        eff.append("    clear_variable = %s" % v)
eff.append("    clear_variable = GER_region_selected")
eff.append("    GER_region_game_hide_all_overlays = yes")
eff.append("}")
EFFECTS = "\n".join(eff) + "\n"

# ---------------------------------------------------------------- 测试决议
ADJ = {  # 由区块精灵的不透明像素外扩 2px 求得的相邻关系（只用于「相邻不同色」测试）
    "R01": ["R02", "R15"], "R02": ["R01", "R03", "R04", "R06", "R08", "R11", "R15"],
    "R03": ["R02", "R04"], "R04": ["R02", "R03", "R05", "R06"], "R05": ["R04", "R06", "R13"],
    "R06": ["R02", "R04", "R05", "R07", "R08", "R13", "R16"], "R07": ["R06", "R08"],
    "R08": ["R02", "R06", "R07", "R09", "R11"], "R09": ["R08", "R10", "R11"],
    "R10": ["R09", "R11", "R12"], "R11": ["R02", "R08", "R09", "R10", "R12", "R15"],
    "R12": ["R10", "R11", "R14", "R15"], "R13": ["R05", "R06"], "R14": ["R12", "R15"],
    "R15": ["R01", "R02", "R11", "R12", "R14"], "R16": ["R06"],
}
CHECKER_COLORS = [3, 4, 6, 2]   # 红、蓝、绿、中立
checker = {}
for k in sorted(ADJ, key=lambda k: -len(ADJ[k])):
    used = {checker.get(n) for n in ADJ[k]}
    checker[k] = next(c for c in CHECKER_COLORS if c not in used)


def dec(name, body, desc_extra=None):
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
         + ["clear_variable = %s" % v for v in TEST_VARS])
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
       ' GER_region_game_quote: "“我的故事并不让人愉快。它不像虚构的故事那般甜美和谐。它有荒诞和迷惘的味道，疯狂和梦境的味道。它的味道，就像那些不再想自我欺骗之人的生活的味道。”"',
       ' GER_region_game_selected_name: "[GER_region_selected_name]"',
       ' GER_region_game_selected_none: "（选中地区名称）"',
       ' GER_region_game_support_label: "支持度"',
       ' GER_region_game_control_label: "控制度"',
       ' GER_region_game_policy_label: "行动方针"',
       ' GER_region_panel_garrison_label: "驻区方针"',
       ' GER_region_panel_empty: ""',
       ' GER_region_panel_support_value: "[?GER_region_sel_support|0]%"',
       ' GER_region_panel_control_value: "[?GER_region_sel_control|0]%"',
       ' GER_region_panel_support_tooltip: "§Y支持度§!：[?GER_region_sel_support|0]%\\n\\n[GER_region_panel_support_body]"',
       ' GER_region_panel_control_tooltip: "§Y控制度§!：[?GER_region_sel_control|0]%\\n\\n[GER_region_panel_control_body]"',
       ' GER_region_panel_photo_caption: "§Y[GER_region_sel_photo_caption]§!"',
       ' GER_region_panel_leader_name: "[GER_region_sel_leader_name]"',
       ' GER_region_panel_leader_tt: "[GER_region_sel_leader_tt]"',
       ' GER_region_panel_core_title: "[GER_region_sel_type]"',
       ' GER_region_panel_core_tooltip: "§Y[GER_region_sel_type]§!\\n\\n[GER_region_sel_core_desc]"',
       ' GER_region_panel_status_policy_on: "§G生效中§!"',
       ]
loc += [' GER_region_type_%d: "%s"' % (f, n) for f, n in sorted(TYPE_NAMES.items())]
loc.append(" # 地图悬停提示：第一行「地区名：类型」，下面接手写介绍（%s）" % HAND_TT_LOC)
for r in regions:
    loc.append(' %s: "[%s]\\n\\n[%s]"' % (r["tooltip"], r["head"], r["body"]))
    loc.append(' %s_none: "§Y%s§!"' % (r["head"], r["name"]))
    for f, tn in sorted(TYPE_NAMES.items()):
        loc.append(' %s_%d: "§Y%s：%s§!"' % (r["head"], f, r["name"], tn))
loc.append(" # 行动方针条：名字、悬停提示写在 %s；花费、天数在 gen_region_game.py 的 DAILY_ROWS" % HAND_PANEL_LOC)
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
        loc.append(' GER_region_panel_row_%d_status_days: "§G生效中 [?%s|0]天§!"' % (n, row["sel_days"]))
        loc.append(' GER_region_panel_row_%d_status_weeks: "§G生效中 [?%s|0]周§!"' % (n, row["sel_weeks"]))
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
    panel_entries.append((ld["tt"], "【待定】" + ld["cname"]))
for r in regions:
    panel_entries.append((r["caption_key"], ""))
append_missing(HAND_PANEL_LOC, panel_entries, header=[
    "地区博弈 · 右侧面板文字（手写，脚本只在末尾补缺的键，不改已有行）",
    "行动方针名称取自策划案第 5、6 页；花费和天数在 gen_region_game.py 的 DAILY_ROWS 里，颜色由界面加。",
    "GER_region_panel_support_tt / _control_tt = 支持度、控制度的悬停说明（上面会自动加一行当前数值）。",
    "GER_region_panel_core_N_desc = 核心区方块的悬停说明。",
    "GER_region_<区块id>_photo_caption = 照片右下角小字（拍摄地 / 年份），留空就不显示。",
    "领导人序号见 tools/GER_region_game/gen_region_game.py 的 LEADERS。"])
LOC_GUI = "\n".join(loc) + "\n"

dl = ["l_simp_chinese:",
      " # 由 %s 生成，不要手改" % GEN_TAG,
      ' GER_region_game_test_category: "【测试】地区博弈地图"',
      ' GER_region_game_test_category_desc: "地区博弈地图的素材和接口测试。每个决议执行后会自动打开地区博弈界面。"',
      ' GER_region_test_reset: "重置为开局画面"',
      ' GER_region_test_reset_desc: "隐藏全部区块和割让盖板，只剩无缝整块斜线 + 阿尔萨斯-洛林、巴伐利亚缺角两块。"',
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

# ---------------------------------------------------------------- 行动方针（决议）的手写文件：只在不存在时生成
def write_if_missing(path_rel, text):
    if os.path.exists(os.path.join(MOD, *path_rel.split("/"))):
        return
    write(path_rel, text)


_reg_list = "，".join("%d=%s(%s)" % (r["idx"], r["name"], r["key"]) for r in regions)
ae = ["# 地区博弈 · 行动方针（决议）的效果。手写文件：%s 只在文件不存在时生成一次，之后不会覆盖。" % GEN_TAG,
      "#",
      "# 已由界面自动处理（不用在这里写）：扣政治点数、按天计时、生效中显示暗黄、驻区方针切换。",
      "# 花费和天数在 gen_region_game.py 的 DAILY_ROWS / GARRISON_COST 里改。",
      "#",
      "# 每条决议有这几个钩子，都在本国（GER）作用域执行：",
      "#   GER_region_action_N           点击时（政治点数已扣）",
      "#   GER_region_action_N_biweekly  生效期间每满 %d 天一次（生效 >= %d 天的日常决议、驻区方针才有）" % (BIWEEKLY, BIWEEKLY),
      "#   GER_region_action_N_complete  计时结束那天（有生效天数的日常决议才有）",
      "# 被操作的地区 = 变量 GER_region_target：%s。" % _reg_list,
      "# 地区变量：GER_region_Rxx_support / _control（0-100）、_state（类型=帧号）、_leader。",
      "# 改支持度 / 控制度可以用现成的小工具（自动夹在 0-100）：",
      "#   set_temp_variable = { GER_region_delta = 3 }  GER_region_target_add_support = yes",
      "#   set_temp_variable = { GER_region_delta = -2 } GER_region_target_add_control = yes",
      "# 注意：scripted_effect 不能是空的（实测空的引擎不认，点击会整段失效），每个钩子里至少留一句。",
      ""]
NOOP = "    set_temp_variable = { GER_region_noop = 1 }   # 占位（空的 scripted_effect 引擎不认），写了效果后可删"
at = ["# 地区博弈 · 行动方针（决议）能否点击的额外条件。手写文件：%s 只在文件不存在时生成一次。" % GEN_TAG,
      "# 界面已经自带的条件：选中了地区、该地区这条不在生效中、政治点数够；驻区方针（9-12）还要支持度、控制度双满。",
      "# 这里返回假时按钮不可点（状态字变灰）。冷却、解锁国策、每个地区限点几次等写在这里，目标地区 = GER_region_selected。",
      ""]
for row in ROWS:
    n = row["n"]
    if row["garrison"]:
        kind = "驻区方针，切换 %dpp，一直生效到切换为止" % row["cost"]
    elif row["days"]:
        kind = "日常决议，%dpp，生效 %d 天" % (row["cost"], row["days"])
    else:
        kind = "日常决议，%dpp，立即生效" % row["cost"]
    ae += ["# ======== %d %s（%s）" % (n, row["cname"], kind),
           "# 策划案：%s" % ACTION_NOTES[n - 1],
           "GER_region_action_%d = {" % n, NOOP, "}"]
    if row["garrison"] or row["days"] >= BIWEEKLY:
        ae += ["GER_region_action_%d_biweekly = {" % n, NOOP, "}"]
    if not row["garrison"] and row["days"]:
        ae += ["GER_region_action_%d_complete = {" % n, NOOP, "}"]
    ae.append("")
    at += ["# %d %s（%s）" % (n, row["cname"], kind),
           "GER_region_action_%d_allowed = {" % n,
           "    always = yes",
           "}", ""]
write_if_missing(ACTIONS_EFFECTS, "\n".join(ae))
write_if_missing(ACTIONS_TRIGGERS, "\n".join(at))
write("common/on_actions/GER_region_game_on_actions.txt",
      "# 由 %s 生成，不要手改。地区博弈：行动方针每日计时\non_actions = {\n    on_daily_GER = {\n"
      "        effect = { GER_region_game_daily_tick = yes }\n    }\n}\n" % GEN_TAG)

# ---------------------------------------------------------------- 写文件
splice("interface/GER_region_game.gfx", GFX_TEMPLATE,
       {"panel_sprites": "\n".join(sprite_lines(panel_sprites)), "sprites": "\n".join(gfx_lines)})
splice("interface/GER_region_game.gui", GUI_TEMPLATE, {"map_layers": GUI_MAP, "right_panel": GUI_PANEL})
splice("common/scripted_guis/GER_region_game.txt", SGUI_TEMPLATE,
       {"properties": "\n".join(props), "triggers": "\n".join(trig), "effects": "\n".join(clicks)})
write("common/scripted_localisation/GER_region_game.txt", SCRIPTED_LOC)
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
_panel_used = set(PANEL_FILES) | {PHOTO_STRIP}
for _f in sorted(os.listdir(PANEL_DIR)):
    if _f.lower().endswith(".png") and _f not in _panel_used:
        os.remove(os.path.join(PANEL_DIR, _f))
        print("删除不再使用的面板素材", _f)
print("素材 %d 张 -> %s" % (len(sprites), GFX_DIR_REL))
print("相邻不同色配色：", checker)
