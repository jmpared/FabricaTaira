from kit import *
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

def paw(cv, img, x, y, s=1.0):
    ellipse(cv, img, x, y - 1.2 * s, 4.9 * s, 3.9 * s)
    cv.circle(img, x - 3.0 * s, y - 0.6 * s, 2.6 * s); cv.circle(img, x + 3.0 * s, y - 0.6 * s, 2.6 * s); cv.circle(img, x, y - 2.9 * s, 2.4 * s)
    for dx, dy, a in [(-6.6, 4.6, 28), (-2.4, 7.4, 9), (2.4, 7.4, -9), (6.6, 4.6, -28)]:
        ellipse(cv, img, x + dx * s, y + dy * s, 1.4 * s, 1.85 * s, a)

def back_text(cv, lines):
    im = cv.blank()
    for txt, y, h in lines: cv.text(im, txt, 0, y, h, font=FB)
    return cv.sdf(im.transpose(Image.FLIP_LEFT_RIGHT))

def band(S, a, b):  # franja entre a y b mm hacia adentro del borde
    return inter(S + a, -(S + b))

# ---------------- 01 corazón
c = Canvas(48, 48)
h = c.blank(); c.circle(h, -7.8, 5.0, 9.6); c.circle(h, 7.8, 5.0, 9.6); c.poly(h, [(-17.2, 2.4), (17.2, 2.4), (0, -17.5)])
S_h = closing(c, c.sdf(h), 2.5)
lug = c.blank(); c.circle(lug, 0, 13.6, 4.0); hole = c.blank(); c.circle(hole, 0, 14.5, 1.9)
S_base = diff(union(S_h, c.sdf(lug)), c.sdf(hole))
nm = c.blank(); NOM = "LUNA"; cap = 5.4
while c.text_width(NOM, cap, track=1.2) > 20 and cap > 3.5: cap -= 0.1
c.text(nm, NOM, 0, 5.0, cap, track=1.2)
pw = c.blank(); paw(c, pw, 0, -5.4, 0.72)
S_deco = union(band(S_h, 1.1, 2.5), c.sdf(nm), c.sdf(pw))
S_back = back_text(c, [("SI ME PERDÍ", 4.0, 2.2), ("11 1234-5678", -0.6, 3.0), ("LLAMÁ", -5.0, 2.4)])
r1 = build("01_corazon", "Chapita corazón", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(1, 0, 4),
           info=dict(titulo="Chapita corazón con nombre y huella — 2 colores sin AMS", title_en="Heart pet tag with name & paw — 2 colors, no AMS",
                     desc="Chapita identificatoria con forma de corazón: borde, nombre y huellita encastrados en otro color. Atrás lleva el teléfono grabado.",
                     desc_en="Heart-shaped ID tag with press-fit border, name and paw in a second color. Phone number engraved on the back."))
print(r1["base"], r1["encastres"])

# ---------------- 02 hueso premium
c = Canvas(64, 36)
b = c.blank()
c.rrect(b, 0, 0, 30, 11.5, 1.0)
for sx in (-1, 1):
    for sy in (-1, 1): c.circle(b, sx * 15.2, sy * 5.0, 6.2)
S_b = closing(c, c.sdf(b), 2.2)
lug = c.blank(); c.circle(lug, -24.4, 0, 4.0); c.rrect(lug, -20.5, 0, 8, 5.5, 1.2)
hole = c.blank(); c.circle(hole, -25.2, 0, 1.9)
S_base = diff(union(S_b, c.sdf(lug)), c.sdf(hole))
nm = c.blank(); NOM = "ROCKY"; cap = 6.4
while c.text_width(NOM, cap, track=1.2) > 25 and cap > 3.5: cap -= 0.1
c.text(nm, NOM, 0, 0, cap, track=1.2)
dots = c.blank()
for sx in (-1, 1):
    for sy in (-1, 1): c.circle(dots, sx * 15.4, sy * 5.0, 1.3)
S_deco = union(band(S_b, 1.1, 2.4), c.sdf(nm), c.sdf(dots))
S_back = back_text(c, [("SI ME PERDÍ, LLAMÁ", 2.6, 2.2), ("11 1234-5678", -2.0, 3.0)])
r2 = build("02_hueso_premium", "Hueso premium", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(3, 0, 2),
           info=dict(titulo="Chapita hueso premium con nombre — 2 colores sin AMS", title_en="Premium bone pet tag with name — 2 colors, no AMS",
                     desc="Hueso con borde y nombre encastrados en otro color. Atrás, teléfono grabado. Ideal para perros medianos y grandes.",
                     desc_en="Bone tag with press-fit border and name in a second color. Phone engraved on the back."))
print(r2["base"], r2["encastres"])
sheet([r1["covers"][0], r2["covers"][0], r1["covers"][1], r2["covers"][1]], "out/coleccion/vuelta_01_02.jpg")
