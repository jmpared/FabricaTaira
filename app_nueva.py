"""Fábrica Taira — app interna (versión nueva).

Cambios respecto de app_web.py:
- Menú por secciones: solo se carga la sección que estás mirando (antes se cargaban las 8 pestañas en cada toque).
- Lecturas con caché de 60 s que se limpia automáticamente después de cada cambio.
- Inicio con resumen, producción con tarjetas y botones, stock editable en tabla, recetas editables.
- La sesión se renueva sola (antes vencía a la hora y aparecían errores de permisos).
"""
import json
import time
from datetime import datetime, date

import pandas as pd
import streamlit as st
from supabase import create_client

from precios import mostrar_pestana_precios

SUPABASE_URL = "https://gxnoakudooorcsnqcklm.supabase.co"
SUPABASE_KEY = "sb_publishable_CVNOChVw7tkKeC60qSHvWQ_3bTVbIMd"
ADMINS = {"mininopared@gmail.com", "eleminino.pared@gmail.com"}

st.set_page_config(page_title="Fábrica Taira", page_icon="🏭", layout="wide")

st.markdown(
    """
<style>
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 1.6rem; padding-bottom: 3rem;}
h1 {font-size: 1.9rem !important;}
div[data-testid="stMetric"] {background: #fff; border: 1px solid #efdfbf; border-radius: 14px; padding: 12px 14px;}
div[data-testid="stMetricLabel"] p {font-size: .9rem;}
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {border-radius: 10px; font-weight: 700; min-height: 2.6rem;}
.chip {display:inline-block; padding:2px 9px; border-radius:999px; font-size:.78rem; font-weight:700;}
.chip.rojo {background:#fde2e2; color:#a50e13;} .chip.ambar {background:#fff1cc; color:#7a5200;} .chip.verde {background:#dff5e6; color:#17663a;}
.sub {color:#7a6a5c; font-size:.9rem;}
</style>
""",
    unsafe_allow_html=True,
)

ss = st.session_state
for k, v in {"autenticado": False, "access_token": None, "refresh_token": None, "vence": 0, "avisos": []}.items():
    ss.setdefault(k, v)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)


# =====================================================================
# Sesión
# =====================================================================
def guardar_sesion(session, email=None):
    ss.access_token = session.access_token
    ss.refresh_token = session.refresh_token
    ss.vence = time.time() + int(getattr(session, "expires_in", 3600) or 3600) - 120
    if email:
        ss.email_user = email.strip().lower()
        ss.user = email.split("@")[0].capitalize()


def asegurar_token():
    if ss.access_token and time.time() > ss.vence and ss.refresh_token:
        try:
            res = sb.auth.refresh_session(ss.refresh_token)
            guardar_sesion(res.session)
        except Exception:
            cerrar_sesion()
            st.warning("La sesión venció. Ingresá de nuevo.")
            st.stop()
    if ss.access_token:
        sb.postgrest.auth(ss.access_token)


def cerrar_sesion():
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
    return ss.get("user", "Taller")


# =====================================================================
# Datos (con caché por usuario)
# =====================================================================
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


def refrescar():
    leer.clear()


def registrar(usuario_, accion, detalle):
    try:
        sb.table("registros").insert({
            "usuario": usuario_, "accion": accion, "detalle": detalle,
            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }).execute()
    except Exception:
        pass
    refrescar()


def avisar(tipo, msg):
    ss.avisos.append((tipo, msg))


def mostrar_avisos():
    for tipo, msg in ss.avisos:
        getattr(st, tipo)(msg)
    ss.avisos = []


def num(v, d=0.0):
    try:
        return float(v) if v is not None and v == v else d
    except Exception:
        return d


def es_cinta(mp):
    return str(mp.get("tipo") or "").lower().startswith("longitud") or str(mp.get("categoria") or "").lower() == "cinta"


def stock_mp(mp):
    """Stock en unidades de uso: cinta en metros, herrajes en unidades."""
    return num(mp.get("longitud")) / 100 if es_cinta(mp) else num(mp.get("cantidad"))


def minimo_mp(mp):
    return num(mp.get("minimo")) / 100 if es_cinta(mp) else num(mp.get("minimo"))


def receta_de(p):
    r = p.get("receta")
    if isinstance(r, str):
        try:
            r = json.loads(r)
        except Exception:
            r = []
    return r if isinstance(r, list) else []


def texto_receta(p):
    r = receta_de(p)
    return ", ".join(f"{i.get('cantidad', '')} {i.get('material', '')}" for i in r) if r else "Sin receta"


def bajo(stock, minimo):
    return minimo > 0 and stock <= minimo


def fmt(n):
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".").rstrip("0").rstrip(",")


