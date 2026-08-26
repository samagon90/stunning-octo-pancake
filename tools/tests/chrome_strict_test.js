// ЭМУЛЯЦИЯ ХРОМА: ellipse ВАЛИДИРУЕТ радиусы и БРОСАЕТ при отрицательных — как в реальном Chrome
class ChromeCtx {
  constructor(){ this.images=0; }
  save(){} restore(){} translate(){} scale(){} rotate(){} setTransform(){}
  beginPath(){} closePath(){} moveTo(){} lineTo(){} arcTo(){} quadraticCurveTo(){} bezierCurveTo(){}
  arc(x,y,r){ if (r<0) throw new Error('IndexSizeError: arc radius '+r); }
  ellipse(x,y,rx,ry){
    if (rx<0) throw new Error("IndexSizeError: Failed to execute 'ellipse': The "+(rx>ry?'major':'minor')+"-axis radius provided ("+rx+") is negative.");
    if (ry<0) throw new Error("IndexSizeError: ry negative");
  }
  rect(){} strokeRect(){} clearRect(){} fill(){} stroke(){} clip(){} setLineDash(){}
  drawImage(){ this.images++; }
  fillRect(){} fillText(){} strokeText(){}
  createLinearGradient(){ return {addColorStop(){}}; }
  createRadialGradient(){ return {addColorStop(){}}; }
  measureText(){ return {width:10}; }
  filter;
}
const rec = new ChromeCtx();
global.document = { readyState:'complete', createElement:()=>({style:{},appendChild(){},addEventListener(){},set textContent(v){},get textContent(){return ''},remove(){},select(){},onclick:null}), getElementById:()=>({getContext:()=>rec,style:{},addEventListener(){},getBoundingClientRect:()=>({left:0,top:0,width:1920,height:1080})}), body:{appendChild(){}} };
global.addEventListener = () => {};
global.window = { addEventListener(){}, __DM_ERRS:[] };
global.CanvasRenderingContext2D = { prototype: ChromeCtx.prototype };
global.navigator = { userAgent:'chrome-test' };
global.innerWidth = 1920; global.innerHeight = 1080;
global.requestAnimationFrame = () => {};
global.Image = class { set src(v){ this.complete=true; this.naturalWidth=300; this.naturalHeight=400; } };
global.localStorage = { getItem(){return null;}, setItem(){} };
const fs = require('fs');
let js = fs.readFileSync('/tmp/check.js','utf8').replace('"use strict";','');
const test = `
dmStartT = -1e12;
// меню: раньше работало и должно работать
drawMenu();
console.log('Меню (хром-строгий): без ошибок ✓');
// бой: раньше умирал на метках пола (радиус -6)
startBattle(1); autoMode=true;
let frames=0;
while (!battleOver && frames<7200){
  tick(1/60);
  drawBattle();   // КАЖДЫЙ кадр рисуем — как в браузере
  frames++;
}
console.log('Бой (каждый кадр с отрисовкой):', battleOver&&battleOver.win?'ПОБЕДА':'??', '| кадров:', frames, '| camX:', Math.round(camX), '| картинок за последний кадр:', rec.images);
console.log('Ошибок поймано:', (window.__DM_ERRS||[]).length, (window.__DM_ERRS||[]).slice(0,2).join(' | ')||'-');
drawMenu();
console.log('ИТОГ: отрисовка не падает ✓');
`;
eval(js + '\n' + test);
process.exit(0);
