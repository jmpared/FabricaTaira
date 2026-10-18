from shapes import *

# ---------------- 02b medalla redonda (rehecha)
R = 17.0
c = Canvas(44, 50)
b = c.blank(); c.circle(b, 0, 0, R); c.circle(b, 0, R + 1.8, 4.6); c.rrect(b, 0, R - 1.0, 8, 6, 1.5)
hole = c.blank(); c.circle(hole, 0, R + 2.4, 1.9)
S_base = diff(c.sdf(b), c.sdf(hole))
ring = c.blank(); c.circle(ring, 0, 0, R - 1.1); c.circle(ring, 0, 0, R - 2.6, fill=0)
pw = c.blank(); paw(c, pw, 0, -3.6, 0.95)
nm = c.blank(); text_arc(c, nm, "LOLA", 10.4, 3.8, top=True, track=1.0)
S_deco = union(c.sdf(ring), c.sdf(pw), c.sdf(nm))
S_back = back_text(c, [("11 1234-5678", 0, 3.2), ("LLAMÁ", -5.5, 2.6)], arc=[("SI ME PERDÍ", 12.2, 2.4)])
r1 = build("03_medalla_redonda", "Medalla con nombre", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(0, 3, 2),
           info=dict(titulo="Medalla redonda con huella y nombre en arco — 2 colores sin AMS", title_en="Round pet tag with paw & curved name — 2 colors, no AMS",
                     desc="Medalla clásica de 34 mm con aro, huella y nombre en arco encastrados en otro color. Atrás: 'Si me perdí, llamá' y teléfono.",
                     desc_en="Classic 34 mm round tag with press-fit ring, paw and curved name. Back: phone number engraved."))

# ---------------- 02b chapita huella (rehecha)
c = Canvas(56, 56)
def pad(img):
    ellipse(c, img, 0, -5.5, 12.0, 8.6)
    for x in (-6.2, 6.2): c.circle(img, x, -9.2, 5.6)
    c.circle(img, 0, -11.2, 5.6)
TOES = [(-12.8, 4.9, 30), (-4.7, 9.6, 9), (4.7, 9.6, -9), (12.8, 4.9, -30)]
def toes(img):
    for x, y, a in TOES: ellipse(c, img, x, y, 3.5, 4.6, a)
allm = c.blank(); pad(allm); toes(allm)
S_b = closing(c, grow(c.sdf(allm), 2.0), 3.2)
lug = c.blank(); c.circle(lug, 0, 16.0, 4.3); hole = c.blank(); c.circle(hole, 0, 16.0, 1.9)
S_base = diff(union(S_b, c.sdf(lug)), c.sdf(hole))
pm = c.blank(); pad(pm); S_pad = c.sdf(pm)
tm = c.blank(); toes(tm)
cap = fit_cap(c, "MILO", 17.0, 6.0)
nm = c.blank(); c.text(nm, "MILO", 0, -6.6, cap, track=1.2)
S_deco = union(band(S_pad, 0, 1.3), c.sdf(tm), c.sdf(nm))
S_back = back_text(c, [("SI ME PERDÍ, LLAMÁ", -1.2, 2.0), ("11 1234-5678", -6.0, 3.0)])
r2 = build("04_chapita_huella", "Chapita huella", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(1, 4, 0),
           info=dict(titulo="Chapita con forma de huella y nombre — 2 colores sin AMS", title_en="Paw-shaped pet tag with name — 2 colors, no AMS",
                     desc="Chapita con forma de huella: dedos, contorno de la almohadilla y nombre encastrados en otro color. Teléfono grabado atrás.",
                     desc_en="Paw-shaped ID tag: toes, pad outline and name press-fit in a second color. Phone engraved on the back."))

# ---------------- 05 cabeza de gato
c = Canvas(48, 52)
f = c.blank(); ellipse(c, f, 0, -2, 17.5, 14.5)
c.poly(f, [(-16.5, 3.0), (-13.5, 19.5), (-3.5, 11.0)]); c.poly(f, [(16.5, 3.0), (13.5, 19.5), (3.5, 11.0)])
S_f = closing(c, c.sdf(f), 1.6)
S_f = -closing(c, -S_f, 1.0)  # redondear puntas de orejas
lug = c.blank(); c.circle(lug, 0, 13.6, 3.9); hole = c.blank(); c.circle(hole, 0, 14.2, 1.8)
S_base = diff(union(S_f, c.sdf(lug)), c.sdf(hole))
d = c.blank()
c.poly(d, [(-13.2, 7.0), (-12.3, 15.6), (-7.0, 10.6)]); c.poly(d, [(13.2, 7.0), (12.3, 15.6), (7.0, 10.6)])   # orejas internas
ellipse(c, d, -6.0, 2.6, 2.4, 3.1); ellipse(c, d, 6.0, 2.6, 2.4, 3.1)                                      # ojos
c.poly(d, [(-1.8, -0.6), (1.8, -0.6), (0, -2.6)])                                                          # nariz
for sx in (-1, 1):
    line(c, d, sx * 4.8, -2.4, sx * 13.0, -1.7, 1.1)
    line(c, d, sx * 4.8, -4.3, sx * 12.4, -5.6, 1.1)
S_ear_eye = c.sdf(d)
cap = fit_cap(c, "SIMBA", 22.5, 4.4, track=1.0)
nm = c.blank(); c.text(nm, "SIMBA", 0, -9.5, cap, track=1.0)
S_deco = union(S_ear_eye, c.sdf(nm))
S_back = back_text(c, [("SI ME PERDÍ, LLAMÁ", 0.5, 2.2), ("11 1234-5678", -4.6, 3.0)])
r3 = build("05_cabeza_gato", "Chapita gato", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(3, 4, 1),
           info=dict(titulo="Chapita cabeza de gato con nombre — 2 colores sin AMS", title_en="Cat head pet tag with name — 2 colors, no AMS",
                     desc="Chapita para gatos con forma de cabeza: orejas, ojos, nariz, bigotes y nombre encastrados en otro color. Liviana (3,2 mm).",
                     desc_en="Cat-head ID tag: ears, eyes, nose, whiskers and name press-fit in a second color. Lightweight."),
           )
sheet([r1["covers"][0], r2["covers"][0], r3["covers"][0], r3["covers"][1]], "out/coleccion/vuelta_03_05.jpg")
