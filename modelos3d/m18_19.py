from shapes import *

def sitting_dog(cv, img, x, y, s=1.0):
    """silueta geométrica de perro sentado mirando a la derecha (altura ~ 40*s)"""
    def P(px, py): return (x + px * s, y + py * s)
    ellipse(cv, img, *P(0, -6), 9.5 * s, 12.5 * s, -8)                 # cuerpo
    cv.circle(img, *P(-4.5, -13.5), 7.5 * s)                            # cadera
    cv.circle(img, *P(5.5, 12.5), 6.6 * s)                              # cabeza
    ellipse(cv, img, *P(11.5, 10.6), 4.4 * s, 3.0 * s, -10)             # hocico
    cv.poly(img, [P(1.2, 15.5), P(0.4, 23.5), P(6.5, 17.8)])            # oreja
    cv.poly(img, [P(1.0, 6.0), P(9.5, 7.0), P(8.0, -4.0), P(1.0, -3.0)])   # cuello/pecho
    cv.rrect(img, *P(6.2, -13.0), 3.6 * s, 14 * s, 1.6 * s)             # pata delantera
    ellipse(cv, img, *P(8.4, -19.6), 4.0 * s, 1.8 * s)                  # pie delantero
    ellipse(cv, img, *P(-1.0, -20.0), 6.5 * s, 2.0 * s)                 # pie trasero
    cv.poly(img, [P(-10.5, -15.0), P(-15.5, -10.0), P(-14.0, -8.8), P(-9.5, -12.5)])   # cola

# ---------------- 18 cartel caca
c = Canvas(128, 88, res=0.04)
p = c.blank(); c.rrect(p, 0, 0, 120, 80, 7)
S_p = c.sdf(p)
holes = c.blank(); c.circle(holes, -52.5, 33, 2.0); c.circle(holes, 52.5, 33, 2.0)
S_base = diff(S_p, c.sdf(holes))
dg = c.blank(); sitting_dog(c, dg, -34.0, 0.0, 1.25)
S_dog = closing(c, c.sdf(dg), 1.2)
t = c.blank()
c.text(t, "ACÁ NO", 20.0, 17.0, 9.0, track=1.6)
c.text(t, "SE HACE", 20.0, 1.0, 9.0, track=1.6)
c.text(t, "CACA", 20.0, -17.0, 12.0, track=2.0)
S_deco = union(band(S_p, 1.6, 3.6), S_dog, c.sdf(t))
r1 = build("18_cartel_caca", "Cartel 'Acá no se hace caca'", "2 colores sin AMS · 120 × 80 mm", c, S_base, S_deco, None, combos=(2, 3, 0),
           info=dict(titulo="Cartel 'ACÁ NO SE HACE CACA' con perro — 2 colores sin AMS", title_en="Funny 'No pooping here' dog sign (Spanish) — 2 colors, no AMS",
                     desc="Cartel con humor para la vereda, el jardín o el palier: 'ACÁ NO SE HACE CACA' con silueta de perro sentado. Letras, borde y perro encastrados en otro color. Dos agujeros para tornillo o precinto.",
                     desc_en="Funny Spanish sign 'No pooping here' with a sitting dog silhouette. Press-fit text, border and dog. Two holes for screws or zip ties.",
                     tags="cartel, perro, caca, no pooping, dog sign, humor, funny, jardín, vereda, multicolor, no AMS, press fit"))

# ---------------- 19 imán terapia
c = Canvas(104, 54, res=0.03)
p = c.blank(); c.rrect(p, 0, 0, 96, 45, 6)
S_p = c.sdf(p)
d = c.blank()
c.text(d, "MI PERRO ES", 0, 7.0, 5.2, track=1.2)
c.text(d, "MI TERAPIA", 0, -6.2, 6.6, track=1.3)
for sx in (-1, 1): paw(c, d, sx * 37.4, 0.4, 0.66)
S_deco = union(band(S_p, 1.4, 3.0), c.sdf(d))
mag = c.blank(); c.circle(mag, -20, 0, 5.15); c.circle(mag, 20, 0, 5.15)
r2 = build("19_iman_terapia", "Imán 'Mi perro es mi terapia'", "2 colores sin AMS · imán de 10×2 mm", c, S_p, S_deco, c.sdf(mag),
           combos=(1, 0, 4), base_h=4.4, back_d=2.1,
           info=dict(titulo="Imán 'MI PERRO ES MI TERAPIA' — 2 colores sin AMS", title_en="'My dog is my therapy' fridge magnet (Spanish) — 2 colors, no AMS",
                     desc="Imán de heladera de 96 × 45 mm con la frase 'Mi perro es mi terapia' y huellitas encastradas en otro color. Atrás, 2 huecos para imanes de neodimio de 10 × 2 mm.",
                     desc_en="96 × 45 mm fridge magnet: 'My dog is my therapy' (Spanish) with press-fit paws. Two pockets for 10 × 2 mm magnets.",
                     tags="fridge magnet, imán, heladera, terapia, therapy, dog lover, regalo, gift, frase, multicolor, no AMS, press fit"))
sheet([r1["covers"][0], r2["covers"][0], r1["covers"][1], r2["covers"][1]], "out/coleccion/vuelta_18_19.jpg")
