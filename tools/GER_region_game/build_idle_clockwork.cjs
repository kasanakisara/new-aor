// Export the accepted 2D canvas at 1x speed; no browser runtime is needed in HOI4.
// NODE_PATH must include playwright. Usage: node build_idle_clockwork.cjs OUTPUT_DIR
const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
const out=path.resolve(process.argv[2]);fs.mkdirSync(out,{recursive:true});
const source=fs.readFileSync(path.join(__dirname,'idle_clockwork_source.html'),'utf8');
const js=source.match(/<script>([\s\S]*?)<\/script>/)[1];
let helpers=js.slice(js.indexOf('const TAU='),js.indexOf('function draw(t)'));
// Keep illumination fixed in panel space so rotationally symmetric loops join cleanly.
helpers=helpers.replace('const g=ctx.createLinearGradient(x-r,y-r,x+r,y+r);',
    'const m=ctx.getTransform(),a=-Math.atan2(m.b,m.a),dx=r*(Math.cos(a)-Math.sin(a)),dy=r*(Math.sin(a)+Math.cos(a)); const g=ctx.createLinearGradient(x-dx,y-dy,x+dx,y+dy);');
helpers=helpers.replace('function gear(x,y,n,angle,spokes,dim=1)',"function gear(x,y,n,angle,spokes,dim=1,part='full')");
helpers=helpers.replace("ctx.shadowColor='#070907';","if(part!=='spokes'){ctx.shadowColor='#070907';");
helpers=helpers.replace('for(let i=0;i<spokes;i++) {',"} if(part!=='rim'){ for(let i=0;i<spokes;i++) {");
helpers=helpers.replace(/ctx\.restore\(\);\s*}\s*$/, "} ctx.restore();\n}\n");
const draw=js.slice(js.indexOf('function draw(t)'),js.indexOf('function renderControls'));
const base=draw.slice(draw.indexOf("ctx.fillStyle='#181c18'"),draw.indexOf('// Shadow train.'))+'ctx.restore();';
const pend=draw.slice(draw.indexOf('const swing='),draw.indexOf('// Meshed pitch circles:'));
const front='ctx.save();ctx.beginPath();ctx.rect(9,9,302,713);ctx.clip();'+draw.slice(draw.indexOf('// Static bearing bridges'),draw.lastIndexOf('\n}'));
const layers=[
{name:'base',rect:[0,0,320,731],frames:1,period:0,code:base},
{name:'rear_upper',rect:[196,60,108,108],frames:64,period:Math.PI*2/.17,code:'gear(249,113,28,-t*.17,5,0);'},
{name:'rear_lower',rect:[0,396,120,128],frames:64,period:Math.PI*2/.12,code:'gear(53,460,34,t*.12,5,0);'},
{name:'pendulum',rect:[92,392,136,284],frames:60,period:3.8,code:pend},
{name:'gear_upper',rect:[0,80,204,208],frames:40,period:(Math.PI*2/6)/.075,code:'gear(100,180,60,t*.075,6);'},
{name:'gear_right',rect:[164,172,152,152],frames:48,period:(Math.PI*2/5)/.1125,code:'gear(235,245,40,-t*.1125+.039,5);'},
{name:'gear_lower_rim',rect:[0,244,244,252],frames:24,period:(Math.PI*2/76)/.059210526,code:"gear(113,369,76,t*.059210526+.025,6,1,'rim');"},
{name:'gear_lower_spokes',rect:[0,244,244,252],frames:32,period:(Math.PI*2/6)/.059210526,code:"gear(113,369,76,t*.059210526+.025,6,1,'spokes');"},
{name:'foreground',rect:[0,0,320,731],frames:1,period:0,code:front}
];
(async()=>{
const browser=await chromium.launch({executablePath:process.env.AOR_BROWSER||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
try {const page=await browser.newPage();
for(const layer of layers){
const png=await page.evaluate(({helpers,layer})=>{
const c=document.createElement('canvas');c.width=640;c.height=1462;const ctx=c.getContext('2d');
const paint=new Function('ctx','t',helpers+'\n'+layer.code);
const [x,y,w,h]=layer.rect,strip=document.createElement('canvas');strip.width=w*layer.frames;strip.height=h;
const g=strip.getContext('2d');
function render(t){ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,640,1462);ctx.setTransform(2,0,0,2,0,0);ctx.save();ctx.beginPath();ctx.rect(9,9,302,713);ctx.clip();if(layer.name==='base'){ctx.restore();ctx.save();}paint(ctx,t);ctx.restore();}
for(let i=0;i<layer.frames;i++){render(i*layer.period/layer.frames);g.drawImage(c,x*2,y*2,w*2,h*2,i*w,0,w,h);}
if(layer.frames>1){render(0);const first=ctx.getImageData(0,0,640,1462).data;render(layer.period);const last=ctx.getImageData(0,0,640,1462).data;let total=0;for(let j=0;j<first.length;j++)total+=Math.abs(first[j]-last[j]);if(total/first.length>.35)throw Error(layer.name+' loop seam: '+total/first.length);}
return strip.toDataURL('image/png').split(',')[1];
},{helpers,layer});
fs.writeFileSync(path.join(out,layer.name+'.png'),Buffer.from(png,'base64'));console.log(layer.name+' '+layer.frames+' frames');
}
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(layers.map(({code,...rest})=>rest),null,2));
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
