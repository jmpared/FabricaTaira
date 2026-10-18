from shapes import *

def sitting_cat(cv, img, x, y, s=1.0):
    def P(px, py): return (x + px * s, y + py * s)
    ellipse(cv, img, *P(0, -4.0), 4.8 * s, 5.8 * s)
    cv.circle(img, *P(0, 2.8), 3.5 * s)
    cv.poly(img, [P(-3.3, 3.8), P(-2.5, 7.4), P(-0.6, 5.7)]); cv.poly(img, [P(3.3, 3.8), P(2.5, 7.4), P(0.6, 5.7)])
    ellipse(cv, img, *P(-2.0, -9.6), 2.2 * s, 1.1 * s); ellipse(cv, img, *P(2.0, -9.6), 2.2 * s, 1.1 * s)
    pts = [(3.8, -8.8), (6.4, -7.6), (7.6, -5.0), (7.4, -2.0)]
    for (a, b), (c2, d) in zip(pts, pts[1:]): line(cv, img, *P(a, b), *P(c2, d), 1.7 * s)

# ---------------- 20 chapita médica
c = Canvas(46, 52)
sq = c.blank(); c.rrect(sq, 0, -1.5, 36, 36, 7)
S_sq = c.sdf(sq)
lug = c.blank(); c.circle(lug, 0, 17.6, 4.2); hole = c.blank(); c.circle(hole, 0, 18.4, 1.9)
S_base = diff(union(S_sq, c.sdf(lug)), c.sdf(hole))
d = c.blank()
c.rrect(d, 0, 5.2, 4.6, 14.0, 0.8); c.rrect(d, 0, 5.2, 14.0, 4.6, 0.8)          # cruz
cap = fit_cap(c, "BRUNO", 26.0, 5.8)
c.text(d, "BRUNO", 0, -9.6, cap, track=1.3)
S_deco = union(band(S_sq, 1.1, 2.5), c.sdf(d))
S_back = back_text(c, [("NECESITO", 8.6, 2.4), ("MEDICACIÓN", 5.0, 2.4), ("DUEÑO 11 1234-5678", -0.4, 2.3), ("VET 11 8765-4321", -4.6, 2.3)])
r1 = build("20_chapita_medica", "Chapita médica", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(3, 1, 0),
           info=dict(titulo="Chapita médica con cruz para mascotas que toman medicación — 2 colores sin AMS", title_en="Medical alert pet tag with cross — 2 colors, no AMS",
                     desc="Pensada por un veterinario: chapita con cruz para perros y gatos que necesitan medicación (diabéticos, epilépticos, cardíacos). Atrás: 'Necesito medicación', teléfono del dueño y del veterinario. Cruz, borde y nombre encastrados en otro color (sugerido: blanco sobre rojo).",
                     desc_en="Designed by a vet: medical alert tag for pets on medication. Back: 'I need medication', owner's and vet's phone. Press-fit cross, border and name.",
                     tags="medical alert, chapita médica, medicación, diabetes, epilepsia, veterinario, pet tag, dog tag, perro, gato, multicolor, no AMS, press fit"))

# ---------------- 21 medalla gato
R = 17.0
c = Canvas(44, 50)
b = c.blank(); c.circle(b, 0, 0, R); c.circle(b, 0, R + 1.8, 4.6); c.rrect(b, 0, R - 1.0, 8, 6, 1.5)
hole = c.blank(); c.circle(hole, 0, R + 2.4, 1.9)
S_base = diff(c.sdf(b), c.sdf(hole))
ring = c.blank(); c.circle(ring, 0, 0, R - 1.1); c.circle(ring, 0, 0, R - 2.6, fill=0)
ct = c.blank(); sitting_cat(c, ct, -0.6, -1.4, 1.0)
S_cat = closing(c, c.sdf(ct), 0.5)
nm = c.blank(); text_arc(c, nm, "MICHI", 11.0, 3.9, top=True, track=1.6)
S_deco = union(c.sdf(ring), S_cat, c.sdf(nm))
S_back = back_text(c, [("11 1234-5678", 0, 3.2), ("LLAMÁ", -5.5, 2.6)], arc=[("SI ME PERDÍ", 12.2, 2.4)])
r2 = build("21_medalla_gato", "Medalla gato", "2 colores sin AMS · encastre a presión", c, S_base, S_deco, S_back, combos=(4, 3, 1),
           info=dict(titulo="Medalla redonda para gato con silueta y nombre — 2 colores sin AMS", title_en="Round cat tag with cat silhouette & curved name — 2 colors, no AMS",
                     desc="Medalla liviana para gatos: aro, silueta de gato sentado y nombre en arco encastrados en otro color. Teléfono grabado atrás.",
                     desc_en="Lightweight round cat tag with press-fit ring, sitting cat silhouette and curved name. Phone engraved on the back.",
                     tags="cat tag, gato, chapita, medalla, cat silhouette, pet tag, multicolor, no AMS, press fit"))
sheet([r1["covers"][0], r2["covers"][0], r1["covers"][1], r2["covers"][1]], "out/coleccion/vuelta_20_21.jpg")
