"""Chapita con forma de huella: base (color 1) + dedos, contorno de almohadilla y nombre encastrados (color 2)."""
import os, sys
from extru import *
from cover import shot, title
from PIL import Image

NOMBRE = (sys.argv[1] if len(sys.argv) > 1 else "MILO").upper()
TEL = sys.argv[2] if len(sys.argv) > 2 else "11 1234-5678"
TOL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
C1, C2 = (sys.argv[4] if len(sys.argv) > 4 else "#e2557f"), (sys.argv[5] if len(sys.argv) > 5 else "#fbf6ee")
BASE_H, POCKET_D, INS_H, BACK_D = 3.2, 1.6, 2.0, 0.4
OUT = f"out/huella_{NOMBRE}"; os.makedirs(OUT, exist_ok=True)
c = Canvas(56, 56)

def pad(img, g=0.0):
    ellipse(c, img, 0, -5.5, 12.0 + g, 8.6 + g)
    for x in (-6.2, 6.2): c.circle(img, x, -9.2, 5.6 + g)
    c.circle(img, 0, -11.2, 5.6 + g)
TOES = [(-12.6, 4.2, 30), (-4.7, 9.6, 9), (4.7, 9.6, -9), (12.6, 4.2, -30)]
def toes(img, g=0.0):
    for x, y, a in TOES: ellipse(c, img, x, y, 3.5 + g, 4.6 + g, a)

# contorno general: todo agrandado y "cerrado" para que sea una sola pieza
allm = c.blank(); pad(allm); toes(allm)
S_all = c.sdf(allm)
S_base = closing(c, grow(S_all, 2.0), 3.2)
hole = c.blank(); c.circle(hole, 0, 16.0, 1.9)
# asegurar material alrededor del agujero
lug = c.blank(); c.circle(lug, 0, 16.0, 4.3)
S_base = diff(union(S_base, c.sdf(lug)), c.sdf(hole))

# encastres: dedos + aro de la almohadilla + nombre
pm = c.blank(); pad(pm); S_pad = c.sdf(pm)
S_ring = inter(S_pad, -(S_pad + 1.3))          # banda de 1.3 mm por dentro del borde
tm = c.blank(); toes(tm); S_toes = c.sdf(tm)
cap = 6.0
while c.text_width(NOMBRE, cap, track=0.4) > 17.0 and cap > 3.5: cap -= 0.1
nm = c.blank(); c.text(nm, NOMBRE, 0, -6.6, cap, track=0.4); S_nom = c.sdf(nm)
S_deco = union(S_ring, S_toes, S_nom)

tel = c.blank(); fb = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
c.text(tel, TEL, 0, -6.0, 3.0, font=fb); c.text(tel, "SI ME PERDÍ, LLAMÁ", 0, -1.2, 2.0, font=fb)
tel = tel.transpose(Image.FLIP_LEFT_RIGHT); S_tel = c.sdf(tel)

base = Stack(c)
base.slab(0, BACK_D, diff(S_base, S_tel))
base.slab(BACK_D, BASE_H - POCKET_D, S_base)
base.slab(BASE_H - POCKET_D, BASE_H, diff(S_base, grow(S_deco, TOL)))
Vb, Fb = base.mesh(); print("base", check(Vb, Fb))
ins = Stack(c); ins.slab(0, 0.25, grow(S_deco, -0.2)); ins.slab(0.25, INS_H, S_deco)
Vi, Fi = ins.mesh(); print("encastres", check(Vi, Fi))

write_3mf(f"{OUT}/huella_{NOMBRE}_plato1_base.3mf", [("base", Vb, Fb)])
write_3mf(f"{OUT}/huella_{NOMBRE}_plato2_encastres.3mf", [("encastres", Vi, Fi)])
write_stl(f"{OUT}/huella_base.stl", Vb, Fb); write_stl(f"{OUT}/huella_encastres.stl", Vi, Fi)
z = BASE_H - POCKET_D
img = shot([(Vb, Fb, C1, (0, 0, 0)), (Vi, Fi, C2, (0, 0, z))], elev=58, azim=-14)
title(img, "Chapita huella", "2 colores sin AMS · encastre a presión").convert("RGB").save(f"{OUT}/portada.jpg", quality=92)
shot([(Vb, Fb, C1, (0, 0, 0)), (Vi, Fi, C2, (58, 0, 0))], elev=60, azim=-8).convert("RGB").save(f"{OUT}/piezas.jpg", quality=90)
Vr = Vb.copy(); Vr[:, 0] *= -1; Vr[:, 2] = Vr[:, 2].max() - Vr[:, 2]
shot([(Vr, Fb, C1, (0, 0, 0))], elev=75, azim=0).convert("RGB").save(f"{OUT}/atras.jpg", quality=90)
