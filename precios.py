"""Pestaña "Costos y Precios" de la app de Fábrica Taira.

Flujo:
  1. Se cargan los precios de las materias primas (cinta por metro, herrajes por unidad).
  2. Cada producto del catálogo se vincula con su receta (producto de stock), y se le pone
     mano de obra y margen.
  3. Se GENERAN PROPUESTAS de precio (desde costos o con un aumento por porcentaje).
     Las propuestas NO se publican: quedan en "precio_propuesto".
  4. El administrador revisa y APRUEBA. Recién ahí cambia "precio_publicado", que es lo que
     ve el catálogo online. Cada aprobación queda en el historial y se puede deshacer.
"""
import json
import math
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

SIN_RECETA = "— sin receta —"
ALERTA_VARIACION = 30  # % de cambio a partir del cual se marca para revisar con cuidado


# ---------------------------------------------------------------------------
# Cálculos (sin Streamlit, para poder probarlos)
# ---------------------------------------------------------------------------
def es_cinta(mp):
    return str(mp.get("tipo") or "").lower().startswith("longitud") or str(mp.get("categoria") or "").lower() == "cinta"


def indice_materias(lista_mp):
    """Nombre (en minúscula) -> materia prima. Si hay nombres repetidos, gana la que tiene precio."""
    idx = {}
    for mp in lista_mp:
        clave = str(mp.get("nombre") or "").strip().lower()
        if not clave:
            continue
        if clave not in idx or (idx[clave].get("precio") in (None, 0) and mp.get("precio") not in (None, 0)):
            idx[clave] = mp
    return idx


def leer_receta(receta):
    if isinstance(receta, str):
        try:
            receta = json.loads(receta)
        except Exception:
            return []
    return receta if isinstance(receta, list) else []


def costo_receta(receta, idx_mp):
    """Devuelve (costo, faltantes). La cinta se carga por metro y la receta la usa en cm."""
    costo, faltantes = 0.0, []
    for item in leer_receta(receta):
        nombre = str(item.get("material") or "").strip()
        cant = float(item.get("cantidad") or 0)
        mp = idx_mp.get(nombre.lower())
        if not mp:
            faltantes.append(f"{nombre} (no existe)")
            continue
        precio = mp.get("precio")
        if precio in (None, "") or float(precio) <= 0:
            faltantes.append(f"{nombre} (sin precio)")
            continue
        precio = float(precio)
        costo += (cant / 100.0) * precio if es_cinta(mp) else cant * precio
    return round(costo, 2), faltantes


def redondear(valor, paso):
    if not paso:
        return round(valor, 2)
    return float(math.ceil(valor / paso) * paso)


def precio_sugerido(costo, mano_obra, margen, paso=0):
    return redondear((costo + float(mano_obra or 0)) * (1 + float(margen or 0) / 100.0), paso)


def variacion(actual, nuevo):
    if actual in (None, 0) or nuevo is None:
        return None
    return round((float(nuevo) / float(actual) - 1) * 100, 1)


# ---------------------------------------------------------------------------
# Pantalla
# ---------------------------------------------------------------------------
def _ahora():
    return datetime.now(timezone.utc).isoformat()


def _num(v, defecto=0.0):
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return defecto
        return float(v)
    except Exception:
        return defecto


