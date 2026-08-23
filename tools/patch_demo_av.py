#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Апгрейд демо до «сайт-версии»: полноценный аудио-движок (3 темы музыки,
панорама, компрессор), босс-бар, лучи света, лепестки, искры, трещины,
глифы умений, рамки портретов, шаги марша, сохранение в localStorage."""
import io, sys

HTML = "/home/user/stunning-octo-pancake/prototype/index.html"
s = io.open(HTML, encoding="utf-8").read()
P = []

# ============ 1. ЗВУК: движок вместо писков ============
old_sfx = """// ---------- Звук ----------
let AC = null;
function audio(){ if(!AC){ try{ AC = new (window.AudioContext||window.webkitAudioContext)(); }catch(e){} } return AC; }
function beep(freq, dur, type, vol){
  const ac = audio(); if(!ac) return;
  const o = ac.createOscillator(), g = ac.createGain();
  o.type = type||'square'; o.frequency.value = freq;
  g.gain.setValueAtTime(vol||0.12, ac.currentTime);
  g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + dur);
  o.connect(g); g.connect(ac.destination); o.start(); o.stop(ac.currentTime + dur);
}
const SFX = {
  click(){ beep(880,.06); },
  whoosh(){ beep(300,.08,'sine',.07); beep(180,.1,'triangle',.1); },
  hit(){ beep(140,.1,'triangle',.15); },
  crit(){ beep(180,.12,'triangle',.18); beep(1320,.15,'sine',.08); },
  cast(){ beep(520,.18,'sine',.1); },
  heal(){ beep(523,.1,'sine',.1); setTimeout(()=>beep(784,.14,'sine',.1),90); },
  win(){ [523,659,784,1046].forEach((f,i)=>setTimeout(()=>beep(f,.16,'square',.1), i*130)); },
  lose(){ [392,330,262].forEach((f,i)=>setTimeout(()=>beep(f,.22,'sawtooth',.1), i*160)); },
  boss(){ beep(90,.5,'sawtooth',.2); beep(60,.6,'sawtooth',.15); },
  slam(){ beep(70,.3,'sawtooth',.25); beep(50,.4,'triangle',.3); }
};"""
new_sfx = """// ---------- Звук: движок (шины, панорама по миру, музыка-шедулер) ----------
let AC = null, MASTER=null, SFX_BUS=null, MUS_BUS=null, NOISE_BUF=null;
const AudioState = { music:.55, sfx:.9, theme:'menu' };
function audio(){
  if (AC){ if (AC.state==='suspended') AC.resume(); return AC; }
  try{ AC = new (window.AudioContext||window.webkitAudioContext)(); }catch(e){ return null; }
  const comp = AC.createDynamicsCompressor();
  comp.threshold.value=-18; comp.ratio.value=6; comp.attack.value=.004; comp.release.value=.18;
  MASTER = AC.createGain(); MASTER.gain.value=.9;
  SFX_BUS = AC.createGain(); SFX_BUS.gain.value=AudioState.sfx;
  MUS_BUS = AC.createGain(); MUS_BUS.gain.value=AudioState.music*.5;
  SFX_BUS.connect(MASTER); MUS_BUS.connect(MASTER); MASTER.connect(comp); comp.connect(AC.destination);
  NOISE_BUF = AC.createBuffer(1, AC.sampleRate*1.2, AC.sampleRate);
  const d = NOISE_BUF.getChannelData(0);
  for (let i=0;i<d.length;i++) d[i]=Math.random()*2-1;
  Music.start();
  return AC;
}
function panOf(x){ if (x==null) return 0; return Math.max(-1, Math.min(1,(x-(camX+VW/2))/(VW*.6)))*.7; }
function tone(o){ // {f,f2,dur,type,vol,x,delay}
  const ac=audio(); if(!ac) return;
  const t0=ac.currentTime+(o.delay||0);
  const osc=ac.createOscillator(), g=ac.createGain();
  osc.type=o.type||'sine'; osc.frequency.setValueAtTime(o.f,t0);
  if (o.f2) osc.frequency.exponentialRampToValueAtTime(Math.max(20,o.f2),t0+o.dur);
  g.gain.setValueAtTime(0,t0);
  g.gain.linearRampToValueAtTime(o.vol||.1,t0+.008);
  g.gain.exponentialRampToValueAtTime(.001,t0+o.dur);
  let n=osc;
  if (o.x!=null && ac.createStereoPanner){ const p=ac.createStereoPanner(); p.pan.value=panOf(o.x); osc.connect(p); n=p; }
  n.connect(g); g.connect(SFX_BUS);
  osc.start(t0); osc.stop(t0+o.dur+.05);
}
function noiz(o){ // {dur,vol,x,hp,lp,delay}
  const ac=audio(); if(!ac) return;
  const t0=ac.currentTime+(o.delay||0);
  const src=ac.createBufferSource(); src.buffer=NOISE_BUF; src.loop=true;
  const f=ac.createBiquadFilter(); f.type=o.hp?'highpass':'lowpass'; f.frequency.value=o.hp||o.lp||1200;
  const g=ac.createGain();
  g.gain.setValueAtTime(0,t0);
  g.gain.linearRampToValueAtTime(o.vol||.1,t0+.006);
  g.gain.exponentialRampToValueAtTime(.001,t0+o.dur);
  let n=src;
  if (o.x!=null && ac.createStereoPanner){ const p=ac.createStereoPanner(); p.pan.value=panOf(o.x); src.connect(p); n=p; }
  n.connect(f); f.connect(g); g.connect(SFX_BUS);
  src.start(t0); src.stop(t0+o.dur+.05);
}
const SFX = {
  click(){ tone({f:760,f2:980,dur:.06,type:'square',vol:.05}); },
  whoosh(x){ noiz({dur:.12,vol:.09,x:x,hp:900}); tone({f:320,f2:120,dur:.1,type:'sine',vol:.05,x:x}); },
  hit(x){ tone({f:150,f2:55,dur:.12,type:'triangle',vol:.2,x:x}); noiz({dur:.06,vol:.07,x:x,lp:2600}); },
  crit(x){ tone({f:180,f2:50,dur:.16,type:'triangle',vol:.24,x:x}); tone({f:1560,f2:2100,dur:.14,type:'sine',vol:.09,x:x,delay:.01}); noiz({dur:.1,vol:.09,x:x,hp:1400}); },
  cast(x){ tone({f:280,f2:880,dur:.2,type:'sawtooth',vol:.05,x:x}); tone({f:560,f2:1760,dur:.18,type:'sine',vol:.045,x:x,delay:.02}); },
  heal(x){ [523,659,784].forEach((f,i)=>tone({f,dur:.22,type:'sine',vol:.08,x:x,delay:i*.07})); },
  win(){ [523,659,784,1046,1318].forEach((f,i)=>{ tone({f,dur:.3,type:'triangle',vol:.12,delay:i*.12}); tone({f:f/2,dur:.3,type:'sine',vol:.06,delay:i*.12}); }); },
  lose(){ [392,330,262,196].forEach((f,i)=>tone({f,dur:.34,type:'sawtooth',vol:.07,delay:i*.17})); },
  boss(x){ tone({f:98,f2:40,dur:.7,type:'sawtooth',vol:.2,x:x}); tone({f:103,f2:44,dur:.7,type:'sawtooth',vol:.16,x:x}); noiz({dur:.7,vol:.09,x:x,lp:300}); },
  slam(x){ tone({f:60,f2:26,dur:.5,type:'sine',vol:.32,x:x}); noiz({dur:.35,vol:.14,x:x,lp:500}); },
  step(x,alt){ noiz({dur:.05,vol:.03,x:x,lp:alt?900:700}); }
};
// Музыка: 3 темы, процедурный шедулер с опережением
const Music = (()=>{
  const THEMES = {
    menu:  { bpm:74,  roots:[57,53,48,55], mode:[0,3,7,10], bass:.55, arp:.3,  drums:0 },
    battle:{ bpm:112, roots:[57,53,60,55], mode:[0,3,7,12], bass:1,   arp:.55, drums:.5 },
    boss:  { bpm:136, roots:[50,50,46,53], mode:[0,3,7,10], bass:1,   arp:.8,  drums:1, dark:1 }
  };
  const n2f = n => 440*Math.pow(2,(n-69)/12);
  let beat=0, nextT=0, timer=null;
  function mus(f,t0,dur,type,vol,lp){
    const ac=AC;
    const o=ac.createOscillator(), g=ac.createGain(), flt=ac.createBiquadFilter();
    o.type=type; o.frequency.value=f; o.detune.value=Math.random()*10-5;
    flt.type='lowpass'; flt.frequency.value=lp||900;
    g.gain.setValueAtTime(0,t0);
    g.gain.linearRampToValueAtTime(vol,t0+.25);
    g.gain.setValueAtTime(vol,t0+dur*.55);
    g.gain.linearRampToValueAtTime(0,t0+dur);
    o.connect(flt); flt.connect(g); g.connect(MUS_BUS);
    o.start(t0); o.stop(t0+dur+.1);
  }
  function drum(t0,f,dur,vol){
    const ac=AC, o=ac.createOscillator(), g=ac.createGain();
    o.type='sine'; o.frequency.setValueAtTime(f*2,t0); o.frequency.exponentialRampToValueAtTime(f*.6,t0+dur);
    g.gain.setValueAtTime(vol,t0); g.gain.exponentialRampToValueAtTime(.001,t0+dur);
    o.connect(g); g.connect(MUS_BUS); o.start(t0); o.stop(t0+dur+.05);
  }
  function hat(t0,vol){
    const ac=AC; if(!NOISE_BUF) return;
    const src=ac.createBufferSource(); src.buffer=NOISE_BUF;
    const f=ac.createBiquadFilter(); f.type='highpass'; f.frequency.value=6000;
    const g=ac.createGain();
    g.gain.setValueAtTime(vol,t0); g.gain.exponentialRampToValueAtTime(.001,t0+.05);
    src.connect(f); f.connect(g); g.connect(MUS_BUS); src.start(t0); src.stop(t0+.08);
  }
  function schedule(){
    const ac=AC; if(!ac) return;
    const th=THEMES[AudioState.theme]||THEMES.menu;
    const spb=60/th.bpm/2; // восьмые
    while (nextT < ac.currentTime + .4){
      const t0=nextT, b=beat, root=th.roots[Math.floor(b/8)%th.roots.length];
      if (th.bass && b%2===0) mus(n2f(root-12), t0, spb*1.8, 'triangle', .10*th.bass);
      if (th.bass>.9 && b%8===6) mus(n2f(root-12+(th.dark?1:0)), t0, spb*1.2, 'triangle', .08);
      if (b%8===0) th.mode.forEach(iv=>mus(n2f(root+iv), t0, spb*7.6, 'sawtooth', .026, 700));
      if (th.arp){
        const seq=[0,7,12,15,7,12,19,12];
        mus(n2f(root+12+seq[b%8]), t0, spb*.9, 'square', .02*th.arp, 2400);
      }
      if (th.drums>0){
        if (b%4===0) drum(t0, 52, .16, .11*th.drums);
        if (th.drums>.9 && b%4===2) drum(t0, 44, .12, .09*th.drums);
        if (b%2===1) hat(t0, .028*th.drums+.012);
      }
      beat++; nextT+=spb;
    }
  }
  return {
    start(){ if (timer||!AC) return; nextT=AC.currentTime+.1; timer=setInterval(schedule,120); },
    setTheme(name){ if (AudioState.theme!==name){ AudioState.theme=name; beat=0; if(AC) nextT=Math.max(nextT,AC.currentTime+.05); } },
    setMusicVol(v){ if(MUS_BUS) MUS_BUS.gain.value=v*.5; },
    setSfxVol(v){ if(SFX_BUS) SFX_BUS.gain.value=v; }
  };
})();"""
P.append((old_sfx, new_sfx))

# ============ 2. Сохранение (localStorage) ============
P.append((
"let unlocked = 1, rewards = null;",
"""let unlocked = 1, rewards = null;

