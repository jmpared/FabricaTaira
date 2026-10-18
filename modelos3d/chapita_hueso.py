"""Chapita identificatoria tipo hueso, 2 colores por encastre (se imprime 1 color por vez).
Base: hueso con argolla, huecos con forma de letra. Letras: piezas sueltas que entran a presión.
Atrás: teléfono grabado en espejo (se lee dando vuelta la chapita)."""
import os, sys
from extru import *
from render import render

NOMBRE = (sys.argv[1] if len(sys.argv) > 1 else "TOBY").upper()
TEL = sys.argv[2] if len(sys.argv) > 2 else "11 1234-5678"
TOL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
BASE_H, POCKET_D, LETRA_H, BACK_D = 3.2, 1.6, 2.0, 0.4
OUT = f"out/chapita_hueso_{NOMBRE}"; os.makedirs(OUT, exist_ok=True)

c = Canvas(60, 34)
def hueso(img, L=40.0, H=23.0, r=5.9, body=12.0, grow_=0.0):
    hx = L / 2 - r * 0.9; hy = H / 2 - r
    c.rrect(img, 0, 0, 2 * hx, body + 2 * grow_, 1.0)
    for sx in (-1, 1):
        for sy in (-1, 1): c.circle(img, sx * hx, sy * hy, r + grow_)
hb = c.blank(); hueso(hb)
tab = c.blank(); c.circle(tab, -24.6, 0, 4.2); c.rrect(tab, -20.0, 0, 10, 5.5, 1.2)   # oreja para la argolla
ring = c.blank(); c.circle(ring, -25.2, 0, 1.9)
S_out = diff(union(c.sdf(hb), c.sdf(tab)), c.sdf(ring))

# nombre: ajustar altura para que entre en el cuerpo del hueso
cap = 8.0
while c.text_width(NOMBRE, cap, track=0.35) > 26.5 and cap > 4.5: cap -= 0.1
nm = c.blank(); c.text(nm, NOMBRE, 0.8, 0, cap, track=0.35)
S_nom = c.sdf(nm)

# teléfono atrás (espejado)
tel = c.blank(); c.text(tel, TEL, 0.8, 0, 3.0, font="/usr/share/fonts/opentype/inter/Inter-Bold.otf", mirror=True)
S_tel = c.sdf(tel)

base = Stack(c)
base.slab(0, BACK_D, diff(S_out, S_tel))
base.slab(BACK_D, BASE_H - POCKET_D, S_out)
base.slab(BASE_H - POCKET_D, BASE_H, diff(S_out, grow(S_nom, TOL)))
Vb, Fb = base.mesh(); print("base", check(Vb, Fb))

letras = Stack(c)
letras.slab(0, 0.25, grow(S_nom, -0.22))  # bisel escalonado inferior
letras.slab(0.25, LETRA_H, S_nom)
Vl, Fl = letras.mesh(); print("letras", check(Vl, Fl))

write_stl(f"{OUT}/chapita_base_color1.stl", Vb, Fb)
write_stl(f"{OUT}/chapita_letras_color2.stl", Vl, Fl)
write_3mf(f"{OUT}/chapita_{NOMBRE}_plato1_base.3mf", [("base", Vb, Fb)])
write_3mf(f"{OUT}/chapita_{NOMBRE}_plato2_letras.3mf", [("letras", Vl, Fl)])

# vistas
z_in = BASE_H - POCKET_D
render([(Vb, Fb, "#c8161d", (0, 0, 0)), (Vl, Fl, "#f4c430", (0, 0, z_in))], f"{OUT}/vista_armada.png", elev=52, azim=-18)
render([(Vb, Fb, "#c8161d", (0, 0, 0)), (Vl, Fl, "#f4c430", (0, -30, 0))], f"{OUT}/vista_piezas.png", elev=55, azim=-12)
Vr = Vb.copy(); Vr[:, 0] *= -1; Vr[:, 2] = Vr[:, 2].max() - Vr[:, 2]; Fr = Fb
render([(Vr, Fr, "#c8161d", (0, 0, 0))], f"{OUT}/vista_atras.png", elev=70, azim=0, W=1200, H=750)