def mostrar_pestana_precios(supabase, lista_mp, lista_productos, usuario, es_admin, registrar):
    st.header("💲 Costos y Precios")
    st.caption(
        "Cargá los precios de los insumos → el sistema calcula el precio de cada producto → "
        "vos revisás y aprobás. **Nada cambia en el catálogo online hasta que se aprueba.**"
    )

    try:
        catalogo = supabase.table("catalogo").select("*").order("orden").execute().data or []
    except Exception as e:
        st.error(f"No se pudo leer el catálogo: {e}")
        return

    idx_mp = indice_materias(lista_mp)
    stock_por_id = {p["id"]: p for p in lista_productos if "id" in p}
    stock_por_nombre = {p["nombre"]: p for p in lista_productos}

    paso = st.selectbox(
        "Redondeo de precios sugeridos",
        [0, 10, 50, 100],
        index=2,
        format_func=lambda x: "Sin redondeo" if x == 0 else f"Hacia arriba, de a ${x}",
        key="precios_redondeo",
    )

    # ---------------------------------------------------------------- 1
    st.subheader("1️⃣ Precios de los insumos")
    st.caption("Cintas: precio **por metro**. Herrajes: precio **por unidad**. Podés cargarlo cualquiera del equipo.")
    if not lista_mp:
        st.info("No hay materias primas cargadas.")
    else:
        df_mp = pd.DataFrame([
            {
                "id": m.get("id"),
                "Insumo": m.get("nombre"),
                "Tipo": "Cinta (por metro)" if es_cinta(m) else "Herraje (por unidad)",
                "Precio": _num(m.get("precio"), None) if m.get("precio") is not None else None,
                "Actualizado": (str(m.get("precio_actualizado") or "")[:10]) or "—",
            }
            for m in sorted(lista_mp, key=lambda x: (not es_cinta(x), str(x.get("nombre", "")).lower()))
        ])
        ed_mp = st.data_editor(
            df_mp,
            key="editor_mp_precios",
            hide_index=True,
            use_container_width=True,
            disabled=["id", "Insumo", "Tipo", "Actualizado"],
            column_config={
                "id": None,
                "Precio": st.column_config.NumberColumn("Precio $", min_value=0.0, step=1.0, format="$ %.2f"),
            },
        )
        sin_precio = int(ed_mp["Precio"].isna().sum())
        if sin_precio:
            st.caption(f"⚠️ {sin_precio} insumos todavía sin precio.")
        if st.button("💾 Guardar precios de insumos", use_container_width=True, key="guardar_mp_precios"):
            orig = {r["id"]: r["Precio"] for _, r in df_mp.iterrows()}
            cambios = 0
            for _, r in ed_mp.iterrows():
                nuevo, viejo = r["Precio"], orig.get(r["id"])
                nuevo_n = None if pd.isna(nuevo) else float(nuevo)
                viejo_n = None if (viejo is None or pd.isna(viejo)) else float(viejo)
                if nuevo_n != viejo_n:
                    supabase.table("materias_primas").update({
                        "precio": nuevo_n,
                        "unidad": "metro" if r["Tipo"].startswith("Cinta") else "unidad",
                        "precio_actualizado": _ahora(),
                    }).eq("id", r["id"]).execute()
                    registrar(usuario, "Precio insumo", f"{r['Insumo']}: {viejo_n} → {nuevo_n}")
                    cambios += 1
            if cambios:
                st.success(f"Se guardaron {cambios} precios. Ahora generá las propuestas en el paso 3.")
                st.rerun()
            else:
                st.info("No había cambios para guardar.")

    # ---------------------------------------------------------------- 2
    st.divider()
    st.subheader("2️⃣ Receta, mano de obra y margen")
    st.caption(
        "Para cada producto fabricado elegí qué receta usa (los productos de tu stock), cuánto es la mano de obra "
        "y qué margen querés ganar. **Precio sugerido = (materiales + mano de obra) × (1 + margen %).**"
    )
    fabricados = [c for c in catalogo if c.get("linea") == "fabricado"]
    cats_fab = sorted({c.get("categoria") or "" for c in fabricados})
    cat_sel = st.selectbox("Categoría", ["Todas"] + cats_fab, key="precios_cat_fab")
    visibles = [c for c in fabricados if cat_sel == "Todas" or c.get("categoria") == cat_sel]

    opciones_receta = [SIN_RECETA] + sorted(stock_por_nombre.keys(), key=str.lower)
    filas = []
    for c in visibles:
        stock = stock_por_id.get(c.get("producto_stock_id"))
        costo, falt = (costo_receta(stock.get("receta"), idx_mp) if stock else (None, []))
        sug = precio_sugerido(costo, c.get("mano_obra"), c.get("margen"), paso) if (stock and not falt and costo) else None
        filas.append({
            "id": c["id"],
            "Producto": c["nombre"],
            "Receta": stock["nombre"] if stock else SIN_RECETA,
            "Mano de obra": _num(c.get("mano_obra")),
            "Margen %": _num(c.get("margen")),
            "Materiales": costo if (stock and not falt) else None,
            "Sugerido": sug,
            "Publicado": _num(c.get("precio_publicado"), None) if c.get("precio_publicado") is not None else None,
            "Falta": ", ".join(falt) if falt else ("" if stock else "vincular receta"),
        })
    df_fab = pd.DataFrame(filas)
    if df_fab.empty:
        st.info("No hay productos fabricados en esta categoría.")
    else:
        ed_fab = st.data_editor(
            df_fab,
            key=f"editor_fab_{cat_sel}",
            hide_index=True,
            use_container_width=True,
            disabled=["id", "Producto", "Materiales", "Sugerido", "Publicado", "Falta"],
            column_config={
                "id": None,
                "Receta": st.column_config.SelectboxColumn("Receta", options=opciones_receta, required=True),
                "Mano de obra": st.column_config.NumberColumn("Mano de obra $", min_value=0.0, step=10.0, format="$ %.2f"),
                "Margen %": st.column_config.NumberColumn("Margen %", min_value=0.0, max_value=1000.0, step=1.0, format="%.0f %%"),
                "Materiales": st.column_config.NumberColumn("Materiales $", format="$ %.2f"),
                "Sugerido": st.column_config.NumberColumn("Sugerido $", format="$ %.2f"),
                "Publicado": st.column_config.NumberColumn("Publicado $", format="$ %.2f"),
                "Falta": st.column_config.TextColumn("Para calcular falta"),
            },
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Guardar recetas, mano de obra y márgenes", use_container_width=True, key="guardar_fab"):
                orig = df_fab.set_index("id")
                cambios = 0
                for _, r in ed_fab.iterrows():
                    o = orig.loc[r["id"]]
                    if (r["Receta"], _num(r["Mano de obra"]), _num(r["Margen %"])) != (o["Receta"], _num(o["Mano de obra"]), _num(o["Margen %"])):
                        stock = stock_por_nombre.get(r["Receta"])
                        supabase.table("catalogo").update({
                            "producto_stock_id": stock["id"] if stock else None,
                            "mano_obra": _num(r["Mano de obra"]),
                            "margen": _num(r["Margen %"]),
                        }).eq("id", int(r["id"])).execute()
                        cambios += 1
                if cambios:
                    registrar(usuario, "Costos de productos", f"Actualizó receta/mano de obra/margen de {cambios} productos")
                    st.success(f"Se guardaron {cambios} productos.")
                    st.rerun()
                else:
                    st.info("No había cambios para guardar.")
        with c2:
            with st.popover("Aplicar a toda la categoría", use_container_width=True):
                mo_cat = st.number_input("Mano de obra $", min_value=0.0, step=10.0, key="mo_cat")
                mg_cat = st.number_input("Margen %", min_value=0.0, step=1.0, key="mg_cat")
                if st.button(f"Aplicar a {len(visibles)} productos", key="aplicar_cat"):
                    for c in visibles:
                        supabase.table("catalogo").update({"mano_obra": mo_cat, "margen": mg_cat}).eq("id", c["id"]).execute()
                    registrar(usuario, "Costos de productos", f"Mano de obra ${mo_cat} y margen {mg_cat}% en {cat_sel}")
                    st.rerun()

    # ---------------------------------------------------------------- 3
    st.divider()
    st.subheader("3️⃣ Generar propuestas de precio")
    st.caption("Esto **no publica nada**: deja los precios nuevos en espera para que los revises en el paso 4.")
    modo = st.radio("¿Cómo querés calcular?", ["Desde costos (recetas)", "Aumento por porcentaje"], horizontal=True, key="modo_prop")

    if modo == "Desde costos (recetas)":
        calculables = []
        for c in fabricados:
            stock = stock_por_id.get(c.get("producto_stock_id"))
            if not stock or _num(c.get("margen")) <= 0:
                continue
            costo, falt = costo_receta(stock.get("receta"), idx_mp)
            if falt or not costo:
                continue
            nuevo = precio_sugerido(costo, c.get("mano_obra"), c.get("margen"), paso)
            if c.get("precio_publicado") is None or round(nuevo, 2) != round(_num(c.get("precio_publicado")), 2):
                calculables.append((c, nuevo))
        st.write(f"Productos listos para calcular (con receta, insumos con precio y margen cargado): **{len(calculables)}**")
        if st.button("Generar propuestas desde costos", type="primary", disabled=not calculables, key="gen_costos"):
            for c, nuevo in calculables:
                supabase.table("catalogo").update({"precio_propuesto": nuevo, "motivo_propuesta": "Costos"}).eq("id", c["id"]).execute()
            registrar(usuario, "Propuesta de precios", f"Generó {len(calculables)} propuestas desde costos")
            st.success(f"Se generaron {len(calculables)} propuestas. Revisalas en el paso 4.")
            st.rerun()
    else:
        lineas = st.multiselect("Línea", ["fabricado", "importado"], default=["importado"], key="pct_lineas",
                                format_func=lambda x: "Fabricados" if x == "fabricado" else "Importados")
        cats = sorted({c.get("categoria") or "" for c in catalogo if c.get("linea") in lineas})
        cats_pct = st.multiselect("Categorías (vacío = todas)", cats, key="pct_cats")
        pct = st.number_input("Aumento %", min_value=-90.0, max_value=500.0, value=10.0, step=1.0, key="pct_valor")
        objetivo = [c for c in catalogo if c.get("linea") in lineas and (not cats_pct or c.get("categoria") in cats_pct)
                    and c.get("precio_publicado") is not None]
        st.write(f"Productos afectados: **{len(objetivo)}**")
        if st.button(f"Generar propuestas con {pct:+.0f}%", type="primary", disabled=not objetivo, key="gen_pct"):
            for c in objetivo:
                nuevo = redondear(_num(c["precio_publicado"]) * (1 + pct / 100.0), paso)
                supabase.table("catalogo").update({"precio_propuesto": nuevo, "motivo_propuesta": f"Aumento {pct:+.0f}%"}).eq("id", c["id"]).execute()
            registrar(usuario, "Propuesta de precios", f"Aumento {pct:+.0f}% en {len(objetivo)} productos")
            st.success(f"Se generaron {len(objetivo)} propuestas. Revisalas en el paso 4.")
            st.rerun()

    # ---------------------------------------------------------------- 4
    st.divider()
    st.subheader("4️⃣ Revisar y aprobar")
    pendientes = [c for c in catalogo if c.get("precio_propuesto") is not None]
    if not pendientes:
        st.success("No hay precios esperando aprobación. El catálogo online está al día.")
    else:
        df_p = pd.DataFrame([
            {
                "id": c["id"],
                "Aprobar": True,
                "Producto": c["nombre"],
                "Categoría": c.get("categoria"),
                "Actual": _num(c.get("precio_publicado"), None) if c.get("precio_publicado") is not None else None,
                "Nuevo": _num(c.get("precio_propuesto")),
                "Cambio %": variacion(c.get("precio_publicado"), c.get("precio_propuesto")),
                "Motivo": c.get("motivo_propuesta") or "",
            }
            for c in pendientes
        ])
        grandes = df_p[df_p["Cambio %"].abs() >= ALERTA_VARIACION] if df_p["Cambio %"].notna().any() else df_p.iloc[0:0]
        st.write(f"**{len(df_p)}** precios esperando aprobación.")
        if len(grandes):
            st.warning(f"⚠️ {len(grandes)} productos cambian {ALERTA_VARIACION}% o más. Revisalos antes de aprobar: puede ser un error de carga.")
        ed_p = st.data_editor(
            df_p,
            key="editor_aprobacion",
            hide_index=True,
            use_container_width=True,
            disabled=["id", "Producto", "Categoría", "Actual", "Cambio %", "Motivo"] + ([] if es_admin else ["Aprobar", "Nuevo"]),
            column_config={
                "id": None,
                "Aprobar": st.column_config.CheckboxColumn("✔"),
                "Actual": st.column_config.NumberColumn("Actual $", format="$ %.2f"),
                "Nuevo": st.column_config.NumberColumn("Nuevo $", min_value=0.0, format="$ %.2f"),
                "Cambio %": st.column_config.NumberColumn("Cambio", format="%+.1f %%"),
            },
        )
        st.download_button(
            "📥 Descargar propuestas (Excel / CSV)",
            data=ed_p.drop(columns=["id", "Aprobar"]).to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            file_name=f"propuestas_precios_{datetime.now():%Y-%m-%d}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        if not es_admin:
            st.info("🔒 Solo el administrador puede aprobar o descartar precios.")
        else:
            sel = ed_p[ed_p["Aprobar"]]
            a1, a2 = st.columns(2)
            with a1:
                if st.button(f"✅ Aprobar y publicar {len(sel)} precios", type="primary", disabled=sel.empty, use_container_width=True, key="aprobar"):
                    por_id = {c["id"]: c for c in pendientes}
                    for _, r in sel.iterrows():
                        c = por_id[int(r["id"])]
                        nuevo = round(_num(r["Nuevo"]), 2)
                        supabase.table("precios_historial").insert({
                            "catalogo_id": c["id"], "nombre": c["nombre"],
                            "precio_anterior": c.get("precio_publicado"), "precio_nuevo": nuevo,
                            "motivo": c.get("motivo_propuesta"), "aprobado_por": usuario,
                        }).execute()
                        supabase.table("catalogo").update({
                            "precio_publicado": nuevo, "precio_propuesto": None,
                            "motivo_propuesta": None, "actualizado": _ahora(),
                        }).eq("id", c["id"]).execute()
                    registrar(usuario, "Aprobó precios", f"Publicó {len(sel)} precios nuevos en el catálogo")
                    st.success(f"¡Listo! {len(sel)} precios publicados. El catálogo online ya los muestra.")
                    st.rerun()
            with a2:
                if st.button(f"🗑️ Descartar {len(sel)} propuestas", disabled=sel.empty, use_container_width=True, key="descartar"):
                    for _, r in sel.iterrows():
                        supabase.table("catalogo").update({"precio_propuesto": None, "motivo_propuesta": None}).eq("id", int(r["id"])).execute()
                    registrar(usuario, "Descartó precios", f"Descartó {len(sel)} propuestas")
                    st.rerun()

    # ---------------------------------------------------------------- Historial
    with st.expander("📜 Historial de precios aprobados"):
        try:
            hist = supabase.table("precios_historial").select("*").order("fecha", desc=True).limit(300).execute().data or []
        except Exception:
            hist = []
        if not hist:
            st.write("Todavía no se aprobó ningún cambio de precio.")
        else:
            df_h = pd.DataFrame(hist)
            df_h["fecha"] = df_h["fecha"].astype(str).str[:16].str.replace("T", " ")
            st.dataframe(
                df_h[["fecha", "nombre", "precio_anterior", "precio_nuevo", "motivo", "aprobado_por"]],
                hide_index=True, use_container_width=True,
            )
            if es_admin:
                st.caption("¿Te equivocaste? Elegí un cambio y se crea una propuesta para volver al precio anterior (la aprobás en el paso 4).")
                opciones = {f"{h['fecha'][:16]} · {h['nombre']} · {h['precio_anterior']} → {h['precio_nuevo']}": h for h in hist
                            if h.get("catalogo_id") and h.get("precio_anterior") is not None}
                if opciones:
                    elegido = st.selectbox("Cambio a deshacer", list(opciones.keys()), key="deshacer_sel")
                    if st.button("↩️ Proponer volver al precio anterior", key="deshacer"):
                        h = opciones[elegido]
                        supabase.table("catalogo").update({"precio_propuesto": h["precio_anterior"], "motivo_propuesta": "Deshacer cambio"}).eq("id", h["catalogo_id"]).execute()
                        st.rerun()
