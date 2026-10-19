from navkit import *
import sys
QUE = sys.argv[1:] or ["cartel", "bola", "etiquetas", "llaveros", "pino"]
blank = lambda c: c.blank()
def circ(c, x, y, r): m = c.blank(); c.circle(m, x, y, r); return c.sdf(m)

if "cartel" in QUE:
    for lang, l1, l2, sl in (("es", "PAPÁ NOEL", "¡PARÁ ACÁ!", "N03_cartel_papa_noel"), ("en", "SANTA", "STOP HERE!", "N03b_cartel_santa_stop_here")):
        c = Canvas(112, 176, res=0.05)
        bd = c.blank(); c.rrect(bd, 0, 50, 100, 56, 6)
        st = c.blank(); c.poly(st, [(-6, 22), (6, 22), (6, -62), (0, -78), (-6, -62)])
        S_board = c.sdf(bd); S_base = union(S_board, c.sdf(st))
        t = c.blank()
        cap1 = fit_cap(c, l1, 70, 10.0, track=1.4); c.text(t, l1, 0, 61, cap1, font=FB, track=1.4)
        cap2 = fit_cap(c, l2, 84, 12.0, track=1.4); c.text(t, l2, 0, 40, cap2, font=FB, track=1.4)
        for sx in (-1, 1): c.poly(t, star_pts(5.2, 2.2, cx=sx * 41, cy=61))
        S_rel = union(band(S_board, 1.6, 3.4), c.sdf(t))
        save(sl, "Cartel Papá Noel" if lang == "es" else "Santa Stop Here", "con estaca · 2 colores sin AMS",
             [(sl, flat2(c, S_base, S_rel))], [("#c8161d", "#fbf6ee"), ("#1e6b3a", "#f2c14e"), ("#fbf6ee", "#c8161d")])

if "bola" in QUE:
    c = Canvas(76, 92, res=0.04)
    b = c.blank(); c.circle(b, 0, -4, 33); c.rrect(b, 0, 31, 15, 9, 1.5); c.circle(b, 0, 38, 4.2)
    S_base = diff(c.sdf(b), circ(c, 0, 38, 1.9))
    S_ball = circ(c, 0, -4, 33)
    cap = c.blank(); c.rrect(cap, 0, 31, 13, 7, 1.2)
    deco = c.blank()
    for k in range(-3, 4):                       # guirnalda de puntitos abajo
        a = np.radians(-90 + k * 14); c.circle(deco, 26 * np.cos(a), -4 + 26 * np.sin(a), 1.6)
    for x, y, R in ((-17, 14, 4.2), (17, 14, 4.2), (0, 21, 3.0)): c.poly(deco, star_pts(R, R * 0.45, cx=x, cy=y))
    S_rel = union(band(S_ball, 1.4, 3.0), c.sdf(cap), c.sdf(deco))
    save("N04_bola_con_nombre", "Bola navideña", "lugar para el nombre · sin AMS", [("bola", flat2(c, S_base, S_rel))],
         [("#c8161d", "#f2c14e"), ("#1f3a5f", "#e8eef7"), ("#1e6b3a", "#fbf6ee")])

if "etiquetas" in QUE:
    for lang, a, b2, sl in (("es", "PARA:", "DE:", "N05_etiquetas_regalo"), ("en", "TO:", "FROM:", "N05b_gift_tags")):
        objs = []
        for forma in ("pino", "estrella", "regalo", "redonda"):
            c = Canvas(62, 70, res=0.04); s = c.blank()
            if forma == "pino":
                c.poly(s, [(-24, -26), (24, -26), (24, 14), (12, 26), (-12, 26), (-24, 14)])
            elif forma == "estrella": c.poly(s, star_pts(31, 15, cx=0, cy=-2))
            elif forma == "regalo": c.rrect(s, 0, -4, 50, 46, 4); c.circle(s, -6, 22, 6); c.circle(s, 6, 22, 6)
            else: c.circle(s, 0, -2, 28)
            S0 = closing(c, c.sdf(s), 1.5) if forma != "redonda" else c.sdf(s)
            S_base = diff(S0, circ(c, 0, 20 if forma != "regalo" else 8, 2.2) if forma != "regalo" else circ(c, 0, 22, 2.2))
            if forma == "regalo": S_base = diff(S0, circ(c, -6, 22, 2.2))
            t = c.blank(); y0 = -2 if forma != "pino" else -6
            cap = 4.2; c.text(t, a, -9 if lang == "es" else -12, y0 + 6, cap, font=FB, track=0.8)
            c.text(t, b2, -11 if lang == "es" else -10, y0 - 5, cap, font=FB, track=0.8)
            xs = 13 if forma != "estrella" else 9
            line(c, t, -2, y0 + 3.9, xs, y0 + 3.9, 1.2); line(c, t, -2 if lang == "es" else 2, y0 - 7.1, xs, y0 - 7.1, 1.2)
            if forma == "pino":
                for w, y in ((14, 13), (10, 18)): c.poly(t, [(-w / 2 + 14, y - 4), (w / 2 + 14, y - 4), (14, y + 3)])
            S_rel = union(band(S0, 1.2, 2.6), c.sdf(t))
            objs.append((f"{sl}_{forma}", flat2(c, S_base, S_rel)))
        save(sl, "Etiquetas para regalos" if lang == "es" else "Gift Tags", "set de 4 · 2 colores sin AMS", objs,
             [("#c8161d", "#fbf6ee"), ("#1e6b3a", "#f2c14e"), ("#fbf6ee", "#c8161d")])

