"""Convert the accepted canvas render to native HOI4 sprites and install scoped GUI hooks.
Usage: python install_idle_clockwork.py PATH_TO_BUILD_DIR
The hooks intentionally live outside the map generator's GENERATED sections.
"""
from pathlib import Path
import json, sys, hashlib
from PIL import Image

MOD = Path(__file__).resolve().parents[2]
BUILD = Path(sys.argv[1]).resolve()
layers = json.loads((BUILD / 'manifest.json').read_text(encoding='utf-8'))
assets = MOD / 'gfx/interface/GER_region_game/idle_clockwork'
assets.mkdir(parents=True, exist_ok=True)
gfx = ['# Accepted 2D clockwork, 1x speed. Native real-time animation; no game ticks/events.', 'spriteTypes = {']
icons = []
for layer in layers:
    name = layer['name']
    x, y, w, h = layer['rect']
    count = layer['frames']
    source = Image.open(BUILD / (name + '.png')).convert('RGBA')
    assert source.size == (w * count, h)
    assert w * count <= 8192 and h <= 8192
    target = assets / (name + '.dds')
    # Uncompressed RGBA preserves fine etched lines and avoids BC3 halos on alpha edges.
    unchanged = False
    if target.exists():
        with Image.open(target) as previous:
            unchanged = previous.size == source.size and previous.mode == 'RGBA' and previous.tobytes() == source.tobytes()
    if not unchanged:
        source.save(target, format='DDS')
    with Image.open(target) as check:
        assert check.size == source.size and check.mode == 'RGBA'
        assert check.tobytes() == source.tobytes()
    kind = 'frameAnimatedSpriteType' if count > 1 else 'spriteType'
    gfx += [f'    {kind} = {{', f'        name = "GFX_GER_region_idle_{name}"',
            f'        texturefile = "gfx/interface/GER_region_game/idle_clockwork/{name}.dds"']
    if count > 1:
        gfx += [f'        noOfFrames = {count}', f'        animation_rate_fps = {count / layer["period"]:.9f}',
                '        looping = yes', '        play_on_show = yes', '        pause_on_loop = 0.0',
                '        alwaystransparent = yes', '        effectFile = "gfx/FX/buttonstate_blendframes.lua"']
    gfx += ['    }']
    icons += ['            iconType = {', f'                name = "GER_region_idle_{name}"',
              f'                spriteType = "GFX_GER_region_idle_{name}"',
              f'                position = {{ x = {x} y = {y} }}',
              '                alwaystransparent = yes', '            }']
gfx += ['}', '']
(MOD / 'interface/GER_region_idle_clockwork.gfx').write_text('\n'.join(gfx), encoding='utf-8')

gui_hook = '\n'.join(['', '        # BEGIN AOR_IDLE_CLOCKWORK (hand-maintained, outside generated panel)',
    '        containerWindowType = {', '            name = "GER_region_idle_clockwork"',
    '            position = { x = 1281 y = 150 }', '            size = { width = 320 height = 731 }',
    *icons, '        }', '        # END AOR_IDLE_CLOCKWORK', ''])
trigger_hook = '\n'.join([''] + [
    '            # BEGIN AOR_IDLE_CLOCKWORK',
    '            # 待机时钟（盖在决议框上）：地图全开之前显示；巴伐利亚危机进行中（右侧是巴伐利亚决议）隐藏，危机结束后重新显示。',
    '            # 容器和里面的图标各写一条，条件相同。',
    '            GER_region_idle_clockwork_visible = {',
    '                NOT = {',
    '                    OR = {',
    '                        check_variable = { GER_region_panel_list^num > 0 }',
    '                        has_country_flag = GER_region_map_opened',
    '                        has_country_flag = GER_region_bavaria_phase',
    '                    }',
    '                }',
    '            }',
    '            GER_region_idle_full_scene_visible = {',
    '                NOT = {',
    '                    OR = {',
    '                        check_variable = { GER_region_panel_list^num > 0 }',
    '                        has_country_flag = GER_region_map_opened',
    '                        has_country_flag = GER_region_bavaria_phase',
    '                    }',
    '                }',
    '            }',
    '            # END AOR_IDLE_CLOCKWORK',
    ''])

def hook(relative, anchor, addition):
    p = MOD / relative
    original = p.read_bytes()
    text = original.decode('utf-8-sig')
    if '# BEGIN AOR_IDLE_CLOCKWORK' in text:
        import re
        text = re.sub(r'\n[ \t]*# BEGIN AOR_IDLE_CLOCKWORK[^\n]*\n.*?^[ \t]*# END AOR_IDLE_CLOCKWORK\r?\n', '', text, flags=re.S|re.M)
    assert text.count(anchor) == 1
    text = text.replace(anchor, anchor + addition)
    # Preserve original BOM and newline convention.
    text = text.replace('\r\n', '\n')
    if b'\r\n' in original:
        text = text.replace('\n', '\r\n')
    p.write_bytes((b'\xef\xbb\xbf' if original.startswith(b'\xef\xbb\xbf') else b'') + text.encode('utf-8'))

hook('interface/GER_region_game.gui', '# <<< GENERATED: right_panel', gui_hook)
hook('common/scripted_guis/GER_region_game.txt', '# <<< GENERATED: triggers', trigger_hook)

# Reconstruct a frame from the actual installed DDS files for visual verification.
preview = Image.new('RGBA', (320, 731))
for layer in layers:
    x,y,w,h = layer['rect']
    im = Image.open(assets / (layer['name'] + '.dds')).convert('RGBA').crop((0,0,w,h))
    preview.alpha_composite(im, (x,y))
preview.save(BUILD / 'installed_preview.png')
manifest = {str(p.relative_to(MOD)): {'bytes':p.stat().st_size, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in [*assets.glob('*.dds'), MOD/'interface/GER_region_idle_clockwork.gfx',
                      MOD/'interface/GER_region_game.gui',MOD/'common/scripted_guis/GER_region_game.txt']}
(BUILD / 'installed_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(f'Installed {len(layers)} layers, {sum(p.stat().st_size for p in assets.glob("*.dds"))/1048576:.2f} MiB textures')
