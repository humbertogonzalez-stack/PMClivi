import streamlit as st
import pandas as pd
from datetime import date
import uuid
from supabase import create_client, Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Clivi: Comando de Crecimiento", layout="wide")

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

# --- CSS ---
st.markdown("""
<style>
    .task-card { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 10px; border-left: 5px solid transparent; color: #1a202c; }
    .task-title { font-size: 14px; font-weight: 700; margin-bottom: 4px; }
    .task-meta { font-size: 11px; color: #4a5568; display: flex; justify-content: space-between; align-items: center; }
    .area-tag { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; text-transform: uppercase; color: white; }
    .priority-badge { font-size: 9px; font-weight: bold; padding: 1px 5px; border-radius: 4px; text-transform: uppercase; }
    .st-paid { border-left-color: #FF4B4B; } .st-paid .area-tag { background-color: #FF4B4B; }
    .st-organic { border-left-color: #2ECC71; } .st-organic .area-tag { background-color: #2ECC71; }
    .st-motion { border-left-color: #9B59B6; } .st-motion .area-tag { background-color: #9B59B6; }
    .st-design { border-left-color: #3498DB; } .st-design .area-tag { background-color: #3498DB; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
c_head1, c_head2, c_head3 = st.columns([1, 7, 2])
with c_head2:
    try: st.image("logo_clivi.png", width=120)
    except: pass
    st.title("Centro de Mando de Marketing")
with c_head3:
    if st.button("🏠 Tablero", use_container_width=True): st.session_state.view = "tablero"; st.rerun()
    if st.button("🗑️ Papelera", use_container_width=True): st.session_state.view = "papelera"; st.rerun()

st.markdown("---")

# --- VISTA: PAPELERA ---
if st.session_state.view == "papelera":  # <--- AQUÍ ESTABA EL ERROR
    st.subheader("🗑️ Papelera")
    res = supabase.table("clivi_tareas_marketing").select("*").eq("eliminada", True).execute()
    df_trash = pd.DataFrame(res.data)
    if df_trash.empty: st.info("Vacía.")
    else:
        for _, t in df_trash.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([6, 2, 2])
                c1.write(f"**{t['titulo']}**")
                if c2.button("🔄 Restaurar", key=f"r_{t['id']}"):
                    supabase.table("clivi_tareas_marketing").update({"eliminada": False}).eq("id", t['id']).execute()
                    st.cache_data.clear(); st.rerun()
                if c3.button("❌ Borrar", key=f"d_{t['id']}"):
                    supabase.table("clivi_tareas_marketing").delete().eq("id", t['id']).execute()
                    st.cache_data.clear(); st.rerun()
    st.stop()

# --- VISTA: TABLERO ---
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
                nt_desc = st.text_area("Descripción")
            
            if st.form_submit_button("Crear"):
                if nt_t and nt_aut and nt_as != "Seleccionar...":
                    supabase.table("clivi_tareas_marketing").insert({
                        "id": str(uuid.uuid4()), "titulo": nt_t, "area": nt_a, "estado": "Backlog",
                        "prioridad": nt_p, "asignado_a": nt_as, "autor": nt_aut, 
                        "fecha_limite": str(nt_dl), "descripcion": nt_desc, "eliminada": False
                    }).execute()
                    if "@" in nt_as: enviar_notificacion(nt_as, nt_t, nt_aut)
                    st.session_state.show_add_form = False; st.cache_data.clear(); st.rerun()

# --- EDITOR ---
if st.session_state.editing_task_id and not df.empty:
    task = df[df['id'] == st.session_state.editing_task_id].iloc[0]
    with st.form("edit"):
        st.subheader(f"✏️ Editando: {task['titulo']}")
        e1, e2 = st.columns(2)
        with e1:
            et = st.text_input("Título", value=task['titulo'])
            es = st.selectbox("Estado", ['Backlog', 'Por Hacer', 'En Proceso', 'Terminado'], index=['Backlog', 'Por Hacer', 'En Proceso', 'Terminado'].index(task['estado']))
            ep = st.selectbox("Prioridad", ['Baja', 'Media', 'Alta', 'Urgente'], index=['Baja', 'Media', 'Alta', 'Urgente'].index(task.get('prioridad', 'Media')))
        with e2:
            eas = st.text_input("Asignado", value=task['asignado_a'])
            ed = st.text_area("Descripción", value=task['descripcion'] if pd.notna(task['descripcion']) else "")
            en = st.text_area("Notas", value=task['notas'] if pd.notna(task['notas']) else "")
        
        eb1, eb2, eb3 = st.columns([2, 2, 6])
        if eb1.form_submit_button("💾 Guardar"):
            supabase.table("clivi_tareas_marketing").update({"titulo": et, "estado": es, "prioridad": ep, "asignado_a": eas, "descripcion": ed, "notas": en}).eq("id", task['id']).execute()
            st.session_state.editing_task_id = None; st.cache_data.clear(); st.rerun()
        if eb2.form_submit_button("❌ Cancelar"): st.session_state.editing_task_id = None; st.rerun()
        if eb3.form_submit_button("🗑️ Eliminar"):
            supabase.table("clivi_tareas_marketing").update({"eliminada": True}).eq("id", task['id']).execute()
            st.session_state.editing_task_id = None; st.cache_data.clear(); st.rerun()

# --- KANBAN ---
if not df.empty:
    if filtro != 'Todas': df = df[df['area'] == filtro]
    est = ['Backlog', 'Por Hacer', 'En Proceso', 'Terminado']
    p_cols = {'Baja': '#A0AEC0', 'Media': '#4A5568', 'Alta': '#ED8936', 'Urgente': '#E53E3E'}
    a_css = {'Pagado': 'st-paid', 'Orgánico': 'st-organic', 'Motion': 'st-motion', 'Diseño': 'st-design'}
    cols = st.columns(4)
    for i, col_name in enumerate(est):
        with cols[i]:
            st.markdown(f"### {col_name}")
            tareas = df[df['estado'] == col_name]
            for _, t in tareas.iterrows():
                pc = p_cols.get(t.get('prioridad', 'Media'), '#4A5568')
                st.markdown(f'<div class="task-card {a_css.get(t["area"], "")}"><div style="display: flex; justify-content: space-between;"><span class="area-tag">{t["area"]}</span><span class="priority-badge" style="color: {pc}; border: 1px solid {pc};">{t.get("prioridad", "Media")}</span></div><div class="task-title">{t["titulo"]}</div><div class="task-meta"><span>📅 {t["fecha_limite"]}</span><b>👤 {t["asignado_a"]}</b></div></div>', unsafe_allow_html=True)
                b1, b2, b3 = st.columns([1,1,2])
                if i > 0 and b1.button("⬅️", key=f"l_{t['id']}"):
                    supabase.table("clivi_tareas_marketing").update({"estado": est[i-1]}).eq("id", t['id']).execute(); st.cache_data.clear(); st.rerun()
                if i < 3 and b2.button("➡️", key=f"r_{t['id']}"):
                    supabase.table("clivi_tareas_marketing").update({"estado": est[i+1]}).eq("id", t['id']).execute(); st.cache_data.clear(); st.rerun()
                if i == 3 and b2.button("🗑️", key=f"t_{t['id']}"):
                    supabase.table("clivi_tareas_marketing").update({"eliminada": True}).eq("id", t['id']).execute(); st.cache_data.clear(); st.rerun()
                if b3.button("Detalles", key=f"d_{t['id']}", use_container_width=True): st.session_state.editing_task_id = t['id']; st.rerun()
