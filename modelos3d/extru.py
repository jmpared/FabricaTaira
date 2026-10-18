"""Generador de sólidos por capas (2.5D) con malla mínima y estanca.
Cada pieza es una pila de 'losas' (z0, z1, campo SDF 2D). El contorno se extrae a nivel 0
con precisión sub-pixel, las paredes son verticales y las tapas se triangulan por recorte de orejas.
Supuesto: los contornos de losas vecinas no se cruzan (o coinciden o están anidados)."""
import numpy as np, struct, zipfile
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from skimage import measure
from matplotlib.path import Path

FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"

# ---------------------------------------------------------------- lienzo 2D
class Canvas:
    def __init__(self, w, h, res=0.02):
        self.w, self.h, self.res = w, h, res
        self.nx, self.ny = int(round(w / res)), int(round(h / res))
    def blank(self): return Image.new("L", (self.nx, self.ny), 0)
    def px(self, x, y): return ((x + self.w / 2) / self.res, (self.h / 2 - y) / self.res)
    def circle(self, img, x, y, r, fill=255):
        (a, b), (c, d) = self.px(x - r, y + r), self.px(x + r, y - r)
        ImageDraw.Draw(img).ellipse([a, b, c, d], fill=fill)
    def rrect(self, img, x, y, w, h, r, fill=255):
        (a, b), (c, d) = self.px(x - w / 2, y + h / 2), self.px(x + w / 2, y - h / 2)
        ImageDraw.Draw(img).rounded_rectangle([a, b, c, d], radius=r / self.res, fill=fill)
    def poly(self, img, pts, fill=255):
        ImageDraw.Draw(img).polygon([self.px(x, y) for x, y in pts], fill=fill)
    def text(self, img, s, x, y, cap_h, font=FONT, mirror=False, track=0.0, fill=255):
        """texto centrado en (x, y) con altura de mayúscula cap_h (mm); track = espacio extra entre letras (mm)"""
        ref = ImageFont.truetype(font, 400); hb = ref.getbbox("H"); k = cap_h / (hb[3] - hb[1])
        fs = max(10, int(round(400 * k / self.res)))
        f = ImageFont.truetype(font, fs); hb = f.getbbox("H")
        W = int(sum(f.getlength(ch) for ch in s) + track / self.res * len(s) + fs * 2)
        tmp = Image.new("L", (W, fs * 2), 0); d = ImageDraw.Draw(tmp); cx = fs // 2
        for ch in s:
            d.text((cx, 0), ch, font=f, fill=255); cx += f.getlength(ch) + track / self.res
        bb = tmp.getbbox()
        if not bb: return
        tmp = tmp.crop((bb[0], 0, bb[2], tmp.height))
        if mirror: tmp = tmp.transpose(Image.FLIP_LEFT_RIGHT)
        px, py = self.px(x, y)
        img.paste(fill, (int(px - tmp.width / 2), int(py - (hb[1] + hb[3]) / 2)), tmp)
    def text_width(self, s, cap_h, font=FONT, track=0.0):
        f = ImageFont.truetype(font, 400); hb = f.getbbox("H"); k = cap_h / (hb[3] - hb[1])
        tmp = Image.new("L", (int(sum(f.getlength(c) for c in s) + 800), 900), 0); d = ImageDraw.Draw(tmp); cx = 100
        for ch in s: d.text((cx, 0), ch, font=f, fill=255); cx += f.getlength(ch) + track / k
        bb = tmp.getbbox(); return (bb[2] - bb[0]) * k
    def sdf(self, img):
        m = np.asarray(img) > 127
        return (ndimage.distance_transform_edt(~m) - ndimage.distance_transform_edt(m)) * self.res

# operaciones sobre campos (negativo = adentro)
def union(*a): return np.minimum.reduce(a)
def inter(*a): return np.maximum.reduce(a)
def diff(a, *b): return np.maximum(a, -np.minimum.reduce(b))
def grow(a, t): return a - t       # agranda la forma t mm