# =====================================================================
# Operaciones de stock
# =====================================================================
def ajustar_stock(producto, delta):
    """Suma o resta stock sin dejarlo negativo y sin pisar cambios de otro operario."""
    try:
        for _ in range(3):
            fila = sb.table("productos").select("cantidad").eq("nombre", producto).execute().data
            if not fila:
                return False, f"No se encontró '{producto}'."
            leido = fila[0].get("cantidad")
            actual = num(leido)
            nuevo = actual + delta
            if nuevo < 0:
                return False, f"Stock insuficiente de '{producto}': hay {actual:g}."
            res = sb.table("productos").update({"cantidad": nuevo}).eq("nombre", producto).eq("cantidad", leido).execute()
            if res.data:
                return True, f"'{producto}': {actual:g} → {nuevo:g}"
        return False, f"El stock de '{producto}' cambió mientras se guardaba. Probá de nuevo."
    except Exception as e:
        return False, f"Error con '{producto}': {e}"


def descontar_insumos(producto, unidades):
    try:
        det = sb.rpc("descontar_insumos", {"p_producto": producto, "p_unidades": unidades}).execute().data or []
    except Exception as e:
        avisar("error", f"Se sumó el stock de '{producto}' pero NO se descontaron insumos: {e}")
        return
    usados = []
    for d in det:
        if d.get("aviso"):
            avisar("warning", f"{producto}: {d.get('material', '')} {d['aviso']}".strip())
            continue
        cm = d.get("unidad") == "cm"
        a_txt = (lambda v: f"{fmt(num(v) / 100)} m") if cm else (lambda v: f"{num(v):g} u.")
        usados.append(f"{a_txt(d['usado'])} de {d['material']}")
        if d.get("negativo"):
            avisar("error", f"⚠️ {d['material']} quedó en negativo ({a_txt(d['queda'])}). Recontá ese insumo.")
        elif d.get("bajo"):
            avisar("warning", f"⚠️ Queda poco {d['material']}: {a_txt(d['queda'])}.")
    if usados:
        avisar("info", f"🧪 Insumos descontados por {unidades:g}× {producto}: " + ", ".join(usados))
        registrar(usuario(), "Descuento de insumos", f"{unidades:g}x {producto}: " + ", ".join(usados))


def terminar_orden(orden):
    nombre, cant = orden["producto"], num(orden["cantidad"])
    ok, msg = ajustar_stock(nombre, cant)
    if not ok:
        avisar("error", f"No se terminó la orden #{orden['id']}: {msg}")
        return
    sb.table("pedidos_produccion").update({
        "estado": "Finalizado", "fecha_finalizacion": str(date.today())
    }).eq("id", orden["id"]).execute()
    registrar(usuario(), "Producto Terminado", f"Finalizó lote ID {orden['id']} (+{cant:g} {nombre})")
    descontar_insumos(nombre, cant)
    avisar("success", f"✅ Orden #{orden['id']} terminada. {msg}")


