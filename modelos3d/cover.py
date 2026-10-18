"""Portadas tipo foto de producto: fondo degradé, sombra suave, título."""
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from render import render
import numpy as np
FB = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"; FR = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"

def bg_grad(W, H, c1, c2):
    y = np.linspace(0, 1, H)[:, None, None]; x = np.linspace(-1, 1, W)[None, :, None]
    a, b = np.array(c1, float), np.array(c2, float)
    t = np.clip(y * 0.8 + (x ** 2) * 0.15, 0, 1)
    return Image.fromarray((a * (1 - t) + b * t).astype(np.uint8))

def shot(parts, W=1600, H=1200, elev=50, azim=-20, c1=(250, 246, 238), c2=(222, 214, 200), margin=0.16, dy=0):
    obj = render(parts, None, elev=elev, azim=azim, W=W, H=H, margin=margin, transparent=True)
    base = bg_grad(W, H, c1, c2).convert("RGBA")
    if dy:
        o2 = Image.new('RGBA', (W, H), (0, 0, 0, 0)); o2.paste(obj, (0, int(dy))); obj = o2
    a = obj.split()[3]
    sh = Image.new("RGBA", (W, H), (60, 40, 20, 0)); sh.putalpha(a.point(lambda v: int(v * 0.45)))
    sh = sh.transform((W, H), Image.AFFINE, (1, 0, -18, 0, 1, -34)).filter(ImageFilter.GaussianBlur(26))
    base.alpha_composite(sh); base.alpha_composite(obj)
    return base

def title(img, t1, t2=None, color=(43, 29, 20)):
    d = ImageDraw.Draw(img); W, H = img.size
    f1 = ImageFont.truetype(FB, int(H * 0.065)); d.text((W * 0.05, H * 0.05), t1, font=f1, fill=color)
    if t2:
        f2 = ImageFont.truetype(FR, int(H * 0.032)); d.text((W * 0.05, H * 0.05 + H * 0.08), t2, font=f2, fill=(110, 95, 80))
    return img
