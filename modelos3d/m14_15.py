from shapes import *

# ---------------- 14 imán hueso
c = Canvas(108, 52, res=0.03)
b = c.blank()
c.rrect(b, 0, 0, 72, 24, 2)
for sx in (-1, 1):
    for sy in (-1, 1): c.circle(b, sx * 37.0, sy * 9.5, 11.0)
S_b = closing(c, c.sdf(b), 3.0)
d = c.blank()
c.text(d, "NO TE OLVIDES", 0, 4.4, 4.0, track=1.2)
c.text(d, "DEL PASEO", 0, -4.6, 5.4, track=1.5)
for sx in (-1, 1): paw(c, d, sx * 35.2, 0.4, 0.62)
S_deco = union(band(S_b, 1.4, 3.0), c.sdf(d))
mag = c.blank(); c.circle(mag, -22, 0, 5.15); c.circle(mag, 22, 0, 5.15)
r1 = build("14_iman_hueso_paseo", "Imán 'No te olvides del paseo'", "2 colores sin AMS · imán de 10×2 mm", c, S_b, S_deco, c.sdf(mag),
           combos=(0, 3, 2), base_h=4.4, back_d=2.1,
           info=dict(titulo="Imán de heladera hueso 'No te olvides del paseo' — 2 colores sin AMS", title_en="Bone fridge magnet 'Don't forget the walk' (Spanish) — 2 colors, no AMS",
                     desc="Imán de heladera con forma de hueso (95 mm) que recuerda el paseo diario. Letras, borde y huellas encastrados en otro color. Atrás tiene 2 huecos para imanes de neodimio de 10 × 2 mm (se pegan con una gota de cianoacrilato).",
                     desc_en="95 mm bone-shaped fridge magnet. Press-fit text, border and paws. Two pockets on the back for 10 × 2 mm neodymium magnets.",
                     tags="fridge magnet, imán, heladera, hueso, bone, paseo, dog walk, perro, humor, multicolor, no AMS, press fit"))

# ---------------- 15 señalador
c = Canvas(32, 88)
p = c.blank(); c.rrect(p, 0, 0, 26, 82, 4)
S_p = c.sdf(p)
hole = c.blank(); c.circle(hole, 0, 32.6, 1.8)
S_base = diff(S_p, c.sdf(hole))
d = c.blank()
for i, (x, y) in enumerate([(-3.2, -26), (3.2, -12), (-3.2, 2), (3.2, 16)]): paw(c, d, x, y, 0.72)
S_deco = union(band(S_p, 1.2, 2.6), c.sdf(d))
r2 = build("15_senalador_huellas", "Señalador huellas", "2 colores sin AMS · 26 × 82 mm", c, S_base, S_deco, None, combos=(4, 1, 2), base_h=2.4,
           info=dict(titulo="Señalador de libro con huellitas — 2 colores sin AMS", title_en="Paw prints bookmark — 2 colors, no AMS",
                     desc="Señalador de 26 × 82 mm con un caminito de huellas y borde encastrados en otro color. Agujero arriba para una borla o cinta. Regalo ideal para lectores con perro.",
                     desc_en="26 × 82 mm bookmark with a trail of press-fit paw prints and border. Hole for a tassel.",
                     tags="bookmark, señalador, paw prints, huellas, libro, book lover, dog lover, regalo, gift, multicolor, no AMS, press fit"))
sheet([r1["covers"][0], r2["covers"][0], r1["covers"][1], r2["covers"][1]], "out/coleccion/vuelta_14_15.jpg")
