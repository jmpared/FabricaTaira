import os, numpy as np
from extru import *
from shapes import line
from cover import shot, title
import kit

def star_pts(R, r, n=5, rot=90, cx=0, cy=0):
    return [(cx + (R if i % 2 == 0 else r) * np.cos(np.radians(rot + i * 180 / n)), cy + (R if i % 2 == 0 else r) * np.sin(np.radians(rot + i * 180 / n))) for i in range(2 * n)]

def star3d(R, r, t, n=5):
    """estrella facetada 3D en el plano XZ (parada), centro en el origen"""
    ring = [(x, 0.0, z) for x, z in star_pts(R, r, n)]
    V = np.array(ring + [(0, -t, 0), (0, t, 0)], float); k = len(ring); F = []
    for i in range(k):
        j = (i + 1) % k
        F.append((i, j, k)); F.append((j, i, k + 1))
    return V, np.array(F)

def save(slug, titulo, sub, parts, combos, elev=30, azim=-25, objname=None, flip=False):
    out = f"out/navidad/{slug}"; os.makedirs(out, exist_ok=True)
    for _, V, F in parts:
        k = check(V, F); assert k["estanca"] and k["orientada"], (slug, k)
    write_3mf_assembled(f"{out}/{slug}.3mf", parts, name=slug)
    covers = []
    for n, cols in enumerate(combos):
        img = shot([((V * np.array([1, -1, -1]) if flip else V), F, c, (0, 0, 0)) for (_, V, F), c in zip(parts, cols)], elev=elev, azim=azim, margin=0.14 if n else 0.2, dy=60 if n == 0 else 0)
        if n == 0: img = title(img, titulo, sub)
        p = f"{out}/portada{'' if n == 0 else '_' + str(n + 1)}.jpg"; img.convert("RGB").save(p, quality=92); covers.append(p)
    return covers

# ---------------- arbolito apilable de escritorio
LAY, H = 16, 3.0
c = Canvas(100, 100, res=0.06)
tree = Stack(c)
for i in range(LAY):
    R = 38 - i * 2.2; r = R * 0.55
    im = c.blank(); c.poly(im, star_pts(R, r, n=8, rot=90 + i * 5.0))
    S = c.sdf(im)
    if i == 0: S = union(S, c.sdf((lambda m: (c.circle(m, 0, 0, 14), m)[1])(c.blank())))
    S = closing(c, S, 0.8)
    if i: S = inter(S, grow(prev, 0.3))   # sin voladizos: cada piso queda adentro del de abajo
    prev = S
    tree.slab(i * H, (i + 1) * H, S)
Vt, Ft = tree.mesh(); Vt = Vt.copy(); Vt[:, 2] -= Vt[:, 2].min()
top = Vt[:, 2].max()
Vs, Fs = star3d(9.5, 4.0, 3.2)
Vs[:, 2] += top + 9.5 * 0.81 - 1.0      # la punta de abajo entra 1 mm en el árbol
cx, cy = (Vt[:, 0].max() + Vt[:, 0].min()) / 2, (Vt[:, 1].max() + Vt[:, 1].min()) / 2
Vs[:, 0] += cx; Vs[:, 1] += cy
cov = save("N01_arbolito_escritorio", "Arbolito de escritorio", "apilable · 2 colores sin AMS",
           [("árbol (color 1)", Vt, Ft), ("estrella (color 2)", Vs, Fs)],
           [("#1e6b3a", "#f2c14e"), ("#f4f1ea", "#d4af37"), ("#0f3d2e", "#e63946")], elev=158, azim=-20)
print("arbolito", Vt[:, 0].max() - Vt[:, 0].min(), "x", top + 2 * 9.5 * 0.9, "mm")

# ---------------- copos de nieve (6) para colgar
def flake(cv, im, kind, w=1.6):
    for k in range(6):
        a = np.radians(90 + 60 * k); u = np.array([np.cos(a), np.sin(a)]); nrm = np.array([-u[1], u[0]])
        P = lambda d, s=0: (u * d + nrm * s)
        line(cv, im, 0, 0, *P(30), w)
        if kind == 0:
            for d, L in ((12, 7), (20, 6), (26, 3.5)):
                for s in (-1, 1): line(cv, im, *P(d), *(P(d) + (u * 0.55 + nrm * s * 0.83) * L), w)
        elif kind == 1:
            for d, L in ((14, 9), (23, 5)):
                for s in (-1, 1): line(cv, im, *P(d), *(P(d) + (u * 0.5 + nrm * s * 0.87) * L), w)
            cv.circle(im, *P(30), 2.2)
        elif kind == 2:
            cv.poly(im, [tuple(P(16)), tuple(P(21, 3.5)), tuple(P(26)), tuple(P(21, -3.5))])
            for s in (-1, 1): line(cv, im, *P(9), *(P(9) + (u * 0.5 + nrm * s * 0.87) * 6), w)
        elif kind == 3:
            for d in (10, 18, 25):
                for s in (-1, 1): line(cv, im, *P(d), *P(d + 3, s * (8 - d * 0.22)), w)
        elif kind == 4:
            line(cv, im, *P(14, -7), *P(14, 7), w); line(cv, im, *P(22, -4.5), *P(22, 4.5), w)
            cv.circle(im, *P(30), 2.0)
        else:
            for d, L in ((8, 5), (15, 8), (22, 6), (27, 3)):
                for s in (-1, 1): line(cv, im, *P(d), *(P(d) + (u * 0.6 + nrm * s * 0.8) * L), w)
    cv.circle(im, 0, 0, 6.5)

NOMBRES = ["Cristal", "Estrella", "Diamante", "Helecho", "Escarcha", "Pino"]
FC = []
for kind in range(6):
    c = Canvas(78, 82, res=0.04)
    im = c.blank(); flake(c, im, kind, w=2.2)
    S = c.sdf(im)
    loop = c.blank(); c.circle(loop, 0, 33.5, 3.6); hole = c.blank(); c.circle(hole, 0, 33.5, 1.7)
    S_base = diff(union(S, c.sdf(loop)), c.sdf(hole))
    S_rel = union(grow(S, -0.6), c.sdf((lambda m: (c.circle(m, 0, 0, 4.2), m)[1])(c.blank())))
    S_rel = inter(S_rel, -c.sdf((lambda m: (c.circle(m, 0, 33.5, 3.0), m)[1])(c.blank())))
    b = Stack(c); b.slab(0, 3.2, S_base); Vb, Fb = b.mesh(); Vb = Vb.copy(); Vb[:, 2] -= Vb[:, 2].min()
    d = Stack(c); d.slab(0, 0.8, S_rel); Vd, Fd = d.mesh(); Vd = Vd.copy(); Vd[:, 2] += 3.2 - Vd[:, 2].min()
    slug = f"N02_copo_{kind + 1}_{NOMBRES[kind].lower()}"
    cov = save(slug, f"Copo de nieve «{NOMBRES[kind]}»", "adorno · 2 colores sin AMS",
               [("copo (color 1)", Vb, Fb), ("relieve (color 2)", Vd, Fd)],
               [("#dfe9f5", "#3a7bd5"), ("#1f3a5f", "#e8eef7"), ("#c0c6cc", "#d4af37")], elev=55, azim=-12)
    FC.append(cov[1])
kit.sheet(FC, "out/navidad/copos_set.jpg", cols=3, w=600)
print("ok")
