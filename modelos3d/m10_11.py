from shapes import *
import math

def star(cv, img, x, y, ro, ri, rot=90):
    pts = []
    for k in range(10):
        r = ro if k % 2 == 0 else ri; a = math.radians(rot + k * 36)
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    cv.poly(img, pts)

def soften(cv, S, r): return -closing(cv, -closing(cv, S, r), r)

def hexagon(cv, img, x, y, r, rot=0):
    cv.poly(img, [(x + r * math.cos(math.radians(rot + 60 * k)), y + r * math.sin(math.radians(rot + 60 * k))) for k in range(6)])

# ---------------- 10 medalla estrella
R = 17.0
c = Canvas(44, 50)
b = c.blank(); c.circle(b, 0, 0, R); c.circle(b, 0, R + 1.8, 4.6); c.rrect(b, 0, R - 1.0, 8, 6, 1.5)
hole = c.blank(); c.circle(hole, 0, R + 2.4, 1.9)
S_base = diff(c.sdf(b), c.sdf(hole))
ring = c.blank(); c.circle(ring, 0, 0, R - 1.1); c.circle(ring, 0, 0, R - 2.6, fill=0)
st = c.blank(); star(c, st, 0, -2.6, 7.6, 3.5)
S_star = soften(c, c.sdf(st), 0.5)
nm = c.blank(); text_arc(c, nm, "COCO", 10.6, 3.6, top=True, track=1.5)
S_deco = union(c.sdf(ring), S_star, c.sdf(nm))
S_back = back_text(c, [("11 1234-5678", 0, 3.2), ("LLAMÁ", -5.5, 2.6)], arc=[("SI ME PERDÍ", 12.2, 2.4)])
r1 = build("10_medalla_estrella", "Medalla estrella", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(3, 0, 4),
           info=dict(titulo="Medalla redonda con estrella y nombre en arco — 2 colores sin AMS", title_en="Round pet tag with star & curved name — 2 colors, no AMS",
                     desc="Variante de la medalla clásica con una estrella grande en el centro. Aro, estrella y nombre encastrados en otro color.",
                     desc_en="Round 34 mm tag with a big star, ring and curved name press-fit in a second color.",
                     tags="pet tag, dog tag, star, estrella, chapita, medalla, perro, gato, multicolor, no AMS, press fit"))

# ---------------- 11 hexágono geométrico
c = Canvas(46, 50)
hx = c.blank(); hexagon(c, hx, 0, -1.0, 18.5, rot=0)
S_hx = soften(c, c.sdf(hx), 1.8)
lug = c.blank(); c.circle(lug, 0, 16.2, 4.0); hole = c.blank(); c.circle(hole, 0, 17.0, 1.9)
S_base = diff(union(S_hx, c.sdf(lug)), c.sdf(hole))
g = c.blank()
hexagon(c, g, 0, 1.4, 5.2, rot=30)                                                    # almohadilla hexagonal
for (x, y) in [(-7.4, 5.6), (-2.6, 9.2), (2.6, 9.2), (7.4, 5.6)]: hexagon(c, g, x, y, 2.05, rot=30)   # dedos
S_paw = soften(c, c.sdf(g), 0.35)
cap = fit_cap(c, "NALA", 15.0, 4.4)
nm = c.blank(); c.text(nm, "NALA", 0, -8.6, cap, track=1.3)
S_deco = union(band(S_hx, 1.1, 2.5), S_paw, c.sdf(nm))
S_back = back_text(c, [("SI ME PERDÍ, LLAMÁ", 2.4, 2.2), ("11 1234-5678", -2.4, 3.0)])
r2 = build("11_hexagono_geometrico", "Chapita hexágono", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(2, 4, 0),
           info=dict(titulo="Chapita hexagonal moderna con huella geométrica — 2 colores sin AMS", title_en="Modern hexagon pet tag with geometric paw — 2 colors, no AMS",
                     desc="Diseño moderno: hexágono con huella hecha de hexágonos, borde y nombre encastrados en otro color. Teléfono grabado atrás.",
                     desc_en="Modern hexagon tag with a geometric (hexagon) paw, border and name press-fit in a second color.",
                     tags="hexagon, geometric, modern, pet tag, dog tag, chapita, huella, perro, gato, multicolor, no AMS, press fit"))
sheet([r1["covers"][0], r2["covers"][0], r1["covers"][1], r2["covers"][1]], "out/coleccion/vuelta_10_11.jpg")
