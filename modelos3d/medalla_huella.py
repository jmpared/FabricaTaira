"""Medalla redonda premium: aro, huella y nombre en arco encastrados (color 2) sobre base (color 1).
Atrás: teléfono grabado. Uso: python3 medalla_huella.py NOMBRE "TELEFONO" [TOL]"""
import os, sys
from extru import *
from cover import shot, title

NOMBRE = (sys.argv[1] if len(sys.argv) > 1 else "LOLA").upper()
TEL = sys.argv[2] if len(sys.argv) > 2 else "11 1234-5678"
TOL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
C1, C2 = (sys.argv[4] if len(sys.argv) > 4 else "#1f3a5f"), (sys.argv[5] if len(sys.argv) > 5 else "#f2c14e")
BASE_H, POCKET_D, INS_H, BACK_D = 3.2, 1.6, 2.0, 0.4
R = 17.0
OUT = f"out/medalla_{NOMBRE}"; os.makedirs(OUT, exist_ok=True)
c = Canvas(44, 50)

# ---- base
b = c.blank(); c.circle(b, 0, 0, R); c.circle(b, 0, R + 1.2, 4.6); c.rrect(b, 0, R - 1.5, 8, 6, 1.5)
hole = c.blank(); c.circle(hole, 0, R + 1.6, 1.9)
S_base = diff(c.sdf(b), c.sdf(hole))

# ---- motivos (color 2)
ring = c.blank(); c.circle(ring, 0, 0, R - 1.1); c.circle(ring, 0, 0, R - 2.6, fill=0)
paw = c.blank()
ellipse(c, paw, 0, -4.6, 4.9, 3.9)                      # almohadilla
c.circle(paw, -3.0, -4.0, 2.6); c.circle(paw, 3.0, -4.0, 2.6); c.circle(paw, 0, -6.3, 2.4)   # lóbulos inferiores
for x, y, a in [(-6.1, 1.5, 28), (-2.2, 3.9, 9), (2.2, 3.9, -9), (6.1, 1.5, -28)]:
    ellipse(c, paw, x, y, 1.7, 2.25, a)
cap = 3.9
while True:
    nm = c.blank(); text_arc(c, nm, NOMBRE, 11.4, cap, top=True, track=0.45)
    # que no invada el aro ni la huella: ancho angular máximo ~ 150°
    from PIL import ImageFont
    f = ImageFont.truetype(FONT, 400); hb = f.getbbox("H"); k = cap / (hb[3] - hb[1])
    span = (sum(f.getlength(ch) for ch in NOMBRE) * k + 0.45 * (len(NOMBRE) - 1)) / 11.4
    if span < np.radians(150) or cap < 3.0: break
    cap -= 0.1
S_ring, S_paw, S_nom = c.sdf(ring), c.sdf(paw), c.sdf(nm)
S_deco = union(S_ring, S_paw, S_nom)

tel = c.blank()
text_arc(c, tel, "SI ME PERDÍ", 12.2, 2.4, top=True, font="/usr/share/fonts/opentype/inter/Inter-Bold.otf", track=0.25)
c.text(tel, TEL, 0, 0, 3.2, font="/usr/share/fonts/opentype/inter/Inter-Bold.otf")
c.text(tel, "LLAMÁ", 0, -5.5, 2.6, font="/usr/share/fonts/opentype/inter/Inter-Bold.otf")
from PIL import Image
tel = tel.transpose(Image.FLIP_LEFT_RIGHT)  # espejo: se lee al dar vuelta
S_tel = c.sdf(tel)

base = Stack(c)
base.slab(0, BACK_D, diff(S_base, S_tel))
base.slab(BACK_D, BASE_H - POCKET_D, S_base)
base.slab(BASE_H - POCKET_D, BASE_H, diff(S_base, grow(S_deco, TOL)))
Vb, Fb = base.mesh(); print("base", check(Vb, Fb))
ins = Stack(c)
ins.slab(0, 0.25, grow(S_deco, -0.2)); ins.slab(0.25, INS_H, S_deco)
Vi, Fi = ins.mesh(); print("encastres", check(Vi, Fi))

write_3mf(f"{OUT}/medalla_{NOMBRE}_plato1_base.3mf", [("base", Vb, Fb)])
write_3mf(f"{OUT}/medalla_{NOMBRE}_plato2_encastres.3mf", [("encastres", Vi, Fi)])
write_stl(f"{OUT}/medalla_base.stl", Vb, Fb); write_stl(f"{OUT}/medalla_encastres.stl", Vi, Fi)

z = BASE_H - POCKET_D
img = shot([(Vb, Fb, C1, (0, 0, 0)), (Vi, Fi, C2, (0, 0, z))], elev=58, azim=-14)
title(img, "Medalla con nombre", "2 colores sin AMS · encastre a presión").convert("RGB").save(f"{OUT}/portada.jpg", quality=92)
Vr = Vb.copy(); Vr[:, 0] *= -1; Vr[:, 2] = Vr[:, 2].max() - Vr[:, 2]
shot([(Vr, Fb, C1, (0, 0, 0))], elev=75, azim=0).convert("RGB").save(f"{OUT}/atras.jpg", quality=90)
shot([(Vb, Fb, C1, (0, 0, 0)), (Vi, Fi, C2, (46, 0, 0))], elev=60, azim=-8).convert("RGB").save(f"{OUT}/piezas.jpg", quality=90)
