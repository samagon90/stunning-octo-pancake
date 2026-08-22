#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Патч веб-демо: анимации персонажей (выпад/вспышка/смерть/спавн), снаряды,
взмахи, кольца AoE, искры лечения, анимированное окружение (частицы, руны,
параллакс), тряска экрана, баннеры волн, отклик на тап. Применяется к
prototype/index.html точечными заменами; каждая замена проверяется."""
import io, sys

HTML = "/home/user/stunning-octo-pancake/prototype/index.html"
src = io.open(HTML, encoding="utf-8").read()

patches = []

# 1) spawnEnemy: таймеры анимаций + пыль спавна + босс-эффект
patches.append((
"""    r: tpl.boss? 74: 38, atkT: Math.random(), facing:-1 });
  if (tpl.boss) SFX.boss();
}""",
"""    r: tpl.boss? 74: 38, atkT: Math.random(), facing:-1,
    spawnT:.35, lungeT:0, hitT:0, deathT:0, moving:false });
  fxSpawnDust(enemies[enemies.length-1].x, enemies[enemies.length-1].y + 20);
  if (tpl.boss){ SFX.boss(); shake(12, .5); bannerText = tpl.n.toUpperCase() + '!'; bannerT = 1.8; }
}"""))

# 2) beginWave: баннер волны
patches.append((
"""  spawnQueue = [];
  lvl.waves[waveIdx].forEach(g => { for(let k=0;k<g.cnt;k++) spawnQueue.push({...g, delay: k*0.7}); });
  waveTimer = 0;
}""",
"""  spawnQueue = [];
  lvl.waves[waveIdx].forEach(g => { for(let k=0;k<g.cnt;k++) spawnQueue.push({...g, delay: k*0.7}); });
  waveTimer = 0;
  bannerText = 'ВОЛНА ' + (waveIdx+1); bannerT = 1.2;
}"""))

# 3) startBattle: сброс FX
patches.append((
"""  levelIdx = i; resetTeam(); enemies = []; floats = [];
  waveIdx = 0; battleTime = 0; battleOver = null; rewards = null; autoMode = false;""",
"""  levelIdx = i; resetTeam(); enemies = []; floats = [];
  effects = []; ripple = null; bannerT = 0; shakeT = 0; shakeMag = 0;
  waveIdx = 0; battleTime = 0; battleOver = null; rewards = null; autoMode = false;"""))

# 4) hurt: вспышка урона, тряска на крите, смерть с "пуфом"
patches.append((
"""  t.hp -= d;
  addFloat(t.x + (Math.random()*40-20), t.y - t.r - 16, Math.round(d), crit? '#ff9a3d' : (t.team===0? '#ff5a5a':'#ffffff'), crit);
  crit? SFX.crit() : SFX.hit();
  if (t.hp <= 0){ t.hp = 0; t.alive = false; }
}""",
"""  t.hp -= d;
  t.hitT = .25;
  if (crit) shake(4, .12);
  addFloat(t.x + (Math.random()*40-20), t.y - t.r - 16, Math.round(d), crit? '#ff9a3d' : (t.team===0? '#ff5a5a':'#ffffff'), crit);
  crit? SFX.crit() : SFX.hit();
  if (t.hp <= 0){
    t.hp = 0; t.alive = false; t.deathT = .55;
    fxPoof(t.x, t.y - t.r, EL[t.el].c);
    if (t.boss) shake(10, .4);
  }
}"""))

# 5) атака героев: выпад + снаряд/взмах
patches.append((
"""        u.atkT -= dt;
        if (u.atkT <= 0){ u.atkT = 1/(u.role==='Танк'? .8 : 1.05); hurt(t, u, 1, false); u.facing = Math.sign(t.x-u.x)||1; }""",
"""        u.atkT -= dt;
        if (u.atkT <= 0){
          u.atkT = 1/(u.role==='Танк'? .8 : 1.05);
          u.lungeT = .22;
          if (u.range > 180) fxProjectile(u, t, EL[u.el].c, false);
          else fxSlash(t.x, t.y - t.r*.6, EL[u.el].c);
          hurt(t, u, 1, false);
          u.facing = Math.sign(t.x-u.x)||1;
        }"""))

# 6) атака врагов: взмах + выпад, босс трясёт
patches.append((
"""    else { e.atkT -= dt; if (e.atkT<=0){ e.atkT = 1/0.9; hurt(t, e, 1, false); } }""",
"""    else {
      e.atkT -= dt;
      if (e.atkT<=0){
        e.atkT = 1/0.9; e.lungeT = .22;
        fxSlash(t.x, t.y - t.r*.6, e.boss? '#c07aff' : EL[e.el].c);
        hurt(t, e, 1, false);
        if (e.boss) shake(5, .2);
      }
    }"""))

# 7) castAbility: эффекты по типам умений
patches.append((
"""    const w = mostWounded(mates)||u;
    w.hp = Math.min(w.maxhp, w.hp + u.atk*ab.k);
    addFloat(w.x, w.y-60, '+'+Math.round(u.atk*ab.k), '#7dff9a');
    SFX.heal();""",
"""    const w = mostWounded(mates)||u;
    w.hp = Math.min(w.maxhp, w.hp + u.atk*ab.k);
    addFloat(w.x, w.y-60, '+'+Math.round(u.atk*ab.k), '#7dff9a');
    fxHeal(w.x, w.y - 30);
    SFX.heal();"""))

patches.append((
"""    for(const m of mates) if(m.alive){ m.hp=Math.min(m.maxhp, m.hp+m.maxhp*ab.k); }
    addFloat(u.x, u.y-80, '★ '+ab.n, '#ffd76a'); SFX.heal();""",
"""    for(const m of mates) if(m.alive){ m.hp=Math.min(m.maxhp, m.hp+m.maxhp*ab.k); fxBuff(m); }
    addFloat(u.x, u.y-80, '★ '+ab.n, '#ffd76a'); SFX.heal();"""))

patches.append((
"""    for(const f of foes) if(f.alive && dist(f,u)<ab.r+60) hurt(f, u, ab.k, true);
    addFloat(u.x, u.y-80, ab.n, EL[u.el].c); SFX.cast();""",
"""    for(const f of foes) if(f.alive && dist(f,u)<ab.r+60) hurt(f, u, ab.k, true);
    fxAoe(u.x, u.y, ab.r + 50, EL[u.el].c);
    addFloat(u.x, u.y-80, ab.n, EL[u.el].c); SFX.cast();"""))

patches.append((
"""  } else { // nuk / line
    const t = nearest(u, foes); if(t) hurt(t, u, ab.k, true);
    addFloat(u.x, u.y-80, ab.n, EL[u.el].c); SFX.cast();
  }""",
"""  } else { // nuk / line
    const t = nearest(u, foes);
    if (t){ fxProjectile(u, t, EL[u.el].c, true); hurt(t, u, ab.k, true); }
    addFloat(u.x, u.y-80, ab.n, EL[u.el].c); SFX.cast();
  }"""))

# 8) tick: таймеры юнитов + FX
patches.append((
"""function tick(dt){
  battleTime += dt;""",
"""function tick(dt){
  battleTime += dt;
  for (const u of [...team, ...enemies]){
    if (u.lungeT > 0) u.lungeT -= dt;
    if (u.hitT > 0) u.hitT -= dt;
    if (u.spawnT > 0) u.spawnT -= dt;
    if (!u.alive && u.deathT > 0) u.deathT -= dt;
  }
  tickFx(dt);"""))

# 9) drawUnit: полная анимация
old_unit = """function drawUnit(u){
  if(!u.alive) return;
  const bob = u.moving? Math.sin(Date.now()/90+u.x)*5 : Math.sin(Date.now()/500+u.x)*2.5;
  const im = IMG[u.artKey];
  const ok = im && im.complete && im.naturalWidth > 0;
  const footY = u.y + u.r*.8;
  const hgt = u.r * (u.boss? 6.1 : 4.5);
  const wdt = ok? hgt * im.naturalWidth / im.naturalHeight : 0;
  const topY = footY - hgt;

  ctx.globalAlpha=.35; ctx.beginPath();
  ctx.ellipse(u.x, footY, u.r*1.05, u.r*.3, 0, 0, 7);
  ctx.fillStyle='#000'; ctx.fill(); ctx.globalAlpha=1;

  if (ok){
    ctx.save();
    ctx.translate(u.x, footY + bob);
    const artDir = u.team===0? 1 : -1;
    if (u.facing !== artDir) ctx.scale(-1,1);
    ctx.drawImage(im, -wdt/2, -hgt, wdt, hgt);
    ctx.restore();
  } else {
    const col = EL[u.el].c;
    circle(u.x, u.y+bob, u.r, u.team===1? shade(col,-45):col, u.team===0? '#e8e8f0':'#3a2a2a');
    circle(u.x, u.y+bob-u.r*.55, u.r*.42, shade(col,70));
  }

  const bw = u.boss? 190: 96;
  const barY = topY - (u.boss? 20:14) + bob;
  ctx.fillStyle='#000a'; ctx.fillRect(u.x-bw/2, barY, bw, 11);
  ctx.fillStyle= u.team===0? '#6dff8a':'#ff6a5a';
  ctx.fillRect(u.x-bw/2, barY, bw*Math.max(0,u.hp/u.maxhp), 11);

  ctx.font = '600 20px Segoe UI'; ctx.textAlign='center';
  ctx.fillStyle = u.boss? '#f5c542' : '#dfe3f0';
  ctx.fillText(u.name, u.x, footY + 30);
}"""
new_unit = """function drawUnit(u){
  if (!u.alive && u.deathT <= 0) return;
  const alive = u.alive;
  const deathK = alive ? 1 : Math.max(0, u.deathT / .55);
  const spawnK = u.spawnT > 0 ? u.spawnT / .35 : 0; // 1 → 0
  const lunge = u.lungeT > 0 ? Math.sin(Math.PI * (1 - u.lungeT/.22)) * 20 * (u.facing || 1) : 0;
  const bob = u.moving ? Math.sin(Date.now()/85 + u.x)*6 : Math.sin(Date.now()/520 + u.x)*2.5;
  const breath = 1 + .015*Math.sin(Date.now()/420 + u.x);
  const im = IMG[u.artKey];
  const ok = im && im.complete && im.naturalWidth > 0;
  const footY = u.y + u.r*.8;
  const scale = 1 + spawnK*.55;
  let hgt = u.r * (u.boss? 6.1 : 4.5) * scale;
  const wdt = ok ? hgt * im.naturalWidth / im.naturalHeight : 0;
  const topY = footY - hgt;

  // тень (тает при смерти)
  ctx.globalAlpha = .35 * deathK;
  ctx.beginPath(); ctx.ellipse(u.x, footY, u.r*1.05*scale, u.r*.3, 0, 0, 7);
  ctx.fillStyle = '#000'; ctx.fill();
  ctx.globalAlpha = alive ? 1 : deathK;

  if (ok){
    ctx.save();
    ctx.translate(u.x + lunge, footY + bob + (alive ? 0 : (1-deathK)*16));
    const artDir = u.team===0 ? 1 : -1;
    if (u.facing !== artDir) ctx.scale(-1, 1);
    if (!alive) ctx.rotate((1-deathK) * .9 * -artDir); // падение
    ctx.scale(1, breath);
    if (u.hitT > 0){ try { ctx.filter = 'brightness(' + (1 + 2.5*(u.hitT/.25)) + ')'; } catch(e){} }
    ctx.drawImage(im, -wdt/2, -hgt, wdt, hgt);
    try { ctx.filter = 'none'; } catch(e){}
    ctx.restore();
  } else {
    const col = EL[u.el].c;
    circle(u.x + lunge, u.y+bob, u.r*scale, u.team===1? shade(col,-45):col, u.team===0? '#e8e8f0':'#3a2a2a');
    circle(u.x + lunge, u.y+bob-u.r*.55*scale, u.r*.42*scale, shade(col,70));
  }
  ctx.globalAlpha = 1;

  if (alive){
    const bw = u.boss? 190: 96;
    const barY = topY - (u.boss? 20:14) + bob;
    ctx.fillStyle='#000a'; ctx.fillRect(u.x-bw/2, barY, bw, 11);
    ctx.fillStyle= u.team===0? '#6dff8a':'#ff6a5a';
    ctx.fillRect(u.x-bw/2, barY, bw*Math.max(0,u.hp/u.maxhp), 11);

    ctx.font = '600 20px Segoe UI'; ctx.textAlign='center';
    ctx.fillStyle = u.boss? '#f5c542' : '#dfe3f0';
    ctx.fillText(u.name, u.x, footY + 30);
  }
}"""
patches.append((old_unit, new_unit))

# 10) drawArena: параллакс + вращающиеся руны
patches.append((
"""  const bg = IMG.bg;
  if (bg && bg.complete && bg.naturalWidth > 0){
    ctx.drawImage(bg, 0, 0, VW, VH);
  } else {""",
"""  const bg = IMG.bg;
  if (bg && bg.complete && bg.naturalWidth > 0){
    const px = Math.sin(Date.now()/5200)*10, py = Math.cos(Date.now()/6700)*6;
    ctx.drawImage(bg, -14 + px, -10 + py, VW + 28, VH + 20);
  } else {"""))

patches.append((
"""  // виньетка для читаемости HUD""",
"""  // вращающиеся руны платформы
  const cx = (ARENA.x0+ARENA.x1)/2, cy = (ARENA.y0+ARENA.y1)/2 + 60, rt = Date.now()/1000;
  ctx.save();
  ctx.globalAlpha = .10 + .05*Math.sin(rt*2);
  ctx.strokeStyle = '#7fb2ff'; ctx.lineWidth = 3;
  for (let i=0;i<3;i++){
    ctx.beginPath();
    ctx.ellipse(cx, cy, 280 + i*62, 105 + i*24, rt*(.2 + .08*i), 0, 7);
    ctx.stroke();
  }
  ctx.restore();

  // виньетка для читаемости HUD"""))

# 11) drawBattle: тряска, частицы, FX, маркер, тап-отклик, баннер, низкое ХП
patches.append((
"""function drawBattle(){
  drawArena();
  for(const e of enemies) drawUnit(e);
  for(const u of team) drawUnit(u);
  drawFloats();
  drawBattleHUD();
  drawResult();
}""",
"""function drawBattle(){
  ctx.save();
  if (shakeT > 0 && shakeMag > 0)
    ctx.translate((Math.random()*2-1)*shakeMag, (Math.random()*2-1)*shakeMag);
  drawArena();
  drawAmbient();
  for(const e of enemies) drawUnit(e);
  for(const u of team) drawUnit(u);
  drawFx();
  drawFloats();

  // маркер точки движения выбранного героя
  const selU = team[sel];
  if (selU && selU.alive && selU.wp){
    ctx.globalAlpha = .5 + .3*Math.sin(Date.now()/180);
    ctx.strokeStyle = '#7dff9a'; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.ellipse(selU.wp.x, selU.wp.y, 26, 10, 0, 0, 7); ctx.stroke();
    ctx.globalAlpha = 1;
  }
  // отклик на тап
  if (ripple){
    const k = ripple.t/.5;
    ctx.globalAlpha = 1-k; ctx.strokeStyle = '#cfe0ff'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(ripple.x, ripple.y, 12 + k*36, 0, 7); ctx.stroke();
    ctx.globalAlpha = 1;
  }
  // баннер волны/босса
  if (bannerT > 0){
    ctx.globalAlpha = Math.min(1, bannerT/.4);
    ctx.textAlign='center'; ctx.font='800 54px Segoe UI';
    ctx.fillStyle='#ffd76a'; ctx.strokeStyle='#000a'; ctx.lineWidth=6;
    ctx.strokeText(bannerText, (ARENA.x0+ARENA.x1)/2, 150);
    ctx.fillText(bannerText, (ARENA.x0+ARENA.x1)/2, 150);
    ctx.globalAlpha = 1;
  }
  ctx.restore();

  // тревога: у героя меньше 30% ХП
  if (team.some(u=>u.alive && u.hp/u.maxhp < .3)){
    const a = .10 + .07*Math.sin(lowHpPulse*5);
    const rg = ctx.createRadialGradient(VW/2,VH/2,VH*.35, VW/2,VH/2,VW*.62);
    rg.addColorStop(0,'rgba(255,40,40,0)'); rg.addColorStop(1,'rgba(255,40,40,'+a+')');
    ctx.fillStyle = rg; ctx.fillRect(0,0,VW,VH);
  }
  drawBattleHUD();
  drawResult();
}"""))

# 12) drawMenu: частицы + дыхание героев + свечение заголовка
patches.append((
"""  ctx.globalAlpha=1;
  // левая половина: заголовок + отряд
  ctx.textAlign='center';
  ctx.font='900 92px Segoe UI'; ctx.fillStyle='#e8ecff';
  ctx.fillText('МАСТЕРА СНОВ', 480, 220);""",
"""  ctx.globalAlpha=1;
  drawAmbient();
  // левая половина: заголовок + отряд
  ctx.textAlign='center';
  ctx.save();
  ctx.shadowColor = '#4d8cf2'; ctx.shadowBlur = 42;
  ctx.font='900 92px Segoe UI'; ctx.fillStyle='#e8ecff';
  ctx.fillText('МАСТЕРА СНОВ', 480, 220);
  ctx.restore();"""))

patches.append((
"""    if (ok){
      const hh = 220, ww = hh * im.naturalWidth / im.naturalHeight;
      ctx.beginPath(); ctx.ellipse(x, y+52, 74, 16, 0, 0, 7); ctx.fillStyle='#0006'; ctx.fill();
      ctx.drawImage(im, x-ww/2, y-hh+55, ww, hh);
    } else {""",
"""    if (ok){
      const hh = 220, ww = hh * im.naturalWidth / im.naturalHeight;
      const bo = Math.sin(Date.now()/420 + i*1.3)*6;
      ctx.beginPath(); ctx.ellipse(x, y+52, 74, 16, 0, 0, 7); ctx.fillStyle='#0006'; ctx.fill();
      ctx.drawImage(im, x-ww/2, y-hh+55+bo, ww, hh);
    } else {"""))

# 13) loop: обновлять окружение всегда
patches.append((
"""  const dt = Math.min(.05, (now-last)/1000) * timeScale;
  last = now;""",
"""  const dtRaw = Math.min(.05, (now-last)/1000);
  const dt = dtRaw * timeScale;
  last = now;
  updateAmbient(dtRaw);"""))

# 14) onDown: тап-отклик
patches.append((
"""    if (!battleOver && p.x>ARENA.x0 && p.x<ARENA.x1 && p.y>ARENA.y0 && p.y<ARENA.y1){
      team[sel].wp = {x:p.x, y:p.y};
    }""",
"""    if (!battleOver && p.x>ARENA.x0 && p.x<ARENA.x1 && p.y>ARENA.y0 && p.y<ARENA.y1){
      team[sel].wp = {x:p.x, y:p.y};
      ripple = {x:p.x, y:p.y, t:0};
    }"""))

fail = 0
for i, (old, new) in enumerate(patches, 1):
    cnt = src.count(old)
    if cnt != 1:
        print(f"ПАТЧ {i}: НЕ НАЙДЕН (вхождений: {cnt})")
        fail += 1
        continue
    src = src.replace(old, new, 1)
    print(f"ПАТЧ {i}: ок")

if fail:
    print("НЕ ПРИМЕНЕНО:", fail, "— файл НЕ записан")
    sys.exit(1)

io.open(HTML, "w", encoding="utf-8").write(src)
print("Сохранено.")