// ---------- Сохранение сайта (localStorage) ----------
const SAVE_KEY = 'dm_save_v1';
try { const sv = JSON.parse(localStorage.getItem(SAVE_KEY)); if (sv){ unlocked = sv.unlocked||1; AudioState.music = sv.music!=null? sv.music : .55; AudioState.sfx = sv.sfx!=null? sv.sfx : .9; } } catch(e){}
function persist(){ try{ localStorage.setItem(SAVE_KEY, JSON.stringify({unlocked, music:AudioState.music, sfx:AudioState.sfx})); }catch(e){} }"""))

# ============ 3. Хелперы графики: панели, лепестки, лучи, искры, трещины ============
P.append((
"""function rrect(x,y,w,h,r,f,s){ ctx.beginPath(); ctx.roundRect(x,y,w,h,r); if(f){ctx.fillStyle=f;ctx.fill();} if(s){ctx.strokeStyle=s;ctx.lineWidth=3;ctx.stroke();} }""",
"""function rrect(x,y,w,h,r,f,s){ ctx.beginPath(); ctx.roundRect(x,y,w,h,r); if(f){ctx.fillStyle=f;ctx.fill();} if(s){ctx.strokeStyle=s;ctx.lineWidth=3;ctx.stroke();} }
function panelBG(x,y,w,h,r){
  const g=ctx.createLinearGradient(0,y,0,y+h);
  g.addColorStop(0,'rgba(22,30,55,0.93)'); g.addColorStop(1,'rgba(10,14,32,0.93)');
  ctx.beginPath(); ctx.roundRect(x,y,w,h,r); ctx.fillStyle=g; ctx.fill();
  ctx.strokeStyle='#2c3a66'; ctx.lineWidth=3; ctx.stroke();
}
// лепестки сна
let petals=[];
for (let i=0;i<16;i++) petals.push({ x:Math.random()*VW, y:Math.random()*VH,
  spd:20+Math.random()*26, ph:Math.random()*7, r:5+Math.random()*7,
  col: Math.random()<.5? 'rgba(255,170,200,' : 'rgba(150,190,255,' });
