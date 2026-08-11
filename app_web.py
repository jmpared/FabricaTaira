import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import json

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.set_page_config(page_title="FÁBRICA TAIRA", page_icon="📦", layout="wide")

# --- CONTROL DE SESIÓN Y OPERARIO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_actual = ""

# --- BARRA LATERAL ---
with st.sidebar:
    if st.session_state.autenticado:
        st.write("🏭 **Fábrica Taira**")
        st.success(f"👷 Operario activo:\n**{st.session_state.usuario_actual}**")
        st.divider()
        if st.button("Cerrar Sesión", width="stretch"):
            supabase.auth.sign_out()
            st.session_state.autenticado = False
            st.session_state.usuario_actual = ""
            st.rerun()

# --- PANTALLA DE LOGIN ---
if not st.session_state.autenticado:
    st.title("FÁBRICA TAIRA")
    st.subheader("Acceso Seguro al Sistema")
    
    usuario_input = st.text_input("Correo electrónico")
    clave_input = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar", width="stretch"):
        if usuario_input and clave_input:
            try:
                auth_res = supabase.auth.sign_in_with_password({"email": usuario_input, "password": clave_input})
                st.session_state.autenticado = True
                nombre = usuario_input.split('@')[0].capitalize()
                st.session_state.usuario_actual = nombre
                st.rerun()
            except Exception as e:
                st.error("Usuario o contraseña incorrectos.")
        else:
            st.error("Por favor, completa ambos campos.")

