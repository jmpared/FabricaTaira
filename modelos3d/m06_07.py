from shapes import *
import math

def star(cv, img, x, y, ro, ri, rot=90):
    pts = []
    for k in range(10):
        r = ro if k % 2 == 0 else ri; a = math.radians(rot + k * 36)
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    cv.poly(img, pts)

def heart(cv, img, x, y, s):
    r = s * 0.28
    cv.circle(img, x - r * 0.95, y + s * 0.12, r); cv.circle(img, x + r * 0.95, y + s * 0.12, r)
    cv.poly(img, [(x - r * 1.9, y + s * 0.03), (x + r * 1.9, y + s * 0.03), (x, y - s * 0.5)])

def soften(cv, S, r):  # redondea esquinas convexas y cóncavas
    return -closing(cv, -closing(cv, S, r), r)

# ---------------- 06 placa K9
c = Canvas(46, 52)
sh = c.blank()
c.poly(sh, [(-15.5, 14.5), (-7.5, 16.8), (0, 14.2), (7.5, 16.8), (15.5, 14.5), (16.5, 1.5), (12.8, -10.5), (0, -19.5), (-12.8, -10.5), (-16.5, 1.5)])
S_sh = soften(c, c.sdf(sh), 1.6)
lug = c.blank(); c.circle(lug, 0, 17.6, 4.0); hole = c.blank(); c.circle(hole, 0, 18.4, 1.9)
S_base = diff(union(S_sh, c.sdf(lug)), c.sdf(hole))
d = c.blank(); star(c, d, 0, 6.6, 3.3, 1.7)
S_star = soften(c, c.sdf(d), 0.45)
k9 = c.blank(); c.text(k9, "K9", 0, -0.9, 7.6, track=1.4)
cap = fit_cap(c, "MAX", 13.0, 3.9)
nm = c.blank(); c.text(nm, "MAX", 0, -8.0, cap, track=1.2)
S_deco = union(band(S_sh, 1.1, 2.5), S_star, c.sdf(k9), c.sdf(nm))
S_back = back_text(c, [("SI ME PERDÍ", 4.0, 2.4), ("LLAMÁ AL", 0.2, 2.4), ("11 1234-5678", -4.4, 3.0)])
r1 = build("06_placa_k9", "Placa K9", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(0, 3, 2),
           info=dict(titulo="Placa de policía K9 con nombre — 2 colores sin AMS", title_en="K9 police badge pet tag with name — 2 colors, no AMS",
                     desc="Chapita con forma de escudo policial: borde, estrella, 'K9' y el nombre encastrados en otro color. Para perros con actitud.",
                     desc_en="Police-badge shaped tag: border, star, 'K9' and name press-fit in a second color. For dogs with attitude.",
                     tags="K9, police dog, dog tag, badge, chapita, placa policía, perro, multicolor, no AMS, press fit, inlay, funny"))

# ---------------- 07 llavero huella con corazón
c = Canvas(44, 46)
s = 0.74
def pad(img):
    ellipse(c, img, 0, -5.5 * s, 12.0 * s, 8.6 * s)
    for x in (-6.2, 6.2): c.circle(img, x * s, -9.2 * s, 5.6 * s)
    c.circle(img, 0, -11.2 * s, 5.6 * s)
TOES = [(-12.8, 4.9, 30), (-4.7, 9.6, 9), (4.7, 9.6, -9), (12.8, 4.9, -30)]
def toes(img):
    for x, y, a in TOES: ellipse(c, img, x * s, y * s, 3.5 * s, 4.6 * s, a)
allm = c.blank(); pad(allm); toes(allm)
S_b = closing(c, grow(c.sdf(allm), 1.6), 2.6)
lug = c.blank(); c.circle(lug, 0, 12.6, 4.6); hole = c.blank(); c.circle(hole, 0, 12.8, 2.4)
S_base = diff(union(S_b, c.sdf(lug)), c.sdf(hole))
pm = c.blank(); pad(pm); tm = c.blank(); toes(tm)
hm = c.blank(); heart(c, hm, 0, -6.0, 8.0)
S_deco = union(diff(c.sdf(pm), grow(c.sdf(hm), 1.0)), c.sdf(tm))
S_back = back_text(c, [("MILO", -5.5, 4.2)])
r2 = build("07_llavero_huella", "Llavero huella", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(1, 0, 4),
           info=dict(titulo="Llavero huella con corazón — 2 colores sin AMS", title_en="Paw keychain with heart — 2 colors, no AMS",
                     desc="Llavero para dueños: huella con almohadilla y dedos encastrados en otro color y un corazón en el centro. Atrás, el nombre de tu mascota grabado.",
                     desc_en="Keychain for pet lovers: press-fit paw with a heart in the pad. Your pet's name engraved on the back.",
                     tags="keychain, llavero, paw, huella, heart, corazón, regalo, dog lover, multicolor, no AMS, press fit"))
sheet([r1["covers"][0], r2["covers"][0], r1["covers"][1], r2["covers"][1]], "out/coleccion/vuelta_06_07.jpg")