function drawPetals(){
  for (const p of petals){
    const a=.22+.18*Math.sin(Date.now()/600+p.ph);
    ctx.fillStyle=p.col+a+')';
    ctx.save(); ctx.translate(p.x,p.y); ctx.rotate(Math.sin(Date.now()/900+p.ph)*.8);
    ctx.beginPath(); ctx.ellipse(0,0,p.r,p.r*.55,0,0,7); ctx.fill(); ctx.restore();
  }
}
function drawRays(){
  ctx.save(); ctx.globalCompositeOperation='screen';
  const t=Date.now()/3000;
  for (let i=0;i<3;i++){
    const x=VW*(.25+.25*i)+Math.sin(t+i)*70;
    const g=ctx.createLinearGradient(x,0,x+140,VH);
    g.addColorStop(0,'rgba(150,175,255,0.05)'); g.addColorStop(1,'rgba(150,175,255,0)');
    ctx.fillStyle=g;
    ctx.beginPath(); ctx.moveTo(x-40,0); ctx.lineTo(x+90,0);
    ctx.lineTo(x+300,VH); ctx.lineTo(x-160,VH); ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}
function fxSparks(x,y,color,dir){
  for (let i=0;i<8;i++) effects.push({t:'p', x, y,
    vx:dir*(60+Math.random()*230), vy:-(30+Math.random()*190), life:.4, T:.4, color});
}
function fxCrack(x,y){
  const segs=[];
  for (let i=0;i<7;i++){
    const a=Math.random()*7, l=50+Math.random()*110;
    segs.push({dx:Math.cos(a)*l, dy:Math.sin(a)*l*.4, m:(Math.random()*30-15)});
  }
  effects.push({t:'crack', x, y, segs, life:1.6, T:1.6});
}"""))

# ============ 5. hurt: искры + звук с панорамой ============
P.append((
"""  t.hp-=d; t.hitT=.22;
  addFloat(t.x,t.y-t.r*2.2,Math.round(d),crit?'#ff9a3d':(t.team===0?'#ff5a5a':'#ffffff'),crit);
  if (crit){ shake(4,.12); freeze(.05); punch=1.045; SFX.crit(); } else SFX.hit();""",
"""  t.hp-=d; t.hitT=.22;
  fxSparks(t.x, t.y-t.r*.4, (EL[from.el]||EL.fire).c, Math.sign(t.x-from.x)||1);
  addFloat(t.x,t.y-t.r*2.2,Math.round(d),crit?'#ff9a3d':(t.team===0?'#ff5a5a':'#ffffff'),crit);
  if (crit){ shake(4,.12); freeze(.05); punch=1.045; SFX.crit(t.x); } else SFX.hit(t.x);"""))

# ============ 6. strike: вуш с координатой ============
P.append(("""  SFX.whoosh();""", """  SFX.whoosh(t.x);"""))

# ============ 7. castAbility: звуки + трещины на AoE ============
P.append((
"    fxHeal(w.x,w.y-20); SFX.heal();",
"    fxHeal(w.x,w.y-20); SFX.heal(w.x);"))
P.append((
"    addFloat(u.x,u.y-90,'★ '+ab.n,'#ffd76a'); SFX.heal();",
"    addFloat(u.x,u.y-90,'★ '+ab.n,'#ffd76a'); SFX.heal(u.x);"))
P.append((
"""    fxAoe(u.x,u.y,ab.r+60,EL[u.el].c);
    punch=1.05; addFloat(u.x,u.y-95,ab.n,EL[u.el].c); SFX.cast();""",
"""    fxAoe(u.x,u.y,ab.r+60,EL[u.el].c); fxCrack(u.x,u.y+30);
    punch=1.05; addFloat(u.x,u.y-95,ab.n,EL[u.el].c); SFX.cast(u.x);"""))
P.append((
"""    if (t){ fxProjectile(u,t,EL[u.el].c,true); hurt(t,u,ab.k,true); }
    addFloat(u.x,u.y-95,ab.n,EL[u.el].c); SFX.cast();""",
"""    if (t){ fxProjectile(u,t,EL[u.el].c,true); hurt(t,u,ab.k,true); }
    addFloat(u.x,u.y-95,ab.n,EL[u.el].c); SFX.cast(u.x);"""))

# ============ 8. босс: тема + слэм с трещинами ============
P.append((
"  if (tpl.boss && u.dropY===0){ /* босс приходит с неба ниже */ }",
"  if (tpl.boss) Music.setTheme('boss');"))
P.append((
"""            fxAoe(s.x,s.y+40,170,'#c07aff'); shake(13,.4); SFX.slam();""",
"""            fxAoe(s.x,s.y+40,170,'#c07aff'); fxCrack(s.x,s.y+40); shake(13,.4); SFX.slam(s.x);"""))

# ============ 9. шаги марша ============
P.append((
"""    if (stepT<=0) stepT=.16;""",
"""    if (stepT<=0){
      stepT=.16;
      const walker = team.find(h=>h.alive&&h.moving);
      if (walker) SFX.step(walker.x, Math.floor(Date.now()/160)%2===0);
    }"""))

# ============ 10. старт/конец боя: темы музыки + сейв ============
P.append((
"""  beginWave();
  scene='battle';
}""",
"""  beginWave();
  scene='battle';
  Music.setTheme('battle');
}"""))
P.append((
"""function endBattle(win){
  if (battleOver) return;""",
"""function endBattle(win){
  if (battleOver) return;
  Music.setTheme('menu');
  persist();"""))

# ============ 11. updateAmbient: лепестки ============
P.append((
"""function updateAmbient(dt){
  for (const p of amb){
    p.y -= p.spd*dt; p.x += Math.sin(Date.now()/1400+p.ph)*p.sway*dt;
    if (p.y < -8){ p.y = VH+8; p.x = Math.random()*VW; }
  }
}""",
"""function updateAmbient(dt){
  for (const p of amb){
    p.y -= p.spd*dt; p.x += Math.sin(Date.now()/1400+p.ph)*p.sway*dt;
    if (p.y < -8){ p.y = VH+8; p.x = Math.random()*VW; }
  }
  for (const p of petals){
    p.y += p.spd*dt; p.x += Math.sin(Date.now()/1100+p.ph)*22*dt;
    if (p.y > VH+10){ p.y = -10; p.x = Math.random()*VW; }
  }
}"""))

# ============ 12. drawBattle: лучи + лепестки ============
P.append((
"""  ctx.restore();
  drawAmbient();
  // туман-слои (светящиеся пятна поверх мира)""",
"""  ctx.restore();
  drawAmbient();
  drawRays();
  drawPetals();
  // туман-слои (светящиеся пятна поверх мира)"""))

