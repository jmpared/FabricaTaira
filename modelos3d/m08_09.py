from shapes import *

def bone(cv, img, x, y, L, H):
    r = H * 0.3
    cv.rrect(img, x, y, L - 2 * r, H * 0.45, H * 0.1)
    for sx in (-1, 1):
        for sy in (-1, 1): cv.circle(img, x + sx * (L / 2 - r), y + sy * (H / 2 - r), r)

# ---------------- 08 cartel de cucha
c = Canvas(126, 46, res=0.04)
p = c.blank(); c.rrect(p, 0, 0, 120, 40, 5)
S_p = c.sdf(p)
holes = c.blank(); c.circle(holes, -52.0, 0, 1.9); c.circle(holes, 52.0, 0, 1.9)
S_base = diff(S_p, c.sdf(holes))
d = c.blank()
c.text(d, "CASA DE", 0, 10.2, 5.0, track=1.6)
cap = fit_cap(c, "ROCKY", 60, 14.0, track=1.6)
c.text(d, "ROCKY", 0, -4.2, cap, track=1.6)
bone(c, d, -40.5, 0, 12, 9); bone(c, d, 40.5, 0, 12, 9)
S_deco = union(band(S_p, 1.4, 3.2), c.sdf(d))
r1 = build("08_cartel_cucha", "Cartel para cucha", "2 colores sin AMS · 120 × 40 mm", c, S_base, S_deco, None, combos=(2, 0, 3),
           info=dict(titulo="Cartel para cucha 'CASA DE…' con nombre — 2 colores sin AMS", title_en="Dog house name sign 'HOME OF…' — 2 colors, no AMS",
                     desc="Cartel de 120 × 40 mm para la cucha o la puerta: borde, 'CASA DE', nombre y dos huesitos encastrados en otro color. Dos agujeros para tornillo.",
                     desc_en="120 × 40 mm sign for the dog house: border, text, name and two bones press-fit in a second color. Two screw holes.",
                     tags="dog house sign, cartel, cucha, nombre, perro, sign, multicolor, no AMS, press fit, inlay, home decor"))

# ---------------- 09 cartel cuidado perro cariñoso
c = Canvas(126, 66, res=0.04)
p = c.blank(); c.rrect(p, 0, 0, 120, 60, 6)
S_p = c.sdf(p)
holes = c.blank(); c.circle(holes, -53.0, 23.0, 1.9); c.circle(holes, 53.0, 23.0, 1.9)
S_base = diff(S_p, c.sdf(holes))
d = c.blank()
c.text(d, "¡CUIDADO!", 0, 15.0, 11.0, track=1.8)
c.text(d, "PERRO CARIÑOSO", 0, -1.0, 7.6, track=1.4)
c.text(d, "¡TE LLENA DE BESOS!", 0, -14.5, 4.2, track=0.9)
paw(c, d, -50.0, -17.5, 0.7); paw(c, d, 50.0, -17.5, 0.7)
S_deco = union(band(S_p, 1.4, 3.2), c.sdf(d))
r2 = build("09_cartel_perro_carinoso", "Cartel perro cariñoso", "2 colores sin AMS · 120 × 60 mm", c, S_base, S_deco, None, combos=(3, 1, 4),
           info=dict(titulo="Cartel '¡Cuidado! Perro cariñoso' — 2 colores sin AMS", title_en="Funny 'Beware: friendly dog' sign (Spanish) — 2 colors, no AMS",
                     desc="Cartel con humor para la puerta o el portón: '¡Cuidado! Perro cariñoso — te va a llenar de besos'. Letras, borde y huellas encastradas en otro color. Dos agujeros para tornillo.",
                     desc_en="Funny Spanish sign: 'Beware! Friendly dog — he will smother you with kisses'. Press-fit letters, border and paws. Two screw holes.",
                     tags="cartel perro, cuidado con el perro, beware of dog, funny sign, humor, puerta, multicolor, no AMS, press fit"))
sheet([r1["covers"][0], r2["covers"][0], r1["covers"][1], r2["covers"][1]], "out/coleccion/vuelta_08_09.jpg")