# ---------------------------------------------------------------- contornos
def loops_of(field, cv, tol=0.006):
    f = np.pad(field, 2, constant_values=field.max() + 1)
    out = []
    for c in measure.find_contours(f, 0.0):
        if len(c) < 8 or np.abs(c[0] - c[-1]).max() > 1e-6: continue
        c = measure.approximate_polygon(c, tol / cv.res)[:-1]
        if len(c) < 3: continue
        x = (c[:, 1] - 2 + 0.5) * cv.res - cv.w / 2
        y = cv.h / 2 - (c[:, 0] - 2 + 0.5) * cv.res
        L = np.stack([x, y], 1)
        if abs(area(L)) < 1e-4: continue
        out.append(L)
    return out

def area(L):
    x, y = L[:, 0], L[:, 1]
    return 0.5 * (np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

def key(L): return (round(abs(area(L)), 4), round(L[:, 0].mean(), 3), round(L[:, 1].mean(), 3), len(L))

def nest(loops):
    """devuelve [(exterior CCW, [huecos CW])] según profundidad de anidamiento"""
    paths = [Path(L) for L in loops]
    depth = []
    for i, L in enumerate(loops):
        p = L[0]
        depth.append(sum(1 for j, P in enumerate(paths) if j != i and P.contains_point(p)))
    polys = []
    for i, L in enumerate(loops):
        if depth[i] % 2: continue
        outer = L if area(L) > 0 else L[::-1]
        holes = []
        for j, H in enumerate(loops):
            if depth[j] == depth[i] + 1 and paths[i].contains_point(H[0]):
                holes.append(H if area(H) < 0 else H[::-1])
        polys.append((outer, holes))
    return polys

# ---------------------------------------------------------------- triangulación (orejas + puentes)
def _bridge(outer, hole):
    m = int(np.argmax(hole[:, 0])); M = hole[m]
    best, bi, bx = None, -1, np.inf
    n = len(outer)
    for i in range(n):
        a, b = outer[i], outer[(i + 1) % n]
        if (a[1] - M[1]) * (b[1] - M[1]) > 0 or a[1] == b[1]: continue
        t = (M[1] - a[1]) / (b[1] - a[1]); x = a[0] + t * (b[0] - a[0])
        if x >= M[0] - 1e-12 and x < bx: bx, bi = x, i
    a, b = outer[bi], outer[(bi + 1) % n]
    pi = bi if a[0] > b[0] else (bi + 1) % n
    P = outer[pi]; I = np.array([bx, M[1]])
    # vértices reflejos dentro del triángulo M-I-P: elegir el de menor ángulo
    tri = Path([M, I, P]); cand = []
    for i in range(n):
        if i == pi: continue
        q = outer[i]
        if q[0] >= M[0] and tri.contains_point(q, radius=-1e-9):
            prv, nxt = outer[i - 1], outer[(i + 1) % n]
            u, w = q - prv, nxt - q
            if u[0] * w[1] - u[1] * w[0] <= 0:
                ang = abs(np.arctan2(q[1] - M[1], q[0] - M[0])); cand.append((ang, np.hypot(*(q - M)), i))
    if cand: pi = min(cand)[2]
    hole_seq = np.concatenate([hole[m:], hole[:m + 1]])
    return np.concatenate([outer[:pi + 1], hole_seq, outer[pi:]])

def earclip(outer, holes):
    from earcut import earcut
    pts = np.concatenate([outer] + list(holes)) if holes else outer
    data = pts.ravel().tolist(); hi = []; k = len(outer)
    for h in holes: hi.append(k); k += len(h)
    t = earcut(data, hi or None)
    tris = []
    for j in range(0, len(t), 3):
        a, b, c = t[j], t[j + 1], t[j + 2]
        A, B, C = pts[a], pts[b], pts[c]
        if (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0]) < 0: b, c = c, b
        tris.append((a, b, c))
    return pts, tris

