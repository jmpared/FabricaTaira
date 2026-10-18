"""Versión 'una sola pieza con partes': base + decoración en relieve, montadas, sin nombres ni texto trasero.
uso: python ensamblado.py m01_02.py [más scripts]"""
import sys, os, runpy, numpy as np
import extru, kit
from extru import Stack, check, write_3mf_assembled, inter, Image
from cover import shot, title

NOMBRES = {"LUNA", "ROCKY", "LOLA", "MILO", "SIMBA", "MAX", "COCO", "NALA", "KIRA", "TOBY", "BRUNO", "MICHI"}
RELIEVE = 0.8   # alto de la parte decorativa sobre la base (4 capas de 0,2)

_text = extru.Canvas.text
def text(self, img, s, *a, **k):
    return img if s.upper() in NOMBRES else _text(self, img, s, *a, **k)
extru.Canvas.text = text
_arc = extru.text_arc
def text_arc(cv, img, s, *a, **k):
    return img if s.upper() in NOMBRES else _arc(cv, img, s, *a, **k)
extru.text_arc = kit.text_arc = text_arc

def build(slug, title_es, sub_es, c, S_base, S_deco, S_back=None, combos=(0, 1, 2), info=None, elev=58, azim=-14,
          base_h=kit.BASE_H, back_d=kit.BACK_D, **_):
    out = f"out/ensamblados/{slug}"; os.makedirs(out, exist_ok=True)
    base = Stack(c)
    if S_back is not None and back_d > 0.5:          # huecos para imán: se conservan
        base.slab(0, back_d, extru.diff(S_base, S_back)); base.slab(back_d, base_h, S_base)
    else:
        base.slab(0, base_h, S_base)
    Vb, Fb = base.mesh(); kb = check(Vb, Fb)
    deco = Stack(c); deco.slab(0, RELIEVE, inter(S_deco, S_base))
    Vd, Fd = deco.mesh(); kd = check(Vd, Fd)
    Vd = Vd.copy(); Vd[:, 2] += base_h - Vd[:, 2].min()
    Vb = Vb.copy(); Vb[:, 2] -= Vb[:, 2].min()
    assert kb["estanca"] and kb["orientada"] and kd["estanca"] and kd["orientada"], (slug, kb, kd)
    write_3mf_assembled(f"{out}/{slug}.3mf", [("base (color 1)", Vb, Fb), ("relieve (color 2)", Vd, Fd)], name=slug)
    covers = []
    for n, ci in enumerate(combos):
        c1, c2 = kit.COMBOS[ci]
        img = shot([(Vb, Fb, c1, (0, 0, 0)), (Vd, Fd, c2, (0, 0, 0))], elev=elev, azim=azim, margin=0.2 if n == 0 else 0.16, dy=60 if n == 0 else 0)
        if n == 0: img = title(img, title_es, "una pieza · 2 partes para elegir color")
        p = f"{out}/portada{'' if n == 0 else '_' + str(n + 1)}.jpg"; img.convert("RGB").save(p, quality=92); covers.append(p)
    size = (np.ptp(Vb[:, 0]), np.ptp(Vb[:, 1]))
    g = (kb["volumen_mm3"] + kd["volumen_mm3"]) / 1000 * 1.24
    open(f"{out}/makerworld.md", "w").write(f"""# {(info or {}).get('titulo', title_es).split(' — ')[0]}

{(info or {}).get('desc', '')}

- Una sola pieza con 2 partes ya montadas: base (color 1) y relieve (color 2).
- Sin AMS: cambio de filamento en la capa donde empieza el relieve ({base_h:.1f} mm).
- Medida {size[0]:.0f} × {size[1]:.0f} mm · base {base_h} mm + relieve {RELIEVE} mm · ~{g:.1f} g.
- Lugar libre para agregar el nombre con la herramienta de texto de Bambu Studio.
""")
    print(slug, "OK", kb["triangulos"], kd["triangulos"])
    return {"slug": slug, "base": kb, "encastres": kd, "covers": covers, "out": out}

kit.build = build
kit.sheet = lambda *a, **k: None
for s in sys.argv[1:]:
    runpy.run_path(s, run_name="__main__")