# --- APLICACIÓN PRINCIPAL ---
else:
    st.title("📦 FÁBRICA TAIRA - Gestión de Stock y Producción Integrada")
    
    tab_tablero, tab_mp, tab_prod, tab_ventas, tab_alertas, tab_masiva, tab_stats = st.tabs(
        ["Producción", "M. Primas", "Productos y Recetas", "Salidas", "Alertas", "Carga Masiva", "📊 Estadísticas"]
    )

    # ==========================================
    # PESTAÑA 1: TABLERO DE PRODUCCIÓN INTEGRADO
    # ==========================================
    with tab_tablero:
        st.header("📋 Tablero de Producción y Registro")
        
        with st.expander("➕ Cargar nueva tarea de producción", expanded=False):
            try:
                res_prods_tablero = supabase.table("productos").select("nombre, receta").execute()
                opciones_tablero = [p["nombre"] for p in res_prods_tablero.data] if res_prods_tablero.data else []
                
                with st.form("form_nueva_tarea", clear_on_submit=True):
                    prod_tarea = st.selectbox("Seleccionar Producto a fabricar", opciones_tablero if opciones_tablero else ["Carga un producto primero"])
                    cant_tarea = st.number_input("Cantidad a fabricar", min_value=1.0, step=1.0)
                    if st.form_submit_button("Crear Tarea"):
                        if opciones_tablero:
                            ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                            nueva_tarea = {
                                "producto": prod_tarea,
                                "cantidad": cant_tarea,
                                "estado": "Pendiente",
                                "creado_por": st.session_state.usuario_actual,
                                "fecha_creacion": ahora
                            }
                            supabase.table("pedidos_produccion").insert(nueva_tarea).execute()
                            st.success("Tarea agregada al tablero.")
                            st.rerun()
                        else:
                            st.error("No hay productos disponibles.")
            except Exception as e:
                st.error(f"Error al cargar productos: {e}")

        st.write("---")
        col_pend, col_prod, col_fin = st.columns(3)
        
        try:
            # Traemos todas las tareas que NO estén archivadas
            tareas = supabase.table("pedidos_produccion").select("*").neq("estado", "Archivado").execute().data or []
            
            with col_pend:
                st.subheader("🔴 Pendientes")
                for t in tareas:
                    if t.get('estado') == 'Pendiente':
                        with st.container(border=True):
                            st.write(f"**{t.get('producto')}** (x{t.get('cantidad')})")
                            st.caption(f"📝 Solicitado por: {t.get('creado_por', 'N/A')} ({t.get('fecha_creacion', '')})")
                            
                            if st.button(f"🚀 Iniciar Producción", key=f"ini_{t['id']}", width="stretch"):
                                ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                                supabase.table("pedidos_produccion").update({
                                    "estado": "En Producción",
                                    "producido_por": st.session_state.usuario_actual,
                                    "fecha_produccion": ahora
                                }).eq("id", t['id']).execute()
                                st.rerun()

            with col_prod:
                st.subheader("🟡 En Producción")
                for t in tareas:
                    if t.get('estado') == 'En Producción':
                        with st.container(border=True):
                            st.write(f"**{t.get('producto')}** (x{t.get('cantidad')})")
                            st.caption(f"⚙️ Fabricando: {t.get('producido_por', 'N/A')} desde {t.get('fecha_produccion', '')}")
                            
                            if st.button(f"✅ Finalizar (Integrar Stock)", key=f"fin_{t['id']}", width="stretch"):
                                prod_nombre = t.get('producto')
                                cant_producida = float(t.get('cantidad', 0))
                                
                                prod_info = supabase.table("productos").select("*").eq("nombre", prod_nombre).execute().data
                                
                                if prod_info:
                                    receta_json = prod_info[0].get("receta", "[]")
                                    try:
                                        receta = json.loads(receta_json) if isinstance(receta_json, str) else receta_json
                                    except:
                                        receta = []
                                    
                                    if not receta:
                                        st.error(f"⚠️ El producto '{prod_nombre}' no tiene una receta cargada. Ve a la pestaña 'Productos y Recetas' y asocia los insumos.")
                                    else:
                                        receta_valida = True
                                        for ing in receta:
                                            mp_nombre = ing.get("materia_prima")
                                            cant_necesaria = float(ing.get("cantidad", 0)) * cant_producida
                                            
                                            mp_data = supabase.table("materias_primas").select("*").eq("nombre", mp_nombre).execute().data
                                            if mp_data:
                                                mp_actual = mp_data[0]
                                                tipo_medida = mp_actual.get("tipo", "")
                                                campo_stock = "longitud" if "Longitud" in tipo_medida else "cantidad"
                                                stock_disponible = float(mp_actual.get(campo_stock, 0))
                                                
                                                if stock_disponible < cant_necesaria:
                                                    st.error(f"⚠️ Stock insuficiente de '{mp_nombre}'. Necesitas {cant_necesaria} y hay {stock_disponible}.")
                                                    receta_valida = False
                                                    break
                                            else:
                                                st.error(f"⚠️ La materia prima '{mp_nombre}' de la receta ya no existe en el inventario.")
                                                receta_valida = False
                                                break
                                        
                                        if receta_valida:
                                            for ing in receta:
                                                mp_nombre = ing.get("materia_prima")
                                                cant_necesaria = float(ing.get("cantidad", 0)) * cant_producida
                                                mp_data = supabase.table("materias_primas").select("*").eq("nombre", mp_nombre).execute().data
                                                mp_actual = mp_data[0]
                                                tipo_medida = mp_actual.get("tipo", "")
                                                campo_stock = "longitud" if "Longitud" in tipo_medida else "cantidad"
                                                nuevo_stock_mp = float(mp_actual.get(campo_stock, 0)) - cant_necesaria
                                                
                                                supabase.table("materias_primas").update({campo_stock: nuevo_stock_mp}).eq("nombre", mp_nombre).execute()

                                            stock_prod_actual = float(prod_info[0].get("cantidad", 0))
                                            nuevo_stock_prod = stock_prod_actual + cant_producida
                                            supabase.table("productos").update({"cantidad": nuevo_stock_prod}).eq("nombre", prod_nombre).execute()

                                            ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                                            supabase.table("pedidos_produccion").update({
                                                "estado": "Finalizado",
                                                "fecha_finalizacion": ahora
                                            }).eq("id", t['id']).execute()
                                            
                                            st.success(f"¡Producción finalizada! Se sumaron {cant_producida} al stock de productos y se descontaron los insumos.")
                                            st.rerun()

            with col_fin:
                st.subheader("🟢 Finalizados")
                for t in tareas:
                    if t.get('estado') == 'Finalizado':
                        with st.container(border=True):
                            st.write(f"**{t.get('producto')}** (x{t.get('cantidad')})")
                            st.caption(f"Terminado el: {t.get('fecha_finalizacion', '')}")
                            # EN LUGAR DE BORRAR, CAMBIAMOS EL ESTADO A 'Archivado' PARA QUE QUEDE EN LA BASE DE DATOS
                            if st.button(f"📥 Archivar al Historial", key=f"arch_{t['id']}", width="stretch"):
                                supabase.table("pedidos_produccion").update({"estado": "Archivado"}).eq("id", t['id']).execute()
                                st.success("Tarea enviada al historial permanente.")
                                st.rerun()

        except Exception as e:
            st.error(f"Error al cargar el tablero: {e}")

        st.divider()
        st.subheader("📁 Registro Histórico Permanente de Producción")
        try:
            # Mostramos TODO el historial (incluyendo los archivados y finalizados)
            tareas_reg = supabase.table("pedidos_produccion").select("*").execute().data or []
            if tareas_reg:
                df_tareas = pd.DataFrame(tareas_reg)
                st.dataframe(df_tareas, width="stretch")
                
                csv_tareas = df_tareas.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar Registro Histórico Completo en CSV",
                    data=csv_tareas,
                    file_name="historial_produccion_taira.csv",
                    mime="text/csv",
                )
            else:
                st.info("No hay registros de producción todavía.")
        except Exception as e:
            st.error(f"Error al mostrar registros: {e}")

    # ==========================================
    # PESTAÑA 2: MATERIA PRIMA (CON DESCARGA)
    # ==========================================
    with tab_mp:
        st.header("Ingreso de Materia Prima")
        with st.form("form_mp", clear_on_submit=True):
            nombre = st.text_input("Nombre de la materia prima")
            categoria = st.selectbox("Categoría", ["Cinta", "Herrajes", "Hilo", "General"])
            tipo = st.selectbox("Tipo de Medida", ["Longitud (cm)", "Unidades"])
            cantidad = st.number_input("Cantidad / Longitud", min_value=0.0, step=1.0)
            minimo = st.number_input("Stock Mínimo para Alerta", min_value=0.0, step=1.0)
            
            submit_mp = st.form_submit_button("Guardar Materia Prima")
            if submit_mp:
                if nombre and cantidad > 0:
                    nuevo_item = {
                        "nombre": nombre,
                        "categoria": categoria,
                        "tipo": tipo,
                        "longitud": cantidad if "Longitud" in tipo else 0.0,
                        "cantidad": cantidad if "Longitud" not in tipo else 0.0,
                        "minimo": minimo,
                        "fecha": datetime.now().strftime("%d/%m/%Y")
                    }
                    try:
                        supabase.table("materias_primas").insert(nuevo_item).execute()
                        st.success("Materia prima guardada.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.subheader("Stock Registrado de Materias Primas")
        try:
            res = supabase.table("materias_primas").select("*").execute()
            if res.data:
                df_mp = pd.DataFrame(res.data)
                st.dataframe(df_mp, width="stretch")
                
                csv_mp = df_mp.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar Inventario de Materias Primas",
                    data=csv_mp,
                    file_name="materias_primas_taira.csv",
                    mime="text/csv",
                )
                
                st.divider()
                st.write("🗑️ **Eliminar un registro incorrecto**")
                nombres_mp = [item['nombre'] for item in res.data]
                mp_a_eliminar = st.selectbox("Selecciona la Materia Prima a eliminar:", nombres_mp)
                confirmar_mp = st.checkbox(f"⚠️ Estoy seguro de que deseo eliminar '{mp_a_eliminar}'")
                
                if st.button("Eliminar Materia Prima", disabled=not confirmar_mp):
                    supabase.table("materias_primas").delete().eq("nombre", mp_a_eliminar).execute()
                    st.success("Registro eliminado.")
                    st.rerun()
            else:
                st.info("No hay registros cargados aún.")
        except Exception as e:
            st.error(f"Error: {e}")

    # ==========================================
    # PESTAÑA 3: PRODUCTOS Y RECETAS (ILIMITADO + EDICIÓN Y BORRADO)
    # ==========================================
    with tab_prod:
        st.header("Gestión de Productos y Recetas Ilimitadas")
        
        try:
            mp_res = supabase.table("materias_primas").select("nombre").execute()
            lista_mps = [m["nombre"] for m in mp_res.data] if mp_res.data else []
        except:
            lista_mps = []

        if "num_insumos" not in st.session_state:
            st.session_state.num_insumos = 2

        with st.form("form_prod_receta_dinamica"):
            nombre_p = st.text_input("Nombre del Producto")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                cant_p = st.number_input("Cantidad Inicial en Stock", min_value=0.0)
            with col_c2:
                min_p = st.number_input("Stock Mínimo", min_value=0.0)
                
            foto_p = st.file_uploader("Subir foto del producto (Opcional)", type=["jpg", "png", "jpeg"])
            
            st.write("---")
            st.subheader("📋 Configuración de Insumos (Receta Ilimitada)")
            st.info("Añade todos los insumos que necesites utilizando el botón correspondiente.")

            insumos_configurados = []
            for i in range(st.session_state.num_insumos):
                c_ins, c_cant = st.columns([2, 1])
                with c_ins:
                    ins_nombre = st.selectbox(f"Materia Prima #{i+1}", ["-- Seleccionar --"] + lista_mps, key=f"crear_ins_{i}")
                with c_cant:
                    ins_cant = st.number_input(f"Cantidad #{i+1}", min_value=0.0, step=0.1, key=f"crear_cant_{i}")
                
                if ins_nombre != "-- Seleccionar --" and ins_cant > 0:
                    insumos_configurados.append({"materia_prima": ins_nombre, "cantidad": ins_cant})

            submit_p = st.form_submit_button("Guardar Producto y Receta Nueva")
            
            if submit_p and nombre_p:
                url_foto = ""
                try:
                    if foto_p is not None:
                        extension = foto_p.name.split('.')[-1]
                        nombre_archivo = f"{int(datetime.now().timestamp())}.{extension}"
                        supabase.storage.from_("productos_fotos").upload(nombre_archivo, foto_p.getvalue())
                        url_foto = supabase.storage.from_("productos_fotos").get_public_url(nombre_archivo)

                    producto_nuevo = {
                        "nombre": nombre_p,
                        "cantidad": cant_p,
                        "minimo": min_p,
                        "receta": json.dumps(insumos_configurados)
                    }
                    if url_foto:
                        producto_nuevo["foto_url"] = url_foto

                    supabase.table("productos").insert(producto_nuevo).execute()
                    st.success("¡Producto y receta registrados exitosamente!")
                    st.session_state.num_insumos = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar el producto: {e}")

        if st.button("➕ Añadir otro insumo a la lista"):
            st.session_state.num_insumos += 1
            st.rerun()

        st.divider()
        st.subheader("📁 Registro Completo, Edición y Eliminación de Productos")
        
        try:
            res_p = supabase.table("productos").select("*").execute()
            if res_p.data:
                df_productos = pd.DataFrame(res_p.data)
                st.dataframe(df_productos[['nombre', 'cantidad', 'minimo', 'receta']], width="stretch")
                
                csv_prod = df_productos.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar Registro de Productos y Recetas",
                    data=csv_prod,
                    file_name="productos_recetas_taira.csv",
                    mime="text/csv",
                )

                st.write("---")
                st.subheader("✏️ Editar o Eliminar un Producto Específico")
                nombres_productos = [p["nombre"] for p in res_p.data]
                prod_seleccionado = st.selectbox("Selecciona el producto a gestionar:", nombres_productos)
                
                datos_actuales = [p for p in res_p.data if p["nombre"] == prod_seleccionado][0]
                
                with st.form(f"form_editar_{prod_seleccionado}"):
                    st.write(f"Editando producto: **{prod_seleccionado}**")
                    nuevo_stock = st.number_input("Modificar Stock Actual", value=float(datos_actuales.get("cantidad", 0)), min_value=0.0)
                    nuevo_minimo = st.number_input("Modificar Stock Mínimo", value=float(datos_actuales.get("minimo", 0)), min_value=0.0)
                    
                    st.info("Puedes reescribir o actualizar la receta actual de este producto en formato JSON o agregar una nueva.")
                    receta_actual_txt = datos_actuales.get("receta", "[]")
                    nueva_receta_input = st.text_area("Receta (Estructura de insumos)", value=receta_actual_txt)
                    
                    confirmar_edicion = st.checkbox("Estoy seguro de actualizar este producto")
                    submit_edicion = st.form_submit_button("Guardar Cambios de Edición", disabled=not confirmar_edicion)
                    
                    if submit_edicion:
                        try:
                            supabase.table("productos").update({
                                "cantidad": nuevo_stock,
                                "minimo": nuevo_minimo,
                                "receta": nueva_receta_input
                            }).eq("nombre", prod_seleccionado).execute()
                            st.success("¡Producto y receta actualizados correctamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar: {e}")

                st.write("---")
                st.write("🗑️ **Eliminar definitivamente un producto obsoleto**")
                confirmar_borrado = st.checkbox(f"⚠️ Confirmo que deseo ELIMINAR por completo '{prod_seleccionado}' de la base de datos")
                if st.button("Eliminar Producto Seleccionado", disabled=not confirmar_borrado):
                    supabase.table("productos").delete().eq("nombre", prod_seleccionado).execute()
                    st.success("Producto eliminado exitosamente.")
                    st.rerun()

            else:
                st.info("No hay productos cargados aún.")
        except Exception as e:
            st.error(f"Error al cargar productos: {e}")

    # ==========================================
    # PESTAÑA 4: SALIDAS / VENTAS
    # ==========================================
    with tab_ventas:
        st.header("Registrar Salida / Venta")
        try:
            res_prods = supabase.table("productos").select("nombre").execute()
            opciones_prods = [p["nombre"] for p in res_prods.data] if res_prods.data else []
            
            if opciones_prods:
                prod_sel = st.selectbox("Seleccionar Producto", opciones_prods)
                cant_salida = st.number_input("Cantidad a Salir", min_value=1.0)
                if st.button("Confirmar Salida"):
                    venta = {
                        "fecha": datetime.now().strftime("%d/%m/%Y"),
                        "producto": prod_sel,
                        "cantidad": cant_salida
                    }
                    supabase.table("ventas_historial").insert(venta).execute()
                    
                    stock_actual = supabase.table("productos").select("cantidad").eq("nombre", prod_sel).execute().data[0]["cantidad"]
                    nuevo_stock = max(0, stock_actual - cant_salida)
                    supabase.table("productos").update({"cantidad": nuevo_stock}).eq("nombre", prod_sel).execute()
                    
                    st.success(f"Salida registrada y stock descontado. Quedan {nuevo_stock} unidades.")
                    st.rerun()
            else:
                st.info("Carga productos antes de registrar salidas.")
        except Exception as e:
            st.error(f"Error: {e}")

    # ==========================================
    # PESTAÑA 5: ALERTAS
    # ==========================================
    with tab_alertas:
        st.header("Panel de Alertas de Stock")
        try:
            mp_data = supabase.table("materias_primas").select("*").execute().data or []
            prod_data = supabase.table("productos").select("*").execute().data or []
            
            alertas = []
            for item in mp_data:
                cant = item.get("longitud", 0) if "Longitud" in item.get("tipo", "") else item.get("cantidad", 0)
                if cant <= item.get("minimo", 0):
                    alertas.append(f"⚠️ Bajo stock MP: **{item.get('nombre')}** (Quedan: {cant})")
            
            for item in prod_data:
                if item.get("cantidad", 0) <= item.get("minimo", 0):
                    alertas.append(f"⚠️ Bajo stock Producto: **{item.get('nombre')}** (Quedan: {item.get('cantidad')})")

            if alertas:
                for a in alertas:
                    st.warning(a)
            else:
                st.success("✓ Todo el stock está en niveles óptimos.")
        except Exception as e:
            st.error(f"Error: {e}")

    # ==========================================
    # PESTAÑA 6: CARGA MASIVA
    # ==========================================
    with tab_masiva:
        st.header("Carga Masiva de Stock")
        st.write("Pega aquí la lista en formato texto separado por comas (CSV).")
        destino = st.radio("¿Dónde vas a cargar estos datos?", ["Productos", "Materias Primas"])
        st.info("El formato debe ser exacto por línea: **Nombre, Cantidad, Minimo**")
        data_input = st.text_area("Pega tu lista aquí:", height=200, placeholder="Ejemplo:\nCinta Negra, 50, 5\nHerraje Tipo A, 20, 5")
        
        if st.button("Procesar Lista", width="stretch"):
            if data_input:
                lineas = data_input.strip().split('\n')
                errores = 0
                exitos = 0
                for linea in lineas:
                    if not linea.strip():
                        continue
                    partes = linea.split(',')
                    if len(partes) >= 3:
                        try:
                            nombre_item = partes[0].strip()
                            cantidad_item = float(partes[1].strip())
                            minimo_item = float(partes[2].strip())
                            if destino == "Productos":
                                supabase.table("productos").insert({
                                    "nombre": nombre_item,
                                    "cantidad": cantidad_item,
                                    "minimo": minimo_item,
                                    "receta": "[]"
                                }).execute()
                            else:
                                supabase.table("materias_primas").insert({
                                    "nombre": nombre_item,
                                    "categoria": "General", 
                                    "tipo": "Unidades",
                                    "cantidad": cantidad_item,
                                    "longitud": 0.0,
                                    "minimo": minimo_item,
                                    "fecha": datetime.now().strftime("%d/%m/%Y")
                                }).execute()
                            exitos += 1
                        except Exception:
                            errores += 1
                    else:
                        errores += 1
                if errores == 0:
                    st.success(f"¡Se cargaron {exitos} registros con éxito!")
                else:
                    st.warning(f"Se cargaron {exitos} registros, pero hubo errores en {errores} líneas.")
            else:
                st.error("El cuadro de texto está vacío.")

    # ==========================================
    # PESTAÑA 7: ESTADÍSTICAS
    # ==========================================
    with tab_stats:
        st.header("📊 Análisis de Datos y Rendimiento")
        
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.subheader("🏆 Productos Más Vendidos / Salidas")
            try:
                ventas_data = supabase.table("ventas_historial").select("*").execute().data
                if ventas_data:
                    df_ventas = pd.DataFrame(ventas_data)
                    if not df_ventas.empty and "producto" in df_ventas.columns and "cantidad" in df_ventas.columns:
                        ventas_agrupadas = df_ventas.groupby("producto")["cantidad"].sum().reset_index()
                        ventas_agrupadas = ventas_agrupadas.sort_values(by="cantidad", ascending=False)
                        st.bar_chart(ventas_agrupadas, x="producto", y="cantidad", color="#2ecc71")
                    else:
                        st.info("Datos de ventas insuficientes.")
                else:
                    st.info("No hay suficientes datos de ventas para el gráfico.")
            except Exception as e:
                st.error(f"Error al cargar gráficas: {e}")

        with col_graf2:
            st.subheader("🏭 Productos Más Fabricados")
            try:
                tareas_data = supabase.table("pedidos_produccion").select("*").eq("estado", "Finalizado").execute().data
                if tareas_data:
                    df_tareas = pd.DataFrame(tareas_data)
                    if not df_tareas.empty and "producto" in df_tareas.columns and "cantidad" in df_tareas.columns:
                        prod_agrupada = df_tareas.groupby("producto")["cantidad"].sum().reset_index()
                        prod_agrupada = prod_agrupada.sort_values(by="cantidad", ascending=False)
                        st.bar_chart(prod_agrupada, x="producto", y="cantidad", color="#3498db")
                    else:
                        st.info("Datos de producción insuficientes.")
                else:
                    st.info("No hay suficientes datos de producción finalizada.")
            except Exception as e:
                st.error(f"Error al cargar gráficas: {e}")