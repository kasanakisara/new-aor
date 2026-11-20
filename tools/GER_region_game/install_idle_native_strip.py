"""Replace the unsupported custom-atlas player with a native, whole-frame strip.
Uses 32 full scenes at 256x585, displayed at scale 1.25. No custom shader.
Usage: python -X utf8 install_idle_native_strip.py ATLAS_PNG QA_DIRECTORY
"""
from pathlib import Path
from PIL import Image,ImageStat,ImageChops
import sys,re,json,hashlib
MOD=Path(__file__).resolve().parents[2]
src=Path(sys.argv[1]);qa=Path(sys.argv[2]);qa.mkdir(parents=True,exist_ok=True)
atlas=Image.open(src).convert('RGBA')
assert atlas.size==(7680,7320)
COUNT,W,H,PERIOD=32,256,585,15.2
assert W*COUNT <= 8192, 'HOI4 texture limit, not the GPU/D3D11 maximum'
strip=Image.new('RGBA',(W*COUNT,H))
def frame(i):
    i%=240;x=(i%24)*320;y=(i//24)*732
    return atlas.crop((x,y,x+320,y+731))
for i in range(COUNT):
    position=i*240/COUNT
    index=int(position)
    image=Image.blend(frame(index),frame(index+1),position-index)
    strip.paste(image.resize((W,H),Image.Resampling.LANCZOS),(i*W,0))
assets=MOD/'gfx/interface/GER_region_game/idle_clockwork'
dest=assets/'full_scene_native_32f.dds'
# RGBA avoids BC3 block alignment and compression issues in 585-pixel-high frames.
strip.save(dest,format='DDS')
decoded=Image.open(dest).convert('RGBA')
assert decoded.size==(8192,585) and decoded.tobytes()==strip.tobytes()
decoded.crop((0,0,W,H)).resize((320,731),Image.Resampling.LANCZOS).save(qa/'native_preview.png')
frames=[decoded.crop((i*W,0,(i+1)*W,H)).convert('RGB') for i in range(COUNT)]
frames[0].save(qa/'native_frames.gif',save_all=True,append_images=frames[1:],duration=[480 if i%2==0 else 470 for i in range(COUNT)],loop=0)
gfx='''# Native full-scene frame animation. No animation block, atlas sampler or custom shader.
spriteTypes = {
    frameAnimatedSpriteType = {
        name = "GFX_GER_region_idle_full_scene"
        texturefile = "gfx/interface/GER_region_game/idle_clockwork/full_scene_native_32f.dds"
        noOfFrames = 32
        animation_rate_fps = 2.105263158
        looping = yes
        play_on_show = yes
        pause_on_loop = 0.0
        alwaystransparent = yes
        effectFile = "gfx/FX/buttonstate_blendframes.lua"
    }
}
'''
(MOD/'interface/GER_region_idle_clockwork.gfx').write_text(gfx,encoding='utf-8')
gui=MOD/'interface/GER_region_game.gui';original=gui.read_bytes();text=original.decode('utf-8-sig')
pattern=r'(name = "GER_region_idle_full_scene"[\s\S]*?position = \{ x = 0 y = 0 \})(?:\s*scale = [\d.]+)?'
text,n=re.subn(pattern,r'\1\n                scale = 1.25',text)
assert n==1
text=text.replace('\r\n','\n')
if b'\r\n' in original:text=text.replace('\n','\r\n')
gui.write_bytes((b'\xef\xbb\xbf' if original.startswith(b'\xef\xbb\xbf') else b'')+text.encode())
report={'implementation':'native frameAnimatedSpriteType + original buttonstate_blendframes',
        'texture':str(dest),'size':[8192,585],'frames':COUNT,'period':PERIOD,'fps':COUNT/PERIOD,
        'display_scale':1.25,'dds_lossless':True,'one_whole_scene_per_frame':True,
        'custom_shader_dependency':False,'texture_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
        'in_game_visual_verification':False}
(qa/'native_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)
