const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..');
const txt=p=>fs.readFileSync(path.join(root,p),'utf8').replace(/^\ufeff/,'');
const tech=txt('common/technologies/infantry.txt');
const gfx=txt('interface/AOR_infantry_v41.gfx');
const loc=txt('localisation/simp_chinese/AOR_infantry_v41_l_simp_chinese.yml');
const eq=txt('common/units/equipment/infantry.txt');
const names=[...tech.matchAll(/^\taor_inf_([a-z0-9]+) = \{/gm)].map(x=>'aor_inf_'+x[1]);
const blocks={};for(let i=0;i<names.length;i++){let begin=tech.indexOf(`\t${names[i]} = {`),end=i+1<names.length?tech.indexOf(`\t${names[i+1]} = {`):tech.lastIndexOf('\n}');blocks[names[i]]=tech.slice(begin,end)}
const errors=[];
if(!fs.readFileSync(path.join(root,'localisation/simp_chinese/AOR_infantry_v41_l_simp_chinese.yml'),'utf8').startsWith('\ufeff'))errors.push('localization missing UTF-8 BOM');
for(const id of ['aor_s01a_equipment_bonus','aor_s02a_equipment_bonus','aor_bolt_equipment_1919','aor_bolt_equipment_1927','aor_bolt_equipment_1930'])if(!new RegExp(`^ ${id}:0 `,'m').test(loc))errors.push(`${id} localization`);
if(names.length!==46||new Set(names).size!==46)errors.push('node count');
const positions={};const edges=[];const incoming={};
for(const [id,b] of Object.entries(blocks)){
 const pos=b.match(/position = \{ x = (\d+) y = (\d+) \}/);if(!pos)errors.push(`${id} position`);else positions[id]=[+pos[1],+pos[2]];
 if(!new RegExp(`^ ${id}:0 `,'m').test(loc)||!new RegExp(`^ ${id}_desc:0 `,'m').test(loc))errors.push(`${id} localization`);
 if(!gfx.includes(`GFX_${id}_medium`))errors.push(`${id} icon`);
 if(/\t\tallow = \{ has_tech = aor_inf_/.test(b))errors.push(`${id} has redundant prerequisite tooltip`);
 for(const match of b.matchAll(/leads_to_tech = (aor_inf_[a-z0-9]+)/g)){const next=match[1];if(!blocks[next])errors.push(`${id} dangling path ${next}`);else{edges.push([id,next]);(incoming[next]??=[]).push(id);}}
 const equip=b.match(/enable_equipments = \{ ([^ }]+) \}/);if(equip&&!eq.includes(`\t${equip[1]} = {`))errors.push(`${id} missing equipment ${equip[1]}`);
}
for(const id of names){const count=(incoming[id]||[]).length;if(['aor_inf_r01','aor_inf_l00','aor_inf_u01','aor_inf_m01','aor_inf_e01','aor_inf_t01'].includes(id)?count!==0:count!==1)errors.push(`${id} incoming paths ${count}`);}
const support=txt('common/technologies/support.txt');
if(/\t\tallow = \{ has_tech = aor_inf_/.test(support))errors.push('support tree has redundant prerequisite tooltip');
for(const [parent,child] of [['f01','f02'],['n01','n02'],['n02','n03'],['mg1','mg2'],['mg2','mg3'],['mg1','mg_t'],['mg1','mg_o']]){
 const start=support.indexOf(`\taor_inf_${parent} = {`),next=support.indexOf('\n\taor_inf_',start+1),block=support.slice(start,next<0?support.length:next);
 if(start<0||!block.includes(`leads_to_tech = aor_inf_${child}`))errors.push(`support path ${parent} -> ${child}`);
}
const vanilla='E:\\SteamLibrary\\steamapps\\common\\Hearts of Iron IV';
for(const m of gfx.matchAll(/name = "GFX_(aor_inf_[a-z0-9]+)_medium" texturefile = "([^"]+)"/g))if(blocks[m[1]]&&!fs.existsSync(path.join(root,m[2]))&&!fs.existsSync(path.join(vanilla,m[2])))errors.push(`${m[1]} missing texture`);
const sum={};for(const b of Object.values(blocks)){const p=b.match(/^\t\tinfantry = \{ ([^}]+) \}/m);if(!p)continue;for(const m of p[1].matchAll(/([a-z_]+) = (-?[\d.]+)/g))sum[m[1]]=(sum[m[1]]||0)+(+m[2]);}
for(const [k,v] of Object.entries({soft_attack:.23,defense:.19,breakthrough:.23,max_strength:.05,supply_consumption:-.08,max_organisation:2}))if(Math.abs((sum[k]||0)-v)>1e-8)errors.push(`ordinary infantry ${k} = ${sum[k]} expected ${v}`);
const gui=txt('interface/countrytechtreeview.gui');
if(!/name = "countrytechtreeview"\s+position = \{ x=-3 y=78 \}/.test(gui))errors.push('technology view height differs from focus view');
if(!/name = "folder_tabs"\s+position = \{ x=0 y=0 \}/.test(gui))errors.push('technology category tabs vertical position');
if(!/name = "infantry_folder"\s+position = \{ x=0 y=47 \}\s+size = \{ width = 100%% height = 100%% \}\s+margin = \{ top = 13 left = 13 bottom = 24 right = 25\}/.test(gui))errors.push('infantry scrollbar right margin');
if((gui.match(/quadTextureSprite ="GFX_tiled_bg"/g)||[]).length!==12||(gui.match(/quadTextureSprite ="GFX_tiled_focus_bg"/g)||[]).length!==12)errors.push('focus-style folder backgrounds');
if(gui.includes('GFX_tiled_window_2b_border')||/spriteType = "GFX_(?:(?:infantry|support|artillery|naval|air|industry|engineering)_techtree_bg|armortech_bg)"/.test(gui))errors.push('old technology background remains');
for(const id of ['aor_inf_r01','aor_inf_l00','aor_inf_u01','aor_inf_m01','aor_inf_e01','aor_inf_t01'])if(!gui.includes(`name = "${id}_tree"`))errors.push(`${id} missing grid`);
for(const id of ['infantry_at_tree','paratroopers_tree'])if(gui.includes(`name = "${id}"`))errors.push(`${id} still visible`);
const legacy=txt('common/technologies/AOR_legacy_infantry_aux.txt');
for(const id of ['infantry_at','infantry_at2','infantry_at3','infantry_at4','paratroopers','paratroopers2','paratroopers3']){
 const re=new RegExp(`\\b${id} = \\{ allow = \\{ always = no \\} research_cost = 1 start_year = \\d+ \\}`);
 if(!re.test(legacy))errors.push(`${id} compatibility stub missing or active`);
}
const retired=legacy.split('\tbicycle_infantry = {')[0];
if(/folder\s*=|enable_subunits\s*=|enable_equipments\s*=|\b(?:soft_attack|hard_attack|defense|breakthrough)\s*=/.test(retired))errors.push('legacy compatibility tech has position or bonus');
const col=id=>positions[id]?.[1];
if(col('aor_inf_r01')!==(col('aor_inf_r02')+col('aor_inf_s01'))/2)errors.push('1900 rifle branch not centered');
for(const [small,big] of [['s01a','s01'],['s02a','s02']])if(col('aor_inf_'+small)!==col('aor_inf_'+big))errors.push(`${small} not centered`);
if(!(col('aor_inf_u07')===col('aor_inf_u04')-1&&col('aor_inf_u06')===col('aor_inf_u04')+1))errors.push('climate branches not compact');
const frames=[['tiled_research_bg',100,760],['tiled_research_bg_2',900,530],['tiled_research_bg_3',1460,500]];
for(const [name,x,w] of frames){const re=new RegExp(`name = "${name}"\\s+position = \\{ x\\s*=\\s*${x}\\s+y\\s*=\\s*105\\s*\\}\\s+size = \\{ width = ${w} height = 1200 \\}`);if(!re.test(gui))errors.push(`${name} frame bounds`)}
if(gui.includes('name = "aor_infantry_v41_right_bg"'))errors.push('extra fourth frame');
if(!/name = "aor_inf_l00_tree" position = \{ x = 245 y = 160 \}/.test(gui))errors.push('squad tree grid offset');
const customArtDir=path.join(root,'gfx/interface/technologies/aor_infantry');
const customArt=fs.readdirSync(customArtDir).filter(x=>x.endsWith('.png'));
if(customArt.length!==46)errors.push(`custom artwork count ${customArt.length}`);
for(const file of customArt){const id=file.replace(/\.png$/,'');if(!blocks[id])errors.push(`${file} has no first-page node`);if(!gfx.includes(`name = "GFX_${id}_medium" texturefile = "gfx/interface/technologies/aor_infantry/${file}"`))errors.push(`${file} sprite mapping`);const png=fs.readFileSync(path.join(customArtDir,file));if(png.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')errors.push(`${file} PNG signature`);const [w,h]=[png.readUInt32BE(16),png.readUInt32BE(20)];const expected=/enable_equipments/.test(blocks[id])?[98,54]:[64,64];if(w!==expected[0]||h!==expected[1])errors.push(`${file} size ${w}x${h}`);}
if(!gfx.includes('name = "GFX_aor_inf_l04_medium" texturefile = "gfx/interface/technologies/aor_infantry/aor_inf_l04.png"'))errors.push('missing 1930 squad icon');
const geometry=[];for(const [id,[r,c]] of Object.entries(positions)){const big=/enable_equipments/.test(blocks[id]);const squad=/^aor_inf_(?:l|g)/.test(id);geometry.push({id,x:(squad?245:210)+c*70,y:160+r*67,w:big?183:72,h:big?84:72});}
let overlaps=[];for(let i=0;i<geometry.length;i++)for(let j=i+1;j<geometry.length;j++){let a=geometry[i],b=geometry[j];if(a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h)overlaps.push([a.id,b.id])}
if(overlaps.length)errors.push(`overlaps ${JSON.stringify(overlaps)}`);
const geo=Object.fromEntries(geometry.map(x=>[x.id,x]));
function segmentHitsBox(a,b,r){let x1=a.x+a.w/2,y1=a.y+a.h/2,x2=b.x+b.w/2,y2=b.y+b.h/2,t0=0,t1=1;for(const [p,q] of [[-(x2-x1),x1-r.x],[x2-x1,r.x+r.w-x1],[-(y2-y1),y1-r.y],[y2-y1,r.y+r.h-y1]]){if(p===0){if(q<0)return false;continue}let t=q/p;if(p<0)t0=Math.max(t0,t);else t1=Math.min(t1,t);if(t0>t1)return false}return true}
const crossings=[];for(const [from,to] of edges){for(const r of geometry){if(r.id===from||r.id===to)continue;if(segmentHitsBox(geo[from],geo[to],r))crossings.push([from,to,r.id])}}
if(crossings.length)errors.push(`straight line crossings ${JSON.stringify(crossings)}`);
const countryDir=path.join(root,'history','countries');let missing=[];
for(const file of fs.readdirSync(countryDir)){
 const p=path.join(countryDir,file);if(!file.endsWith('.txt')||!fs.statSync(p).isFile())continue;
 const s=fs.readFileSync(p,'utf8');const granted=new Set([...s.matchAll(/aor_inf_[a-z0-9]+ = 1/g)].map(x=>x[0].split(' = ')[0]));
 for(const id of granted){if(!blocks[id])continue;for(const r of incoming[id]||[])if(!granted.has(r))missing.push([file,id,r]);}
}
console.log(JSON.stringify({nodes:names.length,edges:edges.length,overlaps:overlaps.length,straightLineCrossings:crossings.length,ordinaryInfantryTotals:sum,missingCountryPrerequisiteCount:missing.length,missingByPrerequisite:Object.fromEntries([...new Set(missing.map(x=>x[2]))].map(x=>[x,missing.filter(y=>y[2]===x).length])),missingCountryPrerequisites:missing.slice(0,8),errors},null,2));
if(errors.length)process.exitCode=1;
