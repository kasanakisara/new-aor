# -*- coding: utf-8 -*-
"""
地区博弈地图 GUI 生成脚本（AOR / GER）

读取美术素材文件夹里的 14_素材清单.json 和 16_区块素材清单.json：
  1. 把素材原样（逐字节）复制到 gfx/interface/GER_region_game/，文件名改成英文；
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
需要 Pillow（只用于把 2 帧点击条拼成 3 帧，纯像素复制）：python -m pip install pillow
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

# 摇摆（state 5）暂时显示成帧 2；以后启用黄色时把这里改成 None
SWING_STATE, SWING_DISPLAY_FRAME = 5, 2
USED_FRAMES = [1, 2, 3, 4, 6]          # 当前使用的 5 种颜色（帧 5、7 保留在素材里）

GEN_TAG = "tools/GER_region_game/gen_region_game.py"

# 正式悬浮介绍直接手写在这个本地化文件里，脚本只读不写；
# 这里已有的键，生成的本地化文件就不再输出【待定】占位，避免重复键。
HAND_TT_LOC = "localisation/simp_chinese/gui/GER_region_game_tt_l_simp_chinese.yml"


def hand_written_keys():
    path = os.path.join(MOD, *HAND_TT_LOC.split("/"))
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8-sig") as f:
        return set(re.findall(r"^\s*([A-Za-z0-9_.]+):\d*\s*\"", f.read(), flags=re.M))


# ---------------------------------------------------------------- 工具函数
def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("不是 PNG：" + path)
    return struct.unpack(">II", head[16:24])


def copy_asset(src_rel, dst_name, expect_w, expect_h):
    src = os.path.join(SRC, *src_rel.split("/"))
    w, h = png_size(src)
    if (w, h) != (expect_w, expect_h):
        raise ValueError("尺寸不符 %s：实际 %dx%d，清单推算 %dx%d" % (src_rel, w, h, expect_w, expect_h))
    dst = os.path.join(GFX_DIR, dst_name)
    shutil.copyfile(src, dst)          # 逐字节复制，不做任何处理
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
    out.save(dst, "PNG")
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
    with open(path, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
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

regions = []    # 16 个区块
by_id = {r["id"]: r for r in M16["regions"]}
for r in M16["regions"]:
    if r["frames"] != 7:
        continue
    hit = by_id[r["id"] + "_hit"]
    assert (hit["x"], hit["y"], hit["w"], hit["h"]) == (r["x"], r["y"], r["w"], r["h"])
    regions.append({
        "id": r["id"],                       # R01_WeserEms
        "key": r["id"].split("_")[0],        # R01  （变量用）
        "name": r["name"],
        "x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"],
        "file": "区块/" + r["file"], "hit_file": "区块/" + hit["file"],
    })
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
                              copy_asset(r["file"], "%s_fill.png" % r["id"], r["w"] * 7, r["h"]), 7)
    r["sp_hit"] = add_sprite("GFX_GER_region_%s_hit" % r["id"],
                             copy_asset(r["hit_file"], "%s_hit.png" % r["id"], r["w"] * 3, r["h"]), 3, True)
for o in overlays:
    o["sp_fill"] = add_sprite("GFX_GER_region_OV_%s" % o["id"],
                              copy_asset(o["file"], "OV_%s.png" % o["id"], o["w"], o["h"]), 1)
    o["sp_hit"] = add_sprite("GFX_GER_region_OV_%s_hit" % o["id"],
                             copy_hit2_as_3(o["hit_file"], "OV_%s_hit.png" % o["id"], o["w"], o["h"]), 3, True)

# ---------------------------------------------------------------- 命名约定
for r in regions:
    r["el_fill"] = "GER_region_%s_fill" % r["id"]
    r["el_btn"] = "GER_region_%s_button" % r["id"]
    r["v_open"] = "GER_region_%s_open" % r["key"]      # =1 显示（已开放）
    r["v_state"] = "GER_region_%s_state" % r["key"]    # 1-7 逻辑状态（5=摇摆）
    r["v_frame"] = "GER_region_%s_frame" % r["key"]    # 1-7 实际显示帧（由 sync 计算）
    r["tt"] = "GER_region_%s_tt" % r["id"]
    r["name_key"] = "GER_region_%s_name" % r["id"]
for i, r in enumerate(regions, 1):
    r["idx"] = i                                      # GER_region_selected 的取值
for o in overlays:
    o["el_fill"] = "GER_region_OV_%s" % o["id"]
    o["el_btn"] = "GER_region_OV_%s_button" % o["id"]
    o["v_shown"] = "GER_region_OV_%s_shown" % o["id"]  # =1 显示
    o["tt"] = "GER_region_OV_%s_tt" % o["id"]

# ---------------------------------------------------------------- .gfx
gfx_lines = []
for name, path, frames, tcheck in sprites:
    gfx_lines.append("spriteType = {")
    gfx_lines.append('    name = "%s"' % name)
    gfx_lines.append('    texturefile = "%s"' % path)
    if frames > 1:
        gfx_lines.append("    noOfFrames = %d" % frames)
    if tcheck:
        gfx_lines.append("    transparencecheck = yes")
    gfx_lines.append("}")
GFX_TEMPLATE = """spriteTypes = {
    # 右侧面板占位框：tiled_plain_bg_lined 的金线贴着贴图外缘，
    # 小框用 8px 的 borderSize，避免默认 64px 边角在 30px 高的框里叠在一起。
    corneredTileSpriteType = {
        name = "GFX_GER_region_game_frame"
        size = { x = 190 y = 190 }
        textureFile = "gfx/interface/tiles/tiled_plain_bg_lined.dds"
        borderSize = { x = 8 y = 8 }
        tilingCenter = yes
        effectFile = "gfx/FX/buttonstate_nodowneffect.lua"
    }

    # 地图素材：像素对齐，GUI 里一律 scale = 1，不要缩放。
    {{GEN:sprites}}
}
"""

# ---------------------------------------------------------------- .gui 地图层
def icon(name, sprite, x, y, frame=None, transparent=True):
    s = ["iconType = {",
         '    name = "%s"' % name,
         '    spriteType = "%s"' % sprite,
         "    position = { x = %d y = %d }" % (x, y)]
    if frame:
        s.append("    frame = %d" % frame)
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
L.append("# 层 4：16 个区块精灵（7 帧）。默认隐藏；帧号 = var:GER_region_Rxx_frame")
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
    L += button(r["el_btn"], r["sp_hit"], r["x"], r["y"], r["tt"])
for o in overlays:
    L += button(o["el_btn"], o["sp_hit"], o["x"], o["y"], o["tt"])
L += button("GER_region_alsace_lorraine_button", "GFX_GER_region_alsace_lorraine_hit", AL_H["x"], AL_H["y"],
            "GER_region_alsace_lorraine_tt")
L += button("GER_region_bav_corner_button", "GFX_GER_region_bav_corner_hit", BC_H["x"], BC_H["y"],
            "GER_region_bav_corner_tt")
GUI_MAP = "\n".join(L)


def frame_box(name, x, y, w, h, text=None, font="hoi_16mbs"):
    s = ["containerWindowType = {",
         '    name = "%s"' % name,
         "    position = { x = %d y = %d }" % (x, y),
         "    size = { width = %d height = %d }" % (w, h),
         '    background = { name = "%s_bg" quadTextureSprite = "GFX_GER_region_game_frame" }' % name]
    if text:
        s += ["    instantTextboxType = {",
              '        name = "%s_text"' % name,
              "        position = { x = 4 y = %d }" % max(2, (h - 20) // 2),
              '        font = "%s"' % font,
              '        text = "%s"' % text,
              "        maxWidth = %d" % (w - 8),
              "        maxHeight = %d" % min(h - 4, 22),
              "        format = centre",
              "    }"]
    s.append("}")
    return "\n".join(s)


def text_button(name, x, y, w, h, text):
    return "\n".join([
        "buttonType = {",
        '    name = "%s"' % name,
        "    position = { x = %d y = %d }" % (x, y),
        "    size = { x = %d y = %d }" % (w, h),
        '    quadTextureSprite = "GFX_GER_region_game_frame"',
        '    buttonText = "%s"' % text,
        '    buttonFont = "hoi_16mbs"',
        "    clicksound = click_default",
        "}"])


RX = MAP_X + CANVAS_W + 16       # 右侧面板左边 1280
RX2 = RX + 133                   # 右列 1413
RIGHT_PANEL = "\n".join([
    "# ---- 右侧面板：只是框架占位，美术之后替换（此段只在首次生成时写出，之后可以随便手改）----",
    frame_box("GER_region_game_name_box", RX, 12, 284, 30, "GER_region_game_selected_name"),
    frame_box("GER_region_game_photo_box", RX, 52, 320, 96, "GER_region_game_photo_label"),
    frame_box("GER_region_game_leader_box", RX, 164, 118, 28, "GER_region_game_leader_label"),
    frame_box("GER_region_game_portrait_box", RX, 200, 118, 168, "GER_region_game_portrait_label"),
    frame_box("GER_region_game_logo_box", RX2 + 11, 164, 168, 168, "GER_region_game_logo_label"),
    frame_box("GER_region_game_support_box", RX2, 344, 93, 30, "GER_region_game_support_label"),
    frame_box("GER_region_game_control_box", RX2 + 93, 344, 94, 30, "GER_region_game_control_label"),
    "# 支持度 / 控制度竖条（之后可换成 vertical progressbar）",
    frame_box("GER_region_game_support_bar", RX2 + 28, 386, 36, 490),
    frame_box("GER_region_game_control_bar", RX2 + 122, 386, 36, 490),
    frame_box("GER_region_game_policy_box", RX, 386, 118, 110, "GER_region_game_policy_label"),
    text_button("GER_region_game_policy_1_button", RX, 516, 118, 28, "GER_region_game_policy_1"),
    text_button("GER_region_game_policy_2_button", RX, 556, 118, 28, "GER_region_game_policy_2"),
    text_button("GER_region_game_policy_3_button", RX, 596, 118, 28, "GER_region_game_policy_3"),
])

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

        %(RIGHT)s

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
       "CW": CANVAS_W, "CH": CANVAS_H, "CW10": CANVAS_W - 20,
       "RIGHT": indent(RIGHT_PANEL, 8).lstrip()}

# ---------------------------------------------------------------- scripted_gui
props = ["%s = { frame = var:%s }" % (r["el_fill"], r["v_frame"]) for r in regions]
trig = ["# 区块：显示 = 已开放（GER_region_Rxx_open = 1）；隐藏时不画、不挡鼠标"]
for r in regions:
    trig.append("%s_visible = { check_variable = { %s = 1 } }" % (r["el_fill"], r["v_open"]))
    trig.append("%s_visible = { check_variable = { %s = 1 } }" % (r["el_btn"], r["v_open"]))
trig.append("# 割让盖板：显示 = GER_region_OV_xxx_shown = 1；盖板点击图只出提示，不写 click 效果")
for o in overlays:
    trig.append("%s_visible = { check_variable = { %s = 1 } }" % (o["el_fill"], o["v_shown"]))
    trig.append("%s_visible = { check_variable = { %s = 1 } }" % (o["el_btn"], o["v_shown"]))

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
                }
            }
        }
    }

    # 地区博弈主界面
    # 接口（全部存在本国变量里，没设过 = 开局状态）：
    #   GER_region_Rxx_open  = 1      区块已开放（显示精灵 + 点击条）
    #   GER_region_Rxx_state = 1..7   逻辑状态：1 斜线 2 中立 3 左 4 右 5 摇摆 6 特殊 7 备用
    #   GER_region_Rxx_frame          实际显示帧，由 GER_region_game_sync_frames 从 state 算出（摇摆暂显示帧 2）
    #   GER_region_OV_<id>_shown = 1  显示对应割让盖板
    #   GER_region_selected = 1..16   最后点击的区块（右上名称框显示它的名字）
    # 区块点击效果 / 选中（点击条帧 3）/ 悬浮文字：待定，之后再接
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

clicks = ["# 点击区块：记下选中的区块，右上名称框随之显示该区块名"]
for r in regions:
    clicks.append("%s_click = { set_variable = { GER_region_selected = %d } }" % (r["el_btn"], r["idx"]))

sl = ["# 由 %s 生成，不要手改。" % GEN_TAG,
      "# 右上名称框：按 GER_region_selected 显示区块名，没选时显示占位。",
      "defined_text = {",
      "    name = GER_region_selected_name"]
for r in regions:
    sl.append("    text = { trigger = { check_variable = { GER_region_selected = %d } } localization_key = %s }"
              % (r["idx"], r["name_key"]))
sl += ["    text = { localization_key = GER_region_game_selected_none }", "}"]
SCRIPTED_LOC = "\n".join(sl) + "\n"

# ---------------------------------------------------------------- scripted_effects
eff = ["# 由 %s 生成，不要手改。" % GEN_TAG, ""]
eff.append("# 把每个区块的逻辑状态 state 换算成显示帧 frame。")
eff.append("# 摇摆（state %d）暂时显示成帧 %d；以后启用黄色（帧 5）时，改脚本里的 SWING_DISPLAY_FRAME 再重跑。"
           % (SWING_STATE, SWING_DISPLAY_FRAME))
eff.append("GER_region_game_sync_frames = {")
for r in regions:
    if SWING_DISPLAY_FRAME:
        eff.append("    if = { limit = { check_variable = { %s = %d } } set_variable = { %s = %d } }"
                   % (r["v_state"], SWING_STATE, r["v_frame"], SWING_DISPLAY_FRAME))
        eff.append("    else = { set_variable = { %s = %s } }" % (r["v_frame"], r["v_state"]))
    else:
        eff.append("    set_variable = { %s = %s }" % (r["v_frame"], r["v_state"]))
eff.append("}")
eff.append("")
eff.append("# 隐藏全部割让盖板")
eff.append("GER_region_game_hide_all_overlays = {")
for o in overlays:
    eff.append("    clear_variable = %s" % o["v_shown"])
eff.append("}")
eff.append("")
eff.append("# 回到开局画面：全部区块隐藏、全部盖板隐藏")
eff.append("GER_region_game_reset_to_opening = {")
for r in regions:
    eff.append("    clear_variable = %s" % r["v_open"])
    eff.append("    clear_variable = %s" % r["v_state"])
    eff.append("    clear_variable = %s" % r["v_frame"])
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
D += dec("GER_region_test_reset", ["GER_region_game_reset_to_opening = yes",
                                   "clear_variable = GER_region_test_color_idx",
                                   "clear_variable = GER_region_test_next",
                                   "clear_variable = GER_region_test_ov_next"])
D += dec("GER_region_test_open_all", open_all(2))
D += dec("GER_region_test_checker", sum((["set_variable = { %s = 1 }" % r["v_open"],
                                          "set_variable = { %s = %d }" % (r["v_state"], checker[r["key"]])]
                                         for r in regions), []))
cyc = ["add_to_variable = { GER_region_test_color_idx = 1 }",
       "if = { limit = { check_variable = { GER_region_test_color_idx > %d } } set_variable = { GER_region_test_color_idx = 1 } }"
       % len(USED_FRAMES)]
for i, fr in enumerate(USED_FRAMES, 1):
    cyc.append("if = { limit = { check_variable = { GER_region_test_color_idx = %d } } set_variable = { GER_region_test_color = %d } }"
               % (i, fr))
D += dec("GER_region_test_cycle_color", cyc + open_all("GER_region_test_color"))
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
D += dec("GER_region_test_swing", open_all(SWING_STATE))
D += dec("GER_region_test_silesia_lost", open_all(2) + ["set_variable = { GER_region_R07_state = 1 }"])
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
       ' GER_region_game_photo_label: "历史照片或地图"',
       ' GER_region_game_leader_label: "主导人物"',
       ' GER_region_game_portrait_label: "照片"',
       ' GER_region_game_logo_label: "社民党logo"',
       ' GER_region_game_support_label: "支持度"',
       ' GER_region_game_control_label: "控制度"',
       ' GER_region_game_policy_label: "行动方针"',
       ' GER_region_game_policy_1: "方针一"',
       ' GER_region_game_policy_2: "方针二"',
       ' GER_region_game_policy_3: "方针三"',
       ]
loc += [' %s: "%s"' % (r["name_key"], r["name"]) for r in regions]
HAND = hand_written_keys()
tt_all = [("GER_region_locked_all_tt", "整个德国"),
          ("GER_region_alsace_lorraine_tt", "阿尔萨斯-洛林"),
          ("GER_region_bav_corner_tt", "巴伐利亚缺角")]
tt_all += [(r["tt"], r["name"]) for r in regions] + [(o["tt"], o["name"]) for o in overlays]
loc.append(" # 悬浮介绍（*_tt）不在这个文件里，全部在 %s" % HAND_TT_LOC)
# 手写文件里缺哪个 tt 键，就在文件末尾补一行【待定】占位；已有的行一律不碰。
_missing = [(k, n) for k, n in tt_all if k not in HAND]
if _missing:
    _p = os.path.join(MOD, *HAND_TT_LOC.split("/"))
    if not os.path.exists(_p):
        with open(_p, "w", encoding="utf-8-sig", newline="") as f:
            f.write("l_simp_chinese:\r\n")
    with open(_p, "rb") as f:
        _ends_nl = f.read().endswith(b"\n")
    with open(_p, "a", encoding="utf-8", newline="") as f:
        if not _ends_nl:
            f.write("\r\n")       # 最后一行没换行时先补换行，免得占位接到手写行末尾
        for k, n in _missing:
            f.write(' %s: "【待定】%s"\r\n' % (k, n))
    print("手写介绍文件补了 %d 条占位" % len(_missing))
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
      ' GER_region_test_cycle_color: "全部区块换下一种颜色"',
      ' GER_region_test_cycle_color_desc: "按 帧1 斜线 → 帧2 中立 → 帧3 红 → 帧4 蓝 → 帧6 绿 循环。上一次切到：帧[?GER_region_test_color]。"',
      ' GER_region_test_next_region: "逐个开放下一个区块（红）"',
      ' GER_region_test_next_region_desc: "每点一次多开放一个区块（帧 3），顺序：%s。已开放到第 [?GER_region_test_next] 个，16 个之后重来。"' % reg_order,
      ' GER_region_test_swing: "全部区块设为摇摆"',
      ' GER_region_test_swing_desc: "state = 5（摇摆）。目前应显示成帧 2 的中立色，而不是黄色。"',
      ' GER_region_test_silesia_lost: "西里西亚整块割走（帧 1）"',
      ' GER_region_test_silesia_lost_desc: "全部区块中立，只有西里西亚切到帧 1 斜线。"',
      ' GER_region_test_all_overlays: "显示全部区块和全部割让盖板"',
      ' GER_region_test_all_overlays_desc: "16 个区块 + 11 张盖板全部打开，检查叠放和性能。"',
      ' GER_region_test_denmark_1: "丹麦阶段一：石勒苏益格托管"',
      ' GER_region_test_denmark_1_desc: "只显示 SHL_trust_all 盖板。"',
      ' GER_region_test_denmark_2: "丹麦阶段二：北石勒苏益格归丹麦"',
      ' GER_region_test_denmark_2_desc: "隐藏 SHL_trust_all，显示 SHL_north_Denmark，同时开放汉堡-石荷区块（中立）露出中部。"',
      ' GER_region_test_next_overlay: "逐张显示下一张割让盖板"',
      ' GER_region_test_next_overlay_desc: "每次只显示一张盖板，顺序：%s。当前第 [?GER_region_test_ov_next] 张。"' % ov_order]
LOC_DEC = "\n".join(dl) + "\n"

# ---------------------------------------------------------------- 写文件
splice("interface/GER_region_game.gfx", GFX_TEMPLATE, {"sprites": "\n".join(gfx_lines)})
splice("interface/GER_region_game.gui", GUI_TEMPLATE, {"map_layers": GUI_MAP})
splice("common/scripted_guis/GER_region_game.txt", SGUI_TEMPLATE,
       {"properties": "\n".join(props), "triggers": "\n".join(trig), "effects": "\n".join(clicks)})
write("common/scripted_localisation/GER_region_game.txt", SCRIPTED_LOC)
write("common/scripted_effects/GER_region_game_effects.txt", EFFECTS)
write("common/decisions/GER_region_game_test.txt", DECISIONS)
write("common/decisions/categories/GER_region_game_test.txt", CATEGORY)
write("localisation/simp_chinese/gui/GER_region_game_l_simp_chinese.yml", LOC_GUI, bom=True, crlf=True)
write("localisation/simp_chinese/decision/GER_region_game_test_l_simp_chinese.yml", LOC_DEC, bom=True, crlf=True)
print("素材 %d 张 -> %s" % (len(sprites), GFX_DIR_REL))
print("相邻不同色配色：", checker)