# =====================================================================
# Páginas
# =====================================================================
def pagina_inicio():
    st.title(f"Hola, {usuario()} 👋")
    st.markdown(f"<div class='sub'>{datetime.now():%d/%m/%Y} · Resumen de la fábrica</div>", unsafe_allow_html=True)
    st.write("")
    prods, mps = datos("productos", "nombre"), datos("materias_primas", "nombre")
    pedidos = datos("pedidos_produccion", "id", desc=True)
    ventas = datos("ventas_historial", "id", desc=True)
    hoy = str(date.today())

    p_bajo = [p for p in prods if bajo(num(p.get("cantidad")), num(p.get("minimo")))]
    m_bajo = [m for m in mps if bajo(stock_mp(m), minimo_mp(m))]
    pend = [p for p in pedidos if p.get("estado") == "Pendiente"]
    curso = [p for p in pedidos if p.get("estado") == "En Producción"]
    v_hoy = sum(num(v.get("cantidad")) for v in ventas if str(v.get("fecha", ""))[:10] == hoy)
    f_hoy = sum(num(p.get("cantidad")) for p in pedidos if p.get("estado") == "Finalizado" and str(p.get("fecha_finalizacion", ""))[:10] == hoy)

    c = st.columns(4)
    c[0].metric("Órdenes pendientes", len(pend))
    c[1].metric("En producción", len(curso))
    c[2].metric("Fabricado hoy", f"{f_hoy:g} u.")
    c[3].metric("Vendido hoy", f"{v_hoy:g} u.")

    st.write("")
    a, b = st.columns(2)
    with a:
        with st.container(border=True):
            st.subheader(f"🔴 Productos con stock bajo ({len(p_bajo)})")
            if not p_bajo:
                st.success("Todo en orden.")
            for p in sorted(p_bajo, key=lambda x: num(x.get("cantidad")))[:12]:
                st.markdown(f"**{p['nombre']}** — hay {num(p.get('cantidad')):g} (mín. {num(p.get('minimo')):g})")
            if p_bajo and st.button("Crear órdenes de producción para estos", use_container_width=True):
                for p in p_bajo:
                    falta = max(num(p.get("minimo")) * 2 - num(p.get("cantidad")), 1)
                    sb.table("pedidos_produccion").insert({
                        "producto": p["nombre"], "cantidad": falta, "estado": "Pendiente",
                        "fecha_creacion": str(date.today()), "creado_por": usuario(),
                    }).execute()
                registrar(usuario(), "Nuevo Pedido", f"Órdenes automáticas para {len(p_bajo)} productos con stock bajo")
                avisar("success", f"Se crearon {len(p_bajo)} órdenes (cada una lleva el stock al doble del mínimo).")
                st.rerun()
    with b:
        with st.container(border=True):
            st.subheader(f"🧪 Insumos para reponer ({len(m_bajo)})")
            if not m_bajo:
                st.success("Todo en orden.")
            for m in sorted(m_bajo, key=lambda x: stock_mp(x))[:12]:
                u = "m" if es_cinta(m) else "u."
                st.markdown(f"**{m['nombre']}** — quedan {fmt(stock_mp(m))} {u} (mín. {fmt(minimo_mp(m))} {u})")

    st.write("")
    st.subheader("Accesos rápidos")
    q = st.columns(4)
    if q[0].button("🏭 Nueva orden", use_container_width=True):
        st.switch_page(PAGINAS["produccion"])
    if q[1].button("📦 Ver stock", use_container_width=True):
        st.switch_page(PAGINAS["stock"])
    if q[2].button("💰 Registrar venta", use_container_width=True):
        st.switch_page(PAGINAS["ventas"])
    if q[3].button("🚚 Llegaron insumos", use_container_width=True):
        ss["stock_vista"] = "Materias primas"
        st.switch_page(PAGINAS["stock"])


def pagina_produccion():
    st.title("🏭 Producción")
    prods = datos("productos", "nombre")
    pedidos = datos("pedidos_produccion", "id", desc=True)
    nombres = [p["nombre"] for p in prods]

    with st.container(border=True):
        st.subheader("Nueva orden")
        with st.form("nueva_orden", clear_on_submit=True, border=False):
            c1, c2, c3 = st.columns([3, 1, 1.4], vertical_alignment="bottom")
            prod = c1.selectbox("Producto", nombres, index=None, placeholder="Elegí o escribí para buscar…")
            cant = c2.number_input("Cantidad", min_value=1, value=10, step=1)
            ya = c3.checkbox("Ya está terminada", help="Marcalo si ya se fabricó: suma al stock y descuenta insumos al instante.")
            if st.form_submit_button("Guardar", type="primary", use_container_width=True):
                if not prod:
                    st.warning("Elegí un producto.")
                else:
                    res = sb.table("pedidos_produccion").insert({
                        "producto": prod, "cantidad": cant, "estado": "En Producción" if ya else "Pendiente",
                        "fecha_creacion": str(date.today()), "creado_por": usuario(),
                        **({"fecha_produccion": str(date.today()), "producido_por": usuario()} if ya else {}),
                    }).execute()
                    registrar(usuario(), "Nuevo Pedido", f"Pidió {cant}x {prod}")
                    if ya and res.data:
                        terminar_orden(res.data[0])
                    else:
                        avisar("success", f"Orden guardada: {cant}× {prod}")
                    st.rerun()

    pend = [p for p in pedidos if p.get("estado") == "Pendiente"]
    curso = [p for p in pedidos if p.get("estado") == "En Producción"]
    izq, der = st.columns(2)

    with izq:
        st.subheader(f"⏳ Pendientes ({len(pend)})")
        if pend and st.button("▶ Iniciar todas", use_container_width=True, key="ini_todas"):
            for p in pend:
                sb.table("pedidos_produccion").update({"estado": "En Producción", "fecha_produccion": str(date.today()), "producido_por": usuario()}).eq("id", p["id"]).execute()
            registrar(usuario(), "Inicio Producción", f"Inició {len(pend)} órdenes")
            st.rerun()
        if not pend:
            st.caption("No hay órdenes pendientes.")
        for p in pend:
            with st.container(border=True):
                a, b = st.columns([3, 1.2], vertical_alignment="center")
                a.markdown(f"**{num(p['cantidad']):g}× {p['producto']}**  \n<span class='sub'>#{p['id']} · {p.get('fecha_creacion') or ''} · {p.get('creado_por') or ''}</span>", unsafe_allow_html=True)
                if b.button("▶ Iniciar", key=f"ini{p['id']}", use_container_width=True):
                    sb.table("pedidos_produccion").update({"estado": "En Producción", "fecha_produccion": str(date.today()), "producido_por": usuario()}).eq("id", p["id"]).execute()
                    registrar(usuario(), "Inicio Producción", f"Inició lote ID {p['id']}")
                    st.rerun()

    with der:
        st.subheader(f"🔧 En producción ({len(curso)})")
        if not curso:
            st.caption("No hay órdenes en curso.")
        for p in curso:
            with st.container(border=True):
                a, b = st.columns([3, 1.2], vertical_alignment="center")
                a.markdown(f"**{num(p['cantidad']):g}× {p['producto']}**  \n<span class='sub'>#{p['id']} · desde {p.get('fecha_produccion') or ''} · {p.get('producido_por') or ''}</span>", unsafe_allow_html=True)
                if b.button("✅ Terminar", key=f"fin{p['id']}", type="primary", use_container_width=True):
                    terminar_orden(p)
                    st.rerun()

    st.divider()
    with st.expander("📋 Historial de órdenes"):
        df = pd.DataFrame(pedidos)
        if df.empty:
            st.caption("Sin órdenes.")
        else:
            estado = st.radio("Estado", ["Todas", "Pendiente", "En Producción", "Finalizado"], horizontal=True, key="hist_estado")
            if estado != "Todas":
                df = df[df["estado"] == estado]
            cols = [c for c in ["id", "producto", "cantidad", "estado", "fecha_creacion", "creado_por", "fecha_finalizacion", "producido_por"] if c in df.columns]
            st.dataframe(df[cols], hide_index=True, use_container_width=True)
            if es_admin() and pedidos:
                c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
                op = {f"#{p['id']} · {num(p['cantidad']):g}× {p['producto']} · {p.get('estado')}": p["id"] for p in pedidos}
                sel = c1.selectbox("Eliminar orden (solo admin)", list(op.keys()), index=None, key="del_orden")
                if c2.button("🗑️ Eliminar", disabled=not sel, use_container_width=True):
                    sb.table("pedidos_produccion").delete().eq("id", op[sel]).execute()
                    registrar(usuario(), "Eliminó Pedido", f"Se eliminó la orden ID {op[sel]}")
                    st.rerun()


