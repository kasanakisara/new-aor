const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const source = 'C:\\Users\\DONG\\Desktop\\新建文件夹 (4)';
const target = path.join(root, 'gfx', 'interface', 'technologies', 'aor_infantry');
const gfxFile = path.join(root, 'interface', 'AOR_infantry_v41.gfx');

// The filename after the colon is the original exported PNG on the desktop.
const art = {
  r01: '1900 基础栓动.png',
  r02: '1919 大战制式步枪.png',
  r03: '1921 战后改良步枪.png',
  r04: '1924 制式短步枪.png',
  r06: '1927 改良制式短步枪.png',
  r07: '1930 标准化制式步枪.png',
  b01: '刺刀与背带配套.png',
  w01: '枪械防尘与保养.png',
  r04a: '机械瞄具改良.png',
  r05: '枪托与护木改良.png',
  r08: '枪械零件互换.png',
  s01: '1919 早期自装填步枪.png',
  s01a: '1921 自装填机构改良.png',
  s02: '1924 改良试验型.png',
  s02a: '自装填步枪勤务改良.png',
  s03: '1930 自装填定型.png',
  l00: '1900步兵随伴武器.png',
  l01: '1919大战班用武器.png',
  l05: '班用武器·1921 主线.png',
  l03: '1924年的 轻机枪勤务改良.png',
  l06: '班用武器·1927 主线.png',
  l04: '1930版用火力整合.png',
  g01: '班用武器·1919 右支.png',
  g06: '班用武器·1921 右支.png',
  g05: '班用武器·1924 右支.png',
  g03: '班用武器·1927 右支.png',
  g07: '班用武器·1930 右支.png',
  u01: '1900野战服装.png',
  u02: '钢盔.png',
  u04: '防护装具改良.png',
  u07: '热区服装.png',
  u06: '寒区.png',
  u05: '行军装备整合.png',
  u08: '伪装罩衣.png',
  m01: '海军陆战队一级.png',
  m02: '海军陆战队二级.png',
  m04: '海军陆战队三级.png',
  m03: '海军陆战队四级.png',
  e01: '突击部队一级.png',
  e02: '突击部队二级.png',
  e03: '突击部队三级.png',
  b02: '突击部队四级.png',
  t01: '山地步兵一级.png',
  t02: '山地二级.png',
  t04: '山地三级.png',
  t03: '山地四级.png',
};

const files = fs.readdirSync(source).filter(name => name.toLowerCase().endsWith('.png'));
const mapped = Object.values(art);
if (mapped.length !== 46 || new Set(mapped).size !== 46) throw new Error('Expected 46 distinct art mappings');
const unassigned = files.filter(name => !mapped.includes(name));
const missing = mapped.filter(name => !files.includes(name));
if (unassigned.length || missing.length) throw new Error(JSON.stringify({ unassigned, missing }));

let gfx = fs.readFileSync(gfxFile, 'utf8');
for (const id of Object.keys(art)) {
  const sprite = `GFX_aor_inf_${id}_medium`;
  const re = new RegExp(`(name = "${sprite}" texturefile = ")[^"]+(" \\})`);
  if (!re.test(gfx)) throw new Error(`Missing sprite declaration: ${sprite}`);
  gfx = gfx.replace(re, `$1gfx/interface/technologies/aor_infantry/aor_inf_${id}.png$2`);
}

fs.mkdirSync(target, { recursive: true });
for (const [id, file] of Object.entries(art)) {
  fs.copyFileSync(path.join(source, file), path.join(target, `aor_inf_${id}.png`));
}
fs.writeFileSync(gfxFile, gfx, 'utf8');
console.log(`Installed and registered ${mapped.length} PNGs.`);
