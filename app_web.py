import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
# PEGA AQUÍ TUS DATOS REALES DE SUPABASE (Settings > API)
SUPABASE_URL = "https://gxnoakudooorcsnqcklm.supabase.co"
SUPABASE_KEY = "sb_publishable_CVNOChVw7tkKeC60qSHvWQ_3bTVbIMd" 

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="FÁBRICA TAIRA", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- VARIABLES DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "receta_temp" not in st.session_state:
    st.session_state.receta_temp = []
if "categorias_colores" not in st.session_state:
    st.session_state.categorias_colores = {}

# --- FUNCIÓN DE AUDITORÍA ---
def registrar_movimiento(usuario, accion, detalle):
    try:
        nuevo_registro = {
            "usuario": usuario,
            "accion": accion,
            "detalle": detalle,
            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        supabase.table("registros").insert(nuevo_registro).execute()
    except Exception as e:
        pass

# --- VALIDACIÓN DE ADMINISTRADOR MEJORADA ---
def es_administrador():
    correo = st.session_state.get("email_user", "").strip().lower()
    usuario = st.session_state.get("user", "").strip().lower()
    # Ahora detecta tus dos correos o variantes de tu nombre para asegurar que veas el panel
    correos_admin = ["mininpared@gmail.com", "eleminino.pared@gmail.com"]
    return (correo in correos_admin) or ("minin" in correo) or ("mini" in usuario)

# --- GENERADOR DE COLOR AUTOMÁTICO PARA CATEGORÍAS ---
def obtener_color_categoria(categoria):
    if categoria not in st.session_state.categorias_colores:
        colores = ["#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC3", "#BAE1FF", "#E8BAFF", "#FFBABE"]
        st.session_state.categorias_colores[categoria] = random.choice(colores)
    return st.session_state.categorias_colores[categoria]

# --- NOTIFICACIONES FLOTANTES (TOAST) ---
def verificar_alertas_flotantes(lista_mp, lista_productos):
    for mp in lista_mp:
        cant_actual = float(mp.get('cantidad') or mp.get('longitud') or 0)
        limite_min = float(mp.get('minimo') or 0)
        if cant_actual <= limite_min:
            st.toast(f"⚠️ Stock bajo en Materia Prima: {mp['nombre']} (Actual: {cant_actual})", icon="🚨")
            
    for prod in lista_productos:
        cant_actual = float(prod.get('cantidad') or 0)
        limite_min = float(prod.get('minimo') or 0)
        if cant_actual <= limite_min:
            st.toast(f"⚠️ Stock bajo en Producto: {prod['nombre']} (Actual: {cant_actual})", icon="🚨")

# --- PANTALLA DE ACCESO ---
if not st.session_state.autenticado:
    st.title("Fábrica Taira - Acceso Seguro")
    email = st.text_input("Correo electrónico")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar", use_container_width=True):
        try:
            supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.autenticado = True
            st.session_state.user = email.split('@')[0].capitalize()
            st.session_state.email_user = email.strip().lower()
            st.rerun()
        except Exception as e:
            st.error("Usuario o contraseña incorrectos.")
else:
    # --- MENÚ LATERAL ---
    with st.sidebar:
        st.write("🏭 **Fábrica Taira**")
        st.success(f"Operario: **{st.session_state.user}**")
        if st.button("Cerrar Sesión", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.autenticado = False
            st.session_state.pop("email_user", None)
            st.session_state.pop("user", None)
            st.rerun()

    st.title("📦 FÁBRICA TAIRA - Sistema Integral")
    
    # OBTENER DATOS BASE
    try:
        lista_productos = supabase.table("productos").select("*").execute().data
        lista_mp = supabase.table("materias_primas").select("*").execute().data
    except Exception as e:
        lista_productos = []
        lista_mp = []

    verificar_alertas_flotantes(lista_mp, lista_productos)

    # LAS 6 PESTAÑAS
    tab_prod, tab_mp, tab_stock, tab_ventas, tab_registros, tab_alertas = st.tabs([
        "📋 Producción", 
        "🧪 Materias Primas", 
        "🛠️ Productos y Stock", 
        "📈 Ventas",
        "📜 Registros",
        "⚠️ Alertas"
    ])

    # ==========================================
    # 1. PESTAÑA PRODUCCIÓN Y CICLOS
    # ==========================================
    with tab_prod:
        st.header("Control de Producción y Ciclos")
        st.write(f"Operario actual: **{st.session_state.user}**")
        
        try:
            todos_pedidos = supabase.table("pedidos_produccion").select("*").execute().data
        except Exception as e:
            todos_pedidos = []

        st.markdown("### 📥 1. Registrar Nuevo Pedido")
        with st.form("form_registrar_pedido"):
            nombres_productos = [p['nombre'] for p in lista_productos] if lista_productos else []
            
            if nombres_productos:
                prod_seleccionado = st.selectbox("Seleccionar Producto (Existente)", nombres_productos)
                cant_requerida = st.number_input("Cantidad necesaria", min_value=1, value=1)
                
                if st.form_submit_button("Guardar Pedido de Producción", use_container_width=True):
                    pedido_data = {
                        "producto": prod_seleccionado,
                        "cantidad": cant_requerida,
                        "estado": "Pendiente",
                        "fecha_creacion": str(datetime.now().date()),
                        "creado_por": st.session_state.user
                    }
                    supabase.table("pedidos_produccion").insert(pedido_data).execute()
                    registrar_movimiento(st.session_state.user, "Nuevo Pedido", f"Pidió {cant_requerida}x {prod_seleccionado}")
                    st.success("¡Pedido registrado correctamente!")
                    st.rerun()
            else:
                st.warning("⚠️ Primero debes crear productos en la pestaña 'Productos y Stock'.")
                st.form_submit_button("Guardar Pedido de Producción", disabled=True, use_container_width=True)

        st.markdown("---")
        
        st.markdown("### ⚙️ 2. Gestión de Lotes en Curso")
        
        pendientes = [p for p in todos_pedidos if p.get('estado') == "Pendiente"]
        en_produccion = [p for p in todos_pedidos if p.get('estado') == "En Producción"]
        
        col_iniciar, col_finalizar = st.columns(2)
        
        with col_iniciar:
            st.info("▶️ **INICIAR PRODUCCIÓN**")
            if pendientes:
                opciones_pend = {f"ID {p['id']} | {p['cantidad']}x {p['producto']}": p['id'] for p in pendientes}
                seleccion_iniciar = st.multiselect("Seleccionar órdenes para INICIAR:", list(opciones_pend.keys()))
                
                if st.button("Iniciar Seleccionadas", use_container_width=True, type="primary"):
                    if seleccion_iniciar:
                        for sel in seleccion_iniciar:
                            id_ped = opciones_pend[sel]
                            update_data = {
                                "estado": "En Producción",
                                "fecha_produccion": str(datetime.now().date()),
                                "producido_por": st.session_state.user
                            }
                            supabase.table("pedidos_produccion").update(update_data).eq("id", id_ped).execute()
                            registrar_movimiento(st.session_state.user, "Inicio Producción", f"Inició lote ID {id_ped}")
                        st.success(f"¡Se iniciaron {len(seleccion_iniciar)} órdenes!")
                        st.rerun()
                    else:
                        st.warning("Selecciona al menos una orden.")
            else:
                st.write("✅ No hay pedidos pendientes.")

        with col_finalizar:
            st.success("✅ **FINALIZAR PRODUCCIÓN (Suma al Stock)**")
            if en_produccion:
                opciones_prod = {f"ID {p['id']} | {p['cantidad']}x {p['producto']}": p['id'] for p in en_produccion}
                seleccion_fin = st.multiselect("Seleccionar órdenes TERMINADAS:", list(opciones_prod.keys()))
                
                if st.button("Finalizar Seleccionadas", use_container_width=True, type="primary"):
                    if seleccion_fin:
                        for sel in seleccion_fin:
                            id_ped = opciones_prod[sel]
                            pedido = next((p for p in en_produccion if p['id'] == id_ped), None)
                            
                            if pedido:
                                # 1. Actualizar estado del pedido a finalizado
                                update_fin = {
                                    "estado": "Finalizado",
                                    "fecha_finalizacion": str(datetime.now().date())
                                }
                                supabase.table("pedidos_produccion").update(update_fin).eq("id", id_ped).execute()
                                
                                # 2. SUMAR AL INVENTARIO DE PRODUCTOS
                                prod_nombre = pedido['producto']
                                cant_fabricada = float(pedido['cantidad'])
                                
                                try:
                                    # Traemos la cantidad actual directamente de la DB para ser precisos
                                    prod_db = supabase.table("productos").select("cantidad").eq("nombre", prod_nombre).execute().data
                                    if prod_db:
                                        stock_actual = float(prod_db[0].get("cantidad") or 0)
                                        nuevo_stock = stock_actual + cant_fabricada
                                        supabase.table("productos").update({"cantidad": nuevo_stock}).eq("nombre", prod_nombre).execute()
                                except Exception as e:
                                    pass

                                registrar_movimiento(st.session_state.user, "Producto Terminado", f"Finalizó lote ID {id_ped} (+{cant_fabricada} {prod_nombre})")
                                
                        st.success(f"¡Se finalizaron {len(seleccion_fin)} órdenes y se ACTUALIZÓ el stock!")
                        st.rerun()
                    else:
                        st.warning("Selecciona al menos una orden.")
            else:
                st.write("💤 No hay órdenes en curso en este momento.")

        st.divider()
        st.subheader("📋 3. Órdenes Registradas (Historial General)")
        if todos_pedidos:
            st.dataframe(pd.DataFrame(todos_pedidos), use_container_width=True)
            
            if es_administrador():
                st.markdown("### ⚙️ Administrar Órdenes (Solo Admin)")
                col_edit_ped, col_del_ped = st.columns(2)
                ids_pedidos = [str(p['id']) for p in todos_pedidos]
                
                with col_edit_ped:
                    with st.expander("✏️ Editar Pedido"):
                        id_a_editar = st.selectbox("Seleccionar ID a Editar", ids_pedidos, key="edit_ped_sel")
                        if id_a_editar:
                            ped_data = next((p for p in todos_pedidos if str(p['id']) == id_a_editar), None)
                            with st.form("form_edit_ped"):
                                nuevo_estado = st.selectbox("Estado", ["Pendiente", "En Producción", "Finalizado"], index=["Pendiente", "En Producción", "Finalizado"].index(ped_data.get('estado', 'Pendiente')))
                                nueva_cant = st.number_input("Cantidad", value=int(ped_data.get('cantidad', 1)))
                                if st.form_submit_button("Guardar Cambios"):
                                    supabase.table("pedidos_produccion").update({"estado": nuevo_estado, "cantidad": nueva_cant}).eq("id", int(id_a_editar)).execute()
                                    registrar_movimiento(st.session_state.user, "Editó Pedido", f"ID {id_a_editar} modificado")
                                    st.success("Actualizado.")
                                    st.rerun()
                
                with col_del_ped:
                    with st.expander("🗑️ Eliminar Pedido"):
                        id_a_borrar = st.selectbox("Seleccionar ID a Eliminar", ids_pedidos, key="del_ped_sel")
                        if st.button("Eliminar Orden Seleccionada", type="primary", use_container_width=True):
                            supabase.table("pedidos_produccion").delete().eq("id", int(id_a_borrar)).execute()
                            registrar_movimiento(st.session_state.user, "Eliminó Pedido", f"Se eliminó la orden ID {id_a_borrar}")
                            st.success("Orden eliminada.")
                            st.rerun()
        else:
            st.info("No hay pedidos cargados.")

    # ==========================================
    # 2. PESTAÑA MATERIAS PRIMAS
    # ==========================================
    with tab_mp:
        st.header("Gestión de Materias Primas")
        with st.expander("➕ Cargar Nueva Materia Prima", expanded=True):
            with st.form("form_mp"):
                nombre_mp = st.text_input("Nombre de la Materia Prima")
                categoria_mp = st.selectbox("Tipo de Elemento", ["Herraje (Unidades)", "Cinta (Longitud en cm)"])
                valor_medida = st.number_input("Cantidad o Longitud inicial", min_value=0.0, step=1.0)
                minimo_alerta = st.number_input("Stock Mínimo para Alerta", min_value=0.0, step=1.0)
                
                if st.form_submit_button("Guardar Materia Prima", use_container_width=True):
                    if nombre_mp:
                        if "Cinta" in categoria_mp:
                            tipo_str = "Longitud (cm)"
                            cant = 0
                            longi = valor_medida
                        else:
                            tipo_str = "Unidades"
                            cant = valor_medida
                            longi = 0
                            
                        nueva_mp = {
                            "nombre": nombre_mp,
                            "categoria": "Cinta" if "Cinta" in categoria_mp else "Herraje",
                            "tipo": tipo_str,
                            "cantidad": cant,
                            "longitud": longi,
                            "minimo": minimo_alerta,
                            "fecha": str(datetime.now().date())
                        }
                        supabase.table("materias_primas").insert(nueva_mp).execute()
                        registrar_movimiento(st.session_state.user, "Alta Materia Prima", f"Ingresó {nombre_mp}")
                        st.success("Materia prima guardada correctamente.")
                        st.rerun()

        st.divider()
        st.subheader("Inventario de Materias Primas")
        if lista_mp:
            st.dataframe(pd.DataFrame(lista_mp), use_container_width=True)
            
            if es_administrador():
                st.markdown("### ⚙️ Administrar Materias Primas (Solo Admin)")
                col_edit_mp, col_del_mp = st.columns(2)
                nombres_mps = [m['nombre'] for m in lista_mp]
                
                with col_edit_mp:
                    with st.expander("✏️ Editar Materia Prima"):
                        mp_a_editar = st.selectbox("Seleccionar Materia Prima", nombres_mps, key="edit_mp_sel")
                        if mp_a_editar:
                            datos_mp = next((m for m in lista_mp if m['nombre'] == mp_a_editar), None)
                            with st.form("form_edit_mp"):
                                val_cant = float(datos_mp.get('cantidad') or 0.0)
                                val_long = float(datos_mp.get('longitud') or 0.0)
                                val_actual = val_long if datos_mp.get('tipo') == "Longitud (cm)" else val_cant
                                
                                nuevo_nombre = st.text_input("Nombre", value=datos_mp['nombre'])
                                nueva_cant = st.number_input("Cantidad/Longitud", value=val_actual)
                                nuevo_min = st.number_input("Mínimo", value=float(datos_mp.get('minimo') or 0.0))
                                
                                if st.form_submit_button("Guardar Cambios"):
                                    upd_mp = {
                                        "nombre": nuevo_nombre,
                                        "minimo": nuevo_min,
                                        "cantidad": 0 if datos_mp.get('tipo') == "Longitud (cm)" else nueva_cant,
                                        "longitud": nueva_cant if datos_mp.get('tipo') == "Longitud (cm)" else 0
                                    }
                                    if 'id' in datos_mp:
                                        supabase.table("materias_primas").update(upd_mp).eq("id", datos_mp['id']).execute()
                                    else:
                                        supabase.table("materias_primas").update(upd_mp).eq("nombre", mp_a_editar).execute()
                                    registrar_movimiento(st.session_state.user, "Editó MP", f"Modificó {mp_a_editar}")
                                    st.success("Actualizado.")
                                    st.rerun()

                with col_del_mp:
                    with st.expander("🗑️ Eliminar Materia Prima"):
                        mp_a_borrar = st.selectbox("Seleccionar Materia Prima a Eliminar", nombres_mps, key="del_mp_sel")
                        if st.button("Eliminar Materia Prima", type="primary", use_container_width=True):
                            supabase.table("materias_primas").delete().eq("nombre", mp_a_borrar).execute()
                            registrar_movimiento(st.session_state.user, "Eliminó Materia Prima", f"Se eliminó {mp_a_borrar}")
                            st.success(f"Materia prima '{mp_a_borrar}' eliminada.")
                            st.rerun()
        else:
            st.info("No hay materias primas registradas.")

    # ==========================================
    # 3. PESTAÑA PRODUCTOS Y STOCK
    # ==========================================
    with tab_stock:
        st.header("Gestión de Productos, Categorías y Recetas")
        
        st.subheader("1. Armar Receta (Múltiples Ingredientes)")
        nombres_mp = [m['nombre'] for m in lista_mp] if lista_mp else ["Sin materias primas"]
        sel_mp = st.selectbox("Seleccionar Materia Prima", nombres_mp)
        cant_mp = st.number_input("Cantidad que usa 1 unidad de producto", min_value=0.1, value=1.0)
        
        if st.button("➕ Agregar ingrediente a la receta", use_container_width=True):
            if sel_mp != "Sin materias primas":
                st.session_state.receta_temp.append({"material": sel_mp, "cantidad": cant_mp})
                st.success(f"Agregado: {cant_mp} de {sel_mp}")
                st.rerun()
                
        if st.session_state.receta_temp:
            texto_ingredientes = ", ".join([f"{item['cantidad']}x {item['material']}" for item in st.session_state.receta_temp])
            st.info(f"📋 **Receta actual:** {texto_ingredientes}")
            
            if st.button("🗑️ Limpiar receta temporal", use_container_width=True):
                st.session_state.receta_temp = []
                st.rerun()

        st.divider()
        st.subheader("2. Guardar Producto Nuevo con Categoría")
        with st.form("form_producto"):
            nombre_nuevo_prod = st.text_input("Nombre del Producto Final")
            categoria_prod = st.text_input("Categoría (ej: Cuadernos, Agendas, Calendarios)").strip().capitalize()
            if not categoria_prod:
                categoria_prod = "General"
                
            stock_ini_prod = st.number_input("Stock inicial", min_value=0, value=0)
            minimo_prod = st.number_input("Stock Mínimo para Alertas", min_value=0, value=0)
            
            if st.form_submit_button("Guardar Producto Completo", use_container_width=True):
                if nombre_nuevo_prod:
                    nuevo_prod = {
                        "nombre": nombre_nuevo_prod,
                        "categoria": categoria_prod,
                        "cantidad": stock_ini_prod,
                        "minimo": minimo_prod,
                        "receta": st.session_state.receta_temp 
                    }
                    supabase.table("productos").insert(nuevo_prod).execute()
                    registrar_movimiento(st.session_state.user, "Creó Producto", f"Nuevo producto: {nombre_nuevo_prod} [{categoria_prod}]")
                    st.session_state.receta_temp = [] 
                    st.success("¡Producto y receta guardados con éxito!")
                    st.rerun()
                    
        st.divider()
        st.subheader("Inventario y Filtrado por Categoría")
        if lista_productos:
            productos_limpios = []
            for p in lista_productos:
                receta_raw = p.get('receta', [])
                if isinstance(receta_raw, str):
                    try:
                        receta_raw = json.loads(receta_raw)
                    except:
                        receta_raw = []
                
                if isinstance(receta_raw, list) and len(receta_raw) > 0:
                    str_receta = ", ".join([f"{item.get('cantidad', '')} {item.get('material', '')}" for item in receta_raw])
                else:
                    str_receta = "Sin receta"

                cat = p.get('categoria', 'General')
                productos_limpios.append({
                    "nombre": p.get('nombre'),
                    "categoria": cat,
                    "cantidad": p.get('cantidad', 0),
                    "minimo": p.get('minimo', 0),
                    "receta": str_receta
                })
            
            df_prods = pd.DataFrame(productos_limpios)
            categorias_disponibles = ["Todas"] + list(df_prods['categoria'].unique())
            cat_seleccionada = st.selectbox("Filtrar por Categoría", categorias_disponibles)
            
            if cat_seleccionada != "Todas":
                df_prods_filtrado = df_prods[df_prods['categoria'] == cat_seleccionada]
            else:
                df_prods_filtrado = df_prods
                
            st.dataframe(df_prods_filtrado, use_container_width=True)
            
            if es_administrador():
                st.markdown("### ⚙️ Administrar Productos (Solo Admin)")
                col_edit_prod, col_del_prod = st.columns(2)
                prods_nombres = [p['nombre'] for p in lista_productos]
                
                with col_edit_prod:
                    with st.expander("✏️ Editar Producto"):
                        prod_a_editar = st.selectbox("Seleccionar Producto", prods_nombres, key="edit_prod_sel")
                        if prod_a_editar:
                            datos_prod = next((p for p in lista_productos if p['nombre'] == prod_a_editar), None)
                            with st.form("form_edit_prod"):
                                nuevo_nombre = st.text_input("Nombre", value=datos_prod['nombre'])
                                nueva_cat = st.text_input("Categoría", value=datos_prod.get('categoria', 'General'))
                                nueva_cant = st.number_input("Cantidad", value=int(datos_prod.get('cantidad', 0)))
                                nuevo_min = st.number_input("Mínimo", value=int(datos_prod.get('minimo', 0)))
                                if st.form_submit_button("Guardar Cambios"):
                                    upd_prod = {
                                        "nombre": nuevo_nombre,
                                        "categoria": nueva_cat,
                                        "cantidad": nueva_cant,
                                        "minimo": nuevo_min
                                    }
                                    if 'id' in datos_prod:
                                        supabase.table("productos").update(upd_prod).eq("id", datos_prod['id']).execute()
                                    else:
                                        supabase.table("productos").update(upd_prod).eq("nombre", prod_a_editar).execute()
                                    registrar_movimiento(st.session_state.user, "Editó Producto", f"Modificó {prod_a_editar}")
                                    st.success("Actualizado.")
                                    st.rerun()

                with col_del_prod:
                    with st.expander("🗑️ Eliminar Producto"):
                        prod_a_borrar = st.selectbox("Seleccionar Producto a Eliminar", prods_nombres, key="del_prod_sel")
                        if st.button("Eliminar Producto", type="primary", use_container_width=True):
                            supabase.table("productos").delete().eq("nombre", prod_a_borrar).execute()
                            registrar_movimiento(st.session_state.user, "Eliminó Producto", f"Se eliminó {prod_a_borrar}")
                            st.success(f"Producto '{prod_a_borrar}' eliminado.")
                            st.rerun()
        else:
            st.info("No hay productos cargados.")

    # ==========================================
    # 4. PESTAÑA VENTAS
    # ==========================================
    with tab_ventas:
        st.header("Registro de Salidas y Ventas")
        
        with st.form("form_registrar_venta"):
            st.subheader("📦 Registrar Nueva Salida / Venta")
            nombres_productos = [p['nombre'] for p in lista_productos] if lista_productos else []
            
            if nombres_productos:
                prod_venta = st.selectbox("Seleccionar Producto", nombres_productos)
                cant_venta = st.number_input("Cantidad retirada o vendida", min_value=1, value=1)
                
                if st.form_submit_button("Confirmar Salida (Descuenta Stock)", use_container_width=True):
                    # 1. DESCONTAR DEL STOCK PRIMERO
                    try:
                        prod_db = supabase.table("productos").select("cantidad").eq("nombre", prod_venta).execute().data
                        if prod_db:
                            stock_actual = float(prod_db[0].get("cantidad") or 0)
                            nuevo_stock = stock_actual - cant_venta
                            supabase.table("productos").update({"cantidad": nuevo_stock}).eq("nombre", prod_venta).execute()
                    except Exception as e:
                        pass
                    
                    # 2. REGISTRAR LA VENTA
                    venta_data = {
                        "producto": prod_venta,
                        "cantidad": cant_venta,
                        "registrado_por": st.session_state.user,
                        "fecha": str(datetime.now().date())
                    }
                    supabase.table("ventas_historial").insert(venta_data).execute()
                    
                    registrar_movimiento(st.session_state.user, "Registró Salida/Venta", f"Salida de {cant_venta}x {prod_venta} (-{cant_venta} Stock)")
                    st.success(f"¡Salida registrada con éxito y stock actualizado!")
                    st.rerun()
            else:
                st.warning("⚠️ No hay productos disponibles para registrar salidas.")
                st.form_submit_button("Confirmar Salida (Descuenta Stock)", disabled=True, use_container_width=True)

        st.divider()
        st.subheader("Historial de Salidas Registradas")
        try:
            ventas = supabase.table("ventas_historial").select("*").execute().data
            if ventas:
                st.dataframe(pd.DataFrame(ventas), use_container_width=True)
                
                if es_administrador():
                    st.markdown("### ⚙️ Administrar Ventas (Solo Admin)")
                    col_edit_venta, col_del_venta = st.columns(2)
                    ids_ventas = [str(v['id']) for v in ventas] if 'id' in ventas[0] else []
                    
                    if ids_ventas:
                        with col_edit_venta:
                            with st.expander("✏️ Editar Venta"):
                                id_a_editar = st.selectbox("Seleccionar ID de Venta", ids_ventas, key="edit_venta_sel")
                                if id_a_editar:
                                    datos_venta = next((v for v in ventas if str(v['id']) == id_a_editar), None)
                                    with st.form("form_edit_venta"):
                                        nueva_cant = st.number_input("Cantidad Vendida", value=int(datos_venta.get('cantidad', 1)))
                                        if st.form_submit_button("Guardar Cambios"):
                                            supabase.table("ventas_historial").update({"cantidad": nueva_cant}).eq("id", int(id_a_editar)).execute()
                                            registrar_movimiento(st.session_state.user, "Editó Venta", f"ID {id_a_editar} actualizado")
                                            st.success("Actualizado.")
                                            st.rerun()

                        with col_del_venta:
                            with st.expander("🗑️ Eliminar Venta"):
                                v_a_borrar = st.selectbox("Seleccionar ID a Eliminar", ids_ventas, key="del_venta_sel")
                                if st.button("Eliminar Registro", type="primary", use_container_width=True):
                                    supabase.table("ventas_historial").delete().eq("id", int(v_a_borrar)).execute()
                                    registrar_movimiento(st.session_state.user, "Eliminó Venta", f"Se eliminó registro de venta ID {v_a_borrar}")
                                    st.success("Registro eliminado.")
                                    st.rerun()
            else:
                st.info("No hay ventas registradas.")
        except Exception as e:
            st.error(f"Error al cargar ventas: {e}")

    # ==========================================
    # 5. PESTAÑA REGISTROS (Auditoría)
    # ==========================================
    with tab_registros:
        st.header("📜 Auditoría y Registro General de Movimientos")
        try:
            regs = supabase.table("registros").select("*").order("fecha_hora", desc=True).execute().data
            if regs:
                df_regs = pd.DataFrame(regs)
                
                query_busqueda = st.text_input("🔍 Búsqueda predictiva en registros (escribe operario, acción o detalle):").strip().lower()
                
                if query_busqueda:
                    mask = df_regs.astype(str).apply(lambda x: x.str.lower().str.contains(query_busqueda)).any(axis=1)
                    df_regs_filtrado = df_regs[mask]
                else:
                    df_regs_filtrado = df_regs
                    
                st.dataframe(df_regs_filtrado, use_container_width=True)
                
                st.download_button(
                    label="📥 Descargar Historial Completo (CSV)",
                    data=df_regs.to_csv(index=False).encode('utf-8'),
                    file_name='historial_auditoria_taira.csv',
                    mime='text/csv',
                    use_container_width=True
                )
                
                if es_administrador():
                    st.divider()
                    st.markdown("### ⚙️ Administrar Registros de Auditoría (Solo Admin)")
                    col_edit_reg, col_del_reg = st.columns(2)
                    ids_regs = [str(r['id']) for r in regs] if 'id' in regs[0] else []
                    
                    if ids_regs:
                        with col_edit_reg:
                            with st.expander("✏️ Editar Registro"):
                                reg_a_editar = st.selectbox("Seleccionar ID a Editar", ids_regs, key="edit_reg_sel")
                                if reg_a_editar:
                                    datos_reg = next((r for r in regs if str(r['id']) == reg_a_editar), None)
                                    with st.form("form_edit_reg"):
                                        nuevo_usuario = st.text_input("Usuario", value=datos_reg.get('usuario', ''))
                                        nueva_accion = st.text_input("Acción", value=datos_reg.get('accion', ''))
                                        nuevo_detalle = st.text_area("Detalle", value=datos_reg.get('detalle', ''))
                                        nueva_fecha = st.text_input("Fecha y Hora", value=datos_reg.get('fecha_hora', ''))
                                        
                                        if st.form_submit_button("Guardar Cambios"):
                                            upd_reg = {
                                                "usuario": nuevo_usuario,
                                                "accion": nueva_accion,
                                                "detalle": nuevo_detalle,
                                                "fecha_hora": nueva_fecha
                                            }
                                            supabase.table("registros").update(upd_reg).eq("id", int(reg_a_editar)).execute()
                                            st.success("Registro de auditoría actualizado.")
                                            st.rerun()

                        with col_del_reg:
                            with st.expander("🗑️ Eliminar Registro"):
                                reg_a_borrar = st.selectbox("Seleccionar ID de Registro a Eliminar", ids_regs, key="del_reg_sel")
                                if st.button("Eliminar Definitivamente", type="primary", use_container_width=True):
                                    supabase.table("registros").delete().eq("id", int(reg_a_borrar)).execute()
                                    st.success(f"Registro ID {reg_a_borrar} eliminado.")
                                    st.rerun()
            else:
                st.info("Aún no hay registros de auditoría.")
        except Exception as e:
            st.info("Asegúrate de haber creado la tabla 'registros' en Supabase.")

    # ==========================================
    # 6. PESTAÑA ALERTAS
    # ==========================================
    with tab_alertas:
        st.header("⚠️ Panel de Alertas de Stock Mínimo")
        hay_alertas = False
        
        st.subheader("Materias Primas con Stock Bajo")
        for mp in lista_mp:
            cant_actual = float(mp.get('cantidad') or mp.get('longitud') or 0)
            limite_min = float(mp.get('minimo') or 0)
            if cant_actual <= limite_min:
                st.warning(f"⚠️ **{mp['nombre']}** está bajo de stock. Actual: {cant_actual} (Mínimo: {limite_min})")
                hay_alertas = True
                
        st.subheader("Productos Terminados con Stock Bajo")
        for prod in lista_productos:
            cant_actual = float(prod.get('cantidad') or 0)
            limite_min = float(prod.get('minimo') or 0)
            if cant_actual <= limite_min:
                st.warning(f"⚠️ **{prod['nombre']}** está bajo de stock. Actual: {cant_actual} (Mínimo: {limite_min})")
                hay_alertas = True
                
        if not hay_alertas:
            st.success("✅ Todo el inventario se encuentra en niveles óptimos.")
