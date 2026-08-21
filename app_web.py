import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
# PEGA AQUÍ TUS DATOS REALES DE SUPABASE (Settings > API)
SUPABASE_URL = "https://gxnoakudooorcsnqcklm.supabase.co"
SUPABASE_KEY = "sb_publishable_CVNOChVw7tkKeC60qSHvWQ_3bTVbIMd" 

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- VARIABLES DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "receta_temp" not in st.session_state:
    st.session_state.receta_temp = []

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

# --- FUNCIÓN DE NOTIFICACIONES FLOTANTES (TOAST) ---
def verificar_alertas_flotantes(lista_mp, lista_productos):
    """Muestra notificaciones flotantes si algún stock está por debajo del mínimo."""
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
            st.rerun()

    st.title("📦 FÁBRICA TAIRA - Sistema Integral")
    
    # OBTENER DATOS BASE
    try:
        lista_productos = supabase.table("productos").select("*").execute().data
        lista_mp = supabase.table("materias_primas").select("*").execute().data
    except Exception as e:
        lista_productos = []
        lista_mp = []

    # DISPARAR ALERTAS FLOTANTES EN CUALQUIER PESTAÑA
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
        
        st.markdown("### 🎛️ Panel de Acciones y Pedidos")
        
        # MODIFICACIÓN 2: Formulario de Registro de Pedido con selector de productos existentes y cantidad
        with st.form("form_registrar_pedido"):
            st.subheader("📥 Registrar Nuevo Pedido")
            nombres_productos = [p['nombre'] for p in lista_productos] if lista_productos else []
            
            if nombres_productos:
                prod_seleccionado = st.selectbox("Seleccionar Producto (Existente)", nombres_productos)
                cant_requerida = st.number_input("Cantidad necesaria", min_value=1, value=1)
                
                if st.form_submit_button("Guardar Pedido de Producción"):
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
                st.warning("⚠️ Primero debes crear productos en la pestaña 'Productos y Stock' para poder hacer pedidos.")
                st.form_submit_button("Guardar Pedido de Producción", disabled=True)

        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("⚙️ Iniciar Producción (Siguiente Pendiente)", use_container_width=True):
                update_data = {
                    "estado": "En Producción",
                    "fecha_produccion": str(datetime.now().date()),
                    "producido_por": st.session_state.user
                }
                pendientes = [p for p in supabase.table("pedidos_produccion").select("*").execute().data if p.get('estado') == "Pendiente"]
                if pendientes:
                    ultimo_id = pendientes[-1]['id']
                    supabase.table("pedidos_produccion").update(update_data).eq("id", ultimo_id).execute()
                    registrar_movimiento(st.session_state.user, "Inicio Producción", f"Se inició el lote ID {ultimo_id}")
                    st.success("¡Producción iniciada!")
                    st.rerun()
                else:
                    st.warning("No hay pedidos pendientes para iniciar.")

        with col_btn2:
            if st.button("✅ Producto Terminado", use_container_width=True):
                en_curso = [p for p in supabase.table("pedidos_produccion").select("*").execute().data if p.get('estado') == "En Producción"]
                if en_curso:
                    p = en_curso[-1]
                    update_fin = {
                        "estado": "Finalizado",
                        "fecha_finalizacion": str(datetime.now().date())
                    }
                    supabase.table("pedidos_produccion").update(update_fin).eq("id", p['id']).execute()
                    registrar_movimiento(st.session_state.user, "Producto Terminado", f"Se finalizó el lote de {p['producto']}")
                    st.success("¡Producción finalizada con éxito!")
                    st.rerun()
                else:
                    st.warning("No hay producciones en curso para finalizar.")

        st.divider()
        st.subheader("📋 Órdenes Registradas")
        try:
            todos_pedidos = supabase.table("pedidos_produccion").select("*").execute().data
            if todos_pedidos:
                st.dataframe(pd.DataFrame(todos_pedidos), use_container_width=True)
            else:
                st.info("No hay pedidos cargados.")
        except Exception as e:
            st.error(f"Error al cargar pedidos: {e}")

    # ==========================================
    # 2. PESTAÑA MATERIAS PRIMAS
    # ==========================================
    with tab_mp:
        st.header("Gestión de Materias Primas")
        with st.expander("➕ Cargar Nueva Materia Prima", expanded=True):
            with st.form("form_mp"):
                col1, col2 = st.columns(2)
                with col1:
                    nombre_mp = st.text_input("Nombre de la Materia Prima")
                    categoria_mp = st.selectbox("Tipo de Elemento", ["Herraje (Unidades)", "Cinta (Longitud en cm)"])
                with col2:
                    valor_medida = st.number_input("Cantidad o Longitud inicial", min_value=0.0, step=1.0)
                    minimo_alerta = st.number_input("Stock Mínimo para Alerta", min_value=0.0, step=1.0)
                
                if st.form_submit_button("Guardar Materia Prima"):
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
        else:
            st.info("No hay materias primas registradas.")

    # ==========================================
    # 3. PESTAÑA PRODUCTOS Y STOCK
    # ==========================================
    with tab_stock:
        st.header("Gestión de Productos y Recetas")
        col_receta, col_lista = st.columns(2)
        
        with col_receta:
            st.subheader("1. Armar Receta (Múltiples Ingredientes)")
            nombres_mp = [m['nombre'] for m in lista_mp] if lista_mp else ["Sin materias primas"]
            
            sel_mp = st.selectbox("Seleccionar Materia Prima", nombres_mp)
            cant_mp = st.number_input("Cantidad que usa 1 unidad de producto", min_value=0.1, value=1.0)
            
            if st.button("➕ Agregar ingrediente a la receta"):
                if sel_mp != "Sin materias primas":
                    st.session_state.receta_temp.append({"material": sel_mp, "cantidad": cant_mp})
                    st.success(f"Agregado: {cant_mp} de {sel_mp}")
                    st.rerun()
                    
            if st.session_state.receta_temp:
                st.write("**Ingredientes cargados para este producto:**")
                st.json(st.session_state.receta_temp)
                if st.button("🗑️ Limpiar receta temporal"):
                    st.session_state.receta_temp = []
                    st.rerun()

        with col_lista:
            st.subheader("2. Guardar Producto Nuevo")
            nombre_nuevo_prod = st.text_input("Nombre del Producto Final")
            stock_ini_prod = st.number_input("Stock inicial", min_value=0, value=0)
            minimo_prod = st.number_input("Stock Mínimo para Alertas", min_value=0, value=0)
            
            if st.button("Guardar Producto Completo", use_container_width=True):
                if nombre_nuevo_prod:
                    nuevo_prod = {
                        "nombre": nombre_nuevo_prod,
                        "cantidad": stock_ini_prod,
                        "minimo": minimo_prod,
                        "receta": st.session_state.receta_temp 
                    }
                    supabase.table("productos").insert(nuevo_prod).execute()
                    registrar_movimiento(st.session_state.user, "Creó Producto", f"Nuevo producto: {nombre_nuevo_prod} con receta.")
                    st.session_state.receta_temp = [] 
                    st.success("¡Producto y receta guardados con éxito!")
                    st.rerun()
                    
        st.divider()
        st.subheader("Inventario Actual de Productos")
        if lista_productos:
            st.dataframe(pd.DataFrame(lista_productos), use_container_width=True)
        else:
            st.info("No hay productos cargados.")

    # ==========================================
    # 4. PESTAÑA VENTAS
    # ==========================================
    with tab_ventas:
        st.header("Registro de Salidas y Ventas")
        try:
            ventas = supabase.table("ventas_historial").select("*").execute().data
            if ventas:
                st.dataframe(pd.DataFrame(ventas), use_container_width=True)
            else:
                st.info("No hay ventas registradas.")
        except Exception as e:
            st.error(f"Error al cargar ventas: {e}")

    # ==========================================
    # 5. PESTAÑA REGISTROS
    # ==========================================
    with tab_registros:
        st.header("📜 Auditoría y Registro General de Movimientos")
        try:
            regs = supabase.table("registros").select("*").order("fecha_hora", desc=True).execute().data
            if regs:
                df_regs = pd.DataFrame(regs)
                st.dataframe(df_regs, use_container_width=True)
                st.download_button(
                    label="📥 Descargar Historial Completo (CSV)",
                    data=df_regs.to_csv(index=False).encode('utf-8'),
                    file_name='historial_auditoria_taira.csv',
                    mime='text/csv',
                )
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
