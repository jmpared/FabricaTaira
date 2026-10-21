"""Catálogo en PDF para clientes: fichas con foto, talles y precios, agrupadas por línea y categoría.

No depende de Streamlit: recibe los productos y las fotos ya descargadas (bytes) y devuelve el PDF.
"""
import io
import re

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image as RLImage, KeepTogether, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

ROJO = colors.HexColor("#D7141A")
ROJO_OSC = colors.HexColor("#A50E13")
CREMA = colors.HexColor("#FFF6E5")
CREMA2 = colors.HexColor("#FDECC8")
TINTA = colors.HexColor("#2B1D14")
GRIS = colors.HexColor("#7A6A5C")
VERDE = colors.HexColor("#17663A")
LINEA_FINA = colors.HexColor("#EAD7B0")

WHATSAPP = "+54 9 3741 40-0146"
WEB = "taira-pedidos.netlify.app"

ANCHO_PAG, ALTO_PAG = A4
MARGEN = 12 * mm
GAP = 5 * mm
ANCHO_FICHA = (ANCHO_PAG - 2 * MARGEN - GAP) / 2
ANCHO_FOTO = 30 * mm

_SUFIJO = re.compile(r"\s+(T\.\s*\d+|N°\s*\d+|XL|[SML])\s*$", re.I)


def _e(s):
    """Escapa texto para Paragraph."""
    return (str(s or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _pesos(v):
    if v is None:
        return "Consultar"
    return "$ " + f"{v:,.0f}".replace(",", ".")


def _familia(nombre):
    return _SUFIJO.sub("", (nombre or "").strip()).strip()


def _talle(nombre):
    m = _SUFIJO.search((nombre or "").strip())
    return m.group(1).replace(" ", "") if m else ""


def _st(nombre, **kw):
    base = dict(fontName="Helvetica", fontSize=8, leading=9.6, textColor=TINTA)
    base.update(kw)
    return ParagraphStyle(nombre, **base)


S_FAMILIA = _st("fam", fontName="Helvetica-Bold", fontSize=9.5, leading=11.5)
S_CELDA = _st("celda", fontSize=7.3, leading=8.6)
S_CELDA_C = _st("celdac", fontSize=7.3, leading=8.6, alignment=TA_CENTER)
S_PRECIO = _st("precio", fontName="Helvetica-Bold", fontSize=8, leading=9.4, alignment=TA_RIGHT)
S_PROMO = _st("promo", fontSize=7.3, leading=8.6, textColor=VERDE, alignment=TA_RIGHT)
S_ENCAB = _st("encab", fontName="Helvetica-Bold", fontSize=6.3, leading=7.5, textColor=GRIS)
S_ENCAB_R = _st("encabr", fontName="Helvetica-Bold", fontSize=6.3, leading=7.5, textColor=GRIS, alignment=TA_RIGHT)
S_ETIQ = _st("etiq", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=colors.white, alignment=TA_CENTER)


def _agrupar(productos):
    """Une talles del mismo producto (misma categoría y misma foto, o mismo nombre base) en una ficha."""
    fichas = []
    for p in productos:
        clave = (p.get("linea"), p.get("categoria"), p.get("foto_url") or _familia(p["nombre"]))
        if fichas and fichas[-1]["clave"] == clave:
            fichas[-1]["items"].append(p)
        else:
            fichas.append({"clave": clave, "items": [p]})
    for f in fichas:
        nombres = {_familia(x["nombre"]) for x in f["items"]}
        f["titulo"] = _familia(f["items"][0]["nombre"]) if len(nombres) == 1 else None
    return fichas


def _foto(datos, alto):
    if not datos:
        return None
    try:
        im = Image.open(io.BytesIO(datos))
        w, h = im.size
        esc = min(ANCHO_FOTO / w, alto / h)
        return RLImage(io.BytesIO(datos), width=w * esc, height=h * esc)
    except Exception:
        return None


def _ficha(f, fotos, descuento, mostrar_promo, mostrar_medida):
    items = f["items"]
    promo = mostrar_promo and any(x.get("promo") for x in items)
    variantes = []
    for x in items:
        var = (_talle(x["nombre"]) or ("Único" if len(items) == 1 else "")) if f["titulo"] else x["nombre"]
        med = " · ".join(str(v) for v in (x.get("ancho"), x.get("largo")) if v)
        if (not var or var == "Único") and med and not x.get("largo") and len(items) > 1:
            var, med = med, ""  # p. ej. "Pechera neoprene" con el talle (S, M) cargado en el ancho
        elif not var and med:
            var, med = med, ""
        variantes.append((var, med))
    mostrar_medida = mostrar_medida and any(m for _, m in variantes)
    filas = []
    # Encabezado de la tablita
    enc = [Paragraph("Variante" if not f["titulo"] else "Talle", S_ENCAB)]
    if mostrar_medida:
        enc.append(Paragraph("Medida", S_ENCAB))
    enc.append(Paragraph("Precio", S_ENCAB_R))
    if promo:
        enc.append(Paragraph("6+1 c/u", S_ENCAB_R))
    filas.append(enc)
    for x, (var, med) in zip(items, variantes):
        precio = x.get("precio")
        precio = round(float(precio) * (1 - descuento / 100), 2) if precio is not None else None
        fila = [Paragraph(_e(var), S_CELDA)]
        if mostrar_medida:
            fila.append(Paragraph(_e(med), S_CELDA))
        fila.append(Paragraph(_pesos(precio), S_PRECIO))
        if promo:
            fila.append(Paragraph(_pesos(precio * 6 / 7) if (precio is not None and x.get("promo")) else "", S_PROMO))
        filas.append(fila)

    ancho_tabla = ANCHO_FICHA - (ANCHO_FOTO + 3 * mm if fotos is not None else 0) - 8 * mm
    if mostrar_medida and promo:
        anchos = [0.20, 0.36, 0.23, 0.21]
    elif mostrar_medida:
        anchos = [0.25, 0.47, 0.28]
    elif promo:
        anchos = [0.42, 0.30, 0.28]
    else:
        anchos = [0.62, 0.38]
    if not f["titulo"]:  # variantes con nombre completo: más lugar a la primera columna
        anchos = [anchos[0] + 0.12] + [anchos[1] - 0.12] + anchos[2:] if len(anchos) > 2 else anchos
    tabla = Table(filas, colWidths=[a * ancho_tabla for a in anchos], repeatRows=0)
    tabla.hAlign = "LEFT"
    estilo = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, ROJO),
    ]
    for i in range(1, len(filas)):
        estilo.append(("LINEBELOW", (0, i), (-1, i), 0.3, LINEA_FINA))
    tabla.setStyle(TableStyle(estilo))

    contenido = []
    if f["titulo"]:
        contenido.append(Paragraph(_e(f["titulo"]), S_FAMILIA))
        contenido.append(Spacer(1, 1.5 * mm))
    contenido.append(tabla)
    if promo:
        contenido.append(Spacer(1, 1.2 * mm))
        etiq = Table([[Paragraph("PROMO 6+1", S_ETIQ)]], colWidths=[18 * mm])
        etiq.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), VERDE), ("TOPPADDING", (0, 0), (-1, -1), 1),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5), ("ROUNDEDCORNERS", [3, 3, 3, 3])]))
        etiq.hAlign = "LEFT"
        contenido.append(etiq)

    foto = _foto(fotos.get(items[0].get("foto_url")), 30 * mm) if fotos is not None else None
    if fotos is None:  # catálogo sin fotos: la ficha ocupa todo el ancho de su columna
        cuerpo = Table([[contenido]], colWidths=[ANCHO_FICHA])
    else:
        celda_foto = foto or Paragraph("<font color='#B9A893'>sin foto</font>", _st("sf", alignment=TA_CENTER, fontSize=7))
        cuerpo = Table([[celda_foto, contenido]], colWidths=[ANCHO_FOTO + 3 * mm, ANCHO_FICHA - ANCHO_FOTO - 3 * mm])
    cuerpo.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 0.6, LINEA_FINA), ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROUNDEDCORNERS", [5, 5, 5, 5]),
    ]))
    return cuerpo


