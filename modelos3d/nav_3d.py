from navkit import *
import sys
QUE = sys.argv[1:] or ["estrella", "servilletero", "farolito"]

if "estrella" in QUE:
    Vs, Fs = star3d(40, 20, 12, n=6); Vs[:, 2] += 75
    Vt, Ft = tube(13, 10.2, 0, 45)
    save("N08_estrella_punta_arbol", "Estrella para el árbol", "punta 3D facetada · 2 colores", [("estrella_punta", [("estrella (color 1)", Vs, Fs), ("tubo (color 2)", Vt, Ft)])],
         [("#d4af37", "#1e6b3a"), ("#e8e8e8", "#c8161d"), ("#c8161d", "#f2c14e")], elev=158, azim=-25)

if "servilletero" in QUE:
    c = Canvas(132, 110, res=0.06)          # plano (x, z): z = y + 52
    sil = c.blank()
    for zb, za, wb in [(16, 52, 56), (40, 76, 43), (63, 97, 29)]: c.poly(sil, [(-wb, zb - 52), (0, za - 52), (wb, zb - 52), (0, zb - wb * 0.9 - 52)])   # abajo en V: sin voladizos
    c.rrect(sil, 0, -52 - 20 + 3, 300, 40, 0, fill=0)   # recorte por debajo de z=3
    S = c.sdf(sil)
    for x, z in ((-30, 22), (28, 26), (-14, 34), (12, 48), (-20, 50), (18, 62), (-6, 66), (6, 80)): S = diff(S, c.sdf((lambda m: (c.circle(m, x, z - 52, 2.6), m)[1])(c.blank())))
    low = c.blank(); c.rrect(low, 0, -52 - 40 + 10, 200, 80, 0); L = c.sdf(low)
    S_lo, S_hi = inter(S, L), diff(S, L)
    cb = Canvas(130, 60, res=0.1); bm = cb.blank(); cb.rrect(bm, 0, 0, 122, 52, 4)
    sb = Stack(cb); sb.slab(0, 4, cb.sdf(bm)); Vb, Fb = sb.mesh(); Vb = zfix(Vb)
    lo = merge((Vb, Fb), panel(c, S_lo, 4, -22, 52), panel(c, S_lo, 4, 18, 52))
    hi = merge(panel(c, S_hi, 4, -22, 52), panel(c, S_hi, 4, 18, 52))
    save("N09_servilletero_pinos", "Servilletero de pinos", "cambio de color a los 10 mm", [("servilletero", [("base y troncos (color 1)", *lo), ("pinos (color 2)", *hi)])],
         [("#fbf6ee", "#1e6b3a"), ("#8b5a2b", "#2d6a4f"), ("#c8161d", "#fbf6ee")], elev=150, azim=-30)

if "farolito" in QUE:
    c = Canvas(70, 80, res=0.06)            # plano (x, z): z = y + 35, paredes de 70 mm
    def arch(m, x, z0, w, h):               # abertura con arco arriba
        c.rrect(m, x, z0 + (h - w / 2) / 2 - 35, w, h - w / 2, 0); c.circle(m, x, z0 + h - w / 2 - 35, w / 2)
    def wall(width, kind):
        m = c.blank(); c.rrect(m, 0, 0, width, 70, 0.5)
        if kind == "puerta": arch((m, None)[0], 0, -1, 24, 44) if False else None
        S = c.sdf(m); h = c.blank()
        if kind == "puerta": arch(h, 0, -1, 24, 44)
        else:
            arch(h, 0, 26, 18, 27)
        return diff(S, c.sdf(h))
    front = panel(c, wall(64, "puerta"), 4, -32, 35)
    back = panel(c, wall(64, "ventana"), 4, 28, 35)
    side = panel(c, wall(57, "ventana"), 4, -2, 35)
    sR = side[0].copy(); sR = rot90z(sR, 1); sR[:, 0] += 30           # pared derecha
    sL = side[0].copy(); sL = rot90z(sL, 3); sL[:, 0] -= 30           # pared izquierda
    walls = merge(front, back, (sR, side[1]), (sL, side[1]))
    def pyramid_shell(so, si, z0, h):
        hi = h - (so - si) * h / so
        P = lambda q, zz: [(-q, -q, z0), (q, -q, z0), (q, q, z0), (-q, q, z0)]
        V = np.array(P(so, 0) + [(0, 0, z0 + h)] + P(si, 0) + [(0, 0, z0 + hi)], float); F = []
        for i in range(4):
            j = (i + 1) % 4
            F.append((i, j, 4))                    # exterior
            F.append((5 + j, 5 + i, 9))            # interior (invertido)
            F += [(i, 5 + i, 5 + j), (i, 5 + j, j)]  # anillo de abajo
        return V, np.array(F)
    V2, F2 = pyramid_shell(33, 28.5, 70, 30)
    k = check(V2, F2)
    if k["volumen_mm3"] < 0: F2 = F2[:, ::-1].copy()
    save("N10_farolito_vela_led", "Farolito para vela LED", "casita · se apoya sobre la vela", [("farolito", [("casita (color 1)", *walls), ("techo (color 2)", V2, F2)])],
         [("#fbf6ee", "#c8161d"), ("#1e6b3a", "#f2c14e"), ("#222222", "#fbf6ee")], elev=150, azim=-35)
