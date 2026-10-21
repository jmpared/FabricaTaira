/* catalogo-pdf.js · Catálogo TAIRA en PDF, armado en el navegador sin librerías externas.
   Uso: const bytes = CatalogoPDF.armar(productos, opciones);
   productos: [{nombre, categoria, linea, ancho, largo, precio, promo, foto_url}] (ya ordenados)
   opciones: {titulo, nota, descuento, promo, medida, fecha, fotos: Map(foto_url -> {bytes: Uint8Array JPEG, w, h}) | null} */
(function (global) {
"use strict";
const W = { H: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,278,278,355,556,556,889,667,191,333,333,389,584,278,333,278,278,556,556,556,556,556,556,556,556,556,556,278,278,584,584,584,556,1015,667,667,722,722,667,611,778,722,278,500,667,556,833,722,778,667,778,722,667,611,722,667,944,667,667,611,278,278,278,469,556,333,556,556,500,556,556,278,556,556,222,222,500,222,833,556,556,556,556,333,500,278,556,500,722,500,500,500,334,260,334,584,761,556,0,222,556,333,1000,556,556,333,1000,667,333,1000,0,611,0,0,222,222,333,333,350,556,1000,333,1000,500,333,944,0,500,667,278,333,556,556,556,556,260,556,333,737,370,556,584,333,737,333,400,584,333,333,333,556,537,278,333,333,365,556,834,834,834,611,667,667,667,667,667,667,1000,722,667,667,667,667,278,278,278,278,722,722,778,778,778,778,778,584,778,722,722,722,722,667,667,611,556,556,556,556,556,556,889,500,556,556,556,556,278,278,278,278,556,556,556,556,556,556,556,584,611,556,556,556,556,500,556,500],
  B: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,278,333,474,556,556,889,722,238,333,333,389,584,278,333,278,278,556,556,556,556,556,556,556,556,556,556,333,333,584,584,584,611,975,722,722,722,722,667,611,778,722,278,556,722,611,833,722,778,667,778,722,667,611,722,667,944,667,667,611,333,278,333,584,556,333,556,611,556,611,556,333,611,611,278,278,556,278,889,611,611,611,611,389,556,333,611,556,778,556,556,500,389,280,389,584,761,556,0,278,556,500,1000,556,556,333,1000,667,333,1000,0,611,0,0,278,278,500,500,350,556,1000,333,1000,556,333,944,0,500,667,278,333,556,556,556,556,280,556,333,737,370,556,584,333,737,333,400,584,333,333,333,611,556,278,333,333,365,556,834,834,834,611,722,722,722,722,722,722,1000,722,667,667,667,667,278,278,278,278,722,722,778,778,778,778,778,584,778,722,722,722,722,667,667,611,556,556,556,556,556,556,889,556,556,556,556,556,278,278,278,278,611,611,611,611,611,611,611,584,611,611,611,611,611,556,611,556],
  I: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,278,278,355,556,556,889,667,191,333,333,389,584,278,333,278,278,556,556,556,556,556,556,556,556,556,556,278,278,584,584,584,556,1015,667,667,722,722,667,611,778,722,278,500,667,556,833,722,778,667,778,722,667,611,722,667,944,667,667,611,278,278,278,469,556,333,556,556,500,556,556,278,556,556,222,222,500,222,833,556,556,556,556,333,500,278,556,500,722,500,500,500,334,260,334,584,761,556,0,222,556,333,1000,556,556,333,1000,667,333,1000,0,611,0,0,222,222,333,333,350,556,1000,333,1000,500,333,944,0,500,667,278,333,556,556,556,556,260,556,333,737,370,556,584,333,737,333,400,584,333,333,333,556,537,278,333,333,365,556,834,834,834,611,667,667,667,667,667,667,1000,722,667,667,667,667,278,278,278,278,722,722,778,778,778,778,778,584,778,722,722,722,722,667,667,611,556,556,556,556,556,556,889,500,556,556,556,556,278,278,278,278,556,556,556,556,556,556,556,584,611,556,556,556,556,500,556,500] };
