from shapes import *

def sitting_cat(cv, img, x, y, s=1.0):
    def P(px, py): return (x + px * s, y + py * s)
    ellipse(cv, img, *P(0, -4.0), 4.8 * s, 5.8 * s)
    cv.circle(img, *P(0, 2.8), 3.5 * s)
    cv.poly(img, [P(-3.3, 3.8), P(-2.5, 7.4), P(-0.6, 5.7)]); cv.poly(img, [P(3.3, 3.8), P(2.5, 7.4), P(0.6, 5.7)])
    ellipse(cv, img, *P(-2.0, -9.6), 2.2 * s, 1.1 * s); ellipse(cv, img, *P(2.0, -9.6), 2.2 * s, 1.1 * s)
    pts = [(3.8, -8.8), (6.4, -7.6), (7.6, -5.0), (7.4, -2.0)]
    for (a, b), (c2, d) in zip(pts, pts[1:]): line(cv, img, *P(a, b), *P(c2, d), 1.7 * s)

def bone(cv, img, x, y, L, H):
    r = H * 0.3
    cv.rrect(img, x, y, L - 2 * r, H * 0.45, H * 0.1)
    for sx in (-1, 1):
        for sy in (-1, 1): cv.circle(img, x + sx * (L / 2 - r), y + sy * (H / 2 - r), r)

# ---------------- 22 cartel gato
c = Canvas(128, 68, res=0.04)
p = c.blank(); c.rrect(p, 0, 0, 120, 60, 6)
S_p = c.sdf(p)
holes = c.blank(); c.circle(holes, -53.0, 23.0, 1.9); c.circle(holes, 53.0, 23.0, 1.9)
S_base = diff(S_p, c.sdf(holes))
ct = c.blank(); sitting_cat(c, ct, -40.0, 2.0, 2.0)
S_cat = closing(c, c.sdf(ct), 0.8)
t = c.blank()
c.text(t, "AQUÍ VIVE", 16.0, 13.5, 7.2, track=1.6)
c.text(t, "UN GATO…", 16.0, 0.5, 7.2, track=1.6)
c.text(t, "Y SUS EMPLEADOS", 16.5, -13.0, 4.4, track=1.2)
S_deco = union(band(S_p, 1.4, 3.2), S_cat, c.sdf(t))
r1 = build("22_cartel_gato_empleados", "Cartel 'Aquí vive un gato'", "2 colores sin AMS · 120 × 60 mm", c, S_base, S_deco, None, combos=(4, 3, 2),
           info=dict(titulo="Cartel 'AQUÍ VIVE UN GATO… Y SUS EMPLEADOS' — 2 colores sin AMS", title_en="Funny 'A cat lives here… and its staff' sign (Spanish) — 2 colors, no AMS",
                     desc="Cartel con humor para la puerta: 'Aquí vive un gato… y sus empleados', con silueta de gato. Letras, borde y gato encastrados en otro color. Dos agujeros para tornillo.",
                     desc_en="Funny Spanish door sign: 'A cat lives here… and its staff', with cat silhouette. Press-fit text, border and cat.",
                     tags="cat sign, cartel gato, humor, funny, puerta, door sign, cat lover, regalo, multicolor, no AMS, press fit"))

# ---------------- 23 plaquita plato
c = Canvas(90, 36)
p = c.blank(); c.rrect(p, 0, 0, 80, 28, 7)
S_p = c.sdf(p)
d = c.blank()
c.text(d, "COMIDA DE", 0, 6.4, 4.0, track=1.3)
cap = fit_cap(c, "TOBY", 40.0, 8.4, track=1.6)
c.text(d, "TOBY", 0, -4.0, cap, track=1.6)
bone(c, d, -29.5, 0, 11, 8); bone(c, d, 29.5, 0, 11, 8)
S_deco = union(band(S_p, 1.2, 2.6), c.sdf(d))
r2 = build("23_plaquita_plato", "Plaquita para el plato", "2 colores sin AMS · 80 × 28 mm", c, S_p, S_deco, None, combos=(0, 2, 1),
           info=dict(titulo="Plaquita 'COMIDA DE ____' para el plato o el tacho de alimento — 2 colores sin AMS", title_en="'FOOD OF ____' bowl / food bin label (Spanish) — 2 colors, no AMS",
                     desc="Plaquita de 80 × 28 mm para pegar con cinta doble faz en el plato, el comedero o el tacho de alimento. Letras, borde y huesitos encastrados en otro color.",
                     desc_en="80 × 28 mm label for the bowl or food bin (stick with double-sided tape). Press-fit text, border and bones.",
                     tags="dog bowl label, plato, comedero, alimento, food bin, nombre, perro, gato, multicolor, no AMS, press fit"))
sheet([r1["covers"][0], r2["covers"][0], r1["covers"][1], r2["covers"][1]], "out/coleccion/vuelta_22_23.jpg")