# ============ 13. drawMenu: лучи + лепестки + кнопки громкости ============
P.append((
"""  drawAmbient();
  ctx.textAlign='center';
  ctx.save();
  ctx.shadowColor='#4d8cf2'; ctx.shadowBlur=46;""",
"""  drawAmbient();
  drawRays();
  drawPetals();
  // кнопки громкости (сайт-версия)
  const volBtn = (x, label, val, act)=>{
    circle(x, 70, 34, '#1f2b52', '#4d8cf2');
    ctx.font='700 22px Segoe UI'; ctx.fillStyle='#fff'; ctx.textAlign='center';
    ctx.fillText(label, x, 63);
    ctx.font='600 16px Segoe UI'; ctx.fillStyle='#9fb0e0';
    ctx.fillText(Math.round(val*100)+'%', x, 84);
    menuBtns.push({x:x-40, y:30, w:80, h:80, act});
  };
  volBtn(VW-190, '♪', AudioState.music, 'mvol');
  volBtn(VW-90, '♫', AudioState.sfx, 'svol');
  ctx.textAlign='center';
  ctx.save();
  ctx.shadowColor='#4d8cf2'; ctx.shadowBlur=46;"""))

# ============ 14. onDown меню: обработка кнопок громкости ============
P.append((
"""  if (scene==='menu'){
    for (const b of menuBtns) if (hit(p,b)){ SFX.click(); startBattle(b.i); return; }
    return;
  }""",
"""  if (scene==='menu'){
    for (const b of menuBtns) if (hit(p,b)){
      SFX.click();
      if (b.act==='lvl'){ startBattle(b.i); return; }
      if (b.act==='mvol'){
        AudioState.music = AudioState.music>0? 0 : AudioState.music<.4? .55 : .9;
        if (AudioState.music===.9) AudioState.music=0;
        AudioState.music = AudioState.music===0? .55 : AudioState.music; // цикл 55→90→0
        Music.setMusicVol(AudioState.music); persist(); return;
      }
      if (b.act==='svol'){
        AudioState.sfx = AudioState.sfx>.7? 0 : AudioState.sfx<.3? .5 : .9;
        if (AudioState.sfx===0) AudioState.sfx=.5;
        AudioState.sfx = AudioState.sfx===.5? .5 : AudioState.sfx;
        AudioState.sfx = AudioState.sfx>.9? .9 : AudioState.sfx; // цикл 90→50→0
        if (AudioState.sfx===0){} else {}
        Music.setSfxVol(AudioState.sfx); persist(); return;
      }
      return;
    }
    return;
  }"""))