if "llaveros" in QUE:
    objs = []
    # reno
    c = Canvas(56, 66, res=0.04); s = c.blank()
    ellipse(c, s, 0, -6, 12, 14); ellipse(c, s, -13, 2, 6, 3, 25); ellipse(c, s, 13, 2, 6, 3, -25)
    for sx in (-1, 1):
        line(c, s, sx * 5, 6, sx * 10, 20, 2.6); line(c, s, sx * 10, 20, sx * 9, 28, 2.4)
        line(c, s, sx * 10, 20, sx * 17, 26, 2.4); line(c, s, sx * 8, 15, sx * 15, 15, 2.4)
    line(c, s, 0, 6, 0, 30, 3.4); c.circle(s, 0, 31, 3.8)
    S0 = closing(c, c.sdf(s), 1.0); S_base = diff(S0, circ(c, 0, 31, 1.7))
    r = c.blank(); c.circle(r, 0, -15, 4.6); ellipse(c, r, -13, 2, 3.4, 1.4, 25); ellipse(c, r, 13, 2, 3.4, 1.4, -25)
    c.circle(r, -5, -3, 1.6); c.circle(r, 5, -3, 1.6)
    objs.append(("reno", flat2(c, S_base, c.sdf(r))))
    # papá noel
    c = Canvas(56, 70, res=0.04); s = c.blank()
    c.circle(s, 0, -2, 13)
    for x, y, rr in ((-9, -10, 7), (9, -10, 7), (0, -16, 9), (-4, -20, 6), (4, -20, 6)): c.circle(s, x, y, rr)
    c.poly(s, [(-13, 8), (13, 8), (5, 27)]); c.circle(s, 5, 28.5, 4.6); c.rrect(s, 0, 7, 32, 7, 3)
    S0 = closing(c, c.sdf(s), 1.0); S_base = diff(S0, circ(c, 5, 28.5, 1.7))
    h = c.blank(); c.poly(h, [(-11.5, 11.5), (11.5, 11.5), (4.6, 25.5)]); c.circle(h, 0, -5, 2.6)
    objs.append(("papa_noel", flat2(c, S_base, c.sdf(h))))
    save("N06_llaveros_reno_papa_noel", "Llaveros reno y Papá Noel", "2 colores sin AMS", objs,
         [[("#8b5a2b", "#c8161d"), ("#fbf6ee", "#c8161d")], [("#fbf6ee", "#c8161d"), ("#fbf6ee", "#c8161d")]])

if "pino" in QUE:
    objs = []
    for pieza in ("A", "B"):
        c = Canvas(96, 124, res=0.05); s = c.blank()
        for w, y in ((84, -22), (66, 4), (46, 28)): c.poly(s, [(-w / 2, y - 12), (w / 2, y - 12), (0, y + 22)])
        c.rrect(s, 0, -44, 14, 16, 1); c.rrect(s, 0, -51, 40, 6, 2)                 # tronco y pie
        S0 = closing(c, c.sdf(s), 1.2)
        sl = c.blank()
        if pieza == "A": c.rrect(sl, 0, 20, 3.7, 60, 0.3)       # ranura desde arriba hasta la mitad
        else: c.rrect(sl, 0, -40, 3.7, 60, 0.3)                 # ranura desde abajo hasta la mitad
        S_base = diff(S0, c.sdf(sl))
        d = c.blank()
        for x, y in ((-26, -24), (24, -20), (-14, 4), (17, 8), (-8, 26), (10, 30), (-32, -30), (31, -31)): c.circle(d, x, y, 2.8)
        c.poly(d, star_pts(5.5, 2.3, cx=0, cy=48))
        S_rel = c.sdf(d)
        objs.append((f"pino_{pieza}", flat2(c, S_base, inter(S_rel, -(c.sdf(sl) - 2.2)))))
    save("N07_pino_encastre", "Pino de encastre", "2 piezas que se cruzan · sin AMS", objs,
         [("#1e6b3a", "#f2c14e"), ("#fbf6ee", "#c8161d")], elev=60)