# ---------------------------------------------------------------- pieza
class Stack:
    """slabs: lista de (z0, z1, campo) contiguas de abajo hacia arriba."""
    def __init__(self, cv): self.cv, self.slabs = cv, []
    def slab(self, z0, z1, field): self.slabs.append((z0, z1, field)); return self
    def mesh(self):
        cv = self.cv; V = []; F = []; vid = {}
        def v(x, y, z):
            k = (round(float(x), 6), round(float(y), 6), round(float(z), 6))
            if k not in vid: vid[k] = len(V); V.append(k)
            return vid[k]
        # contornos por losa, reutilizando los idénticos de la losa anterior
        L_by = []; prev = {}
        for z0, z1, f in self.slabs:
            cur = {}
            for L in loops_of(f, cv):
                k = key(L); cur[k] = prev.get(k, L)
            L_by.append(cur); prev = cur
        # paredes
        for (z0, z1, _), loops in zip(self.slabs, L_by):
            for k, L in loops.items():
                for poly in [L]:
                    pass
            for outer, holes in nest(list(loops.values())):
                for ring in [outer] + holes:
                    n = len(ring)
                    for i in range(n):
                        a, b = ring[i], ring[(i + 1) % n]
                        a0, b0, a1, b1 = v(*a, z0), v(*b, z0), v(*a, z1), v(*b, z1)
                        F.append((a0, b0, b1)); F.append((a0, b1, a1))
        # tapas
        levels = [(self.slabs[0][0], {}, L_by[0])]
        for i in range(len(self.slabs) - 1):
            levels.append((self.slabs[i][1], L_by[i], L_by[i + 1]))
        levels.append((self.slabs[-1][1], L_by[-1], {}))
        for z, below, above in levels:
            # región que mira hacia arriba = abajo \ arriba ; hacia abajo = arriba \ abajo
            sym = [L for k, L in below.items() if k not in above] + [L for k, L in above.items() if k not in below]
            if not sym: continue
            # signo: muestrear la losa de abajo para decidir orientación de cada polígono
            for outer, holes in nest(sym):
                pts, tris = earclip(outer, holes)
                c = interior_point(outer, holes)
                up = in_field(below, c) and not in_field(above, c)
                for a, b, cc in tris:
                    ia, ib, ic = v(*pts[a], z), v(*pts[b], z), v(*pts[cc], z)
                    F.append((ia, ib, ic) if up else (ia, ic, ib))
        V = np.array(V, float); F = np.array(F, int)
        F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
        V[:, 2] -= V[:, 2].min()
        return V, F

def interior_point(outer, holes):
    P = Path(outer); Hs = [Path(h) for h in holes]
    xs = np.linspace(outer[:, 0].min(), outer[:, 0].max(), 41)[1:-1]
    ys = np.linspace(outer[:, 1].min(), outer[:, 1].max(), 41)[1:-1]
    for y in ys[::-1][::2].tolist() + ys[::2].tolist():
        for x in xs:
            q = (x, y)
            if P.contains_point(q) and not any(h.contains_point(q) for h in Hs): return q
    return tuple(outer.mean(0))

def in_field(loops, q):
    """punto adentro del material definido por un conjunto de contornos (regla par/impar)"""
    return sum(Path(L).contains_point(q) for L in loops.values()) % 2 == 1

# ---------------------------------------------------------------- verificación y salida
def check(V, F):
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    s = np.sort(e, 1); _, cnt = np.unique(s, axis=0, return_counts=True)
    d, dc = np.unique(e, axis=0, return_counts=True)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6
    return {"estanca": bool((cnt == 2).all()), "orientada": bool((dc == 1).all()), "volumen_mm3": round(vol, 1), "triangulos": len(F)}

