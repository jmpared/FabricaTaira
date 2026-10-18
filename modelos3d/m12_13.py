from shapes import *

def heart(cv, img, x, y, s):
    r = s * 0.28
    cv.circle(img, x - r * 0.95, y + s * 0.12, r); cv.circle(img, x + r * 0.95, y + s * 0.12, r)
    cv.poly(img, [(x - r * 1.9, y + s * 0.03), (x + r * 1.9, y + s * 0.03), (x, y - s * 0.5)])

# ---------------- 12 medalla corazón
R = 17.0
c = Canvas(44, 50)
b = c.blank(); c.circle(b, 0, 0, R); c.circle(b, 0, R + 1.8, 4.6); c.rrect(b, 0, R - 1.0, 8, 6, 1.5)
hole = c.blank(); c.circle(hole, 0, R + 2.4, 1.9)
S_base = diff(c.sdf(b), c.sdf(hole))
ring = c.blank(); c.circle(ring, 0, 0, R - 1.1); c.circle(ring, 0, 0, R - 2.6, fill=0)
hm = c.blank(); heart(c, hm, 0, -2.2, 15.0)
S_heart = closing(c, c.sdf(hm), 1.0)
nm = c.blank(); text_arc(c, nm, "KIRA", 10.6, 3.6, top=True, track=1.5)
S_deco = union(c.sdf(ring), S_heart, c.sdf(nm))
S_back = back_text(c, [("11 1234-5678", 0, 3.2), ("LLAMÁ", -5.5, 2.6)], arc=[("SI ME PERDÍ", 12.2, 2.4)])
r1 = build("12_medalla_corazon", "Medalla corazón", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(1, 4, 0),
           info=dict(titulo="Medalla redonda con corazón y nombre en arco — 2 colores sin AMS", title_en="Round pet tag with heart & curved name — 2 colors, no AMS",
                     desc="Variante de la medalla clásica con un corazón grande en el centro. Aro, corazón y nombre encastrados en otro color.",
                     desc_en="Round 34 mm tag with a big heart, ring and curved name press-fit in a second color.",
                     tags="pet tag, dog tag, heart, corazón, chapita, medalla, perro, gato, multicolor, no AMS, press fit, gift"))

# ---------------- 13 posavasos huella
c = Canvas(96, 96, res=0.04)
p = c.blank(); c.circle(p, 0, 0, 45.0)
S_p = c.sdf(p)
pw = c.blank(); paw(c, pw, 0, -3.0, 3.3)
S_deco = union(band(S_p, 2.0, 4.5), c.sdf(pw))
r2 = build("13_posavasos_huella", "Posavasos huella", "2 colores sin AMS · Ø 90 mm", c, S_p, S_deco, None, combos=(2, 3, 1), base_h=4.0,
           info=dict(titulo="Posavasos con huella — 2 colores sin AMS", title_en="Paw print coaster — 2 colors, no AMS",
                     desc="Posavasos de 90 mm con aro y huella encastrados en otro color. Ideal para regalar de a 4 en colores combinados. Sugerencia: pegá 4 patitas de goma abajo.",
                     desc_en="90 mm coaster with press-fit ring and paw print. Great as a gift set of 4. Add rubber feet underneath.",
                     tags="coaster, posavasos, paw, huella, dog lover, regalo, gift, home, multicolor, no AMS, press fit"))
sheet([r1["covers"][0], r2["covers"][0], r1["covers"][1], r2["covers"][1]], "out/coleccion/vuelta_12_13.jpg")