def _banda(texto, fondo, color_txt, tam, alto, alin=TA_LEFT, negrita=True):
    p = Paragraph(_e(texto), _st("b", fontName="Helvetica-Bold" if negrita else "Helvetica", fontSize=tam,
                                  leading=tam * 1.2, textColor=color_txt, alignment=alin))
    t = Table([[p]], colWidths=[ANCHO_PAG - 2 * MARGEN], rowHeights=[alto])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fondo), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("ROUNDEDCORNERS", [5, 5, 5, 5])]))
    return t


def catalogo_pdf(productos, fecha_txt, fotos=None, descuento=0.0, mostrar_promo=True, mostrar_medida=True,
                 titulo="Catálogo mayorista", nota_extra=""):
    """productos: dicts con nombre, categoria, linea, ancho, largo, precio, promo, foto_url (ordenados).
    fotos: dict foto_url -> bytes de la imagen, o None para un catálogo sin fotos (más liviano)."""
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=MARGEN, rightMargin=MARGEN, topMargin=MARGEN,
                          bottomMargin=14 * mm, title=f"TAIRA - {titulo}", author="TAIRA Fábrica y Distribuidora")

    def pie(canv, d):
        canv.saveState()
        canv.setFillColor(ROJO)
        canv.rect(0, 0, ANCHO_PAG, 8 * mm, stroke=0, fill=1)
        canv.setFillColor(colors.white)
        canv.setFont("Helvetica-Bold", 8)
        canv.drawString(MARGEN, 2.9 * mm, "TAIRA · Fábrica y distribuidora")
        canv.setFont("Helvetica", 8)
        canv.drawCentredString(ANCHO_PAG / 2, 2.9 * mm, f"Pedidos por WhatsApp {WHATSAPP} · {WEB}")
        canv.drawRightString(ANCHO_PAG - MARGEN, 2.9 * mm, f"Página {d.page}")
        canv.restoreState()

    frame = Frame(MARGEN, 14 * mm, ANCHO_PAG - 2 * MARGEN, ALTO_PAG - MARGEN - 14 * mm, id="f",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=pie)])

    hist = []
    # ---------- Portada / encabezado
    logo = Paragraph("TAIRA<super><font size=12>®</font></super>", _st("logo", fontName="Helvetica-Bold", fontSize=40,
                                                                      leading=44, textColor=colors.white, alignment=TA_CENTER))
    sub = Paragraph("FÁBRICA Y DISTRIBUIDORA", _st("sub", fontName="Helvetica-Bold", fontSize=10, leading=13,
                                                  textColor=colors.white, alignment=TA_CENTER))
    cab = Table([[logo], [sub]], colWidths=[ANCHO_PAG - 2 * MARGEN])
    cab.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ROJO), ("TOPPADDING", (0, 0), (-1, 0), 10),
                             ("BOTTOMPADDING", (0, -1), (-1, -1), 10), ("ROUNDEDCORNERS", [8, 8, 8, 8])]))
    hist += [cab, Spacer(1, 3 * mm)]
    texto_desc = f" · Incluye {descuento:g}% de descuento" if descuento else ""
    hist.append(_banda(f"{titulo} · Veterinarias y pet shops", CREMA2, TINTA, 13, 9 * mm, TA_CENTER))
    hist.append(Spacer(1, 1.5 * mm))
    info = [f"Precios vigentes desde el {fecha_txt}{texto_desc}",
            "Envío gratis en Misiones desde $150.000 · a todo el país desde $500.000"]
    if mostrar_promo:
        info.append("PROMO en productos fabricados: llevando 6 del mismo producto y talle, 1 va de regalo (colores surtidos)")
    info.append(f"Pedidos por WhatsApp {WHATSAPP} · Pedí online: {WEB}" + (f" · {nota_extra}" if nota_extra else ""))
    for i, t in enumerate(info):
        hist.append(Paragraph(_e(t), _st(f"i{i}", fontSize=9, leading=12, alignment=TA_CENTER,
                                         textColor=ROJO_OSC if i in (1, 2) else TINTA,
                                         fontName="Helvetica-Bold" if i in (1, 2) else "Helvetica")))
    hist.append(Spacer(1, 5 * mm))

    # ---------- Fichas
    fichas = _agrupar(productos)
    for clave, titulo_linea in (("fabricado", "FABRICADOS POR TAIRA"), ("importado", "PRODUCTOS IMPORTADOS")):
        grupo = [f for f in fichas if f["clave"][0] == clave]
        if not grupo:
            continue
        hist.append(CondPageBreak(60 * mm))
        hist.append(_banda(titulo_linea, ROJO_OSC, colors.white, 13, 9 * mm))
        hist.append(Spacer(1, 3 * mm))
        cats = []
        for f in grupo:
            if f["clave"][1] not in cats:
                cats.append(f["clave"][1])
        for cat in cats:
            de_cat = [f for f in grupo if f["clave"][1] == cat]
            titulo_cat = Paragraph(_e(cat or "Otros"), _st("cat", fontName="Helvetica-Bold", fontSize=12.5, leading=15,
                                                          textColor=ROJO))
            linea_cat = Table([[titulo_cat]], colWidths=[ANCHO_PAG - 2 * MARGEN])
            linea_cat.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1.2, ROJO), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
            filas = []
            celdas = [_ficha(f, fotos, descuento, mostrar_promo, mostrar_medida) for f in de_cat]
            for k in range(0, len(celdas), 2):
                par = celdas[k:k + 2] + ([""] if len(celdas[k:k + 2]) == 1 else [])
                fila = Table([par], colWidths=[ANCHO_FICHA + GAP / 2, ANCHO_FICHA + GAP / 2])
                fila.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                          ("RIGHTPADDING", (0, 0), (0, 0), GAP / 2), ("LEFTPADDING", (1, 0), (1, 0), GAP / 2),
                                          ("RIGHTPADDING", (1, 0), (1, 0), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), GAP / 1.5),
                                          ("TOPPADDING", (0, 0), (-1, -1), 0)]))
                filas.append(fila)
            # el título de la categoría nunca queda solo al pie de una hoja
            hist.append(KeepTogether([linea_cat, Spacer(1, 3 * mm), filas[0]]))
            hist.extend(filas[1:])
            hist.append(Spacer(1, 3 * mm))

    hist.append(Spacer(1, 2 * mm))
    hist.append(Paragraph("Los precios están sujetos a modificaciones. Las fotos son ilustrativas: colores y estampas pueden variar. "
                          "Para más descuentos y formas de pago consultá con el vendedor.",
                          _st("fin", fontSize=8, leading=10, textColor=GRIS, fontName="Helvetica-Oblique",
                              alignment=TA_CENTER)))
    doc.build(hist)
    return buf.getvalue()


def achicar_foto(datos, lado=420, calidad=78):
    """Reduce la foto para que el PDF quede liviano (para mandar por WhatsApp)."""
    try:
        im = Image.open(io.BytesIO(datos))
        im = im.convert("RGB")
        im.thumbnail((lado, lado))
        out = io.BytesIO()
        im.save(out, "JPEG", quality=calidad, optimize=True)
        return out.getvalue()
    except Exception:
        return None
