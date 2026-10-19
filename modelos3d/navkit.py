import os, zipfile, numpy as np
from extru import *
from shapes import line, band, fit_cap
from cover import shot, title
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
BASE, REL = 3.2, 0.8

def zfix(V, z0=0.0):
    V = V.copy(); V[:, 2] += z0 - V[:, 2].min(); return V

def flat2(c, S_base, S_rel, base=BASE, rel=REL):
    b = Stack(c); b.slab(0, base, S_base); Vb, Fb = b.mesh()
    d = Stack(c); d.slab(0, rel, inter(S_rel, S_base)); Vd, Fd = d.mesh()
    return [("base (color 1)", zfix(Vb), Fb), ("relieve (color 2)", zfix(Vd, base), Fd)]

def profile_stack(c, z0, z1, dz, field_at):
    """apila losas finas: field_at(z_medio) -> campo 2D"""
    s = Stack(c); zs = np.arange(z0, z1 + 1e-9, dz)
    if zs[-1] < z1 - 1e-6: zs = np.append(zs, z1)
    for a, b in zip(zs[:-1], zs[1:]): s.slab(a, b, field_at((a + b) / 2))
    V, F = s.mesh(); return zfix(V, z0), F

def star_pts(R, r, n=5, rot=90, cx=0, cy=0):
    return [(cx + (R if i % 2 == 0 else r) * np.cos(np.radians(rot + i * 180 / n)), cy + (R if i % 2 == 0 else r) * np.sin(np.radians(rot + i * 180 / n))) for i in range(2 * n)]

def star3d(R, r, t, n=5):
    ring = [(x, 0.0, z) for x, z in star_pts(R, r, n)]
    V = np.array(ring + [(0, -t, 0), (0, t, 0)], float); k = len(ring); F = []
    for i in range(k):
        j = (i + 1) % k; F.append((i, j, k)); F.append((j, i, k + 1))
    return V, np.array(F)

def tube(ro, ri, z0, z1, n=96):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False); V = []
    for r in (ro, ri):
        for z in (z0, z1): V += [(r * np.cos(t), r * np.sin(t), z) for t in a]
    V = np.array(V); ob, ot, ib, it = 0, n, 2 * n, 3 * n; F = []
    for i in range(n):
        j = (i + 1) % n
        F += [(ob + i, ob + j, ot + j), (ob + i, ot + j, ot + i)]       # pared exterior
        F += [(ib + i, it + j, ib + j), (ib + i, it + i, it + j)]       # pared interior
        F += [(ot + i, ot + j, it + j), (ot + i, it + j, it + i)]       # anillo de arriba
        F += [(ob + i, ib + j, ob + j), (ob + i, ib + i, ib + j)]       # anillo de abajo
    return V, np.array(F)

def _rows(objs, bed=240, gap=8):
    out = []; x = y = rowh = 0.0
    for name, parts in objs:
        allV = np.vstack([V for _, V, _ in parts]); mn, mx = allV.min(0), allV.max(0); w, h = mx[0] - mn[0], mx[1] - mn[1]
        if x + w > bed: x, y, rowh = 0.0, y + rowh + gap, 0.0
        off = np.array([x + 8 - mn[0], y + 8 - mn[1], -mn[2]]); x += w + gap; rowh = max(rowh, h)
        out.append((name, [(pn, V + off, F) for pn, V, F in parts]))
    return out

def write_multi(path, objs):
    """varios objetos, cada uno con sus partes montadas"""
    res, items, nid = [], [], 1
    for name, parts in _rows(objs):
        comps = []
        for pn, V, F in parts:
            vs = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in V)
            ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in F)
            res.append(f'<object id="{nid}" name="{pn}" type="model"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
            comps.append(f'<component objectid="{nid}"/>'); nid += 1
        res.append(f'<object id="{nid}" name="{name}" type="model"><components>{"".join(comps)}</components></object>')
        items.append(f'<item objectid="{nid}"/>'); nid += 1
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="es-AR" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
             + "".join(res) + "</resources><build>" + "".join(items) + "</build></model>")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)

def save(slug, titulo, sub, objs, combos, elev=55, azim=-14, render_objs=None):
    """objs: [(nombre, [(parte, V, F), ...])]. Si hay un solo objeto, 1 objeto con partes."""
    out = f"out/navidad/{slug}"; os.makedirs(out, exist_ok=True)
    for _, parts in objs:
        for pn, V, F in parts:
            k = check(V, F); assert k["estanca"] and k["orientada"], (slug, pn, k)
    write_multi(f"{out}/{slug}.3mf", objs)
    laid = _rows(render_objs or objs, gap=10)
    for n, cols in enumerate(combos):
        per = isinstance(cols[0], tuple)
        L = [(V, F, (cols[j % len(cols)] if per else cols)[i % 2], (0, 0, 0)) for j, (_, parts) in enumerate(laid) for i, (_, V, F) in enumerate(parts)]
        img = shot(L, elev=elev, azim=azim, margin=0.14 if n else 0.2, dy=60 if n == 0 else 0)
        if n == 0: img = title(img, titulo, sub)
        img.convert("RGB").save(f"{out}/portada{'' if n == 0 else '_' + str(n + 1)}.jpg", quality=92)
    print(slug, "ok")

def panel(c, field, thick, y0, zoff):
    """extruye una silueta dibujada en el plano (x, z) y la para vertical: grosor en Y desde y0"""
    s = Stack(c); s.slab(0, thick, field); V, F = s.mesh()
    V = V.copy(); V[:, 2] -= V[:, 2].min()
    W = np.column_stack([V[:, 0], V[:, 2] + y0, V[:, 1] + zoff])
    return W, F[:, ::-1].copy()

def rot90z(V, k=1):
    for _ in range(k): V = np.column_stack([-V[:, 1], V[:, 0], V[:, 2]])
    return V

def merge(*meshes):
    Vs, Fs, n = [], [], 0
    for V, F in meshes: Vs.append(V); Fs.append(F + n); n += len(V)
    return np.vstack(Vs), np.vstack(Fs)
