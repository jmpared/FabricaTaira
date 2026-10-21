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
const MM = 72 / 25.4, PW = 210, PH = 297;
const C = { rojo: [215, 20, 26], rojoOsc: [165, 14, 19], crema: [255, 246, 229], crema2: [253, 236, 200], tinta: [43, 29, 20],
  gris: [122, 106, 92], verde: [23, 102, 58], linea: [234, 215, 176], blanco: [255, 255, 255], sinFoto: [185, 168, 147] };
const WHATSAPP = "+54 9 3741 40-0146", WEB = "taira-pedidos.netlify.app";

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
  constructor() { this.paginas = []; this.imagenes = []; this.nueva(); }
  nueva() { this.ops = []; this.paginas.push(this.ops); }
  y(v) { return n2((PH - v) * MM); }
  rect(x, y, w, h, op = {}) {
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
    this.ops.push(p);
  }
  linea(x1, y1, x2, y2, c, lw) { this.ops.push(`${col(c, "s")} ${n2(lw)} w ${n2(x1 * MM)} ${this.y(y1)} m ${n2(x2 * MM)} ${this.y(y2)} l S`); }
  // y = línea de base, en mm desde arriba
  texto(s, x, y, f, tam, c, alin = "izq") {
    if (s == null || s === "") return;
    let X = x; const a = ancho(s, f, tam);
    if (alin === "der") X = x - a; else if (alin === "centro") X = x - a / 2;
    this.ops.push(`BT /${f} ${n2(tam)} Tf ${col(c, "f")} ${n2(X * MM)} ${this.y(y)} Td ${lit(s)} Tj ET`);
  }
  imagen(img, x, y, w, h) {
    if (!img.nombre) { img.nombre = "Im" + (this.imagenes.length + 1); this.imagenes.push(img); }
    this.ops.push(`q ${n2(w * MM)} 0 0 ${n2(h * MM)} ${n2(x * MM)} ${n2((PH - y - h) * MM)} cm /${img.nombre} Do Q`);
  }
  bytes(titulo) {
    const partes = [], offs = []; let largo = 0;
    const enc = new TextEncoder();
    const add = d => { const b = typeof d === "string" ? enc.encode(d) : d; partes.push(b); largo += b.length; };
    const obj = (n, cuerpo) => { offs[n] = largo; add(`${n} 0 obj\n`); (Array.isArray(cuerpo) ? cuerpo : [cuerpo]).forEach(add); add("\nendobj\n"); };
    add("%PDF-1.4\n"); add(new Uint8Array([37, 226, 227, 207, 211, 10]));
    // 1 catálogo, 2 páginas, 3-5 fuentes, luego imágenes, luego páginas y contenidos
    const nImg0 = 6, nPag0 = nImg0 + this.imagenes.length, total = nPag0 + this.paginas.length * 2;
    obj(1, `<< /Type /Catalog /Pages 2 0 R >>`);
    const kids = this.paginas.map((_, i) => `${nPag0 + i * 2} 0 R`).join(" ");
    obj(2, `<< /Type /Pages /Kids [${kids}] /Count ${this.paginas.length} >>`);
    ["H", "B", "I"].forEach((k, i) => obj(3 + i, `<< /Type /Font /Subtype /Type1 /BaseFont /${FUENTE[k]} /Encoding /WinAnsiEncoding >>`));
    this.imagenes.forEach((im, i) => obj(nImg0 + i, [`<< /Type /XObject /Subtype /Image /Width ${im.w} /Height ${im.h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${im.bytes.length} >>\nstream\n`, im.bytes, "\nendstream"]));
    const xobj = this.imagenes.length ? `/XObject << ${this.imagenes.map((im, i) => `/${im.nombre} ${nImg0 + i} 0 R`).join(" ")} >>` : "";
    this.paginas.forEach((ops, i) => {
      const n = nPag0 + i * 2, flujo = enc.encode(ops.join("\n"));
      obj(n, `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${n2(PW * MM)} ${n2(PH * MM)}] /Resources << /Font << /H 3 0 R /B 4 0 R /I 5 0 R >> ${xobj} >> /Contents ${n + 1} 0 R >>`);
      obj(n + 1, [`<< /Length ${flujo.length} >>\nstream\n`, flujo, "\nendstream"]);
    });
    const info = total; obj(info, `<< /Title ${lit(titulo)} /Author ${lit("TAIRA Fábrica y Distribuidora")} /Producer (TAIRA) >>`);
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
const M = 12, GAP = 5, ANCHO_FICHA = (PW - 2 * M - GAP) / 2, FOTO = 30, PAD = 3, ABAJO = PH - 14;
const T_CELDA = 7.3, L_CELDA = 3.1;

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
  let fr = med && promo ? [0.20, 0.36, 0.23, 0.21] : med ? [0.25, 0.47, 0.28] : promo ? [0.42, 0.30, 0.28] : [0.62, 0.38];
  if (!f.titulo && fr.length > 2) fr = [fr[0] + 0.12, fr[1] - 0.12, ...fr.slice(2)];
  const cols = ["v"].concat(med ? ["m"] : [], ["p"], promo ? ["q"] : []);
  const anchos = fr.map(a => a * anchoT);
  const tituloL = f.titulo ? partir(f.titulo, "B", 9.5, anchoT) : [];
  let h = PAD + tituloL.length * 4.1 + (tituloL.length ? 1.2 : 0) + 3.8;
  const filas = variantes.map(r => {
    let pr = r.x.precio == null ? null : Math.round(r.x.precio * (1 - (op.descuento || 0) / 100) * 100) / 100;
    const celdas = { v: partir(r.v, "H", T_CELDA, anchos[0] - 1), m: med ? partir(r.m, "H", T_CELDA, anchos[1] - 1) : [],
      p: pesos(pr), q: promo && pr != null && r.x.promo ? pesos(pr * 6 / 7) : "" };
    const alto = Math.max(celdas.v.length, celdas.m.length, 1) * L_CELDA + 1.3;
    h += alto;
    return { celdas, alto };
  });
  if (promo) h += 5.2;
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
  F.tituloL.forEach(l => { yy += 4.1; d.texto(l, x0, yy - 0.9, "B", 9.5, C.tinta); });
  if (F.tituloL.length) yy += 1.2;
  // encabezado de la tabla
  const posX = []; let acc = x0; F.anchos.forEach(a => { posX.push(acc); acc += a; });
  const nombres = { v: F.f.titulo ? "Talle" : "Variante", m: "Medida", p: "Precio", q: "6+1 c/u" };
  F.cols.forEach((c, i) => {
    const der = c === "p" || c === "q";
    d.texto(nombres[c], der ? posX[i] + F.anchos[i] - 0.6 : posX[i] + 0.6, yy + 2.6, "B", 6.3, C.gris, der ? "der" : "izq");
  });
  yy += 3.8; d.linea(x0, yy, acc, yy, C.rojo, 0.6);
  F.filas.forEach(r => {
    const base = yy + 0.6 + L_CELDA - 0.6;
    const medio = yy + r.alto / 2 + 1.1;
    F.cols.forEach((c, i) => {
      if (c === "v" || c === "m") r.celdas[c].forEach((l, k) => d.texto(l, posX[i] + 0.6, base + k * L_CELDA, "H", T_CELDA, C.tinta));
      else if (c === "p") d.texto(r.celdas.p, posX[i] + F.anchos[i] - 0.6, medio, "B", 8, C.tinta, "der");
      else d.texto(r.celdas.q, posX[i] + F.anchos[i] - 0.6, medio, "H", T_CELDA, C.verde, "der");
    });
    yy += r.alto; d.linea(x0, yy, acc, yy, C.linea, 0.3);
  });
  if (F.promo) {
    yy += 1.3; d.rect(x0, yy, 18, 3.6, { fill: C.verde, r: 1 });
    d.texto("PROMO 6+1", x0 + 9, yy + 2.55, "B", 6.5, C.blanco, "centro");
  }
}