def pagina_stock():
    st.title("📦 Stock")
    vista = st.radio("Ver", ["Productos", "Materias primas"], horizontal=True, label_visibility="collapsed", key="stock_vista")
    if vista == "Productos":
        stock_productos()
    else:
        stock_insumos()


def stock_productos():
    prods, mps = datos("productos", "nombre"), datos("materias_primas", "nombre")
    c1, c2 = st.columns([2, 1])
    busca = c1.text_input("Buscar", placeholder="Ej: collar talle 3", label_visibility="collapsed")
    cats = sorted({p.get("categoria") or "General" for p in prods})
    cat = c2.selectbox("Categoría", ["Todas"] + cats, label_visibility="collapsed")
    filas = []
    for p in prods:
        if cat != "Todas" and (p.get("categoria") or "General") != cat:
            continue
        if busca and busca.lower() not in p["nombre"].lower():
            continue
        s, m = num(p.get("cantidad")), num(p.get("minimo"))
        filas.append({"id": p["id"], "Estado": "🔴" if bajo(s, m) else "🟢", "Producto": p["nombre"],
                      "Categoría": p.get("categoria") or "General", "Stock": s, "Mínimo": m, "Receta": texto_receta(p)})
    df = pd.DataFrame(filas)
    if df.empty:
        st.info("No hay productos que coincidan.")
    elif es_admin():
        st.caption("Podés corregir stock, mínimo y categoría directamente en la tabla y guardar.")
        ed = st.data_editor(df, key="ed_prod", hide_index=True, use_container_width=True,
                            disabled=["id", "Estado", "Producto", "Receta"],
                            column_config={"id": None, "Estado": st.column_config.TextColumn("", width="small"),
                                           "Stock": st.column_config.NumberColumn(min_value=0, step=1),
                                           "Mínimo": st.column_config.NumberColumn(min_value=0, step=1)})
        if st.button("💾 Guardar cambios", type="primary"):
            orig = df.set_index("id")
            n = 0
            for _, r in ed.iterrows():
                o = orig.loc[r["id"]]
                if (r["Stock"], r["Mínimo"], r["Categoría"]) != (o["Stock"], o["Mínimo"], o["Categoría"]):
                    sb.table("productos").update({"cantidad": num(r["Stock"]), "minimo": num(r["Mínimo"]), "categoria": r["Categoría"]}).eq("id", int(r["id"])).execute()
                    registrar(usuario(), "Editó Producto", f"{r['Producto']}: stock {o['Stock']:g}→{num(r['Stock']):g}, mín {o['Mínimo']:g}→{num(r['Mínimo']):g}")
                    n += 1
            avisar("success" if n else "info", f"Se guardaron {n} productos." if n else "No había cambios.")
            st.rerun()
    else:
        st.dataframe(df.drop(columns=["id"]), hide_index=True, use_container_width=True)

    nombres_mp = sorted({m["nombre"] for m in mps}, key=str.lower)
    with st.expander("➕ Nuevo producto"):
        with st.form("nuevo_prod", clear_on_submit=True):
            a, b = st.columns(2)
            nombre = a.text_input("Nombre")
            categoria = b.selectbox("Categoría", cats + ["Otra…"], index=None, placeholder="Elegí una")
            otra = b.text_input("Si es otra, escribila")
            c, d = st.columns(2)
            ini = c.number_input("Stock inicial", min_value=0, value=0)
            mn = d.number_input("Stock mínimo", min_value=0, value=0)
            st.markdown("**Receta** (lo que lleva 1 unidad · cintas en cm, herrajes en unidades)")
            rec = st.data_editor(pd.DataFrame([{"material": None, "cantidad": 1.0}]), num_rows="dynamic", key="rec_nueva",
                                 use_container_width=True, hide_index=True,
                                 column_config={"material": st.column_config.SelectboxColumn("Insumo", options=nombres_mp),
                                                "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.0, step=1.0)})
            if st.form_submit_button("Guardar producto", type="primary"):
                cat_final = (otra.strip().capitalize() if categoria in (None, "Otra…") else categoria) or "General"
                receta = [{"material": r["material"], "cantidad": num(r["cantidad"])} for _, r in rec.iterrows() if r["material"] and num(r["cantidad"]) > 0]
                if not nombre.strip():
                    st.warning("Poné un nombre.")
                elif any(p["nombre"].strip().lower() == nombre.strip().lower() for p in prods):
                    st.warning("Ya existe un producto con ese nombre.")
                else:
                    sb.table("productos").insert({"nombre": nombre.strip(), "categoria": cat_final, "cantidad": ini, "minimo": mn, "receta": receta}).execute()
                    registrar(usuario(), "Creó Producto", f"Nuevo producto: {nombre.strip()} [{cat_final}]")
                    avisar("success", f"Producto '{nombre.strip()}' creado.")
                    st.rerun()

    if es_admin() and prods:
        with st.expander("🧾 Editar receta de un producto"):
            sel = st.selectbox("Producto", [p["nombre"] for p in prods], index=None, key="rec_sel")
            if sel:
                p = next(x for x in prods if x["nombre"] == sel)
                df_r = pd.DataFrame(receta_de(p) or [{"material": None, "cantidad": 1.0}])
                ed_r = st.data_editor(df_r, num_rows="dynamic", key=f"rec_ed_{p['id']}", use_container_width=True, hide_index=True,
                                      column_config={"material": st.column_config.SelectboxColumn("Insumo", options=nombres_mp),
                                                     "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.0, step=1.0)})
                faltan = [r["material"] for _, r in ed_r.iterrows() if r.get("material") and r["material"] not in nombres_mp]
                if faltan:
                    st.warning("Estos insumos no existen en materias primas: " + ", ".join(faltan))
                if st.button("💾 Guardar receta", type="primary", key="rec_guardar"):
                    receta = [{"material": r["material"], "cantidad": num(r["cantidad"])} for _, r in ed_r.iterrows() if r.get("material") and num(r["cantidad"]) > 0]
                    sb.table("productos").update({"receta": receta}).eq("id", p["id"]).execute()
                    registrar(usuario(), "Editó receta", f"{sel}: " + ", ".join(f"{r['cantidad']:g} {r['material']}" for r in receta))
                    avisar("success", f"Receta de '{sel}' guardada.")
                    st.rerun()
        with st.expander("🗑️ Eliminar producto"):
            c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
            dsel = c1.selectbox("Producto a eliminar", [p["nombre"] for p in prods], index=None, key="del_prod")
            if c2.button("Eliminar", disabled=not dsel, use_container_width=True, key="del_prod_btn"):
                sb.table("productos").delete().eq("nombre", dsel).execute()
                registrar(usuario(), "Eliminó Producto", f"Se eliminó {dsel}")
                avisar("success", f"'{dsel}' eliminado.")
                st.rerun()


def stock_insumos():
    mps = datos("materias_primas", "nombre")
    por_nombre = {m["nombre"]: m for m in mps}

    with st.container(border=True):
        st.subheader("🚚 Llegaron insumos")
        with st.form("ingreso", clear_on_submit=True, border=False):
            a, b, c = st.columns([3, 1.2, 1], vertical_alignment="bottom")
            ins = a.selectbox("Insumo", sorted(por_nombre, key=str.lower), index=None, placeholder="Elegí o escribí para buscar…")
            cant = b.number_input("Cantidad (cinta en metros)", min_value=0.0, value=0.0, step=1.0)
            if c.form_submit_button("Sumar", type="primary", use_container_width=True):
                if not ins or cant <= 0:
                    st.warning("Elegí el insumo y la cantidad.")
                else:
                    m = por_nombre[ins]
                    valor = cant * 100 if es_cinta(m) else cant
                    try:
                        r = sb.rpc("ingresar_insumo", {"p_insumo_id": m["id"], "p_cantidad": valor, "p_usuario": usuario(), "p_origen": "App"}).execute().data
                        q = num(r.get("queda")) / 100 if r.get("unidad") == "cm" else num(r.get("queda"))
                        avisar("success", f"Listo: ahora hay {fmt(q)} {'m' if es_cinta(m) else 'u.'} de {ins}.")
                        refrescar()
                    except Exception as e:
                        avisar("error", f"No se pudo sumar: {e}")
                    st.rerun()

    busca = st.text_input("Buscar insumo", placeholder="Ej: hebilla 20", label_visibility="collapsed")
    filas = []
    for m in mps:
        if busca and busca.lower() not in m["nombre"].lower():
            continue
        s, mn = stock_mp(m), minimo_mp(m)
        filas.append({"id": m["id"], "Estado": "🔴" if bajo(s, mn) else "🟢", "Insumo": m["nombre"],
                      "Tipo": "Cinta (m)" if es_cinta(m) else "Herraje (u.)", "Stock": round(s, 2), "Mínimo": round(mn, 2),
                      "Precio $": m.get("precio")})
    df = pd.DataFrame(filas)
    if df.empty:
        st.info("No hay insumos que coincidan.")
    elif es_admin():
        st.caption("Stock y mínimo de cintas en **metros**. Corregí en la tabla y guardá.")
        ed = st.data_editor(df, key="ed_mp", hide_index=True, use_container_width=True,
                            disabled=["id", "Estado", "Insumo", "Tipo", "Precio $"],
                            column_config={"id": None, "Estado": st.column_config.TextColumn("", width="small"),
                                           "Stock": st.column_config.NumberColumn(min_value=0.0, step=1.0),
                                           "Mínimo": st.column_config.NumberColumn(min_value=0.0, step=1.0),
                                           "Precio $": st.column_config.NumberColumn(format="$ %.2f")})
        if st.button("💾 Guardar cambios", type="primary", key="mp_guardar"):
            orig = df.set_index("id")
            n = 0
            for _, r in ed.iterrows():
                o = orig.loc[r["id"]]
                if (num(r["Stock"]), num(r["Mínimo"])) != (num(o["Stock"]), num(o["Mínimo"])):
                    cinta = r["Tipo"].startswith("Cinta")
                    upd = {"minimo": num(r["Mínimo"]) * (100 if cinta else 1)}
                    upd["longitud" if cinta else "cantidad"] = num(r["Stock"]) * (100 if cinta else 1)
                    sb.table("materias_primas").update(upd).eq("id", r["id"]).execute()
                    registrar(usuario(), "Editó MP", f"{r['Insumo']}: stock {o['Stock']:g}→{num(r['Stock']):g}, mín {o['Mínimo']:g}→{num(r['Mínimo']):g}")
                    n += 1
            avisar("success" if n else "info", f"Se guardaron {n} insumos." if n else "No había cambios.")
            st.rerun()
    else:
        st.dataframe(df.drop(columns=["id"]), hide_index=True, use_container_width=True)

    with st.expander("➕ Nuevo insumo"):
        with st.form("nuevo_mp", clear_on_submit=True):
            a, b = st.columns(2)
            nombre = a.text_input("Nombre (ej: cinta lisa 20, hebilla 25 simple)")
            tipo = b.radio("Tipo", ["Herraje (unidades)", "Cinta (metros)"], horizontal=True)
            c, d = st.columns(2)
            ini = c.number_input("Stock inicial", min_value=0.0, step=1.0)
            mn = d.number_input("Stock mínimo para alerta", min_value=0.0, step=1.0)
            if st.form_submit_button("Guardar insumo", type="primary"):
                cinta = tipo.startswith("Cinta")
                if not nombre.strip():
                    st.warning("Poné un nombre.")
                elif nombre.strip().lower() in {k.lower() for k in por_nombre}:
                    st.warning("Ya existe un insumo con ese nombre.")
                else:
                    sb.table("materias_primas").insert({
                        "nombre": nombre.strip(), "categoria": "Cinta" if cinta else "Herraje",
                        "tipo": "Longitud (cm)" if cinta else "Unidades",
                        "cantidad": 0 if cinta else ini, "longitud": ini * 100 if cinta else 0,
                        "minimo": mn * (100 if cinta else 1), "fecha": str(date.today()),
                    }).execute()
                    registrar(usuario(), "Alta Materia Prima", f"Ingresó {nombre.strip()}")
                    avisar("success", f"Insumo '{nombre.strip()}' creado.")
                    st.rerun()

    if es_admin() and mps:
        with st.expander("🗑️ Eliminar insumo"):
            c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
            op = {f"{m['nombre']} ({'cinta' if es_cinta(m) else 'herraje'}, {fmt(stock_mp(m))})": m["id"] for m in mps}
            dsel = c1.selectbox("Insumo a eliminar", list(op.keys()), index=None, key="del_mp")
            if c2.button("Eliminar", disabled=not dsel, use_container_width=True, key="del_mp_btn"):
                sb.table("materias_primas").delete().eq("id", op[dsel]).execute()
                registrar(usuario(), "Eliminó Materia Prima", f"Se eliminó {dsel}")
                st.rerun()


def pagina_ventas():
    st.title("💰 Ventas y salidas")
    prods = datos("productos", "nombre")
    stock = {p["nombre"]: num(p.get("cantidad")) for p in prods}
    with st.container(border=True):
        with st.form("venta", clear_on_submit=True, border=False):
            a, b, c = st.columns([3, 1, 1.2], vertical_alignment="bottom")
            prod = a.selectbox("Producto", list(stock), index=None, placeholder="Elegí o escribí para buscar…",
                               format_func=lambda n: f"{n}  ·  hay {stock[n]:g}")
            cant = b.number_input("Cantidad", min_value=1, value=1)
            if c.form_submit_button("Registrar salida", type="primary", use_container_width=True):
                if not prod:
                    st.warning("Elegí un producto.")
                else:
                    pid = next(p["id"] for p in prods if p["nombre"] == prod)
                    try:
                        r = sb.rpc("registrar_venta", {"p_producto_id": pid, "p_unidades": cant, "p_usuario": usuario(), "p_origen": "App"}).execute().data
                        if r.get("ok"):
                            avisar("success", f"Listo: quedan {num(r['stock']):g} {prod}.")
                        else:
                            avisar("error", f"No alcanza: hay {num(r['stock']):g} {prod}. No se registró.")
                        refrescar()
                    except Exception as e:
                        avisar("error", f"No se pudo registrar: {e}")
                    st.rerun()

    ventas = datos("ventas_historial", "id", desc=True)
    st.subheader("Últimas salidas")
    df = pd.DataFrame([{"id": v["id"], "Fecha": v.get("fecha"), "Producto": v.get("producto"), "Cantidad": num(v.get("cantidad")),
                        "Registró": v.get("registrado_por")} for v in ventas if v.get("producto")])
    if df.empty:
        st.caption("Todavía no hay salidas registradas.")
        return
    st.dataframe(df.drop(columns=["id"]).head(200), hide_index=True, use_container_width=True)
    if es_admin():
        with st.expander("↩️ Anular una salida (devuelve el stock)"):
            c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
            op = {f"#{r['id']} · {r['Fecha']} · {r['Cantidad']:g}× {r['Producto']}": r for _, r in df.head(100).iterrows()}
            sel = c1.selectbox("Salida", list(op.keys()), index=None, key="anular_sel")
            if c2.button("Anular", disabled=not sel, use_container_width=True):
                r = op[sel]
                ok, msg = ajustar_stock(r["Producto"], r["Cantidad"])
                if ok:
                    sb.table("ventas_historial").delete().eq("id", int(r["id"])).execute()
                    registrar(usuario(), "Anuló venta", f"{sel} ({msg})")
                    avisar("success", f"Salida anulada. {msg}")
                else:
                    avisar("error", msg)
                st.rerun()


def pagina_precios():
    mostrar_pestana_precios(sb, datos("materias_primas", "nombre"), datos("productos", "nombre"), usuario(), es_admin(), registrar)


def pagina_reportes():
    st.title("📊 Reportes")
    vista = st.radio("Ver", ["Producción", "Ventas", "Registro de movimientos"], horizontal=True, label_visibility="collapsed")
    if vista == "Registro de movimientos":
        regs = datos("registros", "id", desc=True)
        df = pd.DataFrame(regs)
        if df.empty:
            st.caption("Sin registros.")
            return
        q = st.text_input("Buscar", placeholder="Operario, acción o detalle…", label_visibility="collapsed")
        if q:
            df = df[df.astype(str).apply(lambda c: c.str.lower().str.contains(q.lower(), regex=False)).any(axis=1)]
        cols = [c for c in ["fecha_hora", "usuario", "accion", "detalle"] if c in df.columns]
        st.dataframe(df[cols], hide_index=True, use_container_width=True)
        st.download_button("📥 Descargar (CSV)", df[cols].to_csv(index=False, sep=";").encode("utf-8-sig"),
                           "registros_taira.csv", "text/csv")
        st.caption("🔒 El registro es de solo lectura.")
        return

    if vista == "Producción":
        filas = [p for p in datos("pedidos_produccion", "id") if p.get("estado") == "Finalizado"]
        df = pd.DataFrame([{"fecha": p.get("fecha_finalizacion"), "producto": p.get("producto"), "cantidad": num(p.get("cantidad"))} for p in filas])
    else:
        filas = [v for v in datos("ventas_historial", "id") if v.get("producto")]
        df = pd.DataFrame([{"fecha": v.get("fecha"), "producto": v.get("producto"), "cantidad": num(v.get("cantidad"))} for v in filas])
    if df.empty:
        st.info("Todavía no hay datos para mostrar.")
        return
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])
    c1, c2 = st.columns(2)
    per = c1.radio("Período", ["Últimos 30 días", "Por semana", "Por mes"], horizontal=True)
    prods = ["Todos"] + sorted(df["producto"].unique())
    pr = c2.selectbox("Producto", prods)
    if pr != "Todos":
        df = df[df["producto"] == pr]
    if per == "Últimos 30 días":
        df = df[df["fecha"] >= pd.Timestamp.now().normalize() - pd.Timedelta(days=30)]
        df["periodo"] = df["fecha"].dt.strftime("%m-%d")
    elif per == "Por semana":
        df["periodo"] = df["fecha"].dt.strftime("%Y-S%V")
    else:
        df["periodo"] = df["fecha"].dt.strftime("%Y-%m")
    if df.empty:
        st.info("No hay datos en ese período.")
        return
    tot = df.groupby("producto")["cantidad"].sum().sort_values(ascending=False)
    m = st.columns(3)
    m[0].metric("Unidades", f"{tot.sum():g}")
    m[1].metric("Productos distintos", len(tot))
    m[2].metric("Más " + ("fabricado" if vista == "Producción" else "vendido"), tot.index[0])
    piv = df.pivot_table(index="periodo", columns="producto", values="cantidad", aggfunc="sum").fillna(0)
    st.bar_chart(piv, use_container_width=True)
    st.dataframe(tot.rename("Unidades").reset_index().rename(columns={"producto": "Producto"}), hide_index=True, use_container_width=True)


# =====================================================================
# Ingreso
# =====================================================================
def pantalla_login():
    _, centro, _ = st.columns([1, 1.3, 1])
    with centro:
        st.write("")
        st.markdown("<h1 style='text-align:center;color:#d7141a;letter-spacing:4px;margin-bottom:0'>TAIRA</h1>"
                    "<p style='text-align:center' class='sub'>Fábrica · acceso del equipo</p>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("Correo electrónico")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", type="primary", use_container_width=True):
                try:
                    res = sb.auth.sign_in_with_password({"email": email.strip(), "password": pw})
                    guardar_sesion(res.session, email)
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
    "inicio": st.Page(pagina_inicio, title="Inicio", icon="🏠", url_path="inicio", default=True),
    "produccion": st.Page(pagina_produccion, title="Producción", icon="🏭", url_path="produccion"),
    "stock": st.Page(pagina_stock, title="Stock", icon="📦", url_path="stock"),
    "ventas": st.Page(pagina_ventas, title="Ventas", icon="💰", url_path="ventas"),
    "precios": st.Page(pagina_precios, title="Costos y precios", icon="💲", url_path="precios"),
    "reportes": st.Page(pagina_reportes, title="Reportes", icon="📊", url_path="reportes"),
}

with st.sidebar:
    st.markdown("<h2 style='color:#d7141a;letter-spacing:3px;margin:0'>TAIRA</h2>", unsafe_allow_html=True)
    st.caption(f"👤 {usuario()}" + (" · administrador" if es_admin() else ""))

nav = st.navigation(list(PAGINAS.values()))

with st.sidebar:
    st.divider()
    st.link_button("🏠 Panel TAIRA", "https://taira-pedidos.netlify.app/inicio.html", use_container_width=True)
    if st.button("🔄 Actualizar datos", use_container_width=True):
        refrescar()
        st.rerun()
    if st.button("Cerrar sesión", use_container_width=True):
        cerrar_sesion()
        st.rerun()

mostrar_avisos()
nav.run()