const FUENTE = { H: "Helvetica", B: "Helvetica-Bold", I: "Helvetica-Oblique" };
const MM = 72 / 25.4; let PW = 210, PH = 297;
const C = { rojo: [215, 20, 26], rojoOsc: [165, 14, 19], crema: [255, 246, 229], crema2: [253, 236, 200], tinta: [43, 29, 20],
  gris: [122, 106, 92], verde: [23, 102, 58], linea: [234, 215, 176], blanco: [255, 255, 255], sinFoto: [185, 168, 147] };
const WHATSAPP = "+54 9 3741 40-0146", WA_LINK = "https://wa.me/5493741400146", WEB = "taira-pedidos.netlify.app";

// ---------------------------------------------------------------- texto (WinAnsi)
const CP = { 0x20AC: 128, 0x201A: 130, 0x0192: 131, 0x201E: 132, 0x2026: 133, 0x2020: 134, 0x2021: 135, 0x02C6: 136, 0x2030: 137,
  0x0160: 138, 0x2039: 139, 0x0152: 140, 0x017D: 142, 0x2018: 145, 0x2019: 146, 0x201C: 147, 0x201D: 148, 0x2022: 149,
  0x2013: 150, 0x2014: 151, 0x02DC: 152, 0x2122: 153, 0x0161: 154, 0x203A: 155, 0x0153: 156, 0x017E: 158, 0x0178: 159 };
function codigos(s) {
  const out = [];
  for (const ch of String(s ?? "")) {
    const u = ch.codePointAt(0);
    if (u >= 32 && u < 127) out.push(u);
    else if (u >= 160 && u < 256) out.push(u);
    else if (CP[u]) out.push(CP[u]);
    else if (u === 0x2715 || u === 0xD7) out.push(0xD7);
    else if (u > 0xFFFF || (u >= 0x2600 && u < 0x2800)) continue; // emojis: se omiten
    else out.push(63); // ?
  }
  return out;
}
function ancho(s, f, tam) { let t = 0; for (const c of codigos(s)) t += W[f][c] || 556; return t / 1000 * tam / MM; } // en mm
function partir(s, f, tam, max) {
  const lineas = []; let actual = "";
  for (const palabra of String(s ?? "").split(/\s+/).filter(Boolean)) {
    const prueba = actual ? actual + " " + palabra : palabra;
    if (ancho(prueba, f, tam) <= max || !actual) {
      if (!actual && ancho(palabra, f, tam) > max) { // palabra sola demasiado larga: cortar
        let trozo = "";
        for (const ch of palabra) { if (ancho(trozo + ch, f, tam) > max && trozo) { lineas.push(trozo); trozo = ""; } trozo += ch; }
        actual = trozo;
      } else actual = prueba;
    } else { lineas.push(actual); actual = palabra; }
  }
  if (actual) lineas.push(actual);
  return lineas.length ? lineas : [""];
}
const lit = s => "(" + codigos(s).map(c => c === 40 || c === 41 || c === 92 ? "\\" + String.fromCharCode(c) : c < 128 ? String.fromCharCode(c) : "\\" + c.toString(8).padStart(3, "0")).join("") + ")";
const n2 = v => (Math.round(v * 100) / 100).toString();
const col = (c, op) => c.map(v => n2(v / 255)).join(" ") + (op === "f" ? " rg" : " RG");