def write_stl(path, V, F):
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(b - a, c - a); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    data = np.zeros(len(F), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
    data["n"], data["a"], data["b"], data["c"] = n, a, b, c
    with open(path, "wb") as f:
        f.write(b"TAIRA 3D".ljust(80, b" ")); f.write(struct.pack("<I", len(F))); f.write(data.tobytes())

def write_3mf(path, parts, gap=5.0, bed=250):
    objs, items = [], []; x = y = rowh = 0.0
    for i, (name, V, F) in enumerate(parts, 1):
        V = V.copy(); V[:, 0] -= V[:, 0].min(); V[:, 1] -= V[:, 1].min()
        w, h = V[:, 0].max(), V[:, 1].max()
        if x + w > bed: x, y, rowh = 0.0, y + rowh + gap, 0.0
        V[:, 0] += x + 10; V[:, 1] += y + 10; x += w + gap; rowh = max(rowh, h)
        vs = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in V)
        ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in F)
        objs.append(f'<object id="{i}" name="{name}" type="model"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
        items.append(f'<item objectid="{i}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="es-AR" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
             + "".join(objs) + "</resources><build>" + "".join(items) + "</build></model>")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)

# ---------------------------------------------------------------- extras de dibujo
def _ellipse_pts(x, y, rx, ry, ang=0.0, n=96):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False); a = np.radians(ang)
    px, py = rx * np.cos(t), ry * np.sin(t)
    return list(zip(x + px * np.cos(a) - py * np.sin(a), y + px * np.sin(a) + py * np.cos(a)))

def ellipse(cv, img, x, y, rx, ry, ang=0.0, fill=255):
    cv.poly(img, _ellipse_pts(x, y, rx, ry, ang), fill)

def text_arc(cv, img, s, radius, cap_h, center=(0, 0), top=True, font=FONT, track=0.3, fill=255):
    """texto sobre un arco: arriba (se lee de izq. a der.) o abajo (también legible)."""
    ref = ImageFont.truetype(font, 400); hb = ref.getbbox("H"); k = cap_h / (hb[3] - hb[1])
    fs = max(10, int(round(400 * k / cv.res))); f = ImageFont.truetype(font, fs); hb = f.getbbox("H")
    widths = [f.getlength(ch) * cv.res + track for ch in s]
    total = sum(widths) - track
    r_mid = radius  # radio de la línea media de las mayúsculas
    ang = total / r_mid  # ángulo total
    a = (np.pi / 2 + ang / 2) if top else (-np.pi / 2 - ang / 2)
    for ch, w in zip(s, widths):
        da = (w - track / 2) / r_mid / 2 if False else (w - track) / r_mid / 2
        ac = a - da if top else a + da
        g = Image.new("L", (int(fs * 1.6), int(fs * 1.6)), 0)
        ImageDraw.Draw(g).text((g.width / 2, g.height / 2 - (hb[1] + hb[3]) / 2 + 0 + fs * 0), ch, font=f, fill=255, anchor="mt") if False else None
        d = ImageDraw.Draw(g); gw = f.getlength(ch)
        d.text((g.width / 2 - gw / 2, g.height / 2 - (hb[1] + hb[3]) / 2), ch, font=f, fill=255)
        rot = np.degrees(ac - np.pi / 2) if top else np.degrees(ac + np.pi / 2)
        g = g.rotate(rot, resample=Image.BICUBIC, expand=False)
        cx, cy = center[0] + r_mid * np.cos(ac), center[1] + r_mid * np.sin(ac)
        px, py = cv.px(cx, cy)
        img.paste(fill, (int(px - g.width / 2), int(py - g.height / 2)), g)
        a = a - (w / r_mid) if top else a + (w / r_mid)

def closing(cv, field, r):
    """redondea uniones (cierra entrantes) de radio r"""
    m = field <= r
    d = (ndimage.distance_transform_edt(~m) - ndimage.distance_transform_edt(m)) * cv.res
    return d + r