function pie(d, n) {
  d.rect(0, PH - 8, PW, 8, { fill: C.rojo });
  d.texto("TAIRA · Fábrica y distribuidora", M, PH - 3, "B", 8, C.blanco);
  d.texto(`Pedidos por WhatsApp ${WHATSAPP} · ${WEB}`, PW / 2, PH - 3, "H", 8, C.blanco, "centro");
  d.texto(`Página ${n}`, PW - M, PH - 3, "H", 8, C.blanco, "der");
}

function armar(productos, op) {
  op = Object.assign({ titulo: "Catálogo mayorista", nota: "", descuento: 0, promo: true, medida: true, fotos: null, fecha: new Date().toLocaleDateString("es-AR") }, op);
  const d = new Doc(); let pag = 1, y = M;
  const saltar = () => { pie(d, pag); d.nueva(); pag++; y = M; };
  const ANCHO = PW - 2 * M;
  // encabezado
  d.rect(M, y, ANCHO, 25, { fill: C.rojo, r: 2.8 });
  const aT = ancho("TAIRA", "B", 40);
  d.texto("TAIRA", PW / 2, y + 15, "B", 40, C.blanco, "centro");
  d.texto("®", PW / 2 + aT / 2 + 0.6, y + 8.5, "B", 12, C.blanco);
  d.texto("FÁBRICA Y DISTRIBUIDORA", PW / 2, y + 21, "B", 10, C.blanco, "centro");
  y += 28;
  d.rect(M, y, ANCHO, 9, { fill: C.crema2, r: 1.8 });
  d.texto(`${op.titulo || "Catálogo"} · Veterinarias y pet shops`, PW / 2, y + 6.2, "B", 13, C.tinta, "centro");
  y += 13;
  const info = [[`Precios vigentes desde el ${op.fecha}${op.descuento ? ` · Incluye ${op.descuento}% de descuento` : ""}`, "H", C.tinta],
    ["Envío gratis en Misiones desde $150.000 · a todo el país desde $500.000", "B", C.rojoOsc]];
  if (op.promo) info.push(["PROMO en productos fabricados: llevando 6 del mismo producto y talle, 1 va de regalo (colores surtidos)", "B", C.rojoOsc]);
  info.push([`Pedidos por WhatsApp ${WHATSAPP} · Pedí online: ${WEB}` + (op.nota ? ` · ${op.nota}` : ""), "H", C.tinta]);
  info.forEach(([t, f, c]) => partir(t, f, 9, ANCHO).forEach(l => { y += 4.2; d.texto(l, PW / 2, y, f, 9, c, "centro"); }));
  y += 6;
  // fichas
  const fichas = agrupar(productos);
  for (const [clave, tit] of [["fabricado", "FABRICADOS POR TAIRA"], ["importado", "PRODUCTOS IMPORTADOS"]]) {
    const grupo = fichas.filter(f => f.linea === clave); if (!grupo.length) continue;
    if (y + 60 > ABAJO) saltar();
    d.rect(M, y, ANCHO, 9, { fill: C.rojoOsc, r: 1.8 }); d.texto(tit, M + 3, y + 6.3, "B", 13, C.blanco); y += 12;
    const cats = [...new Set(grupo.map(f => f.categoria))];
    for (const cat of cats) {
      const medidas = grupo.filter(f => f.categoria === cat).map(f => medirFicha(f, op));
      const filas = []; for (let k = 0; k < medidas.length; k += 2) filas.push(medidas.slice(k, k + 2));
      const altoFila = fl => Math.max(...fl.map(F => F.alto));
      if (y + 9 + altoFila(filas[0]) > ABAJO) saltar();
      d.texto(cat || "Otros", M, y + 5.5, "B", 12.5, C.rojo); d.linea(M, y + 7.5, M + ANCHO, y + 7.5, C.rojo, 1.2); y += 10.5;
      for (const fl of filas) {
        const h = altoFila(fl);
        if (y + h > ABAJO) { saltar(); d.texto(`${cat} (continuación)`, M, y + 4.5, "B", 10, C.gris); y += 7.5; }
        fl.forEach((F, i) => dibujarFicha(d, F, M + i * (ANCHO_FICHA + GAP), y, op));
        y += h + 3.5;
      }
      y += 3;
    }
  }
  const fin = partir("Los precios están sujetos a modificaciones. Las fotos son ilustrativas: colores y estampas pueden variar. Para más descuentos y formas de pago consultá con el vendedor.", "I", 8, ANCHO);
  if (y + fin.length * 3.6 + 2 > ABAJO) saltar();
  fin.forEach(l => { y += 3.6; d.texto(l, PW / 2, y, "I", 8, C.gris, "centro"); });
  pie(d, pag);
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
