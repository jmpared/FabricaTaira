"""Armado estándar de un modelo de la colección: base + encastres, verificación, 3MF, portadas y texto MakerWorld."""
import os, numpy as np
from PIL import Image
from extru import *
from cover import shot, title

TOL = 0.15
BASE_H, POCKET_D, INS_H, BACK_D = 3.2, 1.6, 2.0, 0.4
COMBOS = [("#1f3a5f", "#f2c14e"), ("#e2557f", "#fbf6ee"), ("#2d6a4f", "#f4a261"), ("#222222", "#e63946"), ("#6c4ab6", "#ffd166")]

def build(slug, title_es, sub_es, c, S_base, S_deco, S_back=None, combos=(0, 1, 2), info=None, elev=58, azim=-14, base_h=BASE_H):
    out = f"out/coleccion/{slug}"; os.makedirs(out, exist_ok=True)
    print(slug, 'zonas finas (pared, encastre):', thin_check(c, S_base, S_deco, img_path=f'{out}/_control_paredes.png'))
    margen = float(S_base[grow(S_deco, TOL) < 0].max())
    assert margen < -0.7, f'{slug}: un hueco queda a {-margen:.2f} mm del borde (mínimo 0.7)'
    base = Stack(c)
    top0 = base_h - POCKET_D
    if S_back is not None:
        base.slab(0, BACK_D, diff(S_base, S_back)); base.slab(BACK_D, top0, S_base)
    else:
        base.slab(0, top0, S_base)
    base.slab(top0, base_h, diff(S_base, grow(S_deco, TOL)))
    Vb, Fb = base.mesh(); kb = check(Vb, Fb)
    ins = Stack(c); ins.slab(0, 0.25, grow(S_deco, -0.2)); ins.slab(0.25, INS_H, S_deco)
    Vi, Fi = ins.mesh(); ki = check(Vi, Fi)
    if not (ki["estanca"] and ki["orientada"]):
        print(slug, ': bisel del encastre con contornos coincidentes -> encastre sin bisel')
        ins = Stack(c); ins.slab(0, INS_H, S_deco); Vi, Fi = ins.mesh(); ki = check(Vi, Fi)
    assert kb["estanca"] and kb["orientada"] and ki["estanca"] and ki["orientada"], (kb, ki)
    write_3mf(f"{out}/{slug}_plato1_base.3mf", [("base", Vb, Fb)])
    write_3mf(f"{out}/{slug}_plato2_encastres.3mf", [("encastres", Vi, Fi)])
    covers = []
    for n, ci in enumerate(combos):
        c1, c2 = COMBOS[ci]
        img = shot([(Vb, Fb, c1, (0, 0, 0)), (Vi, Fi, c2, (0, 0, top0))], elev=elev, azim=azim, margin=0.2 if n == 0 else 0.16, dy=60 if n == 0 else 0)
        if n == 0: img = title(img, title_es, sub_es)
        p = f"{out}/portada{'' if n == 0 else '_' + str(n + 1)}.jpg"; img.convert("RGB").save(p, quality=92); covers.append(p)
    c1, c2 = COMBOS[combos[0]]
    w = Vb[:, 0].max() - Vb[:, 0].min()
    shot([(Vb, Fb, c1, (0, 0, 0)), (Vi, Fi, c2, (w + 6, 0, 0))], elev=60, azim=-8).convert("RGB").save(f"{out}/piezas.jpg", quality=90)
    if S_back is not None:
        Vr = Vb.copy(); Vr[:, 0] *= -1; Vr[:, 2] = Vr[:, 2].max() - Vr[:, 2]
        shot([(Vr, Fb, c1, (0, 0, 0))], elev=75, azim=0).convert("RGB").save(f"{out}/atras.jpg", quality=90)
    # estimaciones
    g1, g2 = kb["volumen_mm3"] / 1000 * 1.24, ki["volumen_mm3"] / 1000 * 1.24
    t1, t2 = 5 + kb["volumen_mm3"] / 9 / 60, 4 + ki["volumen_mm3"] / 6 / 60
    size = (Vb[:, 0].max() - Vb[:, 0].min(), Vb[:, 1].max() - Vb[:, 1].min())
    info = info or {}
    md = f"""# {info.get('titulo', title_es)}

**EN:** {info.get('title_en', '')}

## Descripción
{info.get('desc', '')}

- Multicolor **sin AMS**: cada color es una pieza aparte que se encastra a presión (sin pegamento).
- Plato 1: base (color 1). Plato 2: encastres (color 2).
- Medida: {size[0]:.0f} × {size[1]:.0f} mm, espesor {base_h} mm.
- Juego de encastre: {TOL} mm. Si te queda flojo o duro, avisá en comentarios y subo otra variante.

## Description (EN)
{info.get('desc_en', '')}

- Multicolor **without AMS**: each color is a separate part that press-fits (no glue).
- Plate 1: base (color 1). Plate 2: inlays (color 2). Size {size[0]:.0f} × {size[1]:.0f} mm.

## Ajustes sugeridos
- Capa 0,2 mm · 3 paredes · relleno 15 % · sin soportes.
- Base boca arriba con planchado (ironing) en la cara superior.
- Encastres planos; si son chicos, borde (brim) fino o primera capa lenta.

## Estimado (P2S)
- Base: ~{t1:.0f} min · ~{g1:.1f} g
- Encastres: ~{t2:.0f} min · ~{g2:.1f} g

## Etiquetas
{info.get('tags', 'pet tag, dog tag, chapita, mascota, perro, gato, multicolor, no AMS, press fit, inlay, regalo')}
"""
    open(f"{out}/makerworld.md", "w").write(md)
    return {"slug": slug, "base": kb, "encastres": ki, "covers": covers, "out": out}

def sheet(paths, dest, cols=2, w=800):
    ims = [Image.open(p).convert("RGB") for p in paths]
    h = int(w * ims[0].height / ims[0].width); rows = (len(ims) + cols - 1) // cols
    S = Image.new("RGB", (cols * w, rows * h), (245, 241, 234))
    for i, im in enumerate(ims): S.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
    S.save(dest, quality=90); return dest

def thin_check(c, S_base, S_deco, min_wall=0.9, min_feat=0.85, img_path=None):
    """cuenta pixeles de cresta con grosor menor al mínimo (paredes de base / encastres)"""
    from scipy import ndimage
    mat = (S_base < 0) & ~(grow(S_deco, TOL) < 0); ins = S_deco < 0
    out = []
    for m, th in ((mat, min_wall), (ins, min_feat)):
        d = ndimage.distance_transform_edt(m) * c.res * 2
        mx = ndimage.maximum_filter(d, size=5); r = (d >= mx - 1e-9) & m & (d > 0.05) & (d < th)
        out.append(r)
    if img_path:
        img = np.full(mat.shape + (3,), 245, np.uint8); img[mat] = (200, 60, 90); img[ins] = (230, 230, 230)
        img[ndimage.binary_dilation(out[0], iterations=6)] = (0, 0, 255); img[ndimage.binary_dilation(out[1], iterations=6)] = (255, 140, 0)
        Image.fromarray(img).resize((600, int(600 * mat.shape[0] / mat.shape[1]))).save(img_path)
    return int(out[0].sum()), int(out[1].sum())
