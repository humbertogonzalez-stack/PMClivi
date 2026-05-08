import streamlit as st
import pandas as pd
from datetime import date
import uuid
from supabase import create_client, Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Clivi 2.1: Comando de Crecimiento", layout="wide", initial_sidebar_state="collapsed")

# --- CARGA DE SECRETOS ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    EMAIL_USUARIO = st.secrets["EMAIL_USUARIO"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
except Exception as e:
    st.error("Faltan configurar los Secrets en Streamlit Cloud.")
    st.stop()

# --- VARIABLES DE ESTADO ---
if 'show_add_form' not in st.session_state: st.session_state.show_add_form = False
if 'editing_task_id' not in st.session_state: st.session_state.editing_task_id = None
if 'view' not in st.session_state: st.session_state.view = "tablero"

# --- CONEXIÓN ---
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- LISTA DE EQUIPO ---
EQUIPO_CLIVI = [
    "Seleccionar...",
    "humberto.gonzalez@clivi.com.mx",
    "betiana.correa@clivi.com.mx",
    "carolina.rodriguez@clivi.com.mx",
    "Otro (Escribir...)"
]

# --- LÓGICA DE ALMACENAMIENTO (IMÁGENES) ---
def upload_image(file):
    file_name = f"{uuid.uuid4()}_{file.name}"
    supabase.storage.from_("evidencia-marketing").upload(file_name, file.getvalue())
    return supabase.storage.from_("evidencia-marketing").get_public_url(file_name)

