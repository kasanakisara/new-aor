// One baked full-scene flipbook. Requires playwright; OUTPUT directory is argv[2].
const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
const out=path.resolve(process.argv[2]);fs.mkdirSync(out,{recursive:true});
const html=fs.readFileSync(path.join(__dirname,'idle_clockwork_source.html'),'utf8');
const js=html.match(/<script>([\s\S]*?)<\/script>/)[1];
let helpers=js.slice(js.indexOf('const TAU='),js.indexOf('function draw(t)'));
helpers=helpers.replace('const g=ctx.createLinearGradient(x-r,y-r,x+r,y+r);','const m=ctx.getTransform(),a=-Math.atan2(m.b,m.a),dx=r*(Math.cos(a)-Math.sin(a)),dy=r*(Math.sin(a)+Math.cos(a)); const g=ctx.createLinearGradient(x-dx,y-dy,x+dx,y+dy);');
let draw=js.slice(js.indexOf('function draw(t)'),js.indexOf('function renderControls'));
// Plain panel: no perimeter screws, arch lines, engraved scanlines, scale or vignette.
draw=draw.replace(/const back=[\s\S]*?\/\/ Shadow train\./,"ctx.save();ctx.beginPath();ctx.rect(0,0,320,731);ctx.clip();\n// Shadow train.");
draw=draw.replace(/ctx.beginPath\(\);ctx.arc\(160,397,277,[\s\S]*?ctx.restore\(\);\n}/,'ctx.restore();\n}');
// Harmonise gear symmetries to one 15.2-second loop; pendulum remains 3.8 seconds.
// Minor tooth-count adjustments permit exact periodic closure with the retained spokes.
draw=draw.replace('gear(249,113,28,-t*.17,5,0);gear(53,460,34,t*.12,5,0);',
 'gear(249,113,30,-t*(TAU*2/5/15.2),5,0);gear(53,460,35,t*(TAU/5/15.2),5,0);');
draw=draw.replace('gear(100,180,60,t*.075,6);','gear(100,180,60,t*(TAU/6/15.2),6);');
draw=draw.replace('gear(235,245,40,-t*.1125+.039,5);','gear(235,245,40,-t*(TAU/5/15.2)+.039,5);');
draw=draw.replace('gear(113,369,76,t*.059210526+.025,6);','gear(113,369,78,t*(TAU/6/15.2)+.025,6);');
const config={width:320,height:731,cellHeight:732,columns:24,rows:10,frames:240,period:15.2,pendulum_period:3.8};
(async()=>{const browser=await chromium.launch({executablePath:process.env.AOR_BROWSER||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});try{
const page=await browser.newPage();
await page.evaluate(({helpers,draw,config})=>{
const c=document.createElement('canvas');c.width=640;c.height=1462;const ctx=c.getContext('2d');const paint=new Function('ctx','t',helpers+draw+'draw(t);');
const atlas=document.createElement('canvas');atlas.width=config.width*config.columns;atlas.height=config.cellHeight*config.rows;const g=atlas.getContext('2d');
for(let i=0;i<config.frames;i++){paint(ctx,i*config.period/config.frames);const x=(i%config.columns)*320,y=Math.floor(i/config.columns)*732;g.drawImage(c,0,0,640,1462,x,y,320,731);g.drawImage(c,0,1460,640,2,x,y+731,320,1);}
paint(ctx,0);const first=ctx.getImageData(0,0,640,1462).data;paint(ctx,config.period);const end=ctx.getImageData(0,0,640,1462).data;let error=0;for(let i=0;i<first.length;i++)error+=Math.abs(first[i]-end[i]);window.loopError=error/first.length;if(window.loopError>.2)throw Error('Loop seam '+window.loopError);
window.atlas=atlas;window.singlePaint=paint;window.singleCtx=ctx;window.singleCanvas=c;
},{helpers,draw,config});
const data=await page.evaluate(()=>({png:window.atlas.toDataURL('image/png').split(',')[1],error:window.loopError}));
fs.writeFileSync(path.join(out,'full_scene.png'),Buffer.from(data.png,'base64'));
config.loop_mean_error=data.error;fs.writeFileSync(path.join(out,'full_scene.json'),JSON.stringify(config,null,2));
// Exact rendered source is retained for frame and loop QA.
fs.writeFileSync(path.join(out,'render_source.js'),helpers+draw);
console.log(JSON.stringify(config));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
