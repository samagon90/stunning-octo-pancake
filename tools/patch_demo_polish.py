#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Полировка анимаций: отбрасывание при уроне, плавные HP-бары, портал спавна,
искры в полёте снарядов, души при смерти, маркер выбранного героя, баннеры волн,
поза каста у босса при слэме."""
import io, sys

HTML = "/home/user/stunning-octo-pancake/prototype/index.html"
s = io.open(HTML, encoding="utf-8").read()
P = []

# 1) mkUnit: плавный HP-бар
P.append((
"    pose:'idle', castT:0,",
"    pose:'idle', castT:0, hpShow:base.hp,"))

# 2) tick: лерп hpShow + поза каста при слэме босса
P.append((
"""      if (u.windup>0 || u.lungeT>0) u.pose='atk';
      else if (u.castT>0) u.pose='cast';""",
"""      if (u.windup>0 || u.lungeT>0) u.pose='atk';
      else if (u.castT>0 || u.pendingSlam) u.pose='cast';"""))

P.append((
"""  // таймеры анимаций
  for (const u of [...team,...enemies]){
    if (u.spawnT>0) u.spawnT-=dt;""",
"""  // таймеры анимаций
  for (const u of [...team,...enemies]){
    u.hpShow += (u.hp-u.hpShow)*Math.min(1,dt*9);
    if (u.spawnT>0) u.spawnT-=dt;"""))

# 3) hurt: отбрасывание + крит-вспышка + души при смерти + мощная смерть босса
P.append((
"""  t.hp-=d; t.hitT=.22;
  fxSparks(t.x, t.y-t.r*.4, (EL[from.el]||EL.fire).c, Math.sign(t.x-from.x)||1);""",
"""  t.hp-=d; t.hitT=.22;
  t.x += (Math.sign(t.x-from.x)||1)*9; // отбрасывание
  fxSparks(t.x, t.y-t.r*.4, (EL[from.el]||EL.fire).c, Math.sign(t.x-from.x)||1);
  if (crit) fxBurst(t.x, t.y-t.r, '#ffffff', false);"""))

P.append((
"""    t.hp=0; t.alive=false; t.deathT=.55;
    fxPoof(t.x, t.y-t.r,EL[t.el].c);
    freeze(.07);
    if (t.boss){ shake(11,.45); flashT=.22; slowmo(.55); SFX.slam(); }""",
"""    t.hp=0; t.alive=false; t.deathT=.55;
    fxPoof(t.x, t.y-t.r,EL[t.el].c);
    for (let i=0;i<9;i++) effects.push({t:'sp', x:t.x+Math.random()*40-20, y:t.y-t.r,
      vy:-(90+Math.random()*130), life:.9, T:.9, color:EL[t.el].c}); // души стихии
    freeze(.07);
    if (t.boss){
      shake(15,.6); flashT=.3; slowmo(.9); SFX.slam();
      fxBurst(t.x, t.y-t.r*2, '#c07aff', true);
      fxBurst(t.x, t.y-t.r, '#ffffff', true);
    }"""))

# 4) снаряды сыплют искры в полёте
P.append((
"""      e.x+=dx/d*e.sp*dt; e.y+=dy/d*e.sp*dt;
      e.trail.push({x:e.x,y:e.y}); if (e.trail.length>7) e.trail.shift();""",
"""      e.x+=dx/d*e.sp*dt; e.y+=dy/d*e.sp*dt;
      e.trail.push({x:e.x,y:e.y}); if (e.trail.length>7) e.trail.shift();
      if (Math.random()<.45) effects.push({t:'p', x:e.x, y:e.y,
        vx:(Math.random()*2-1)*30, vy:(Math.random()*2-1)*30, life:.3, T:.3, color:e.color});"""))

# 6) HP-бар от плавного значения
P.append((
"    ctx.fillRect(u.x-bw/2,barY,bw*Math.max(0,u.hp/u.maxhp),11);",
"    ctx.fillRect(u.x-bw/2,barY,bw*Math.max(0,u.hpShow/u.maxhp),11);"))
P.append((
"    ctx.fillStyle=g; ctx.fillRect(bx,by,bw*Math.max(0,boss.hp/boss.maxhp),40);",
"    ctx.fillStyle=g; ctx.fillRect(bx,by,bw*Math.max(0,boss.hpShow/boss.maxhp),40);"))

# 7) маркер выбранного героя
P.append((
"""  drawFx();
  drawFloats();
  drawBanner();""",
"""  drawFx();
  drawFloats();
  // маркер выбранного героя
  const selH = team[sel];
  if (selH && selH.alive && !battleOver){
    const pu = .5+.4*Math.sin(Date.now()/200);
    ctx.globalAlpha = pu;
    ctx.strokeStyle = '#7dff9a'; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.ellipse(selH.x, selH.y+selH.r*.8, selH.r*1.25, selH.r*.42, 0, 0, 7); ctx.stroke();
    ctx.globalAlpha = 1;
    const ay = selH.y - selH.r*5.6 + Math.sin(Date.now()/260)*5;
    ctx.fillStyle = '#7dff9a';
    ctx.beginPath(); ctx.moveTo(selH.x-11,ay); ctx.lineTo(selH.x+11,ay); ctx.lineTo(selH.x,ay+15); ctx.closePath(); ctx.fill();
  }
  drawBanner();"""))

# 8) баннеры зачистки
P.append((
"""        phase='march'; marchTarget=roomX(waveIdx+1)-250;
        bannerText='Идём глубже в сон…'; bannerSub=''; bannerT=1.6;""",
"""        phase='march'; marchTarget=roomX(waveIdx+1)-250;
        bannerText='ВОЛНА ЗАЧИЩЕНА! Идём глубже в сон…'; bannerSub=''; bannerT=1.9;"""))
P.append((
"""      } else if (!battleOver) endBattle(true);""",
"""      } else if (!battleOver){ bannerText='СОН ПРОЙДЕН!'; bannerSub=''; bannerT=2; endBattle(true); }"""))

fail=0
for i,(old,new) in enumerate(P,1):
    c=s.count(old)
    if c!=1: print(f"ПАТЧ {i}: НЕ НАЙДЕН ({c})"); fail+=1; continue
    s=s.replace(old,new,1); print(f"ПАТЧ {i}: ок")
if fail: raise SystemExit("не сохранено")
io.open(HTML,"w",encoding="utf-8").write(s)
print("Сохранено")
