from shapes import *
import math

def star(cv, img, x, y, ro, ri, rot=90):
    cv.poly(img, [(x + (ro if k % 2 == 0 else ri) * math.cos(math.radians(rot + k * 36)), y + (ro if k % 2 == 0 else ri) * math.sin(math.radians(rot + k * 36))) for k in range(10)])
def soften(cv, S, r): return -closing(cv, -closing(cv, S, r), r)
def heart(cv, img, x, y, s):
    r = s * 0.28
    cv.circle(img, x - r * 0.95, y + s * 0.12, r); cv.circle(img, x + r * 0.95, y + s * 0.12, r)
    cv.poly(img, [(x - r * 1.9, y + s * 0.03), (x + r * 1.9, y + s * 0.03), (x, y - s * 0.5)])

# ---------------- 16 escudo de club
c = Canvas(46, 54)
sh = c.blank()
c.poly(sh, [(-16, 17.5), (16, 17.5), (16.5, 2), (11, -11), (0, -20), (-11, -11), (-16.5, 2)])
S_sh = soften(c, c.sdf(sh), 2.0)
lug = c.blank(); c.circle(lug, 0, 19.6, 4.0); hole = c.blank(); c.circle(hole, 0, 20.4, 1.9)
S_base = diff(union(S_sh, c.sdf(lug)), c.sdf(hole))
d = c.blank()
c.text(d, "C.A.", 0, 2.0, 6.4, track=1.0)
cap = fit_cap(c, "TOBY", 16.0, 4.9)
c.text(d, "TOBY", 0, -7.3, cap, track=1.3)
st = c.blank(); star(c, st, 0, 10.2, 3.0, 1.45)
S_deco = union(band(S_sh, 1.1, 2.5), c.sdf(d), soften(c, c.sdf(st), 0.4))
S_back = back_text(c, [("SI ME PERDÍ, LLAMÁ", 3.0, 2.2), ("11 1234-5678", -1.6, 3.0)])
r1 = build("16_escudo_club", "Escudo de club", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(0, 3, 2),
           info=dict(titulo="Chapita escudo de club de fútbol 'C.A. + nombre' — 2 colores sin AMS", title_en="Football club crest pet tag with name — 2 colors, no AMS",
                     desc="Para el perro más hincha: escudo estilo club argentino con estrella, 'C.A.' y el nombre encastrados en otro color. Imprimilo con los colores de tu club.",
                     desc_en="Football-club crest pet tag (Argentine style) with star, 'C.A.' and name press-fit in a second color. Print it in your team's colors.",
                     tags="football, fútbol, club, escudo, crest, Argentina, pet tag, chapita, perro, hincha, multicolor, no AMS, press fit"))

# ---------------- 17 llavero ADOPTÁ
c = Canvas(80, 34)
p = c.blank(); c.rrect(p, 2.5, 0, 56, 24, 6)
lug = c.blank(); c.circle(lug, -27.5, 0, 6.0)
S_p = c.sdf(p)
hole = c.blank(); c.circle(hole, -28.0, 0, 2.4)
S_base = diff(closing(c, union(S_p, c.sdf(lug)), 2.0), c.sdf(hole))
d = c.blank()
cap = fit_cap(c, "ADOPTÁ", 32.0, 6.2, track=1.3)
c.text(d, "ADOPTÁ", -2.6, -1.2, cap, track=1.3)
heart(c, d, 21.4, 0.4, 8.2)
S_deco = union(band(S_p, 1.1, 2.4), c.sdf(d))
S_back = back_text(c, [("UN AMIGO", 3.0, 3.0), ("TE ESPERA", -2.6, 3.0)])
r2 = build("17_llavero_adopta", "Llavero ADOPTÁ", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(1, 3, 4),
           info=dict(titulo="Llavero 'ADOPTÁ' con corazón — 2 colores sin AMS", title_en="'ADOPT' keychain with heart (Spanish) — 2 colors, no AMS",
                     desc="Llavero para campañas de adopción y refugios: 'ADOPTÁ', corazón y borde encastrados en otro color. Atrás: 'Un amigo te espera'. Ideal para vender a beneficio.",
                     desc_en="Keychain for adoption campaigns and shelters: 'ADOPTÁ' (adopt), heart and border press-fit. Back: 'A friend is waiting for you'.",
                     tags="adopt, adopta, adopción, shelter, refugio, keychain, llavero, rescue, dog, cat, multicolor, no AMS, press fit"))
sheet([r1["covers"][0], r2["covers"][0], r1["covers"][1], r2["covers"][1]], "out/coleccion/vuelta_16_17.jpg")