# --- LÓGICA DE ENVÍO SMTP ---
def enviar_notificacion(destinatario, tarea_titulo, autor_nombre):
    msg = MIMEMultipart()
    msg['From'] = f"Centro de Mando Clivi <{EMAIL_USUARIO}>"
    msg['To'] = destinatario
    msg['Subject'] = f"🚀 Nueva tarea: {tarea_titulo}"

    cuerpo = f"""
    <html>
        <body style="font-family: sans-serif;">
            <h2 style="color: #2ECC71;">¡Hola!</h2>
            <p><strong>{autor_nombre}</strong> te ha asignado una nueva tarea en el tablero de Marketing.</p>
            <hr>
            <p><b>Tarea:</b> {tarea_titulo}</p>
            <p>Entra al tablero para ver los detalles, la descripción y la fecha límite.</p>
            <br>
            <p><small>Enviado automáticamente desde Clivi Growth Modeling System.</small></p>
        </body>
    </html>
    """
    msg.attach(MIMEText(cuerpo, 'html'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USUARIO, destinatario, msg.as_string())
        server.quit()
        return True
    except:
        return False

# --- CSS MODERNO CLIVI 2.1 ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0e1117; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: 600; font-size: 16px; color: #afb3b8; }
    .stTabs [aria-selected="true"] { color: #2ecc71; border-bottom-color: #2ecc71; }
    
    /* Tarjetas Kanban */
    .task-card { background-color: #1a1c23; padding: 20px; border-radius: 12px; border: 1px solid #2d2f39; margin-bottom: 15px; border-left: 5px solid transparent; transition: 0.3s; }
    .task-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .task-title { color: #ffffff; font-size: 15px; font-weight: 700; margin-bottom: 8px; }
    .task-meta { font-size: 12px; color: #8b949e; display: flex; justify-content: space-between; align-items: center; margin-top: 10px; }
    .area-tag { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; color: white; }
    .priority-badge { font-size: 9px; font-weight: bold; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; }
    .img-preview { width: 100%; height: 140px; object-fit: cover; border-radius: 6px; margin: 10px 0; border: 1px solid #30363d; }
    
    /* Colores Áreas */
    .st-paid { border-left-color: #FF4B4B; } .st-paid .area-tag { background-color: #FF4B4B; }
    .st-organic { border-left-color: #2ECC71; } .st-organic .area-tag { background-color: #2ECC71; }
    .st-motion { border-left-color: #9B59B6; } .st-motion .area-tag { background-color: #9B59B6; }
    .st-design { border-left-color: #3498DB; } .st-design .area-tag { background-color: #3498DB; }

    /* Estética Post-it */
    .postit-container { display: flex; flex-wrap: wrap; gap: 20px; justify-content: flex-start; padding-top: 10px;}
    .postit { 
        width: 240px; height: 240px; padding: 25px; border-radius: 2px;
        box-shadow: 4px 4px 15px rgba(0,0,0,0.25); position: relative;
        transform: rotate(-1.5deg); transition: 0.2s; color: #1a1a1a;
        font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif; font-size: 15px;
        overflow-y: auto; display: flex; flex-direction: column; justify-content: space-between;
    }
    .postit:nth-child(even) { transform: rotate(2deg); }
    .postit:nth-child(3n) { transform: rotate(-1deg); }
    .postit:hover { transform: scale(1.05) rotate(0deg); z-index: 10; box-shadow: 8px 8px 20px rgba(0,0,0,0.4); }
    .postit-meta { font-size: 11px; font-weight: bold; border-top: 1px solid rgba(0,0,0,0.1); padding-top: 8px; text-align: right; opacity: 0.7; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
c_head1, c_head2, c_head3 = st.columns([1, 7, 2])
with c_head2:
    try: st.image("logo_clivi.png", width=120)
    except: pass
    st.title("Centro de Operaciones Growth")
with c_head3:
    if st.button("🏠 Inicio", use_container_width=True): st.session_state.view = "tablero"; st.rerun()
    if st.button("🗑️ Ver Papelera", use_container_width=True): st.session_state.view = "papelera"; st.rerun()

st.markdown("---")

# ==========================================
# VISTA: PAPELERA UNIFICADA
# ==========================================
if st.session_state.view == "papelera":
    st.header("🗑️ Papelera de Reciclaje")
    tab_ptareas, tab_pcuads = st.tabs(["Tareas Eliminadas", "Cuadernos Eliminados"])
    
    with tab_ptareas:
        res = supabase.table("clivi_tareas_marketing").select("*").eq("eliminada", True).execute()
        df_trash = pd.DataFrame(res.data)
        if df_trash.empty: st.info("No hay tareas en la papelera.")
        else:
            for _, t in df_trash.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([6, 2, 2])
                    c1.write(f"📌 **{t['titulo']}**")
                    if c2.button("🔄 Restaurar", key=f"rt_{t['id']}"):
                        supabase.table("clivi_tareas_marketing").update({"eliminada": False}).eq("id", t['id']).execute()
                        st.cache_data.clear(); st.rerun()
                    if c3.button("❌ Borrar Definitivo", key=f"dt_{t['id']}"):
                        supabase.table("clivi_tareas_marketing").delete().eq("id", t['id']).execute()
                        st.cache_data.clear(); st.rerun()
                        
    with tab_pcuads:
        res_c = supabase.table("clivi_cuadernos").select("*").eq("eliminada", True).execute()
        df_trash_c = pd.DataFrame(res_c.data)
        if df_trash_c.empty: st.info("No hay cuadernos en la papelera.")
        else:
            for _, t in df_trash_c.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([6, 2, 2])
                    c1.write(f"📖 **{t['titulo']}**")
                    if c2.button("🔄 Restaurar", key=f"rc_{t['id']}"):
                        supabase.table("clivi_cuadernos").update({"eliminada": False}).eq("id", t['id']).execute()
                        st.cache_data.clear(); st.rerun()
                    if c3.button("❌ Borrar Definitivo", key=f"dc_{t['id']}"):
                        supabase.table("clivi_cuadernos").delete().eq("id", t['id']).execute()
                        st.cache_data.clear(); st.rerun()
    st.stop()

# ==========================================
# NAVEGACIÓN PRINCIPAL
# ==========================================
tab_kanban, tab_cuadernos, tab_muro = st.tabs(["🚀 Tablero de Operaciones", "📒 Cuadernos de Conocimiento", "💡 Muro de Ideas"])

# ------------------------------------------
# PESTAÑA 1: TABLERO KANBAN
# ------------------------------------------
with tab_kanban:
    res = supabase.table("clivi_tareas_marketing").select("*").eq("eliminada", False).execute()
    df = pd.DataFrame(res.data)

    c_act1, c_act2, c_act3 = st.columns([2, 2, 6])
    with c_act1:
        if st.button("+ Nueva Tarea", type="primary", use_container_width=True): st.session_state.show_add_form = True
    with c_act2:
        filtro = st.selectbox("Área", ['Todas', 'Pagado', 'Orgánico', 'Motion', 'Diseño'], label_visibility="collapsed")
    with c_act3:
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📊 Reporte", data=csv, file_name=f"clivi_{date.today()}.csv")

    # --- FORMULARIO NUEVA TAREA ---
    if st.session_state.show_add_form:
        with st.expander("📝 Nueva Tarea", expanded=True):
            with st.form("new_task"):
                f1, f2 = st.columns(2)
                with f1:
                    nt_t = st.text_input("Título*")
                    nt_a = st.selectbox("Área*", ['Pagado', 'Orgánico', 'Motion', 'Diseño'])
                    nt_p = st.selectbox("Prioridad", ['Baja', 'Media', 'Alta', 'Urgente'], index=1)
                    nt_aut = st.text_input("Tu Nombre (Autor)*")
                with f2:
                    nt_as_select = st.selectbox("Asignar a", EQUIPO_CLIVI)
                    nt_as_custom = st.text_input("Nombre/Correo") if nt_as_select == "Otro (Escribir...)" else ""
                    nt_as = nt_as_custom if nt_as_select == "Otro (Escribir...)" else nt_as_select
                    nt_dl = st.date_input("Límite")
                    nt_evidencia = st.file_uploader("Evidencia Visual (Opcional)", type=['png', 'jpg', 'jpeg'])
                
                nt_desc = st.text_area("Descripción")
                
                if st.form_submit_button("Crear Tarea"):
                    if nt_t and nt_aut and nt_as != "Seleccionar...":
                        img_url = None
                        if nt_evidencia:
                            img_url = upload_image(nt_evidencia)

                        supabase.table("clivi_tareas_marketing").insert({
                            "id": str(uuid.uuid4()), "titulo": nt_t, "area": nt_a, "estado": "Backlog",
                            "prioridad": nt_p, "asignado_a": nt_as, "autor": nt_aut, 
                            "fecha_limite": str(nt_dl), "descripcion": nt_desc, "eliminada": False,
                            "imagen_url": img_url
                        }).execute()
                        if "@" in nt_as: enviar_notificacion(nt_as, nt_t, nt_aut)
                        st.session_state.show_add_form = False; st.cache_data.clear(); st.rerun()

    # --- EDITOR TAREAS ---
    if st.session_state.editing_task_id and not df.empty:
        task = df[df['id'] == st.session_state.editing_task_id].iloc[0]
        with st.form("edit"):
            st.subheader(f"✏️ Editando: {task['titulo']}")
            e1, e2 = st.columns(2)
            with e1:
                et = st.text_input("Título", value=task['titulo'])
                es = st.selectbox("Estado", ['Backlog', 'Por Hacer', 'En Proceso', 'Terminado'], index=['Backlog', 'Por Hacer', 'En Proceso', 'Terminado'].index(task['estado']))
                ep = st.selectbox("Prioridad", ['Baja', 'Media', 'Alta', 'Urgente'], index=['Baja', 'Media', 'Alta', 'Urgente'].index(task.get('prioridad', 'Media')))
                eas = st.text_input("Asignado", value=task.get('asignado_a', ''))
            with e2:
                if 'imagen_url' in task and pd.notna(task['imagen_url']) and task['imagen_url']:
                    st.image(task['imagen_url'], use_container_width=True, caption="Evidencia actual")
                
                enueva_img = st.file_uploader("Subir/Reemplazar Imagen", type=['png', 'jpg', 'jpeg'])
                ed = st.text_area("Descripción", value=task.get('descripcion', '') if pd.notna(task.get('descripcion')) else "")
                en = st.text_area("Notas", value=task.get('notas', '') if pd.notna(task.get('notas')) else "")
            
            eb1, eb2, eb3 = st.columns([2, 2, 6])
            if eb1.form_submit_button("💾 Guardar"):
                final_img_url = task.get('imagen_url') if pd.notna(task.get('imagen_url')) else None
                if enueva_img: final_img_url = upload_image(enueva_img)
                
                supabase.table("clivi_tareas_marketing").update({
                    "titulo": et, "estado": es, "prioridad": ep, "asignado_a": eas, 
                    "descripcion": ed, "notas": en, "imagen_url": final_img_url
                }).eq("id", task['id']).execute()
                st.session_state.editing_task_id = None; st.cache_data.clear(); st.rerun()
            
            if eb2.form_submit_button("❌ Cancelar"): st.session_state.editing_task_id = None; st.rerun()
            if eb3.form_submit_button("🗑️ Eliminar"):
                supabase.table("clivi_tareas_marketing").update({"eliminada": True}).eq("id", task['id']).execute()
                st.session_state.editing_task_id = None; st.cache_data.clear(); st.rerun()

    # --- TABLERO VISUAL ---
    if not df.empty:
        if filtro != 'Todas': df = df[df['area'] == filtro]
        est = ['Backlog', 'Por Hacer', 'En Proceso', 'Terminado']
        p_cols = {'Baja': '#A0AEC0', 'Media': '#4A5568', 'Alta': '#ED8936', 'Urgente': '#E53E3E'}
        a_css = {'Pagado': 'st-paid', 'Orgánico': 'st-organic', 'Motion': 'st-motion', 'Diseño': 'st-design'}
        cols = st.columns(4)
        
        for i, col_name in enumerate(est):
            with cols[i]:
                st.markdown(f"<h3 style='color: #cbd5e1; font-size: 18px;'>{col_name}</h3>", unsafe_allow_html=True)
                tareas = df[df['estado'] == col_name]
                for _, t in tareas.iterrows():
                    pc = p_cols.get(t.get('prioridad', 'Media'), '#4A5568')
                    img_tag = ""
                    if 'imagen_url' in t and pd.notna(t['imagen_url']) and t['imagen_url']:
                        img_tag = f"<img src='{t['imagen_url']}' class='img-preview'>"
                    
                    st.markdown(f"""
                    <div class="task-card {a_css.get(t.get('area', ''), '')}">
                        <div style="display: flex; justify-content: space-between;">
                            <span class="area-tag">{t.get('area', '')}</span>
                            <span class="priority-badge" style="color: {pc}; border: 1px solid {pc};">{t.get("prioridad", "Media")}</span>
                        </div>
                        {img_tag}
                        <div class="task-title" style="margin-top: 10px;">{t['titulo']}</div>
                        <div class="task-meta">
                            <span>📅 {t.get("fecha_limite", "--")}</span>
                            <b style="color: #2ecc71;">👤 {t.get("asignado_a", "--")}</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    b1, b2, b3 = st.columns([1,1,2])
                    if i > 0 and b1.button("⬅️", key=f"l_{t['id']}"):
                        supabase.table("clivi_tareas_marketing").update({"estado": est[i-1]}).eq("id", t['id']).execute(); st.cache_data.clear(); st.rerun()
                    if i < 3 and b2.button("➡️", key=f"r_{t['id']}"):
                        supabase.table("clivi_tareas_marketing").update({"estado": est[i+1]}).eq("id", t['id']).execute(); st.cache_data.clear(); st.rerun()
                    if i == 3 and b2.button("🗑️", key=f"t_{t['id']}"):
                        supabase.table("clivi_tareas_marketing").update({"eliminada": True}).eq("id", t['id']).execute(); st.cache_data.clear(); st.rerun()
                    if b3.button("Detalles", key=f"d_{t['id']}", use_container_width=True): 
                        st.session_state.editing_task_id = t['id']; st.rerun()

# ------------------------------------------
# PESTAÑA 2: CUADERNOS
# ------------------------------------------
with tab_cuadernos:
    col_c1, col_c2 = st.columns([1.5, 2])
    
    with col_c1:
        with st.form("nuevo_cuaderno"):
            st.subheader("Nuevo Cuaderno")
            c_titulo = st.text_input("Título del Cuaderno*")
            c_autores = st.text_input("Autores (separados por comas)")
            c_cont = st.text_area("Contenido / Estrategia*", height=350)
            
            if st.form_submit_button("Guardar en Inteligencia", type="primary"):
                if c_titulo and c_cont:
                    supabase.table("clivi_cuadernos").insert({
                        "titulo": c_titulo, "autores": c_autores, "contenido": c_cont, "eliminada": False
                    }).execute()
                    st.success("Cuaderno guardado exitosamente."); st.rerun()

    with col_c2:
        st.subheader("Cuadernos Activos")
        try:
            res_c = supabase.table("clivi_cuadernos").select("*").eq("eliminada", False).order("fecha_creacion", desc=True).execute()
            df_c = pd.DataFrame(res_c.data)
            if df_c.empty:
                st.info("No hay cuadernos activos.")
            else:
                for _, notebook in df_c.iterrows():
                    fecha_str = str(notebook['fecha_creacion']).split('T')[0]
                    with st.expander(f"📖 {notebook['titulo']} | Autor: {notebook.get('autores', 'ND')}"):
                        st.markdown(f"<span style='color: #8b949e; font-size: 12px;'>Fecha: {fecha_str}</span>", unsafe_allow_html=True)
                        st.markdown("---")
                        st.write(notebook['contenido'])
                        if st.button("🗑️ Enviar a Papelera", key=f"del_nb_{notebook['id']}"):
                            supabase.table("clivi_cuadernos").update({"eliminada": True}).eq("id", notebook['id']).execute()
                            st.rerun()
        except Exception as e:
            st.warning("Asegúrate de haber creado la tabla de Cuadernos en Supabase.")

# ------------------------------------------
# PESTAÑA 3: MURO DE IDEAS (POST-ITS)
# ------------------------------------------
with tab_muro:
    st.markdown("### 💡 Muro de Inspiración")
    with st.expander("✨ Pegar nueva idea", expanded=False):
        with st.form("new_postit"):
            p_cont = st.text_area("¿En qué estás pensando?", placeholder="Escribe aquí tu idea brillante...")
            p_col = st.select_slider("Color del Post-it", options=["Amarillo", "Azul", "Verde", "Rosa", "Naranja"])
            p_aut = st.text_input("Firma / Autor")
            color_map = {"Amarillo": "#fef3c7", "Azul": "#dbeafe", "Verde": "#dcfce7", "Rosa": "#fce7f3", "Naranja": "#ffedd5"}
            
            if st.form_submit_button("Pegar en el Muro"):
                if p_cont:
                    try:
                        supabase.table("clivi_postits").insert({"contenido": p_cont, "color": color_map[p_col], "autor": p_aut}).execute()
                        st.rerun()
                    except:
                        st.error("Asegúrate de haber creado la tabla clivi_postits en Supabase.")

    try:
        res_p = supabase.table("clivi_postits").select("*").order("fecha_creacion", desc=True).execute()
        st.markdown('<div class="postit-container">', unsafe_allow_html=True)
        for p in res_p.data:
            # Renderizamos el post-it
            st.markdown(f"""
                <div class="postit" style="background-color: {p['color']};">
                    <div>{p['contenido']}</div>
                    <div class="postit-meta">POR: {p['autor'] or 'Anónimo'}</div>
                </div>
            """, unsafe_allow_html=True)
            # Botón de eliminar (queda justo debajo del post-it en el layout de Streamlit)
            if st.button("Quitar 🗑️", key=f"del_p_{p['id']}"):
                supabase.table("clivi_postits").delete().eq("id", p['id']).execute()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    except:
        pass