# ============ 15. HUD: градиентные панели, рамки стихий, глифы умений, босс-бар ============
P.append((
"""  hudBtns=[];
  rrect(20,70,92,GROUND_BOT-54,24,'#0f1526cc','#2c3a66');
  rrect(1460,70,440,GROUND_BOT-54,24,'#0f1526cc','#2c3a66');""",
"""  hudBtns=[];
  panelBG(20,70,92,GROUND_BOT-54,24);
  panelBG(1460,70,440,GROUND_BOT-54,24);"""))

P.append((
"""    if (ok){
      const hh=s?92:80, ww=hh*im.naturalWidth/im.naturalHeight;
      ctx.drawImage(im,x-ww/2,y-hh*.62,ww,hh);
    }""",
"""    if (ok){
      const hh=s?92:80, ww=hh*im.naturalWidth/im.naturalHeight;
      ctx.drawImage(im,x-ww/2,y-hh*.62,ww,hh);
      ctx.lineWidth=4; ctx.strokeStyle=EL[h.el].c;
      ctx.beginPath(); ctx.arc(x,y,(s?50:43),0,7); ctx.stroke();
    }"""))

P.append((
"""    ctx.font='600 18px Segoe UI'; ctx.textAlign='center';
    ctx.fillStyle=ready?'#e8e8f0':'#667';
    ctx.fillText(ab.n.split(' ')[0].slice(0,11),x+85,y+88);""",
"""    // глиф типа умения
    ctx.strokeStyle=ready?'#fff':'#889'; ctx.lineWidth=3.5; ctx.lineCap='round';
    const gx=x+85, gy=y+52;
    ctx.beginPath();
    if (ab.t==='nuk'){ ctx.moveTo(gx-10,gy+10); ctx.lineTo(gx+10,gy-10); ctx.moveTo(gx+2,gy-10); ctx.lineTo(gx+10,gy-10); ctx.lineTo(gx+10,gy-2); }
    else if (ab.t==='aoe'){ ctx.arc(gx,gy,9,0,7); ctx.moveTo(gx-16,gy); ctx.lineTo(gx-10,gy); ctx.moveTo(gx+10,gy); ctx.lineTo(gx+16,gy); }
    else if (ab.t==='heal'){ ctx.moveTo(gx,gy-10); ctx.lineTo(gx,gy+10); ctx.moveTo(gx-10,gy); ctx.lineTo(gx+10,gy); }
    else if (ab.t==='buff'){ for(let st=0;st<5;st++){ const a2=st/5*Math.PI*2-Math.PI/2; ctx.moveTo(gx+Math.cos(a2)*4,gy+Math.sin(a2)*4); ctx.lineTo(gx+Math.cos(a2)*10,gy+Math.sin(a2)*10); } }
    else { ctx.moveTo(gx-10,gy-6); ctx.lineTo(gx+10,gy-6); ctx.moveTo(gx-10,gy); ctx.lineTo(gx+10,gy); ctx.moveTo(gx-10,gy+6); ctx.lineTo(gx+10,gy+6); }
    ctx.stroke();
    ctx.font='600 18px Segoe UI'; ctx.textAlign='center';
    ctx.fillStyle=ready?'#e8e8f0':'#667';
    ctx.fillText(ab.n.split(' ')[0].slice(0,11),x+85,y+128);"""))

