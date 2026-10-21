/* xlsx-mini: leer y escribir Excel (.xlsx) sin librerías externas.
   Escritura: libro con estilos (fuentes, rellenos, bordes, formatos, combinadas, impresión).
   Lectura: lee por partes, así soporta hojas con un millón de filas vacías. */
(function (global) {
  "use strict";

  // ------------------------------------------------------------- ZIP (escritura, sin compresión)
  const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(b) { let c = 0xFFFFFFFF; for (let i = 0; i < b.length; i++) c = CRC[(c ^ b[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  function zip(files) { // files: [{name, data: string}]
    const enc = new TextEncoder(), partes = [], central = []; let off = 0;
    for (const f of files) {
      const nombre = enc.encode(f.name), datos = enc.encode(f.data), crc = crc32(datos);
      const h = new DataView(new ArrayBuffer(30));
      h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true); h.setUint16(8, 0, true);
      h.setUint16(10, 0, true); h.setUint16(12, 0x21, true); h.setUint32(14, crc, true); h.setUint32(18, datos.length, true);
      h.setUint32(22, datos.length, true); h.setUint16(26, nombre.length, true); h.setUint16(28, 0, true);
      partes.push(new Uint8Array(h.buffer), nombre, datos);
      const c = new DataView(new ArrayBuffer(46));
      c.setUint32(0, 0x02014b50, true); c.setUint16(4, 20, true); c.setUint16(6, 20, true); c.setUint16(8, 0x0800, true);
      c.setUint16(10, 0, true); c.setUint16(12, 0, true); c.setUint16(14, 0x21, true); c.setUint32(16, crc, true);
      c.setUint32(20, datos.length, true); c.setUint32(24, datos.length, true); c.setUint16(28, nombre.length, true);
      c.setUint32(42, off, true);
      central.push(new Uint8Array(c.buffer), nombre);
      off += 30 + nombre.length + datos.length;
    }
    const tamCentral = central.reduce((s, b) => s + b.length, 0);
    const e = new DataView(new ArrayBuffer(22));
    e.setUint32(0, 0x06054b50, true); e.setUint16(8, files.length, true); e.setUint16(10, files.length, true);
    e.setUint32(12, tamCentral, true); e.setUint32(16, off, true);
    return new Blob([...partes, ...central, new Uint8Array(e.buffer)], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
  }

  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "");
  const colL = n => { let s = ""; n++; while (n) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); } return s; };

  // ------------------------------------------------------------- Libro
  class Libro {
    constructor() { this.hojas = []; this.fonts = ['<font><sz val="10"/><name val="Calibri"/></font>']; this.fills = ['<fill><patternFill patternType="none"/></fill>', '<fill><patternFill patternType="gray125"/></fill>']; this.borders = ['<border><left/><right/><top/><bottom/><diagonal/></border>']; this.numFmts = []; this.xfs = ['<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>']; this.cache = new Map(); }
    _idx(arr, xml) { let i = arr.indexOf(xml); if (i < 0) { arr.push(xml); i = arr.length - 1; } return i; }
    /* st: {b, i, sz, color, bg, align:'left|center|right', valign, wrap, fmt:'"$" #,##0.00', borde:{bottom:'thin|medium', color}} */
    estilo(st = {}) {
      const k = JSON.stringify(st); if (this.cache.has(k)) return this.cache.get(k);
      const f = `<font>${st.b ? "<b/>" : ""}${st.i ? "<i/>" : ""}<sz val="${st.sz || 10}"/>${st.color ? `<color rgb="FF${st.color}"/>` : ""}<name val="Calibri"/></font>`;
      const fontId = this._idx(this.fonts, f);
      const fillId = st.bg ? this._idx(this.fills, `<fill><patternFill patternType="solid"><fgColor rgb="FF${st.bg}"/><bgColor indexed="64"/></patternFill></fill>`) : 0;
      let borderId = 0;
      if (st.borde) { const lado = st.borde.bottom ? `<bottom style="${st.borde.bottom}"><color rgb="FF${st.borde.color || "CCCCCC"}"/></bottom>` : "<bottom/>"; borderId = this._idx(this.borders, `<border><left/><right/><top/>${lado}<diagonal/></border>`); }
      let numFmtId = 0;
      if (st.fmt) { let i = this.numFmts.indexOf(st.fmt); if (i < 0) { this.numFmts.push(st.fmt); i = this.numFmts.length - 1; } numFmtId = 164 + i; }
      const al = (st.align || st.valign || st.wrap) ? `<alignment${st.align ? ` horizontal="${st.align}"` : ""} vertical="${st.valign || "center"}"${st.wrap ? ' wrapText="1"' : ""}/>` : "";
      const xf = `<xf numFmtId="${numFmtId}" fontId="${fontId}" fillId="${fillId}" borderId="${borderId}" xfId="0"${numFmtId ? ' applyNumberFormat="1"' : ""}${fontId ? ' applyFont="1"' : ""}${fillId ? ' applyFill="1"' : ""}${borderId ? ' applyBorder="1"' : ""}${al ? ' applyAlignment="1">' + al + "</xf>" : "/>"}`;
      this.xfs.push(xf); const id = this.xfs.length - 1; this.cache.set(k, id); return id;
    }
    hoja(nombre) { const h = new Hoja(this, nombre); this.hojas.push(h); return h; }
    blob() {
      const files = [];
      const sheets = this.hojas.map((h, i) => `<sheet name="${esc(h.nombre.slice(0, 31))}" sheetId="${i + 1}" r:id="rId${i + 1}"/>`).join("");
      files.push({ name: "[Content_Types].xml", data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>${this.hojas.map((h, i) => `<Override PartName="/xl/worksheets/sheet${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join("")}</Types>` });
      files.push({ name: "_rels/.rels", data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>` });
      files.push({ name: "xl/workbook.xml", data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>${sheets}</sheets>${this.hojas.some(h => h.titulos) ? `<definedNames>${this.hojas.map((h, i) => h.titulos ? `<definedName name="_xlnm.Print_Titles" localSheetId="${i}">'${esc(h.nombre.slice(0, 31))}'!$${h.titulos[0]}:$${h.titulos[1]}</definedName>` : "").join("")}</definedNames>` : ""}</workbook>` });
      files.push({ name: "xl/_rels/workbook.xml.rels", data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">${this.hojas.map((h, i) => `<Relationship Id="rId${i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${i + 1}.xml"/>`).join("")}<Relationship Id="rId${this.hojas.length + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>` });
      const nf = this.numFmts.length ? `<numFmts count="${this.numFmts.length}">${this.numFmts.map((f, i) => `<numFmt numFmtId="${164 + i}" formatCode="${esc(f)}"/>`).join("")}</numFmts>` : "";
      files.push({ name: "xl/styles.xml", data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">${nf}<fonts count="${this.fonts.length}">${this.fonts.join("")}</fonts><fills count="${this.fills.length}">${this.fills.join("")}</fills><borders count="${this.borders.length}">${this.borders.join("")}</borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="${this.xfs.length}">${this.xfs.join("")}</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>` });
      this.hojas.forEach((h, i) => files.push({ name: `xl/worksheets/sheet${i + 1}.xml`, data: h.xml() }));
      return zip(files);
    }
  }

  class Hoja {
    constructor(libro, nombre) { this.libro = libro; this.nombre = nombre; this.filas = []; this.anchos = []; this.merges = []; this.grilla = true; this.congelar = 0; this.pie = ""; this.ajustar = false; this.filtro = null; this.titulos = null; }
    /* celdas: valores; estilos: un id o un array de ids (uno por celda) */
    fila(celdas, estilos = 0, alto = null) { this.filas.push({ celdas, estilos, alto }); return this.filas.length; }
    combinar(fila, c1, c2) { this.merges.push(`${colL(c1)}${fila}:${colL(c2)}${fila}`); }
    xml() {
      const filas = this.filas.map((f, i) => {
        const r = i + 1;
        const cs = f.celdas.map((v, j) => {
          const s = Array.isArray(f.estilos) ? (f.estilos[j] || 0) : f.estilos, ref = colL(j) + r, sa = s ? ` s="${s}"` : "";
          if (v === null || v === undefined || v === "") return s ? `<c r="${ref}"${sa}/>` : "";
          if (typeof v === "number" && isFinite(v)) return `<c r="${ref}"${sa}><v>${v}</v></c>`;
          return `<c r="${ref}"${sa} t="inlineStr"><is><t xml:space="preserve">${esc(v)}</t></is></c>`;
        }).join("");
        return `<row r="${r}"${f.alto ? ` ht="${f.alto}" customHeight="1"` : ""}>${cs}</row>`;
      }).join("");
      const vista = `<sheetViews><sheetView workbookViewId="0"${this.grilla ? "" : ' showGridLines="0"'}>${this.congelar ? `<pane ySplit="${this.congelar}" topLeftCell="A${this.congelar + 1}" activePane="bottomLeft" state="frozen"/>` : ""}</sheetView></sheetViews>`;
      const cols = this.anchos.length ? `<cols>${this.anchos.map((w, i) => `<col min="${i + 1}" max="${i + 1}" width="${w}" customWidth="1"/>`).join("")}</cols>` : "";
      return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">${this.ajustar ? '<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>' : ""}${vista}<sheetFormatPr defaultRowHeight="15"/>${cols}<sheetData>${filas}</sheetData>${this.filtro ? `<autoFilter ref="${this.filtro}"/>` : ""}${this.merges.length ? `<mergeCells count="${this.merges.length}">${this.merges.map(m => `<mergeCell ref="${m}"/>`).join("")}</mergeCells>` : ""}<printOptions horizontalCentered="1"/><pageMargins left="0.4" right="0.4" top="0.5" bottom="0.5" header="0.3" footer="0.3"/><pageSetup paperSize="9" orientation="portrait"${this.ajustar ? ' fitToWidth="1" fitToHeight="0"' : ""}/>${this.pie ? `<headerFooter><oddFooter>${esc(this.pie)}</oddFooter></headerFooter>` : ""}</worksheet>`;
    }
  }

  // ------------------------------------------------------------- Lectura
  async function leer(file, maxVacias = 400) {
    const buf = new Uint8Array(await file.arrayBuffer());
    const dv = new DataView(buf.buffer);
    let eocd = -1;
    for (let i = buf.length - 22; i >= Math.max(0, buf.length - 70000); i--) if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
    if (eocd < 0) throw new Error("No es un archivo .xlsx válido");
    const n = dv.getUint16(eocd + 10, true); let p = dv.getUint32(eocd + 16, true);
    const entradas = {}, dec = new TextDecoder();
    for (let k = 0; k < n; k++) {
      const metodo = dv.getUint16(p + 10, true), comp = dv.getUint32(p + 20, true), ln = dv.getUint16(p + 28, true), le = dv.getUint16(p + 30, true), lc = dv.getUint16(p + 32, true), off = dv.getUint32(p + 42, true);
      const nombre = dec.decode(buf.subarray(p + 46, p + 46 + ln));
      entradas[nombre] = { metodo, comp, off };
      p += 46 + ln + le + lc;
    }
    const datos = e => { const lnl = dv.getUint16(e.off + 26, true), lel = dv.getUint16(e.off + 28, true), ini = e.off + 30 + lnl + lel; return buf.subarray(ini, ini + e.comp); };
    const flujo = e => { const b = new Blob([datos(e)]).stream(); return e.metodo === 8 ? b.pipeThrough(new DecompressionStream("deflate-raw")) : b; };
    const texto = async nombre => { const e = entradas[nombre]; if (!e) return ""; return await new Response(flujo(e)).text(); };

    const xmlDoc = s => new DOMParser().parseFromString(s, "application/xml");
    // textos compartidos
    const compartidos = [];
    const ss = await texto("xl/sharedStrings.xml");
    if (ss) for (const si of xmlDoc(ss).getElementsByTagName("si")) compartidos.push([...si.getElementsByTagName("t")].map(t => t.textContent).join(""));
    // hojas
    const wb = xmlDoc(await texto("xl/workbook.xml")), rels = xmlDoc(await texto("xl/_rels/workbook.xml.rels"));
    const destino = {}; for (const r of rels.getElementsByTagName("Relationship")) destino[r.getAttribute("Id")] = r.getAttribute("Target");
    const hojas = [];
    for (const s of wb.getElementsByTagName("sheet")) {
      const rid = s.getAttribute("r:id") || s.getAttributeNS("http://schemas.openxmlformats.org/officeDocument/2006/relationships", "id");
      let t = destino[rid] || ""; t = t.startsWith("/") ? t.slice(1) : "xl/" + t.replace(/^\.\//, "");
      if (entradas[t]) hojas.push({ nombre: s.getAttribute("name"), filas: await leerHoja(flujo(entradas[t]), compartidos, maxVacias) });
    }
    return hojas;
  }

  const ent = s => s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&#(\d+);/g, (_, d) => String.fromCharCode(+d)).replace(/&amp;/g, "&");
  const colN = l => { let n = 0; for (const ch of l) n = n * 26 + ch.charCodeAt(0) - 64; return n - 1; };
  async function leerHoja(stream, compartidos, maxVacias) {
    const lector = stream.pipeThrough(new TextDecoderStream()).getReader();
    const filas = []; let resto = "", vacias = 0, ultima = 0, fin = false;
    const reFila = /<row\b[^>]*?r="(\d+)"[^>]*?(?:\/>|>([\s\S]*?)<\/row>)/g;
    const reCelda = /<c\b([^>]*?)(?:\/>|>([\s\S]*?)<\/c>)/g;
    while (!fin) {
      const { value, done } = await lector.read();
      if (done) fin = true; else resto += value;
      let corte = fin ? resto.length : resto.lastIndexOf("</row>");
      if (corte < 0) continue;
      if (!fin) corte += 6;
      const bloque = resto.slice(0, corte); resto = resto.slice(corte);
      reFila.lastIndex = 0; let m;
      while ((m = reFila.exec(bloque))) {
        const r = +m[1], cont = m[2] || ""; const fila = []; let tiene = false;
        reCelda.lastIndex = 0; let c;
        while ((c = reCelda.exec(cont))) {
          const at = c[1], interior = c[2] || ""; const ref = /r="([A-Z]+)\d+"/.exec(at); if (!ref) continue;
          const tipo = (/t="(\w+)"/.exec(at) || [])[1];
          let v = null;
          if (tipo === "inlineStr") { const ts = interior.match(/<t[^>]*>([\s\S]*?)<\/t>/g); v = ts ? ent(ts.map(x => x.replace(/<[^>]+>/g, "")).join("")) : null; }
          else { const vv = /<v>([\s\S]*?)<\/v>/.exec(interior); if (vv) { v = tipo === "s" ? compartidos[+vv[1]] : tipo === "str" || tipo === "e" ? ent(vv[1]) : tipo === "b" ? vv[1] === "1" : Number(vv[1]); } }
          if (v !== null && v !== "") { fila[colN(ref[1])] = v; tiene = true; }
        }
        if (tiene) { filas[r - 1] = fila; vacias = 0; ultima = r; }
        else if (r - ultima > maxVacias) { fin = true; break; }
      }
      if (!fin && resto.length > 5e6) resto = resto.slice(-1e6);
    }
    try { await lector.cancel(); } catch (e) {}
    return Array.from(filas, f => f ? Array.from(f, x => x === undefined ? null : x) : []);
  }

  function descargar(blob, nombre) {
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = nombre;
    document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  global.XLMini = { Libro, leer, descargar, colL };
})(window);
