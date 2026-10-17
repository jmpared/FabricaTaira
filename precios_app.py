"""TAIRA · Precios — app separada para administrar la lista de precios.

Trabaja sobre la misma tabla 'catalogo' que usan el catálogo online y la app de la fábrica:
lo que se aprueba acá se ve al instante en los dos.
Ningún cambio se publica directo: todo pasa por "propuestas" que el administrador aprueba.
"""
import math
import time
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
from supabase import create_client

import excel_precios as xl

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
def pagina_lista():
    st.title("📋 Lista de precios")
    cat = catalogo()
    ult = ultimos_cambios()
    pend = sum(1 for p in cat if p.get("precio_propuesto") is not None)
    if pend:
        st.info(f"Hay **{pend} precios propuestos** esperando aprobación.")
        if st.button("Ir a revisar y aprobar →"):
            st.switch_page(PAGINAS["aprobar"])

    f1, f2, f3 = st.columns([1.2, 2, 2])
    linea = f1.selectbox("Línea", ["Todas", "Fabricados", "Importados"])
    cats_all = sorted({p.get("categoria") or "" for p in cat if linea == "Todas" or p.get("linea") == ("fabricado" if linea == "Fabricados" else "importado")})
    cats = f2.multiselect("Categorías", cats_all, placeholder="Todas")
    busca = f3.text_input("Buscar", placeholder="Ej: collar pampa")
    vis = [p for p in cat
           if (linea == "Todas" or p.get("linea") == ("fabricado" if linea == "Fabricados" else "importado"))
           and (not cats or p.get("categoria") in cats)
           and (not busca or xl.normalizar(busca) in xl.normalizar(p["nombre"] + " " + (p.get("categoria") or "")))]

    df = pd.DataFrame([{
        "id": p["id"], "✔": False, "Producto": p["nombre"], "Categoría": p.get("categoria"), "Medida": medida(p),
        "Precio actual": num(p.get("precio_publicado")), "Nuevo precio": None,
        "Propuesto": num(p.get("precio_propuesto")),
        "Últ. cambio": (fecha_local(ult.get(p["id"])).strftime("%d/%m/%Y") if ult.get(p["id"]) else "Carga inicial"),
    } for p in vis])
    st.caption(f"{len(vis)} productos en la lista" + (" · Escribí un precio en **Nuevo precio** o tildá ✔ para cambiar varios a la vez." if es_admin() else ""))
    if df.empty:
        st.warning("No hay productos con esos filtros.")
        return

    cfg = {"id": None,
           "✔": st.column_config.CheckboxColumn("✔", width="small"),
           "Precio actual": st.column_config.NumberColumn(format="$ %.2f"),
           "Nuevo precio": st.column_config.NumberColumn(format="$ %.2f", min_value=0.0, step=1.0),
           "Propuesto": st.column_config.NumberColumn("En espera", format="$ %.2f")}
    clave = "lista_" + str(abs(hash((linea, tuple(cats), busca))))
    if es_admin():
        ed = st.data_editor(df, key=clave, hide_index=True, use_container_width=True, height=460, column_config=cfg,
                            disabled=["id", "Producto", "Categoría", "Medida", "Precio actual", "Propuesto", "Últ. cambio"])
    else:
        st.dataframe(df.drop(columns=["✔", "Nuevo precio"]), hide_index=True, use_container_width=True, height=460, column_config=cfg)
        ed = df

    hoy = datetime.now().strftime("%d/%m/%Y")
    exp = df.drop(columns=["✔", "Nuevo precio", "Propuesto"]).rename(columns={"id": "ID TAIRA"})
    exp.insert(3, "Línea", [("Fabricado" if p.get("linea") == "fabricado" else "Importado") for p in vis])
    st.download_button("📥 Descargar esta lista en Excel", xl.excel_lista(exp, hoy),
                       file_name=f"precios_taira_{date.today():%Y-%m-%d}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if not es_admin():
        st.caption("🔒 Solo el administrador puede cambiar precios.")
        return

    escritos = ed[ed["Nuevo precio"].map(num).notna() & (ed["Nuevo precio"].map(num) > 0)]
    if len(escritos):
        st.success(f"Escribiste {len(escritos)} precios nuevos.")
        if st.button(f"💾 Proponer estos {len(escritos)} precios", type="primary"):
            proponer([(r["id"], num(r["Nuevo precio"])) for _, r in escritos.iterrows()], "Cambio individual")
            st.rerun()

    st.divider()
    st.subheader("Cambiar varios a la vez")
    sel = ed[ed["✔"]]
    c1, c2, c3, c4 = st.columns([1.6, 1.6, 1, 1])
    alcance = c1.radio("¿A cuáles?", [f"Tildados ({len(sel)})", f"Todos los de la lista ({len(ed)})"],
                       index=0 if len(sel) else 1, help="Para cambiar una categoría entera, filtrala arriba y elegí 'Todos los de la lista'.")
    tipo = c2.radio("Cambio", ["Aumento / baja en %", "Sumar / restar $", "Precio fijo"])
    valor = c3.number_input("Valor", value=10.0, step=1.0, help="Ej: 10 = +10%. Para bajar, poné un número negativo.")
    paso = c4.selectbox("Redondear", [0, 10, 50, 100], index=1, format_func=lambda x: "No" if x == 0 else f"a ${x}")
    filas = sel if alcance.startswith("Tildados") else ed
    nuevos = []
    for _, r in filas.iterrows():
        act = num(r["Precio actual"])
        if tipo.startswith("Precio fijo"):
            n = valor
        elif act is None:
            continue
        elif tipo.startswith("Aumento"):
            n = act * (1 + valor / 100)
        else:
            n = act + valor
        if n and n > 0:
            nuevos.append((r["id"], r["Producto"], act, redondear(n, paso)))
    if nuevos:
        vista = pd.DataFrame(nuevos, columns=["id", "Producto", "Actual", "Nuevo"]).drop(columns=["id"])
        vista["Cambio"] = [(f"{(n / a - 1) * 100:+.1f}%" if a else "—") for _, _, a, n in nuevos]
        with st.expander(f"Vista previa ({len(nuevos)} productos)", expanded=len(nuevos) <= 8):
            st.dataframe(vista.head(200), hide_index=True, use_container_width=True,
                         column_config={"Actual": st.column_config.NumberColumn(format="$ %.2f"),
                                        "Nuevo": st.column_config.NumberColumn(format="$ %.2f")})
        desc = {"Aumento / baja en %": f"{valor:+g}%", "Sumar / restar $": f"{valor:+g} $", "Precio fijo": f"fijo {pesos(valor)}"}[tipo]
        alcance_txt = ("categoría " + ", ".join(cats)) if (cats and not alcance.startswith("Tildados")) else ("selección" if alcance.startswith("Tildados") else "lista filtrada")
        if st.button(f"Crear {len(nuevos)} propuestas ({desc})", type="primary"):
            proponer([(i, n) for i, _, _, n in nuevos], f"{desc} · {alcance_txt}")
            st.rerun()
    else:
        st.caption("Tildá productos o elegí 'Todos los de la lista' para ver la vista previa.")


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
    "lista": st.Page(pagina_lista, title="Lista de precios", icon="📋", url_path="lista", default=True),
    "aprobar": st.Page(pagina_aprobar, title="Revisar y aprobar", icon="✅", url_path="aprobar"),
    "importar": st.Page(pagina_importar, title="Importar Excel", icon="📤", url_path="importar"),
    "historial": st.Page(pagina_historial, title="Historial", icon="📜", url_path="historial"),
}
with st.sidebar:
    st.markdown("<h2 style='color:#d7141a;letter-spacing:3px;margin:0'>TAIRA</h2><div class='sub'>Precios</div>", unsafe_allow_html=True)
    st.caption(f"👤 {usuario()}" + (" · administrador" if es_admin() else " · solo lectura"))
nav = st.navigation(list(PAGINAS.values()))
with st.sidebar:
    st.divider()
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
