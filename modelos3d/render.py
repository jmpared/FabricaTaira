"""Rasterizador por software con z-buffer (sin dependencias) para verificar mallas y hacer portadas."""
import numpy as np
from PIL import Image

def _rot(elev, azim):
    a, e = np.radians(azim), np.radians(elev)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    return Rx @ Rz

def render(parts, path, elev=55, azim=-25, W=1200, H=900, bg=(242, 239, 232), light=(-0.35, 0.45, 0.82), margin=0.08, ssaa=2, transparent=False):
    """parts: [(V, F, color_hex, offset)] ; vista ortográfica. elev=90 -> desde arriba."""
    R = _rot(90 - elev, azim)
    W2, H2 = W * ssaa, H * ssaa
    allP = []
    for V, F, col, off in parts:
        allP.append((V + np.array(off, float)) @ R.T)
    P = np.vstack(allP); mn, mx = P.min(0), P.max(0)
    sc = min(W2 * (1 - 2 * margin) / (mx[0] - mn[0]), H2 * (1 - 2 * margin) / (mx[1] - mn[1]))
    cx, cy = (mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2
    zbuf = np.full((H2, W2), -np.inf); img = np.zeros((H2, W2, 3)); img[:] = np.array(bg) / 255
    L = np.array(light, float); L /= np.linalg.norm(L)
    zall = np.concatenate([(V + np.array(off, float))[:, 2] for V, F, col, off in parts]); zmin, zmax = zall.min(), zall.max() + 1e-9
    for (V, F, col, off), Q in zip(parts, allP):
        zf = ((V + np.array(off, float))[:, 2][F].mean(1) - zmin) / (zmax - zmin)
        c = np.array([int(col[i:i + 2], 16) for i in (1, 3, 5)]) / 255
        X = (Q[:, 0] - cx) * sc + W2 / 2; Y = H2 / 2 - (Q[:, 1] - cy) * sc; Z = Q[:, 2]
        a, b, d = Q[F[:, 0]], Q[F[:, 1]], Q[F[:, 2]]
        n = np.cross(b - a, d - a); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        vis = n[:, 2] > 1e-6
        Hh = L + np.array([0, 0, 1.0]); Hh /= np.linalg.norm(Hh)
        spec = np.clip(n @ Hh, 0, 1) ** 40 * 0.35
        k = (0.40 + 0.52 * np.clip(n @ L, 0, 1) + 0.10 * np.clip(n[:, 2], 0, 1)) * (0.74 + 0.26 * zf)
        for t in np.nonzero(vis)[0]:
            i0, i1, i2 = F[t]
            xs = np.array([X[i0], X[i1], X[i2]]); ys = np.array([Y[i0], Y[i1], Y[i2]]); zs = np.array([Z[i0], Z[i1], Z[i2]])
            x0, x1 = int(max(0, np.floor(xs.min()))), int(min(W2 - 1, np.ceil(xs.max())))
            y0, y1 = int(max(0, np.floor(ys.min()))), int(min(H2 - 1, np.ceil(ys.max())))
            if x1 < x0 or y1 < y0: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(den) < 1e-12: continue
            w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
            w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
            w2 = 1 - w0 - w1
            m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not m.any(): continue
            z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            m &= z > sub
            sub[m] = z[m]
            img[y0:y1 + 1, x0:x1 + 1][m] = c * k[t] + spec[t]
    rgb = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    alpha = (np.isfinite(zbuf) * 255).astype(np.uint8)
    im = Image.fromarray(np.dstack([rgb, alpha]), "RGBA").resize((W, H), Image.LANCZOS)
    if path: (im if path.endswith('.png') and transparent else im.convert('RGB')).save(path)
    return im
