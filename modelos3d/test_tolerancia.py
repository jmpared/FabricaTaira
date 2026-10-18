"""Pieza de prueba de tolerancias: base con 4 huecos (0.10/0.15/0.20/0.25 mm) + inserto corazón."""
import os
from extru import *

OUT = "out/test_tolerancia"; os.makedirs(OUT, exist_ok=True)
TOLS = [0.10, 0.15, 0.20, 0.25]
BASE_H, POCKET_D, INS_H, LAB_D = 3.0, 1.6, 2.0, 0.4
XS = [-22.5, -7.5, 7.5, 22.5]

def heart(c, img, x, y, s=10.0):
    r = s * 0.27
    c.circle(img, x - r * 0.95, y + s * 0.12, r); c.circle(img, x + r * 0.95, y + s * 0.12, r)
    c.poly(img, [(x - r * 1.92, y + s * 0.02), (x + r * 1.92, y + s * 0.02), (x, y - s * 0.5)])

c = Canvas(68, 26)
outer = c.blank(); c.rrect(outer, 0, 0, 64, 22, 3)
S_out = c.sdf(outer)
pockets = []
for x, t in zip(XS, TOLS):
    im = c.blank(); heart(c, im, x, 2.4); pockets.append(grow(c.sdf(im), t))
lab = c.blank()
for x, t in zip(XS, TOLS): c.text(lab, f"{t:.2f}"[1:], x, -7.6, 2.6)
S_lab = c.sdf(lab)

base = Stack(c)
base.slab(0, BASE_H - POCKET_D, S_out)
base.slab(BASE_H - POCKET_D, BASE_H - LAB_D, diff(S_out, *pockets))
base.slab(BASE_H - LAB_D, BASE_H, diff(S_out, *pockets, S_lab))
Vb, Fb = base.mesh(); print("base", check(Vb, Fb))

c2 = Canvas(14, 14)
im = c2.blank(); heart(c2, im, 0, 0.5); S_h = c2.sdf(im)
ins = Stack(c2)
ins.slab(0, 0.25, grow(S_h, -0.25))      # bisel escalonado: entra fácil y evita la pata de elefante
ins.slab(0.25, INS_H, S_h)
Vi, Fi = ins.mesh(); print("inserto", check(Vi, Fi))

write_stl(f"{OUT}/base_color1.stl", Vb, Fb)
write_stl(f"{OUT}/inserto_color2.stl", Vi, Fi)
write_3mf(f"{OUT}/test_tolerancia_todo.3mf", [("base", Vb, Fb)] + [(f"inserto_{i+1}", Vi, Fi) for i in range(4)])
