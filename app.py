import streamlit as st
import pandas as pd
from datetime import date
import uuid
from supabase import create_client, Client
import resend

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Clivi: Comando de Crecimiento", layout="wide")

# --- VARIABLES DE ESTADO ---
if 'show_add_form' not in st.session_state: st.session_state.show_add_form = False
if 'editing_task_id' not in st.session_state: st.session_state.editing_task_id = None
if 'view' not in st.session_state: st.session_state.view = "tablero"

# --- LISTA DE EQUIPO CLIVI ---
EQUIPO_CLIVI = [
    "Seleccionar...",
    "humberto.gonzalez@clivi.com.mx",
    "betiana.correa@clivi.com.mx",
    "carolina.rodriguez@clivi.com.mx",
    "Otro (Escribir...)"
]

# --- DISEÑO CSS ---
st.markdown("""
<style>
    .task-card { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 10px; border-left: 5px solid transparent; }
    .task-title { font-size: 14px; font-weight: 700; color: #1a202c; margin-bottom: 4px; }
    .task-meta { font-size: 11px; color: #4a5568; display: flex; justify-content: space-between; align-items: center; }
    .area-tag { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; text-transform: uppercase; color: white; }
    .priority-badge { font-size: 9px; font-weight: bold; padding: 1px 5px; border-radius: 4px; text-transform: uppercase; }
    .st-paid { border-left-color: #FF4B4B; } .st-paid .area-tag { background-color: #FF4B4B; }
    .st-organic { border-left-color: #2ECC71; } .st-organic .area-tag { background-color: #2ECC71; }
    .st-motion { border-left-color: #9B59B6; } .st-motion .area-tag { background-color: #9B59B6; }
    .st-design { border-left-color: #3498DB; } .st-design .area-tag { background-color: #3498DB; }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN ---
SUPABASE_URL = "https://hsfgtjagpfmzqbwuhtqg.supabase.co"
SUPABASE_KEY = "sb_publishable_z5UM_bMEymxiupzyTqi_eA_V4c0SZZC"
RESEND_API_KEY = "re_TU_API_KEY_AQUÍ" # <--- PEGA AQUÍ TU API KEY DE RESEND

@st.cache_resource
def init_clients():
    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    resend.api_key = RESEND_API_KEY
    return db

supabase = init_clients()

# --- LÓGICA DE NOTIFICACIÓN ---
def enviar_notificacion(destinatario, tarea_titulo, autor_nombre):
    if "@" in destinatario:
        try:
            resend.Emails.send({
                "from": "Clivi Bot <onboarding@resend.dev>",
                "to": destinatario,
                "subject": f"🚀 Nueva tarea: {tarea_titulo}",
                "html": f"""
                <div style='font-family: sans-serif;'>
                    <h3>¡Hola!</h3>
                    <p><strong>{autor_nombre}</strong> te ha asignado una tarea en el Centro de Mando.</p>
                    <p><b>Tarea:</b> {tarea_titulo}</p>
                    <br>
                    <p>Revisa el tablero para más detalles.</p>
                </div>
                """
            })
            return True
        except Exception as e:
            st.error(f"Error al enviar correo: {e}")
            return False
    return False

# --- FUNCIONES DB ---
def get_tasks(eliminadas=False):
    return pd.DataFrame(supabase.table("clivi_tareas_marketing").select("*").eq("eliminada", eliminadas).execute().data)

def update_db(task_id, data):
    supabase.table("clivi_tareas_marketing").update(data).eq("id", task_id).execute()
    st.cache_data.clear()

# --- HEADER ---
c_head1, c_head2, c_head3 = st.columns([1, 7, 2])
with c_head2:
    try: st.image("logo_clivi.png", width=120)
    except: st.warning("Logo no encontrado")
    st.title("Centro de Mando de Marketing")
with c_head3:
    if st.button("🏠 Tablero Principal", use_container_width=True):
        st.session_state.view = "tablero"; st.session_state.editing_task_id = None; st.rerun()
    if st.button("🗑️ Ver Papelera", use_container_width=True):
        st.session_state.view = "papelera"; st.session_state.editing_task_id = None; st.rerun()

st.markdown("---")

# --- VISTA: PAPELERA ---
if st.session_state.view == "papelera":
    st.subheader("🗑️ Papelera de Reciclaje")
    df_trash = get_tasks(eliminadas=True)
    if df_trash.empty: st.info("Papelera vacía.")
    else:
        for _, t in df_trash.iterrows():
            with st.container(border=True):
                c_t1, c_t2, c_t3 = st.columns([6, 2, 2])
                c_t1.write(f"**{t['titulo']}** | Asignada a: {t['asignado_a']}")
                if c_t2.button("🔄 Restaurar", key=f"res_{t['id']}", use_container_width=True):
                    update_db(t['id'], {"eliminada": False}); st.rerun()
                if c_t3.button("❌ Borrar Definitivo", key=f"pdel_{t['id']}", use_container_width=True):
                    supabase.table("clivi_tareas_marketing").delete().eq("id", t['id']).execute(); st.cache_data.clear(); st.rerun()
    st.stop()

# --- VISTA: TABLERO ---
df = get_tasks(eliminadas=False)
c_act1, c_act2, c_act3 = st.columns([2, 2, 6])
with c_act1:
    if st.button("+ Nueva Tarea", use_container_width=True, type="primary"):
        st.session_state.show_add_form = True; st.session_state.editing_task_id = None
with c_act2:
    filtro_area = st.selectbox("Área", ['Todas', 'Pagado', 'Orgánico', 'Motion', 'Diseño'], label_visibility="collapsed")
with c_act3:
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📊 Reporte Excel", data=csv, file_name=f'clivi_marketing_{date.today()}.csv', mime='text/csv')

# --- FORMULARIO NUEVA TAREA ---
if st.session_state.show_add_form:
    with st.expander("📝 Registrar Nueva Tarea", expanded=True):
        with st.form("new_task"):
            f1, f2 = st.columns(2)
            with f1:
                nt_t = st.text_input("Título*")
                nt_a = st.selectbox("Área*", ['Pagado', 'Orgánico', 'Motion', 'Diseño'])
                nt_p = st.selectbox("Prioridad", ['Baja', 'Media', 'Alta', 'Urgente'], index=1)
                nt_aut = st.text_input("Tu Nombre (Autor)*")
            with f2:
                nt_as_select = st.selectbox("Asignar a integrante", EQUIPO_CLIVI)
                nt_as_custom = st.text_input("Nombre/Correo (si eligió 'Otro')") if nt_as_select == "Otro (Escribir...)" else ""
                nt_as = nt_as_custom if nt_as_select == "Otro (Escribir...)" else nt_as_select
                
                nt_dl = st.date_input("Fecha Límite")
                nt_desc = st.text_area("Descripción")
            
            nb1, nb2 = st.columns([2, 8])
            if nb1.form_submit_button("Crear"):
                if nt_t and nt_aut and nt_as != "Seleccionar...":
                    supabase.table("clivi_tareas_marketing").insert({
                        "id": str(uuid.uuid4()), "titulo": nt_t, "area": nt_a, "estado": "Backlog",
                        "prioridad": nt_p, "asignado_a": nt_as, "autor": nt_aut, 
                        "fecha_limite": str(nt_dl), "descripcion": nt_desc, "eliminada": False
                    }).execute()
                    
                    if "@clivi.com.mx" in nt_as:
                        enviar_notificacion(nt_as, nt_t, nt_aut)
                    
                    st.session_state.show_add_form = False; st.cache_data.clear(); st.rerun()
            if nb2.form_submit_button("Cancelar"): st.session_state.show_add_form = False; st.rerun()

# --- EDITOR DE DETALLES ---
if st.session_state.editing_task_id and not df.empty:
    task = df[df['id'] == st.session_state.editing_task_id].iloc[0]
    with st.form("edit_form"):
        st.subheader(f"✏️ Editando: {task['titulo']}")
        e1, e2 = st.columns(2)
        with e1:
            et = st.text_input("Título", value=task['titulo'])
            es = st.selectbox("Estado", ['Backlog', 'Por Hacer', 'En Proceso', 'Terminado'], index=['Backlog', 'Por Hacer', 'En Proceso', 'Terminado'].index(task['estado']))
            ep = st.selectbox("Prioridad", ['Baja', 'Media', 'Alta', 'Urgente'], index=['Baja', 'Media', 'Alta', 'Urgente'].index(task.get('prioridad', 'Media')))
        with e2:
            eas = st.text_input("Asignado a", value=task['asignado_a'])
            ed = st.text_area("Descripción", value=task.get('descripcion', ''))
            en = st.text_area("Notas / Resultados", value=task.get('notas', ''))
        
        eb1, eb2, eb3 = st.columns([2, 2, 6])
        if eb1.form_submit_button("💾 Guardar"):
            update_db(task['id'], {"titulo": et, "estado": es, "prioridad": ep, "asignado_a": eas, "descripcion": ed, "notas": en})
            st.session_state.editing_task_id = None; st.rerun()
        if eb2.form_submit_button("❌ Cancelar"): st.session_state.editing_task_id = None; st.rerun()
        if eb3.form_submit_button("🗑️ Papelera"): update_db(task['id'], {"eliminada": True}); st.session_state.editing_task_id = None; st.rerun()

# --- TABLERO KANBAN ---
if not df.empty:
    if filtro_area != 'Todas': df = df[df['area'] == filtro_area]
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
                st.markdown(f"""<div class="task-card {a_css.get(t['area'], '')}"><div style="display: flex; justify-content: space-between;"><span class="area-tag">{t['area']}</span><span class="priority-badge" style="color: {pc}; border: 1px solid {pc};">{t.get('prioridad', 'Media')}</span></div><div class="task-title">{t['titulo']}</div><div class="task-meta"><span>📅 {t['fecha_limite']}</span><b>👤 {t['asignado_a']}</b></div></div>""", unsafe_allow_html=True)
                b1, b2, b3 = st.columns([1,1,2])
                if i > 0 and b1.button("⬅️", key=f"l_{t['id']}"): update_db(t['id'], {"estado": est[i-1]}); st.rerun()
                if i < 3 and b2.button("➡️", key=f"r_{t['id']}"): update_db(t['id'], {"estado": est[i+1]}); st.rerun()
                if i == 3 and b2.button("🗑️", key=f"t_{t['id']}"): update_db(t['id'], {"eliminada": True}); st.rerun()
                if b3.button("Detalles", key=f"d_{t['id']}", use_container_width=True): st.session_state.editing_task_id = t['id']; st.rerun()
