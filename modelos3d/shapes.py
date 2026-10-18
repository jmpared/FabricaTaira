"""Formas reutilizables de la colección."""
from kit import *
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

def paw(cv, img, x, y, s=1.0):
    """huella con dedos bien separados (paredes ≥ 0.9 mm a escala ≥ 0.7)"""
    ellipse(cv, img, x, y - 1.2 * s, 4.9 * s, 3.9 * s)
    cv.circle(img, x - 3.0 * s, y - 0.6 * s, 2.6 * s); cv.circle(img, x + 3.0 * s, y - 0.6 * s, 2.6 * s); cv.circle(img, x, y - 2.9 * s, 2.4 * s)
    for dx, dy, a in [(-6.6, 4.6, 28), (-2.4, 7.4, 9), (2.4, 7.4, -9), (6.6, 4.6, -28)]:
        ellipse(cv, img, x + dx * s, y + dy * s, 1.4 * s, 1.85 * s, a)

def back_text(cv, lines, arc=None):
    im = cv.blank()
    for txt, y, h in lines: cv.text(im, txt, 0, y, h, font=FB)
    if arc:
        for txt, r, h in arc: text_arc(cv, im, txt, r, h, top=True, font=FB, track=0.25)
    return cv.sdf(im.transpose(Image.FLIP_LEFT_RIGHT))

def band(S, a, b):
    """franja entre a y b mm hacia adentro del borde de S"""
    return inter(S + a, -(S + b))

def fit_cap(cv, s, maxw, cap, track=1.2, mincap=3.5):
    while cv.text_width(s, cap, track=track) > maxw and cap > mincap: cap -= 0.1
    return cap

def line(cv, img, x0, y0, x1, y1, w):
    """trazo recto de ancho w con puntas redondeadas"""
    import numpy as np
    d = np.array([x1 - x0, y1 - y0], float); L = np.hypot(*d); n = np.array([-d[1], d[0]]) / L * w / 2
    cv.poly(img, [(x0 + n[0], y0 + n[1]), (x1 + n[0], y1 + n[1]), (x1 - n[0], y1 - n[1]), (x0 - n[0], y0 - n[1])])
    cv.circle(img, x0, y0, w / 2); cv.circle(img, x1, y1, w / 2)
