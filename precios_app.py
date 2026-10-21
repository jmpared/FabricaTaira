"""TAIRA · Precios — app separada para administrar la lista de precios.

Trabaja sobre la misma tabla 'catalogo' que usan el catálogo online y la app de la fábrica:
lo que se aprueba acá se ve al instante en los dos.
Ningún cambio se publica directo: todo pasa por "propuestas" que el administrador aprueba.
"""
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
import requests
from supabase import create_client

import excel_precios as xl
import pdf_catalogo as pdfc

SUPABASE_URL = "https://gxnoakudooorcsnqcklm.supabase.co"
SUPABASE_KEY = "sb_publishable_CVNOChVw7tkKeC60qSHvWQ_3bTVbIMd"
ADMINS = {"mininopared@gmail.com", "eleminino.pared@gmail.com"}
ALERTA = 30  # % de variación que se marca para revisar

st.set_page_config(page_title="TAIRA · Precios", page_icon="💲", layout="wide")
st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 1.6rem;}
h1 {font-size: 1.85rem !important;}
div[data-testid="stMetric"] {background:#fff; border:1px solid #efdfbf; border-radius:14px; padding:10px 14px;}
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {border-radius:10px; font-weight:700;}
.sub {color:#7a6a5c; font-size:.9rem;}
</style>""", unsafe_allow_html=True)

ss = st.session_state
for k, v in {"autenticado": False, "access_token": None, "refresh_token": None, "vence": 0, "avisos": []}.items():
    ss.setdefault(k, v)
sb = create_client(SUPABASE_URL, SUPABASE_KEY)


# ================================================================ sesión y datos
def guardar_sesion(s, email=None):
    ss.access_token, ss.refresh_token = s.access_token, s.refresh_token
    ss.vence = time.time() + int(getattr(s, "expires_in", 3600) or 3600) - 120
    if email:
        ss.email_user = email.strip().lower()
        ss.user = email.split("@")[0].capitalize()


def asegurar_token():
    if ss.access_token and time.time() > ss.vence and ss.refresh_token:
        try:
            guardar_sesion(sb.auth.refresh_session(ss.refresh_token).session)
        except Exception:
            salir()
            st.warning("La sesión venció. Ingresá de nuevo.")
            st.stop()
    if ss.access_token:
        sb.postgrest.auth(ss.access_token)


def salir():
    try:
        sb.auth.sign_out()
    except Exception:
        pass
    for k in ("access_token", "refresh_token", "email_user", "user"):
        ss.pop(k, None)
    ss.autenticado = False
    leer.clear()


def es_admin():
    return ss.get("email_user", "") in ADMINS


def usuario():
    return ss.get("user", "")


@st.cache_data(ttl=60, show_spinner=False)
def leer(tabla, token, orden=None, desc=False):
    c = create_client(SUPABASE_URL, SUPABASE_KEY)
    c.postgrest.auth(token)
    q = c.table(tabla).select("*")
    if orden:
        q = q.order(orden, desc=desc)
    return q.execute().data or []


def datos(tabla, orden=None, desc=False):
    try:
        return leer(tabla, ss.access_token, orden, desc)
    except Exception as e:
        st.error(f"No se pudo leer '{tabla}': {e}")
        return []


def avisar(tipo, msg):
    ss.avisos.append((tipo, msg))


def rpc(fn, args):
    try:
        r = sb.rpc(fn, args).execute().data
        leer.clear()
        return r
    except Exception as e:
        avisar("error", f"No se pudo completar: {e}")
        return None


def num(v):
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def pesos(v):
    if v is None:
        return "—"
    return "$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def redondear(v, paso):
    return round(v, 2) if not paso else float(math.ceil(v / paso - 1e-9) * paso)


def fecha_local(ts):
    if not ts:
        return None
    t = pd.to_datetime(ts, utc=True, errors="coerce")
    return None if pd.isna(t) else t.tz_convert("America/Argentina/Buenos_Aires")


def medida(p):
    return " · ".join(str(x) for x in (p.get("ancho"), p.get("largo")) if x)


def catalogo():
    return datos("catalogo", "orden")


def ultimos_cambios():
    return {u["catalogo_id"]: u["ultimo_cambio"] for u in datos("precios_ultimo_cambio")}


def proponer(items, motivo):
    """items: lista de (id, precio)."""
    items = [{"id": int(i), "precio": round(float(p), 2)} for i, p in items if p and p > 0]
    if not items:
        avisar("info", "No había precios para proponer.")
        return
    n = rpc("proponer_precios", {"p_items": items, "p_motivo": motivo})
    if n is not None:
        avisar("success", f"Se crearon {n} propuestas ({motivo}). Revisalas en **Revisar y aprobar**: todavía no se publicaron.")


# ================================================================ páginas
def filtro_linea(p, linea):
    return linea == "Todas" or p.get("linea") == ("fabricado" if linea == "Fabricados" else "importado")


def pagina_lista():
    st.title("📋 Precios")
    cat = catalogo()
    ult = ultimos_cambios()
    pend = sum(1 for p in cat if p.get("precio_propuesto") is not None)
    if pend:
        a, b = st.columns([4, 1.3], vertical_alignment="center")
        a.info(f"Hay **{pend} precios propuestos** esperando aprobación.")
        if b.button("Revisar y aprobar →", use_container_width=True):
            st.switch_page(PAGINAS["aprobar"])

    f1, f2, f3 = st.columns([1.2, 2, 2])
    linea = f1.selectbox("Línea", ["Todas", "Fabricados", "Importados"], key="l_linea")
    cats_all = sorted({p.get("categoria") or "" for p in cat if filtro_linea(p, linea)})
    cats = f2.multiselect("Categorías", cats_all, placeholder="Todas", key="l_cats")
    busca = f3.text_input("Buscar", placeholder="Ej: collar pampa", key="l_busca")
    vis = [p for p in cat if filtro_linea(p, linea) and (not cats or p.get("categoria") in cats)
           and (not busca or xl.normalizar(busca) in xl.normalizar(p["nombre"] + " " + (p.get("categoria") or "")))]
    if not vis:
        st.warning("No hay productos con esos filtros.")
        return

    precios = [num(p.get("precio_publicado")) for p in vis if num(p.get("precio_publicado"))]
    m = st.columns(4)
    m[0].metric("Productos", len(vis))
    m[1].metric("Precio promedio", pesos(sum(precios) / len(precios)) if precios else "—")
    m[2].metric("Más barato", pesos(min(precios)) if precios else "—")
    fechas = [ult[p["id"]] for p in vis if ult.get(p["id"])]
    m[3].metric("Última actualización", fecha_local(max(fechas)).strftime("%d/%m/%Y") if fechas else "Carga inicial")

    df = pd.DataFrame([{
        "id": p["id"], "✔": p["id"] in ss.get("sel_ids", set()), "Producto": p["nombre"], "Categoría": p.get("categoria"),
        "Medida": medida(p), "Precio": num(p.get("precio_publicado")), "Nuevo precio": None,
        "En espera": num(p.get("precio_propuesto")),
        "Últ. cambio": (fecha_local(ult.get(p["id"])).strftime("%d/%m/%Y") if ult.get(p["id"]) else "Carga inicial"),
    } for p in vis])
    cfg = {"id": None, "✔": st.column_config.CheckboxColumn("✔", width="small"),
           "Precio": st.column_config.NumberColumn(format="$ %.2f"),
           "Nuevo precio": st.column_config.NumberColumn(format="$ %.2f", min_value=0.0, step=1.0),
           "En espera": st.column_config.NumberColumn(format="$ %.2f")}
    if not es_admin():
        st.dataframe(df.drop(columns=["✔", "Nuevo precio"]), hide_index=True, use_container_width=True, height=520, column_config=cfg)
        st.caption("🔒 Solo el administrador puede cambiar precios. Para descargar la lista, andá a **Exportar Excel / PDF**.")
        return
    st.caption("✏️ Escribí en **Nuevo precio** para cambiar uno por uno · ✔ tildá para usar una herramienta con varios a la vez.")
    clave = "lista_" + str(abs(hash((linea, tuple(cats), busca))))
    ed = st.data_editor(df, key=clave, hide_index=True, use_container_width=True, height=520, column_config=cfg,
                        disabled=["id", "Producto", "Categoría", "Medida", "Precio", "En espera", "Últ. cambio"])
    visibles = set(df["id"])
    ss.sel_ids = (set(ss.get("sel_ids", set())) - visibles) | set(ed.loc[ed["✔"], "id"])

    escritos = ed[ed["Nuevo precio"].map(num).notna() & (ed["Nuevo precio"].map(num) > 0)]
    a, b = st.columns(2)
    if a.button(f"💾 Proponer {len(escritos)} precios escritos", type="primary", disabled=escritos.empty, use_container_width=True):
        proponer([(r["id"], num(r["Nuevo precio"])) for _, r in escritos.iterrows()], "Cambio individual")
        st.rerun()
    n_sel = len(ss.sel_ids)
    if b.button(f"🧰 Usar una herramienta con los {n_sel} tildados", disabled=not n_sel, use_container_width=True):
        ss["h_alcance"] = "Los tildados en Precios"
        st.switch_page(PAGINAS["herramientas"])


# ---------------------------------------------------------------- herramientas
def elegir_productos(cat):
    """Devuelve los productos a los que se aplica la herramienta."""
    n_sel = len(ss.get("sel_ids", set()))
    alc = st.radio("¿A qué productos?", ["Por filtro", "Los tildados en Precios"], horizontal=True, key="h_alcance",
                   captions=["Línea, categoría, búsqueda, rango de precio", f"{n_sel} tildados"])
    if alc.startswith("Los tildados"):
        prods = [p for p in cat if p["id"] in ss.get("sel_ids", set())]
        if not prods:
            st.info("No hay productos tildados. Tildalos en **Precios** o usá el filtro.")
        return prods, "selección"
    c = st.columns([1.1, 2, 1.6])
    linea = c[0].selectbox("Línea", ["Todas", "Fabricados", "Importados"], key="h_linea")
    cats_all = sorted({p.get("categoria") or "" for p in cat if filtro_linea(p, linea)})
    cats = c[1].multiselect("Categorías", cats_all, placeholder="Todas", key="h_cats")
    busca = c[2].text_input("Nombre contiene", placeholder="Ej: T.3, pampa, comedero", key="h_busca")
    d = st.columns([1, 1, 1.4])
    pmin = d[0].number_input("Precio desde $", min_value=0.0, value=0.0, step=500.0, key="h_pmin")
    pmax = d[1].number_input("Precio hasta $ (0 = sin tope)", min_value=0.0, value=0.0, step=500.0, key="h_pmax")
    promo = d[2].selectbox("Promo 6+1", ["Todos", "Solo con promo", "Solo sin promo"], key="h_promo")
    prods = []
    for p in cat:
        pr = num(p.get("precio_publicado"))
        if not filtro_linea(p, linea) or (cats and p.get("categoria") not in cats):
            continue
        if busca and xl.normalizar(busca) not in xl.normalizar(p["nombre"]):
            continue
        if pmin and (pr is None or pr < pmin) or pmax and (pr is None or pr > pmax):
            continue
        if promo == "Solo con promo" and not p.get("promo") or promo == "Solo sin promo" and p.get("promo"):
            continue
        prods.append(p)
    partes = [linea.lower()] if linea != "Todas" else []
    if cats:
        partes.append(", ".join(cats))
    if busca:
        partes.append(f"'{busca}'")
    if pmin or pmax:
        partes.append(f"precios {pesos(pmin)}–{pesos(pmax) if pmax else '∞'}")
    return prods, " · ".join(partes) or "todos"


def redondeo_ui(key):
    c = st.columns(2)
    modo = c[0].selectbox("Redondeo", ["Sin redondeo", "Múltiplo de $10", "Múltiplo de $50", "Múltiplo de $100", "Múltiplo de $500",
                                       "Terminar en 90", "Terminar en 99"], index=1, key=f"{key}_red")
    sentido = c[1].selectbox("Hacia", ["Arriba", "El más cercano", "Abajo"], key=f"{key}_sent")
    return modo, sentido


def aplicar_redondeo(v, modo, sentido):
    if v is None or modo == "Sin redondeo":
        return round(v, 2) if v is not None else None
    f = {"Arriba": math.ceil, "Abajo": math.floor}.get(sentido, round)
    if modo.startswith("Múltiplo"):
        paso = int(modo.split("$")[1])
        return float(max(f(v / paso - (1e-9 if f is math.ceil else 0)) * paso, paso))
    fin = 90 if modo.endswith("90") else 99
    base = f((v - fin) / 100 - (1e-9 if f is math.ceil else 0)) * 100 + fin
    return float(max(base, fin))


def familia(nombre):
    return re.sub(r"\s+(T\.\s*\d+|N°\s*\d+|[SML]|XL)\s*$", "", nombre.strip(), flags=re.I).strip()


def pagina_herramientas():
    st.title("🧰 Herramientas de precios")
    if not es_admin():
        st.info("🔒 Solo el administrador puede usar las herramientas que cambian precios. Las **Calculadoras** están disponibles para todos.")
        return
    cat = catalogo()
    herramienta = st.selectbox("Herramienta", [
        "📈 Aumento o baja en %",
        "➕ Sumar o restar un monto",
        "🎯 Poner un precio fijo",
        "🪜 Aumento escalonado por rango de precio",
        "📊 Ajuste por inflación acumulada",
        "📏 Escalera de talles (familia de productos)",
        "🔢 Solo redondear precios",
        "↩️ Deshacer una actualización",
    ], key="h_tool")
    st.divider()

    if herramienta.startswith("↩️"):
        return herramienta_deshacer(cat)
    if herramienta.startswith("📏"):
        return herramienta_talles(cat)

    prods, alcance_txt = elegir_productos(cat)
    st.markdown("**Cambio a aplicar**")
    if herramienta.startswith("📈"):
        pct = st.number_input("Porcentaje (negativo para bajar)", value=10.0, step=0.5, key="h_pct")
        calc = lambda a: a * (1 + pct / 100)
        desc = f"{pct:+g}%"
    elif herramienta.startswith("➕"):
        monto = st.number_input("Monto en $ (negativo para restar)", value=500.0, step=50.0, key="h_monto")
        calc = lambda a: a + monto
        desc = f"{'+' if monto >= 0 else '−'}{pesos(abs(monto))}"
    elif herramienta.startswith("🎯"):
        fijo = st.number_input("Precio para todos los elegidos $", min_value=0.0, value=5000.0, step=100.0, key="h_fijo")
        calc = lambda a: fijo
        desc = f"fijo {pesos(fijo)}"
    elif herramienta.startswith("🪜"):
        st.caption("Ejemplo: los productos baratos suben más que los caros. Editá los tramos (hasta 0 = sin tope).")
        tramos = st.data_editor(pd.DataFrame([{"Desde $": 0.0, "Hasta $": 5000.0, "Aumento %": 15.0},
                                              {"Desde $": 5000.0, "Hasta $": 20000.0, "Aumento %": 10.0},
                                              {"Desde $": 20000.0, "Hasta $": 0.0, "Aumento %": 8.0}]),
                                num_rows="dynamic", hide_index=True, key="h_tramos", use_container_width=True)
        tr = [(num(r["Desde $"]) or 0, num(r["Hasta $"]) or 0, num(r["Aumento %"]) or 0) for _, r in tramos.iterrows()]

        def calc(a):
            for d_, h_, p_ in tr:
                if a >= d_ and (not h_ or a < h_):
                    return a * (1 + p_ / 100)
            return a
        desc = "escalonado " + " / ".join(f"{p_:+g}%" for _, _, p_ in tr)
    elif herramienta.startswith("📊"):
        modo = st.radio("Cómo cargar la inflación", ["Mismo % todos los meses", "Un % por mes"], horizontal=True, key="h_inf_modo")
        if modo.startswith("Mismo"):
            c = st.columns(2)
            mens = c[0].number_input("% mensual", value=3.0, step=0.1, key="h_inf_pct")
            meses = c[1].number_input("Meses", min_value=1, value=3, step=1, key="h_inf_meses")
            factor = (1 + mens / 100) ** meses
        else:
            txt = st.text_input("Porcentaje de cada mes, separados por punto y coma", value="3,5; 2,7; 2,4", key="h_inf_lista")
            partes = re.split(r"[;\n/]+", txt) if re.search(r"[;\n/]", txt) else (txt.split(", ") if ", " in txt else txt.split())
            vals = [xl.a_numero(x) for x in partes if xl.a_numero(x) is not None]
            st.caption("Meses tomados: " + ", ".join(f"{v:g}%" for v in vals))
            factor = math.prod(1 + v / 100 for v in vals) if vals else 1
        aplicar = st.slider("Trasladar a precios (%)", 0, 100, 100, 5, key="h_inf_tras",
                            help="Si no querés trasladar toda la inflación, bajá este valor.")
        total = (factor - 1) * aplicar / 100
        st.info(f"Inflación acumulada: **{(factor - 1) * 100:+.2f}%** · se aplica **{total * 100:+.2f}%**")
        calc = lambda a: a * (1 + total)
        desc = f"inflación {total * 100:+.1f}%"
    else:  # solo redondear
        calc = lambda a: a
        desc = "redondeo"
    modo_r, sentido = redondeo_ui("h")
    if herramienta.startswith("🔢"):
        desc = f"redondeo ({modo_r.lower()})"
    vista_y_proponer(prods, calc, modo_r, sentido, f"{desc} · {alcance_txt}")


def vista_y_proponer(prods, calc, modo_r, sentido, motivo_def):
    filas = []
    for p in prods:
        a = num(p.get("precio_publicado"))
        if a is None:
            continue
        n = aplicar_redondeo(calc(a), modo_r, sentido)
        if n and n > 0 and abs(n - a) >= 0.01:
            filas.append({"id": p["id"], "Producto": p["nombre"], "Categoría": p.get("categoria"), "Actual": a, "Nuevo": n,
                          "Variación %": round((n / a - 1) * 100, 1)})
    st.divider()
    if not filas:
        st.caption("Con esta configuración no cambia ningún precio.")
        return
    df = pd.DataFrame(filas)
    m = st.columns(4)
    m[0].metric("Productos que cambian", len(df))
    m[1].metric("Variación promedio", f"{df['Variación %'].mean():+.1f}%")
    m[2].metric("Menor / mayor", f"{df['Variación %'].min():+.1f}% / {df['Variación %'].max():+.1f}%")
    m[3].metric("Suma de la lista", pesos(df["Nuevo"].sum()), delta=f"{(df['Nuevo'].sum() / df['Actual'].sum() - 1) * 100:+.1f}%")
    st.dataframe(df.drop(columns=["id"]).style.map(estilo_variacion, subset=["Variación %"])
                 .format({"Actual": pesos, "Nuevo": pesos, "Variación %": lambda v: f"{v:+.1f}%"}),
                 hide_index=True, use_container_width=True, height=min(420, 38 + 35 * len(df)))
    motivo = st.text_input("Motivo (queda en el historial)", value=motivo_def, key="h_motivo_" + str(abs(hash(motivo_def))))
    if st.button(f"Crear {len(df)} propuestas", type="primary"):
        proponer([(r["id"], r["Nuevo"]) for _, r in df.iterrows()], motivo)
        st.switch_page(PAGINAS["aprobar"])


def herramienta_talles(cat):
    st.caption("Ordena los precios de una familia por talle: elegís el precio del talle más chico y cuánto sube cada talle.")
    fams = {}
    for p in cat:
        fams.setdefault(familia(p["nombre"]), []).append(p)
    fams = {k: v for k, v in fams.items() if len(v) > 1}
    fam = st.selectbox("Familia", sorted(fams), index=None, placeholder="Ej: Collar liso simple", key="h_fam")
    if not fam:
        return
    grupo = fams[fam]
    c = st.columns(3)
    base = c[0].number_input("Precio del primer talle $", min_value=0.0, value=float(num(grupo[0].get("precio_publicado")) or 0), step=50.0, key="h_base")
    tipo = c[1].selectbox("Cada talle sube", ["%", "$"], key="h_tipo_paso")
    paso = c[2].number_input("Cuánto", value=5.0 if tipo == "%" else 200.0, step=1.0, key="h_paso")
    modo_r, sentido = redondeo_ui("t")
    nuevos = {}
    v = base
    for i, p in enumerate(grupo):
        if i:
            v = v * (1 + paso / 100) if tipo == "%" else v + paso
        nuevos[p["id"]] = v
    vista_y_proponer(grupo, lambda a, _it=iter([nuevos[p["id"]] for p in grupo if num(p.get("precio_publicado")) is not None]): next(_it),
                     modo_r, sentido, f"escalera de talles {fam}: base {pesos(base)}, +{paso:g}{tipo} por talle")


def herramienta_deshacer(cat):
    hist = datos("precios_historial", "fecha", desc=True)
    if not hist:
        st.info("Todavía no hay actualizaciones aprobadas para deshacer.")
        return
    lotes = {}
    for h in hist:
        f = fecha_local(h["fecha"])
        clave = f"{f:%d/%m/%Y %H:%M} · {h.get('motivo') or 'sin motivo'}"
        lotes.setdefault(clave, []).append(h)
    lote = st.selectbox("Actualización a deshacer", list(lotes), index=None, placeholder="Elegí una",
                        format_func=lambda k: f"{k} ({len(lotes[k])} productos)", key="h_lote")
    if not lote:
        return
    por_id = {p["id"]: p for p in cat}
    filas, cambiados = [], 0
    for h in lotes[lote]:
        p = por_id.get(h.get("catalogo_id"))
        if not p:
            continue
        if num(p.get("precio_publicado")) != num(h.get("precio_nuevo")):
            cambiados += 1
            continue
        filas.append(p)
    if cambiados:
        st.warning(f"{cambiados} productos ya tuvieron otro cambio después: no se tocan.")
    anteriores = {h["catalogo_id"]: num(h["precio_anterior"]) for h in lotes[lote]}
    vista_y_proponer(filas, lambda a, _ids=iter([p["id"] for p in filas]): anteriores[next(_ids)],
                     "Sin redondeo", "Arriba", f"Deshacer: {lote}")


# ---------------------------------------------------------------- calculadoras
def pagina_calculadoras():
    st.title("🧮 Calculadoras")
    st.caption("Para hacer cuentas rápidas. No cambian ningún precio.")
    t = st.radio("Calculadora", ["Margen y ganancia", "Comisión de cobro", "Promo 6+1 / 10+2", "IVA", "Variación entre dos precios"],
                 horizontal=True, label_visibility="collapsed", key="c_tool")
    st.write("")
    if t == "Margen y ganancia":
        a, b = st.columns(2)
        with a.container(border=True):
            st.markdown("**Tengo el costo → ¿a cuánto vendo?**")
            costo = st.number_input("Costo $", min_value=0.0, value=1000.0, step=50.0, key="c_costo")
            modo = st.radio("Quiero", ["Markup (sobre el costo)", "Margen (sobre el precio)"], key="c_modo")
            pct = st.number_input("%", min_value=0.0, max_value=95.0 if modo.startswith("Margen") else 1000.0, value=40.0, step=1.0, key="c_pct")
            precio = costo * (1 + pct / 100) if modo.startswith("Markup") else costo / (1 - pct / 100)
            st.metric("Precio de venta", pesos(precio), delta=f"ganancia {pesos(precio - costo)}")
        with b.container(border=True):
            st.markdown("**Tengo costo y precio → ¿cuánto gano?**")
            c2 = st.number_input("Costo $", min_value=0.0, value=1000.0, step=50.0, key="c_costo2")
            p2 = st.number_input("Precio de venta $", min_value=0.0, value=1500.0, step=50.0, key="c_precio2")
            if c2 and p2:
                st.metric("Ganancia por unidad", pesos(p2 - c2))
                st.metric("Markup (sobre costo)", f"{(p2 / c2 - 1) * 100:.1f}%")
                st.metric("Margen (sobre precio)", f"{(1 - c2 / p2) * 100:.1f}%")
    elif t == "Comisión de cobro":
        st.markdown("¿A cuánto tengo que cobrar para que me quede un monto neto, después de la comisión de la plataforma?")
        presets = {"Pago Nube · 1 día": 6.09, "Pago Nube · 7 días": 4.39, "Pago Nube · 14 días": 3.49, "Pago Nube · 30 días": 2.97,
                   "Transferencia Pago Nube": 1.5, "Otra": 5.0}
        c = st.columns(3)
        neto = c[0].number_input("Quiero recibir $", min_value=0.0, value=10000.0, step=100.0, key="c_neto")
        pre = c[1].selectbox("Medio de cobro", list(presets), key="c_preset")
        com = c[2].number_input("Comisión %", min_value=0.0, max_value=50.0, value=presets[pre], step=0.1, key=f"c_com_{pre}")
        iva = st.checkbox("La comisión se cobra + IVA (21%)", value=True, key="c_iva")
        total_com = com * (1.21 if iva else 1)
        cobrar = neto / (1 - total_com / 100)
        m = st.columns(3)
        m[0].metric("Cobrar", pesos(cobrar))
        m[1].metric("Se lleva la plataforma", pesos(cobrar - neto))
        m[2].metric("Recargo a aplicar", f"{(cobrar / neto - 1) * 100:.2f}%")
        st.caption("Plan Esencial de Tiendanube (Argentina). Revisá que los porcentajes sigan vigentes antes de usarlos.")
    elif t == "Promo 6+1 / 10+2":
        c = st.columns(2)
        precio = c[0].number_input("Precio unitario de lista $", min_value=0.0, value=3000.0, step=50.0, key="c_promo_p")
        promo = c[1].radio("Promo", ["6+1", "10+2"], horizontal=True, key="c_promo_t")
        lleva, paga = (7, 6) if promo == "6+1" else (12, 10)
        m = st.columns(3)
        m[0].metric(f"Paga por {lleva} unidades", pesos(precio * paga))
        m[1].metric("Le sale cada una", pesos(precio * paga / lleva))
        m[2].metric("Descuento equivalente", f"{(1 - paga / lleva) * 100:.1f}%")
        st.divider()
        objetivo = st.number_input("Si querés que con la promo cada unidad te quede en $…", min_value=0.0, value=2500.0, step=50.0, key="c_promo_obj")
        st.metric("…el precio de lista tiene que ser", pesos(objetivo * lleva / paga))
    elif t == "IVA":
        c = st.columns(3)
        monto = c[0].number_input("Monto $", min_value=0.0, value=10000.0, step=100.0, key="c_iva_m")
        tasa = c[1].selectbox("Alícuota", [21.0, 10.5, 27.0], format_func=lambda x: f"{x:g}%", key="c_iva_t")
        sentido = c[2].radio("El monto es", ["Sin IVA", "Con IVA"], key="c_iva_s")
        if sentido == "Sin IVA":
            st.metric("Con IVA", pesos(monto * (1 + tasa / 100)), delta=f"IVA {pesos(monto * tasa / 100)}")
        else:
            neto = monto / (1 + tasa / 100)
            st.metric("Sin IVA", pesos(neto), delta=f"IVA {pesos(monto - neto)}", delta_color="off")
    else:
        c = st.columns(2)
        a = c[0].number_input("Precio anterior $", min_value=0.0, value=1000.0, step=50.0, key="c_var_a")
        b = c[1].number_input("Precio nuevo $", min_value=0.0, value=1150.0, step=50.0, key="c_var_b")
        if a:
            st.metric("Variación", f"{(b / a - 1) * 100:+.2f}%", delta=pesos(b - a))


# ---------------------------------------------------------------- exportar
SITIO_FOTOS = "https://taira-pedidos.netlify.app/"


@st.cache_data(ttl=6 * 3600, show_spinner=False, max_entries=2000)
def bajar_foto(ruta):
    """Baja una foto del catálogo online y la achica para el PDF. Queda guardada 6 horas."""
    if not ruta:
        return None
    url = ruta if ruta.startswith("http") else SITIO_FOTOS + ruta.lstrip("/")
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return pdfc.achicar_foto(r.content)
    except Exception:
        return None


def bajar_fotos(rutas):
    rutas = [r for r in dict.fromkeys(rutas) if r]
    with ThreadPoolExecutor(max_workers=12) as ex:
        return dict(zip(rutas, ex.map(bajar_foto, rutas)))


def pagina_exportar():
    st.title("📥 Exportar Excel o PDF")
    cat = catalogo()
    tipo = st.radio("Tipo de archivo", ["📄 Catálogo PDF para clientes (con fotos)", "🎨 Lista Excel para clientes (con diseño)",
                                        "🛠️ Planilla de trabajo (para editar y volver a subir)"], key="e_tipo")
    c = st.columns([1.1, 2.5])
    linea = c[0].selectbox("Línea", ["Todas", "Fabricados", "Importados"], key="e_linea")
    cats_all = []
    for p in cat:
        if filtro_linea(p, linea) and p.get("categoria") not in cats_all:
            cats_all.append(p.get("categoria"))
    cats = c[1].multiselect("Categorías (vacío = todas)", cats_all, placeholder="Todas", key="e_cats")
    prods = [p for p in cat if filtro_linea(p, linea) and (not cats or p.get("categoria") in cats)]
    st.caption(f"{len(prods)} productos")
    hoy = datetime.now().strftime("%d/%m/%Y")
    if tipo.startswith("📄"):
        a, b = st.columns(2)
        titulo = a.text_input("Título", value="Catálogo mayorista", key="p_titulo")
        nota = b.text_input("Nota extra (opcional)", placeholder="Ej: Lista especial revendedores", key="p_nota")
        d = st.columns(4)
        desc = d[0].number_input("Descuento para este PDF %", min_value=0.0, max_value=90.0, value=0.0, step=1.0, key="p_desc",
                                 help="Solo cambia el PDF, no los precios publicados.")
        promo = d[1].checkbox("Precio promo 6+1", value=True, key="p_promo")
        med = d[2].checkbox("Medidas", value=True, key="p_med")
        con_fotos = d[3].checkbox("Con fotos", value=True, key="p_fotos", help="Sin fotos sale un PDF mucho más liviano.")
        datos_p = [{"nombre": p["nombre"], "categoria": p.get("categoria"), "linea": p.get("linea"), "ancho": p.get("ancho"),
                    "largo": p.get("largo"), "precio": num(p.get("precio_publicado")), "promo": p.get("promo"),
                    "foto_url": p.get("foto_url")} for p in prods]
        clave = (tuple(p["nombre"] for p in prods), titulo, nota, desc, promo, med, con_fotos)
        if st.button("📄 Armar catálogo PDF", type="primary", disabled=not prods):
            with st.spinner("Armando el catálogo… con fotos puede tardar un minuto la primera vez."):
                fotos = bajar_fotos([p["foto_url"] for p in datos_p]) if con_fotos else None
                ss.pdf_cat = (clave, pdfc.catalogo_pdf(datos_p, hoy, fotos, desc, promo, med, titulo, nota),
                              sum(1 for v in (fotos or {}).values() if v is None))
        if ss.get("pdf_cat") and ss.pdf_cat[0] == clave:
            _, archivo, faltan = ss.pdf_cat
            tam = f"{len(archivo) / 1e6:.1f} MB" if len(archivo) >= 1e6 else f"{len(archivo) / 1e3:.0f} KB"
            st.success(f"Catálogo listo · {tam}")
            if faltan:
                st.warning(f"{faltan} fotos no se pudieron bajar del catálogo online; esas fichas salen sin foto.")
            st.download_button("📥 Descargar catálogo PDF", archivo, file_name=f"Catalogo_TAIRA_{date.today():%d-%m-%Y}.pdf",
                               mime="application/pdf", type="primary")
        elif ss.get("pdf_cat"):
            st.caption("Cambiaste opciones: volvé a tocar **Armar catálogo PDF**.")
        st.caption("Fichas con foto, talles, medidas y precio, agrupadas por línea y categoría. Para mandar por WhatsApp o imprimir en A4. "
                   "Toma los precios **publicados**.")
    elif tipo.startswith("🎨"):
        a, b = st.columns(2)
        titulo = a.text_input("Título", value="Lista de precios mayorista", key="e_titulo")
        nota = b.text_input("Nota extra (opcional)", placeholder="Ej: Lista especial revendedores", key="e_nota")
        d = st.columns(3)
        desc = d[0].number_input("Descuento para esta lista %", min_value=0.0, max_value=90.0, value=0.0, step=1.0, key="e_desc",
                                 help="Solo cambia el archivo, no los precios publicados.")
        promo = d[1].checkbox("Columna con precio promo 6+1", value=True, key="e_promo")
        med = d[2].checkbox("Columna de medidas", value=True, key="e_med")
        datos_x = [{"nombre": p["nombre"], "categoria": p.get("categoria"), "linea": p.get("linea"), "ancho": p.get("ancho"),
                    "largo": p.get("largo"), "precio": num(p.get("precio_publicado")), "promo": p.get("promo")} for p in prods]
        st.download_button("📥 Descargar lista para clientes", xl.excel_lista_clientes(datos_x, hoy, desc, promo, med, titulo, nota),
                           file_name=f"Lista_precios_TAIRA_{date.today():%d-%m-%Y}.xlsx", type="primary",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", disabled=not prods)
        st.caption("Agrupada por línea y categoría, con encabezado TAIRA, envíos y promo. Lista para mandar por WhatsApp o imprimir en A4.")
    else:
        ult = ultimos_cambios()
        exp = pd.DataFrame([{
            "ID TAIRA": p["id"], "Producto": p["nombre"], "Categoría": p.get("categoria"),
            "Línea": "Fabricado" if p.get("linea") == "fabricado" else "Importado", "Medida": medida(p),
            "Precio actual": num(p.get("precio_publicado")),
            "Últ. cambio": (fecha_local(ult.get(p["id"])).strftime("%d/%m/%Y") if ult.get(p["id"]) else "Carga inicial"),
        } for p in prods])
        st.download_button("📥 Descargar planilla de trabajo", xl.excel_lista(exp, hoy), type="primary",
                           file_name=f"planilla_precios_{date.today():%Y-%m-%d}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", disabled=not prods)
        st.caption("Completá la columna amarilla **Precio nuevo** y subila en **Importar Excel** para comparar y aprobar.")


def estilo_variacion(v):
    if v is None or v != v:
        return ""
    if v >= ALERTA:
        return "background-color:#f8c4c4;color:#7a0b0e;font-weight:700"
    if v > 0:
        return "background-color:#fde2e2;color:#a50e13"
    if v < 0:
        return "background-color:#dff5e6;color:#17663a"
    return "color:#7a6a5c"


def pagina_aprobar():
    st.title("✅ Revisar y aprobar")
    cat = catalogo()
    pend = [p for p in cat if p.get("precio_propuesto") is not None]
    if not pend:
        st.success("No hay precios esperando aprobación. Lo que ves en el catálogo online está al día.")
        return
    df = pd.DataFrame([{
        "id": p["id"], "✔": True, "Producto": p["nombre"], "Categoría": p.get("categoria"),
        "Actual": num(p.get("precio_publicado")), "Nuevo": num(p.get("precio_propuesto")),
        "Variación %": (round((num(p["precio_propuesto"]) / num(p["precio_publicado"]) - 1) * 100, 1) if num(p.get("precio_publicado")) else None),
        "Motivo": p.get("motivo_propuesta") or "",
    } for p in pend])
    var = df["Variación %"].dropna()
    m = st.columns(4)
    m[0].metric("Propuestas", len(df))
    m[1].metric("Suben / bajan", f"{int((var > 0).sum())} / {int((var < 0).sum())}")
    m[2].metric("Variación promedio", f"{var.mean():+.1f}%" if len(var) else "—")
    m[3].metric("Mayor cambio", f"{var.abs().max():.1f}%" if len(var) else "—")
    grandes = int((var.abs() >= ALERTA).sum())
    if grandes:
        st.warning(f"⚠️ {grandes} productos cambian {ALERTA}% o más (en rojo fuerte). Revisalos: puede ser un error de carga.")

    st.dataframe(df.drop(columns=["id", "✔"]).style.map(estilo_variacion, subset=["Variación %"])
                 .format({"Actual": pesos, "Nuevo": pesos, "Variación %": lambda v: "—" if v != v or v is None else f"{v:+.1f}%"}),
                 hide_index=True, use_container_width=True, height=min(420, 38 + 35 * len(df)))

    if not es_admin():
        st.info("🔒 Solo el administrador puede aprobar o descartar.")
        return
    with st.expander("Elegir cuáles aprobar (por defecto, todas)"):
        ed = st.data_editor(df[["id", "✔", "Producto", "Actual", "Nuevo", "Variación %"]], key="ed_aprobar", hide_index=True,
                            use_container_width=True, disabled=["id", "Producto", "Actual", "Nuevo", "Variación %"],
                            column_config={"id": None, "Actual": st.column_config.NumberColumn(format="$ %.2f"),
                                           "Nuevo": st.column_config.NumberColumn(format="$ %.2f")})
    ids = [int(i) for i in ed.loc[ed["✔"], "id"]]
    a, b = st.columns(2)
    if a.button(f"✅ Aprobar y publicar {len(ids)}", type="primary", disabled=not ids, use_container_width=True):
        n = rpc("aprobar_precios", {"p_ids": ids, "p_usuario": usuario()})
        if n is not None:
            avisar("success", f"¡Listo! Se publicaron {n} precios. El catálogo online y la app de la fábrica ya los muestran.")
        st.rerun()
    if b.button(f"🗑️ Descartar {len(ids)}", disabled=not ids, use_container_width=True):
        n = rpc("descartar_propuestas", {"p_ids": ids})
        if n is not None:
            avisar("info", f"Se descartaron {n} propuestas. Los precios publicados no cambiaron.")
        st.rerun()


def estilo_estado(fila):
    color = {"Sube": "#fde2e2", "Baja": "#dff5e6", "Igual": "#f4f1ea", "No encontrado": "#fff1cc",
             "Repetido": "#fff1cc", "Sin precio": "#fff1cc"}.get(fila["Estado"], "")
    return [f"background-color:{color}" if color else "" for _ in fila]


def pagina_importar():
    st.title("📤 Importar Excel y comparar")
    st.markdown("<div class='sub'>Subí un Excel con precios nuevos (puede ser la lista que descargás de acá con la columna "
                "<b>Precio nuevo</b> completa, o tu Excel de siempre). Te muestro la comparación antes de tocar nada.</div>",
                unsafe_allow_html=True)
    arch = st.file_uploader("Archivo", type=["xlsx", "csv"], label_visibility="collapsed")
    if not arch:
        return
    try:
        df_in = xl.leer_archivo(arch, arch.name)
    except Exception as e:
        st.error(f"No pude leer el archivo: {e}")
        return
    comp, info = xl.comparar(df_in, catalogo())
    if comp is None:
        st.error("No encontré las columnas de producto y precio. El archivo necesita una columna 'Producto' (o 'ID') y otra de 'Precio'.")
        st.caption("Columnas encontradas: " + ", ".join(map(str, df_in.columns)))
        return
    st.caption(f"Columnas usadas → producto: **{info['col_producto'] or '—'}** · ID TAIRA: **{info['col_id'] or '—'}** · precio: **{info['col_precio']}**")
    if comp.empty:
        st.info("El archivo no trae precios nuevos para comparar. Si es la lista descargada de acá, completá la columna amarilla **Precio nuevo** y volvé a subirla.")
        return

    cambia = comp[comp["Estado"].isin(["Sube", "Baja"])]
    revisar = comp[comp["Estado"].isin(["No encontrado", "Repetido", "Sin precio"])]
    m = st.columns(5)
    m[0].metric("Suben", int((comp["Estado"] == "Sube").sum()))
    m[1].metric("Bajan", int((comp["Estado"] == "Baja").sum()))
    m[2].metric("Sin cambio", int((comp["Estado"] == "Igual").sum()))
    m[3].metric("A revisar", len(revisar))
    m[4].metric("Variación promedio", f"{cambia['Variación %'].mean():+.1f}%" if len(cambia) else "—")

    filtro = st.radio("Mostrar", ["Solo cambios", "Todo", "A revisar"], horizontal=True)
    vista = cambia if filtro == "Solo cambios" else (revisar if filtro == "A revisar" else comp)
    if len(vista):
        st.dataframe(vista.drop(columns=["ID"]).style.apply(estilo_estado, axis=1)
                     .map(estilo_variacion, subset=["Variación %"])
                     .format({"Precio actual": pesos, "Precio nuevo": pesos, "Diferencia $": pesos,
                              "Variación %": lambda v: "—" if v is None or v != v else f"{v:+.1f}%"}),
                     hide_index=True, use_container_width=True, height=min(520, 38 + 35 * len(vista)))
    else:
        st.caption("Nada para mostrar con ese filtro.")

    if len(cambia):
        st.subheader("Variación promedio por categoría")
        porcat = cambia.groupby(cambia["Categoría"].fillna("Sin categoría"))["Variación %"].mean().sort_values()
        st.bar_chart(porcat, horizontal=True, use_container_width=True)

    if len(revisar):
        st.warning(f"{len(revisar)} filas no se pudieron emparejar o no tienen precio. Se muestran en amarillo y **no** se van a cargar.")

    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.download_button("📥 Descargar la comparación en Excel (con colores)", xl.excel_comparacion(comp, arch.name, hoy),
                       file_name=f"comparacion_precios_{date.today():%Y-%m-%d}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if es_admin() and len(cambia):
        st.divider()
        if st.button(f"Cargar los {len(cambia)} cambios como propuestas", type="primary"):
            proponer([(r["ID"], r["Precio nuevo"]) for _, r in cambia.iterrows()], f"Excel: {arch.name}")
            st.switch_page(PAGINAS["aprobar"])


def pagina_historial():
    st.title("📜 Historial de precios")
    hist = datos("precios_historial", "fecha", desc=True)
    if not hist:
        st.info("Todavía no se aprobó ningún cambio de precio. Desde la primera aprobación, cada cambio queda registrado acá con fecha, quién lo aprobó y el motivo.")
        return
    cat = {p["id"]: p for p in catalogo()}
    df = pd.DataFrame([{
        "Fecha": fecha_local(h["fecha"]), "id": h.get("catalogo_id"), "Producto": h.get("nombre"),
        "Categoría": (cat.get(h.get("catalogo_id")) or {}).get("categoria"),
        "Precio anterior": num(h.get("precio_anterior")), "Precio nuevo": num(h.get("precio_nuevo")),
        "Motivo": h.get("motivo"), "Aprobó": h.get("aprobado_por"),
    } for h in hist])
    df["Variación %"] = [round((n / a - 1) * 100, 1) if a and n else None for a, n in zip(df["Precio anterior"], df["Precio nuevo"])]

    c1, c2, c3 = st.columns([2, 1.5, 1.5])
    busca = c1.text_input("Buscar producto", placeholder="Buscar…", key="h_busca")
    cats = c2.multiselect("Categorías", sorted(df["Categoría"].dropna().unique()), placeholder="Todas")
    desde_def = (df["Fecha"].min().date() if len(df) else date.today() - timedelta(days=90))
    rango = c3.date_input("Fechas", value=(desde_def, date.today()), format="DD/MM/YYYY")
    v = df.copy()
    if busca:
        v = v[v["Producto"].map(lambda s: xl.normalizar(busca) in xl.normalizar(s))]
    if cats:
        v = v[v["Categoría"].isin(cats)]
    if isinstance(rango, (list, tuple)) and len(rango) == 2:
        v = v[(v["Fecha"].dt.date >= rango[0]) & (v["Fecha"].dt.date <= rango[1])]

    fechas = v["Fecha"].dt.date.nunique()
    m = st.columns(3)
    m[0].metric("Cambios", len(v))
    m[1].metric("Días con actualización", fechas)
    m[2].metric("Última actualización", v["Fecha"].max().strftime("%d/%m/%Y") if len(v) else "—")

    with st.expander("📅 Actualizaciones por fecha", expanded=True):
        porfecha = v.groupby(v["Fecha"].dt.date).agg(Productos=("Producto", "count"), Variación=("Variación %", "mean"),
                                                     Motivos=("Motivo", lambda s: ", ".join(sorted({x for x in s if x}))[:120]))
        porfecha.index.name = "Fecha"
        st.dataframe(porfecha.sort_index(ascending=False).reset_index().assign(Fecha=lambda d: d["Fecha"].map(lambda x: x.strftime("%d/%m/%Y")),
                                                                                 Variación=lambda d: d["Variación"].map(lambda x: "—" if x != x else f"{x:+.1f}%")),
                     hide_index=True, use_container_width=True)

    mostrar = v.drop(columns=["id"]).assign(Fecha=v["Fecha"].dt.strftime("%d/%m/%Y %H:%M"))
    st.dataframe(mostrar.style.map(estilo_variacion, subset=["Variación %"])
                 .format({"Precio anterior": pesos, "Precio nuevo": pesos, "Variación %": lambda x: "—" if x is None or x != x else f"{x:+.1f}%"}),
                 hide_index=True, use_container_width=True, height=min(480, 38 + 35 * len(mostrar)))
    st.download_button("📥 Descargar historial en Excel", xl.excel_historial(mostrar),
                       file_name=f"historial_precios_{date.today():%Y-%m-%d}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.subheader("Evolución de un producto")
    prods = sorted(v["Producto"].dropna().unique())
    elegido = st.selectbox("Producto", prods, index=None, placeholder="Elegí un producto", key="h_prod")
    h = df[df["Producto"] == elegido].sort_values("Fecha") if elegido else df.iloc[0:0]
    if len(h):
        puntos = [(h["Fecha"].iloc[0] - pd.Timedelta(minutes=1), h["Precio anterior"].iloc[0])] + list(zip(h["Fecha"], h["Precio nuevo"]))
        serie = pd.DataFrame(puntos, columns=["Fecha", "Precio"]).dropna().set_index("Fecha")
        st.line_chart(serie, use_container_width=True)


# ================================================================ armado
def pantalla_login():
    _, c, _ = st.columns([1, 1.3, 1])
    with c:
        st.markdown("<h1 style='text-align:center;color:#d7141a;letter-spacing:4px;margin-bottom:0'>TAIRA</h1>"
                    "<p style='text-align:center' class='sub'>Administración de precios</p>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("Correo electrónico")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", type="primary", use_container_width=True):
                try:
                    guardar_sesion(sb.auth.sign_in_with_password({"email": email.strip(), "password": pw}).session, email)
                    ss.autenticado = True
                except Exception:
                    st.error("Usuario o contraseña incorrectos.")
                if ss.autenticado:
                    st.rerun()


if not ss.autenticado:
    pantalla_login()
    st.stop()
asegurar_token()

PAGINAS = {
    "lista": st.Page(pagina_lista, title="Precios", icon="📋", url_path="lista", default=True),
    "herramientas": st.Page(pagina_herramientas, title="Herramientas", icon="🧰", url_path="herramientas"),
    "aprobar": st.Page(pagina_aprobar, title="Revisar y aprobar", icon="✅", url_path="aprobar"),
    "importar": st.Page(pagina_importar, title="Importar Excel", icon="📤", url_path="importar"),
    "exportar": st.Page(pagina_exportar, title="Exportar Excel / PDF", icon="📥", url_path="exportar"),
    "calculadoras": st.Page(pagina_calculadoras, title="Calculadoras", icon="🧮", url_path="calculadoras"),
    "historial": st.Page(pagina_historial, title="Historial", icon="📜", url_path="historial"),
}
with st.sidebar:
    st.markdown("<h2 style='color:#d7141a;letter-spacing:3px;margin:0'>TAIRA</h2><div class='sub'>Precios</div>", unsafe_allow_html=True)
    st.caption(f"👤 {usuario()}" + (" · administrador" if es_admin() else " · solo lectura"))
nav = st.navigation(list(PAGINAS.values()))
with st.sidebar:
    st.divider()
    st.link_button("🏠 Panel TAIRA", "https://taira-pedidos.netlify.app/inicio.html", use_container_width=True)
    if st.button("🔄 Actualizar", use_container_width=True):
        leer.clear()
        st.rerun()
    if st.button("Cerrar sesión", use_container_width=True):
        salir()
        st.rerun()

for tipo, msg in ss.avisos:
    getattr(st, tipo)(msg)
ss.avisos = []
nav.run()
