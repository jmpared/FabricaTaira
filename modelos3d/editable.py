"""Versión 'editable en Bambu Studio': corre un script de modelo sin el nombre ni el texto trasero
y con juego 0 (el juego lo pone Bambu Studio con la compensación X-Y del objeto encastres).
uso: python editable.py m01_02.py LUNA ROCKY ..."""
import sys, runpy
import extru, kit

SKIP = {s.upper() for s in sys.argv[2:]}
_text = extru.Canvas.text
def text(self, img, s, *a, **k):
    if s.upper() in SKIP: return img
    return _text(self, img, s, *a, **k)
extru.Canvas.text = text

kit.TOL = 0.0
_build = kit.build
def build(slug, title_es, sub_es, c, S_base, S_deco, S_back=None, **k):
    return _build(slug + "_editable", title_es, "nombre editable en Bambu Studio", c, S_base, S_deco, None, **k)
kit.build = build
runpy.run_path(sys.argv[1], run_name="__main__")
