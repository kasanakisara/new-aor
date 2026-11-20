"""Install the one-control full-scene atlas; previous layered renderer is disconnected."""
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
import sys,re,json,hashlib
MOD=Path(__file__).resolve().parents[2]
BUILD=Path(sys.argv[1]).resolve()
assets=MOD/'gfx/interface/GER_region_game/idle_clockwork'
source=Image.open(BUILD/'full_scene.png').convert('RGBA')
assert source.size==(7680,7320)
print('Encoding single atlas...',flush=True)
source.save(assets/'full_scene.dds',format='DDS',pixel_format='DXT5')
print('DDS written',flush=True)
check=Image.open(assets/'full_scene.dds').convert('RGBA')
assert check.size==source.size
diff=ImageStat.Stat(ImageChops.difference(source,check)).mean
assert max(diff[:3])<5, diff
carrier=Image.new('RGBA',(320,731),(255,255,255,255))
carrier.save(assets/'full_scene_carrier.dds',format='DDS')
gfx='''# Single precomposited full-scene animation. 240 frames / 15.2 seconds.
spriteTypes = {
    spriteType = {
        name = "GFX_GER_region_idle_full_scene"
        texturefile = "gfx/interface/GER_region_game/idle_clockwork/full_scene_carrier.dds"
        effectFile = "gfx/FX/GER_region_idle_fullframe.lua"
        animation = {
            animationmaskfile = "gfx/interface/GER_region_game/idle_clockwork/full_scene_carrier.dds"
            animationtexturefile = "gfx/interface/GER_region_game/idle_clockwork/full_scene.dds"
            animationrotation = 0
            animationlooping = yes
            animationtime = 15.2
            animationdelay = 0
            animationblendmode = "add"
            animationtype = "scrolling"
            animationrotationoffset = { x = 0.0 y = 0.0 }
            animationtexturescale = { x = 1.0 y = 1.0 }
        }
        legacy_lazy_load = no
    }
}
'''
(MOD/'interface/GER_region_idle_clockwork.gfx').write_text(gfx,encoding='utf-8')
gui=MOD/'interface/GER_region_game.gui'
raw=gui.read_bytes(); text=raw.decode('utf-8-sig')
replacement='''        # BEGIN AOR_IDLE_CLOCKWORK (single complete frame animation)
        containerWindowType = {
            name = "GER_region_idle_clockwork"
            position = { x = 1281 y = 150 }
            size = { width = 320 height = 731 }
            iconType = {
                name = "GER_region_idle_full_scene"
                spriteType = "GFX_GER_region_idle_full_scene"
                position = { x = 0 y = 0 }
                alwaystransparent = yes
            }
        }
        # END AOR_IDLE_CLOCKWORK'''
text,count=re.subn(r'^[ \t]*# BEGIN AOR_IDLE_CLOCKWORK[^\n]*\n.*?^[ \t]*# END AOR_IDLE_CLOCKWORK',replacement,text,flags=re.S|re.M)
assert count==1
text=text.replace('\r\n','\n')
if b'\r\n' in raw:text=text.replace('\n','\r\n')
gui.write_bytes((b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+text.encode('utf-8'))
check.crop((0,0,320,731)).save(BUILD/'installed_preview.png')
frames=[]
for i in range(0,240,2):
    x=(i%24)*320;y=(i//24)*732
    frames.append(check.crop((x,y,x+320,y+731)).convert('RGB').resize((240,548)))
frames[0].save(BUILD/'installed_preview.gif',save_all=True,append_images=frames[1:],duration=127,loop=0)
report={'single_animation_control':True,'baked_frames':240,'period_seconds':15.2,'pendulum_period_seconds':3.8,'atlas_size':list(check.size),'dds_mean_rgb_error':diff[:3],'removed':['perimeter screws','side rails','arch lines','bottom scale','vignette','outer frame'],'in_game_test':False}
(BUILD/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report),flush=True)