P.append((
"""  const lvl=LEVELS[levelIdx];
  rrect(20,8,900,52,16,'#0f1526cc');
  ctx.font='700 28px Segoe UI'; ctx.fillStyle='#dfe3f0'; ctx.textAlign='center';
  ctx.fillText(`${lvl.name} • волна ${Math.min(waveIdx+1,lvl.waves.length)}/${lvl.waves.length}`,470,44);
}""",
"""  const lvl=LEVELS[levelIdx];
  rrect(20,8,900,52,16,'#0f1526cc');
  ctx.font='700 28px Segoe UI'; ctx.fillStyle='#dfe3f0'; ctx.textAlign='center';
  ctx.fillText(`${lvl.name} • волна ${Math.min(waveIdx+1,lvl.waves.length)}/${lvl.waves.length}`,470,44);
  // БОСС-БАР сверху по центру
  const boss = enemies.find(e=>e.alive&&e.boss&&e.dropY>=0);
  if (boss){
    const bw=760, bx=VW/2-bw/2, by=16;
    const g=ctx.createLinearGradient(bx,0,bx+bw,0);
    g.addColorStop(0,'#ff3a3a'); g.addColorStop(1,'#ffb03a');
    rrect(bx-6,by-6,bw+12,58,14,'#0f1526dd','#c07aff');
    ctx.fillStyle='#2a0d16'; ctx.fillRect(bx,by,bw,40);
    ctx.fillStyle=g; ctx.fillRect(bx,by,bw*Math.max(0,boss.hp/boss.maxhp),40);
    ctx.font='800 26px Segoe UI'; ctx.textAlign='center'; ctx.fillStyle='#fff';
    ctx.fillText(boss.n.toUpperCase(), VW/2, by+28);
  }
}"""))

fail = 0
for i,(old,new) in enumerate(P,1):
    c = s.count(old)
    if c != 1:
        print(f"ПАТЧ {i}: НЕ НАЙДЕН (вхождений {c})"); fail += 1; continue
    s = s.replace(old, new, 1)
    print(f"ПАТЧ {i}: ок")

if fail:
    print("Провал:", fail, "— НЕ сохранено"); sys.exit(1)
io.open(HTML,"w",encoding="utf-8").write(s)
print("Сохранено.")