// ---------------------------------------------------------------- documento
class Doc {
  constructor() { this.paginas = []; this.imagenes = []; this.nombresImg = new Map(); this.nueva(); }
  nueva() { this.ops = []; this.links = []; this.paginas.push({ ops: this.ops, links: this.links }); }
  get nPag() { return this.paginas.length - 1; }
  y(v) { return n2((PH - v) * MM); }
  rect(x, y, w, h, op = {}, destino) {
    const ops = destino || this.ops;
    const r = op.r || 0, X = x * MM, Y = (PH - y - h) * MM, Wd = w * MM, Hd = h * MM;
    let p = "";
    if (op.fill) p += col(op.fill, "f") + " ";
    if (op.stroke) p += col(op.stroke, "s") + " " + n2((op.lw || 0.5)) + " w ";
    if (r) {
      const R = r * MM, k = 0.5523 * R;
      p += `${n2(X + R)} ${n2(Y)} m ${n2(X + Wd - R)} ${n2(Y)} l ${n2(X + Wd - R + k)} ${n2(Y)} ${n2(X + Wd)} ${n2(Y + R - k)} ${n2(X + Wd)} ${n2(Y + R)} c `
        + `${n2(X + Wd)} ${n2(Y + Hd - R)} l ${n2(X + Wd)} ${n2(Y + Hd - R + k)} ${n2(X + Wd - R + k)} ${n2(Y + Hd)} ${n2(X + Wd - R)} ${n2(Y + Hd)} c `
        + `${n2(X + R)} ${n2(Y + Hd)} l ${n2(X + R - k)} ${n2(Y + Hd)} ${n2(X)} ${n2(Y + Hd - R + k)} ${n2(X)} ${n2(Y + Hd - R)} c `
        + `${n2(X)} ${n2(Y + R)} l ${n2(X)} ${n2(Y + R - k)} ${n2(X + R - k)} ${n2(Y)} ${n2(X + R)} ${n2(Y)} c h `;
    } else p += `${n2(X)} ${n2(Y)} ${n2(Wd)} ${n2(Hd)} re `;
    p += op.fill && op.stroke ? "B" : op.fill ? "f" : "S";
    ops.push(p);
  }
  linea(x1, y1, x2, y2, c, lw, punteada, destino) {
    (destino || this.ops).push(`${col(c, "s")} ${n2(lw)} w ${punteada ? "[0.6 1.8] 0 d 1 J" : "[] 0 d 0 J"} ${n2(x1 * MM)} ${this.y(y1)} m ${n2(x2 * MM)} ${this.y(y2)} l S [] 0 d 0 J`);
  }
  // y = línea de base, en mm desde arriba
  texto(s, x, y, f, tam, c, alin = "izq", destino) {
    if (s == null || s === "") return;
    let X = x; const a = ancho(s, f, tam);
    if (alin === "der") X = x - a; else if (alin === "centro") X = x - a / 2;
    (destino || this.ops).push(`BT /${f} ${n2(tam)} Tf ${col(c, "f")} ${n2(X * MM)} ${this.y(y)} Td ${lit(s)} Tj ET`);
  }
  imagen(img, x, y, w, h) {
    let nombre = this.nombresImg.get(img);
    if (!nombre) { nombre = "Im" + (this.imagenes.length + 1); this.nombresImg.set(img, nombre); this.imagenes.push(img); }
    this.ops.push(`q ${n2(w * MM)} 0 0 ${n2(h * MM)} ${n2(x * MM)} ${n2((PH - y - h) * MM)} cm /${nombre} Do Q`);
  }
  // enlace tocable: a otra página ({pagina, y}) o a una web ({uri})
  enlace(x, y, w, h, dest, links) { (links || this.links).push({ rect: [x * MM, (PH - y - h) * MM, (x + w) * MM, (PH - y) * MM], dest }); }
  bytes(titulo) {
    const partes = [], offs = []; let largo = 0;
    const enc = new TextEncoder();
    const add = d => { const b = typeof d === "string" ? enc.encode(d) : d; partes.push(b); largo += b.length; };
    const obj = (n, cuerpo) => { offs[n] = largo; add(`${n} 0 obj\n`); (Array.isArray(cuerpo) ? cuerpo : [cuerpo]).forEach(add); add("\nendobj\n"); };
    add("%PDF-1.4\n"); add(new Uint8Array([37, 226, 227, 207, 211, 10]));
    // 1 catálogo, 2 páginas, 3-5 fuentes, imágenes, páginas + contenidos, enlaces, info
    const nImg0 = 6, nPag0 = nImg0 + this.imagenes.length, nLink0 = nPag0 + this.paginas.length * 2;
    const pagObj = i => nPag0 + i * 2;
    let nLink = nLink0; const linksPorPag = this.paginas.map(p => p.links.map(l => ({ ...l, n: nLink++ })));
    obj(1, `<< /Type /Catalog /Pages 2 0 R /PageMode /UseNone /ViewerPreferences << /DisplayDocTitle true >> >>`);
    obj(2, `<< /Type /Pages /Kids [${this.paginas.map((_, i) => `${pagObj(i)} 0 R`).join(" ")}] /Count ${this.paginas.length} >>`);
    ["H", "B", "I"].forEach((k, i) => obj(3 + i, `<< /Type /Font /Subtype /Type1 /BaseFont /${FUENTE[k]} /Encoding /WinAnsiEncoding >>`));
    this.imagenes.forEach((im, i) => obj(nImg0 + i, [`<< /Type /XObject /Subtype /Image /Width ${im.w} /Height ${im.h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${im.bytes.length} >>\nstream\n`, im.bytes, "\nendstream"]));
    const xobj = this.imagenes.length ? `/XObject << ${this.imagenes.map((im, i) => `/${this.nombresImg.get(im)} ${nImg0 + i} 0 R`).join(" ")} >>` : "";
    this.paginas.forEach((p, i) => {
      const n = pagObj(i), flujo = enc.encode(p.ops.join("\n"));
      const annots = linksPorPag[i].length ? `/Annots [${linksPorPag[i].map(l => `${l.n} 0 R`).join(" ")}]` : "";
      obj(n, `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${n2(PW * MM)} ${n2(PH * MM)}] /Resources << /Font << /H 3 0 R /B 4 0 R /I 5 0 R >> ${xobj} >> ${annots} /Contents ${n + 1} 0 R >>`);
      obj(n + 1, [`<< /Length ${flujo.length} >>\nstream\n`, flujo, "\nendstream"]);
    });
    linksPorPag.flat().forEach(l => {
      const accion = l.dest.uri ? `/A << /S /URI /URI ${lit(l.dest.uri)} >>`
        : `/Dest [${pagObj(Math.min(l.dest.pagina, this.paginas.length - 1))} 0 R /XYZ 0 ${n2((PH - (l.dest.y || 0)) * MM)} null]`;
      obj(l.n, `<< /Type /Annot /Subtype /Link /Rect [${l.rect.map(n2).join(" ")}] /Border [0 0 0] ${accion} >>`);
    });
    const info = nLink; obj(info, `<< /Title ${lit(titulo)} /Author ${lit("TAIRA Fábrica y Distribuidora")} /Producer (TAIRA) >>`);
    const xref = largo;
    let x = `xref\n0 ${info + 1}\n0000000000 65535 f \n`;
    for (let i = 1; i <= info; i++) x += String(offs[i]).padStart(10, "0") + " 00000 n \n";
    add(x + `trailer\n<< /Size ${info + 1} /Root 1 0 R /Info ${info} 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
    const out = new Uint8Array(largo); let p = 0; partes.forEach(b => { out.set(b, p); p += b.length; });
    return out;
  }
}

// ---------------------------------------------------------------- datos
const SUFIJO = /\s+(T\.\s*\d+|N°\s*\d+|XL|[SML])\s*$/i;
const familia = n => String(n || "").trim().replace(SUFIJO, "").trim();
const talle = n => { const m = String(n || "").trim().match(SUFIJO); return m ? m[1].replace(/\s/g, "") : ""; };
const pesos = v => v == null ? "Consultar" : "$ " + Math.round(v).toLocaleString("es-AR");
function agrupar(ps) {
  const fichas = [];
  for (const p of ps) {
    const clave = [p.linea, p.categoria, p.foto_url || familia(p.nombre)].join("|");
    const ult = fichas[fichas.length - 1];
    if (ult && ult.clave === clave) ult.items.push(p); else fichas.push({ clave, linea: p.linea, categoria: p.categoria, items: [p] });
  }
  for (const f of fichas) f.titulo = new Set(f.items.map(x => familia(x.nombre))).size === 1 ? familia(f.items[0].nombre) : null;
  return fichas;
}

// ---------------------------------------------------------------- diseño
// Dos formatos: "celular" (página angosta, una ficha por fila, letra grande) y "a4" (para imprimir, dos fichas por fila).
let M, GAP, COLS, ANCHO_FICHA, FOTO, ABAJO, FS, T_CELDA, L_CELDA, CEL;
const PAD = 3;
function formato(f) {
  CEL = f !== "a4";
  if (CEL) { PW = 100; PH = 178; M = 5; GAP = 0; COLS = 1; FOTO = 28; FS = 1.1; }
  else { PW = 210; PH = 297; M = 12; GAP = 5; COLS = 2; FOTO = 30; FS = 1; }
  ANCHO_FICHA = (PW - 2 * M - GAP * (COLS - 1)) / COLS;
  ABAJO = PH - (CEL ? 11 : 14);
  T_CELDA = 7.3 * FS; L_CELDA = 3.1 * FS;
}

function medirFicha(f, op) {
  const items = f.items, promo = op.promo && items.some(x => x.promo);
  const variantes = items.map(x => {
    let v = f.titulo ? (talle(x.nombre) || (items.length === 1 ? "Único" : "")) : x.nombre;
    let m = [x.ancho, x.largo].filter(Boolean).join(" · ");
    if ((!v || v === "Único") && m && !x.largo && items.length > 1) { v = m; m = ""; }
    else if (!v && m) { v = m; m = ""; }
    return { x, v, m };
  });
  const med = op.medida && variantes.some(r => r.m);
  const xTexto = op.fotos ? PAD + FOTO + 3 : PAD, anchoT = ANCHO_FICHA - xTexto - PAD;
  let fr = med && promo ? (CEL ? [0.165, 0.375, 0.25, 0.21] : [0.20, 0.36, 0.23, 0.21]) : med ? [0.22, 0.50, 0.28] : promo ? [0.42, 0.30, 0.28] : [0.62, 0.38];
  if (!f.titulo && fr.length > 2) fr = [fr[0] + 0.12, fr[1] - 0.12, ...fr.slice(2)];
  const cols = ["v"].concat(med ? ["m"] : [], ["p"], promo ? ["q"] : []);
  const anchos = fr.map(a => a * anchoT);
  const tituloL = f.titulo ? partir(f.titulo, "B", 9.5 * FS, anchoT) : [];
  let h = PAD + tituloL.length * 4.1 * FS + (tituloL.length ? 1.2 : 0) + 3.8 * FS;
  const filas = variantes.map(r => {
    const pr = r.x.precio == null ? null : Math.round(r.x.precio * (1 - (op.descuento || 0) / 100) * 100) / 100;
    const celdas = { v: partir(r.v, "H", T_CELDA, anchos[0] - 1), m: med ? partir(r.m, "H", T_CELDA, anchos[1] - 1) : [],
      p: pesos(pr), q: promo && pr != null && r.x.promo ? pesos(pr * 6 / 7) : "" };
    const alto = Math.max(celdas.v.length, celdas.m.length, 1) * L_CELDA + 1.3;
    h += alto;
    return { celdas, alto };
  });
  if (promo) h += 5.2 * FS;
  h += PAD;
  if (op.fotos) h = Math.max(h, PAD + FOTO + PAD);
  return { f, promo, cols, anchos, tituloL, filas, xTexto, alto: h };
}

function dibujarFicha(d, F, x, y, op) {
  d.rect(x, y, ANCHO_FICHA, F.alto, { fill: C.blanco, stroke: C.linea, lw: 0.6, r: 1.8 });
  if (op.fotos) {
    const im = op.fotos.get(F.f.items[0].foto_url);
    if (im && im.bytes) {
      const e = Math.min(FOTO / im.w, FOTO / im.h), w = im.w * e, h = im.h * e;
      d.imagen(im, x + PAD + (FOTO - w) / 2, y + PAD + (FOTO - h) / 2, w, h);
    } else {
      d.rect(x + PAD, y + PAD, FOTO, FOTO, { fill: C.crema, r: 1.2 });
      d.texto("sin foto", x + PAD + FOTO / 2, y + PAD + FOTO / 2 + 1, "H", 7, C.sinFoto, "centro");
    }
  }
  const x0 = x + F.xTexto; let yy = y + PAD;
  F.tituloL.forEach(l => { yy += 4.1 * FS; d.texto(l, x0, yy - 0.9, "B", 9.5 * FS, C.tinta); });
  if (F.tituloL.length) yy += 1.2;
  const posX = []; let acc = x0; F.anchos.forEach(a => { posX.push(acc); acc += a; });
  const nombres = { v: F.f.titulo ? "Talle" : "Variante", m: "Medida", p: "Precio", q: "6+1 c/u" };
  F.cols.forEach((c, i) => {
    const der = c === "p" || c === "q";
    d.texto(nombres[c], der ? posX[i] + F.anchos[i] - 0.6 : posX[i] + 0.6, yy + 2.6 * FS, "B", 6.3 * FS, C.gris, der ? "der" : "izq");
  });
  yy += 3.8 * FS; d.linea(x0, yy, acc, yy, C.rojo, 0.6);
  F.filas.forEach(r => {
    const base = yy + L_CELDA;
    const medio = yy + r.alto / 2 + 1.1 * FS;
    F.cols.forEach((c, i) => {
      if (c === "v" || c === "m") r.celdas[c].forEach((l, k) => d.texto(l, posX[i] + 0.6, base + k * L_CELDA, "H", T_CELDA, C.tinta));
      else if (c === "p") d.texto(r.celdas.p, posX[i] + F.anchos[i] - 0.6, medio, "B", 8 * FS, C.tinta, "der");
      else d.texto(r.celdas.q, posX[i] + F.anchos[i] - 0.6, medio, "H", T_CELDA, C.verde, "der");
    });
    yy += r.alto; d.linea(x0, yy, acc, yy, C.linea, 0.3);
  });
  if (F.promo) {
    yy += 1.3; const wB = 18 * FS, hB = 3.6 * FS;
    d.rect(x0, yy, wB, hB, { fill: C.verde, r: 1 });
    d.texto("PROMO 6+1", x0 + wB / 2, yy + hB * 0.71, "B", 6.5 * FS, C.blanco, "centro");
  }
}

function pie(d, n, yIndice) {
  const h = CEL ? 8 : 8, base = PH - (CEL ? 3.1 : 3);
  d.rect(0, PH - h, PW, h, { fill: C.rojo });
  if (CEL) {
    d.texto(`WhatsApp ${WHATSAPP.replace("+54 9 ", "")}`, M, base, "B", 7.5, C.blanco);
    d.enlace(0, PH - h, PW * 0.55, h, { uri: WA_LINK });
    const t = `Índice  ·  ${n}`;
    d.texto(t, PW - M, base, "B", 7.5, C.blanco, "der");
    d.enlace(PW * 0.6, PH - h, PW * 0.4, h, { pagina: 0, y: yIndice });
  } else {
    d.texto("TAIRA · Ir al índice", M, base, "B", 8, C.blanco);
    d.enlace(0, PH - h, 45, h, { pagina: 0, y: yIndice });
    d.texto(`Pedidos por WhatsApp ${WHATSAPP} · ${WEB}`, PW / 2, base, "H", 8, C.blanco, "centro");
    d.enlace(PW / 2 - 50, PH - h, 100, h, { uri: WA_LINK });
    d.texto(`Página ${n}`, PW - M, base, "H", 8, C.blanco, "der");
  }
}

function armar(productos, op) {
  op = Object.assign({ formato: "celular", titulo: "Catálogo mayorista", nota: "", descuento: 0, promo: true, medida: true, fotos: null,
    fecha: new Date().toLocaleDateString("es-AR") }, op);
  formato(op.formato);
  const d = new Doc(); let y = M;
  const ANCHO = PW - 2 * M;
  const nuevaPag = () => { d.nueva(); y = M; };
  // ---------- encabezado
  const hCab = CEL ? 22 : 25;
  d.rect(M, y, ANCHO, hCab, { fill: C.rojo, r: 2.8 });
  const tamLogo = CEL ? 32 : 40, aT = ancho("TAIRA", "B", tamLogo);
  d.texto("TAIRA", PW / 2, y + hCab * 0.6, "B", tamLogo, C.blanco, "centro");
  d.texto("®", PW / 2 + aT / 2 + 0.6, y + hCab * 0.34, "B", 11, C.blanco);
  d.texto("FÁBRICA Y DISTRIBUIDORA", PW / 2, y + hCab * 0.84, "B", CEL ? 8.5 : 10, C.blanco, "centro");
  y += hCab + 3;
  const tamT = CEL ? 11 : 13;
  const lt = partir(`${op.titulo || "Catálogo"} · Veterinarias y pet shops`, "B", tamT, ANCHO - 6);
  const hT = lt.length * tamT * 0.45 + 4;
  d.rect(M, y, ANCHO, hT, { fill: C.crema2, r: 1.8 });
  lt.forEach((l, i) => d.texto(l, PW / 2, y + 2 + (i + 0.78) * tamT * 0.45, "B", tamT, C.tinta, "centro"));
  y += hT + 2;
  const tamI = CEL ? 8.3 : 9, lh = tamI * 0.47;
  const info = [[`Precios vigentes desde el ${op.fecha}${op.descuento ? ` · Incluye ${op.descuento}% de descuento` : ""}`, "H", C.tinta],
    ["Envío gratis en Misiones desde $150.000 · a todo el país desde $500.000", "B", C.rojoOsc]];
  if (op.promo) info.push(["PROMO en productos fabricados: llevando 6 del mismo producto y talle, 1 va de regalo (colores surtidos)", "B", C.rojoOsc]);
  info.forEach(([t, f, c]) => partir(t, f, tamI, ANCHO).forEach(l => { y += lh; d.texto(l, PW / 2, y, f, tamI, c, "centro"); }));
  // botón de WhatsApp tocable
  y += 3;
  const tWa = `Pedidos por WhatsApp ${WHATSAPP}`, wWa = Math.min(ANCHO, ancho(tWa, "B", tamI) + 10), hWa = tamI * 0.75;
  d.rect(PW / 2 - wWa / 2, y, wWa, hWa, { fill: [31, 168, 85], r: hWa / 2 });
  d.texto(tWa, PW / 2, y + hWa * 0.67, "B", tamI, C.blanco, "centro");
  d.enlace(PW / 2 - wWa / 2, y, wWa, hWa, { uri: WA_LINK });
  y += hWa + 1.5;
  partir(`Pedí online: ${WEB}` + (op.nota ? ` · ${op.nota}` : ""), "H", tamI, ANCHO).forEach(l => { y += lh; d.texto(l, PW / 2, y, "H", tamI, C.tinta, "centro"); });
  d.enlace(M, y - lh, ANCHO, lh + 1, { uri: "https://" + WEB });
  y += 5;

  // ---------- índice (se completa con los números de página al final)
  const fichas = agrupar(productos);
  const lineas = [["fabricado", "FABRICADOS POR TAIRA"], ["importado", "PRODUCTOS IMPORTADOS"]].filter(([k]) => fichas.some(f => f.linea === k));
  const yIndice = Math.max(0, y - 2);
  const pendientes = []; // {pagina, y, clave}
  const tamX = CEL ? 9 : 10, lx = CEL ? 6.2 : 6;
  d.texto("Índice", M, y + 4, "B", CEL ? 12 : 13, C.rojo); y += 6;
  d.texto("Tocá una categoría para ir directo", M, y + 2.5, "I", CEL ? 7 : 7.5, C.gris); y += 5;
  for (const [clave, tit] of lineas) {
    if (y + lx * 2 > ABAJO) nuevaPag();
    d.texto(tit, M, y + 4, "B", tamX * 0.85, C.rojoOsc); y += lx;
    for (const cat of [...new Set(fichas.filter(f => f.linea === clave).map(f => f.categoria))]) {
      if (y + lx > ABAJO) nuevaPag();
      const nom = partir(cat || "Otros", "H", tamX, ANCHO - 18)[0];
      d.texto(nom, M + 2, y + 4, "H", tamX, C.tinta);
      const fin = M + 2 + ancho(nom, "H", tamX) + 1.5;
      pendientes.push({ pagina: d.nPag, y, clave: clave + "|" + cat, xDots: fin });
      y += lx;
    }
    y += 2;
  }
  const destinos = {};

  // ---------- fichas
  for (const [clave, tit] of lineas) {
    const grupo = fichas.filter(f => f.linea === clave);
    nuevaPag();
    d.rect(M, y, ANCHO, 9, { fill: C.rojoOsc, r: 1.8 }); d.texto(tit, M + 3, y + 6.3, "B", CEL ? 11.5 : 13, C.blanco); y += 12;
    for (const cat of [...new Set(grupo.map(f => f.categoria))]) {
      const medidas = grupo.filter(f => f.categoria === cat).map(f => medirFicha(f, op));
      const filas = []; for (let k = 0; k < medidas.length; k += COLS) filas.push(medidas.slice(k, k + COLS));
      const altoFila = fl => Math.max(...fl.map(F => F.alto));
      if (y + 10 + altoFila(filas[0]) > ABAJO) nuevaPag();
      destinos[clave + "|" + cat] = { pagina: d.nPag, y: Math.max(0, y - 2) };
      d.texto(cat || "Otros", M, y + 5.5, "B", CEL ? 11.5 : 12.5, C.rojo); d.linea(M, y + 7.5, M + ANCHO, y + 7.5, C.rojo, 1.2); y += 10.5;
      for (const fl of filas) {
        const h = altoFila(fl);
        if (y + h > ABAJO) { nuevaPag(); d.texto(`${cat} (continuación)`, M, y + 4.5, "B", 9.5, C.gris); y += 7.5; }
        fl.forEach((F, i) => dibujarFicha(d, F, M + i * (ANCHO_FICHA + GAP), y, op));
        y += h + (CEL ? 3 : 3.5);
      }
      y += 3;
    }
  }
  const fin = partir("Los precios están sujetos a modificaciones. Las fotos son ilustrativas: colores y estampas pueden variar. Para más descuentos y formas de pago consultá con el vendedor.", "I", 8, ANCHO);
  if (y + fin.length * 3.6 + 2 > ABAJO) nuevaPag();
  fin.forEach(l => { y += 3.6; d.texto(l, PW / 2, y, "I", 8, C.gris, "centro"); });

  // ---------- completar índice: puntos, número de página y enlace
  for (const p of pendientes) {
    const dst = destinos[p.clave]; if (!dst) continue;
    const pg = d.paginas[p.pagina], num = String(dst.pagina + 1);
    d.linea(p.xDots, p.y + 3.8, PW - M - ancho(num, "B", tamX) - 1.5, p.y + 3.8, C.gris, 0.5, true, pg.ops);
    d.texto(num, PW - M, p.y + 4, "B", tamX, C.rojo, "der", pg.ops);
    d.enlace(M, p.y - 0.5, ANCHO, lx, dst, pg.links);
  }
  // ---------- pies de página
  d.paginas.forEach((pg, i) => { d.ops = pg.ops; d.links = pg.links; pie(d, i + 1, yIndice); });
  return d.bytes(`TAIRA - ${op.titulo || "Catálogo"}`);
}

// ---------------------------------------------------------------- fotos (solo navegador)
async function fotoJPEG(url, lado = 260) {
  try {
    const r = await fetch(url); if (!r.ok) return null;
    const bmp = await createImageBitmap(await r.blob());
    const e = Math.min(1, lado / Math.max(bmp.width, bmp.height)), w = Math.max(1, Math.round(bmp.width * e)), h = Math.max(1, Math.round(bmp.height * e));
    const cv = document.createElement("canvas"); cv.width = w; cv.height = h;
    const cx = cv.getContext("2d"); cx.fillStyle = "#fff"; cx.fillRect(0, 0, w, h); cx.drawImage(bmp, 0, 0, w, h);
    const blob = await new Promise(ok => cv.toBlob(ok, "image/jpeg", 0.75));
    return { bytes: new Uint8Array(await blob.arrayBuffer()), w, h };
  } catch (e) { return null; }
}
async function bajarFotos(urls, avance) {
  const unicas = [...new Set(urls.filter(Boolean))], fotos = new Map(); let hechas = 0, i = 0;
  const trabajador = async () => { while (i < unicas.length) { const u = unicas[i++]; fotos.set(u, await fotoJPEG(u)); hechas++; avance && avance(hechas, unicas.length); } };
  await Promise.all(Array.from({ length: 8 }, trabajador));
  return fotos;
}

global.CatalogoPDF = { armar, bajarFotos, familia, talle };
})(typeof window !== "undefined" ? window : globalThis);
