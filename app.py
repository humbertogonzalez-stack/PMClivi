import streamlit as st
import pandas as pd
from datetime import date
import uuid
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Clivi: Comando de Crecimiento", layout="wide")

if 'show_add_form' not in st.session_state: st.session_state.show_add_form = False
if 'editing_task_id' not in st.session_state: st.session_state.editing_task_id = None
if 'view' not in st.session_state: st.session_state.view = "tablero" # "tablero" o "papelera"

# --- CSS ---
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

@st.cache_resource
def init_connection(): return create_client(SUPABASE_URL, SUPABASE_KEY)
supabase = init_connection()

# --- CRUD ---
def get_tasks(eliminadas=False):
    return pd.DataFrame(supabase.table("clivi_tareas_marketing").select("*").eq("eliminada", eliminadas).execute().data)

def move_to_trash(task_id, status=True):
    supabase.table("clivi_tareas_marketing").update({"eliminada": status}).eq("id", task_id).execute()
    st.cache_data.clear()

def permanent_delete(task_id):
    supabase.table("clivi_tareas_marketing").delete().eq("id", task_id).execute()
    st.cache_data.clear()

# --- HEADER ---
c_head1, c_head2, c_head3 = st.columns([1, 7, 2])
with c_head2:
    try: st.image("logo_clivi.png", width=120)
    except: st.warning("Logo no encontrado")
    st.title("Centro de Mando de Marketing")

with c_head3:
    if st.button("🏠 Inicio / Tablero", use_container_width=True):
        st.session_state.view = "tablero"; st.session_state.editing_task_id = None; st.rerun()
    if st.button("🗑️ Papelera de Reciclaje", use_container_width=True):
        st.session_state.view = "papelera"; st.session_state.editing_task_id = None; st.rerun()

st.markdown("---")

# --- VISTA: PAPELERA ---
if st.session_state.view == "papelera":
    st.subheader("🗑️ Tareas Eliminadas")
    df_trash = get_tasks(eliminadas=True)
    if df_trash.empty:
        st.info("La papelera está vacía.")
    else:
        for _, t in df_trash.iterrows():
            with st.container(border=True):
                c_t1, c_t2, c_t3 = st.columns([6, 2, 2])
                c_t1.write(f"**{t['titulo']}** ({t['area']}) - Eliminada de: {t['estado']}")
                if c_t2.button("🔄 Restaurar", key=f"res_{t['id']}", use_container_width=True):
                    move_to_trash(t['id'], False); st.rerun()
                if c_t3.button("❌ Borrar Permanente", key=f"delp_{t['id']}", use_container_width=True):
                    permanent_delete(t['id']); st.rerun()
    st.stop()

# --- VISTA: TABLERO (Resto del código original filtrado) ---
c1, c2, c3 = st.columns([2, 2, 4])
with c1:
    if st.button("+ Nueva Tarea", use_container_width=True, type="primary"):
        st.session_state.show_add_form = True; st.session_state.editing_task_id = None
with c2:
    filtro_area = st.selectbox("Filtrar Área", ['Todas', 'Pagado', 'Orgánico', 'Motion', 'Diseño'])

df = get_tasks(eliminadas=False)

# --- EDITOR (Incluye botón de eliminar que manda a papelera) ---
if st.session_state.editing_task_id and not df.empty:
    task_to_edit = df[df['id'] == st.session_state.editing_task_id].iloc[0]
    with st.form("edit_form"):
        st.subheader(f"✏️ Detalles: {task_to_edit['titulo']}")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            e_titulo = st.text_input("Título", value=task_to_edit['titulo'])
            e_estado = st.selectbox("Estado", ['Backlog', 'Por Hacer', 'En Proceso', 'Terminado'], index=['Backlog', 'Por Hacer', 'En Proceso', 'Terminado'].index(task_to_edit['estado']))
            e_prioridad = st.selectbox("Prioridad", ['Baja', 'Media', 'Alta', 'Urgente'], index=['Baja', 'Media', 'Alta', 'Urgente'].index(task_to_edit.get('prioridad', 'Media')))
        with col_e2:
            e_asignado = st.text_input("Asignado a", value=task_to_edit.get('asignado_a', ''))
            e_desc = st.text_area("Descripción", value=task_to_edit.get('descripcion', ''))
            e_notas = st.text_area("Notas", value=task_to_edit.get('notas', ''))
        
        eb1, eb2, eb3 = st.columns([2, 2, 6])
        if eb1.form_submit_button("💾 Guardar"):
            supabase.table("clivi_tareas_marketing").update({"titulo": e_titulo, "estado": e_estado, "prioridad": e_prioridad, "asignado_a": e_asignado, "descripcion": e_desc, "notas": e_notas}).eq("id", st.session_state.editing_task_id).execute()
            st.session_state.editing_task_id = None; st.cache_data.clear(); st.rerun()
        if eb2.form_submit_button("❌ Cancelar"): st.session_state.editing_task_id = None; st.rerun()
        if eb3.form_submit_button("🗑️ Enviar a Papelera"):
            move_to_trash(st.session_state.editing_task_id); st.session_state.editing_task_id = None; st.rerun()

# --- FORMULARIO NUEVA TAREA ---
if st.session_state.show_add_form:
    with st.expander("📝 Crear Nueva Tarea", expanded=True):
        with st.form("new_task"):
            f1, f2 = st.columns(2)
            with f1:
                nt_t = st.text_input("Título*"); nt_a = st.selectbox("Área*", ['Pagado', 'Orgánico', 'Motion', 'Diseño']); nt_p = st.selectbox("Prioridad", ['Baja', 'Media', 'Alta', 'Urgente'], index=1)
            with f2:
                nt_as = st.text_input("Asignado"); nt_dl = st.date_input("Fecha Límite"); nt_st = st.selectbox("Estado", ['Backlog', 'Por Hacer', 'En Proceso', 'Terminado'])
            if st.form_submit_button("Crear"):
                if nt_t:
                    supabase.table("clivi_tareas_marketing").insert({"id": str(uuid.uuid4()), "titulo": nt_t, "area": nt_a, "estado": nt_st, "prioridad": nt_p, "asignado_a": nt_as, "fecha_limite": str(nt_dl), "eliminada": False}).execute()
                    st.session_state.show_add_form = False; st.cache_data.clear(); st.rerun()
            if st.form_submit_button("Cancelar"): st.session_state.show_add_form = False; st.rerun()

# --- KANBAN ---
if not df.empty:
    if filtro_area != 'Todas': df = df[df['area'] == filtro_area]
    estados = ['Backlog', 'Por Hacer', 'En Proceso', 'Terminado']
    priority_colors = {'Baja': '#A0AEC0', 'Media': '#4A5568', 'Alta': '#ED8936', 'Urgente': '#E53E3E'}
    area_css = {'Pagado': 'st-paid', 'Orgánico': 'st-organic', 'Motion': 'st-motion', 'Diseño': 'st-design'}
    cols = st.columns(len(estados))
    for i, estado in enumerate(estados):
        with cols[i]:
            st.markdown(f"### {estado}")
            tareas = df[df['estado'] == estado]
            for _, t in tareas.iterrows():
                p_col = priority_colors.get(t.get('prioridad', 'Media'), '#4A5568')
                st.markdown(f'<div class="task-card {area_css.get(t["area"], "")}"><div style="display: flex; justify-content: space-between;"><span class="area-tag">{t["area"]}</span><span class="priority-badge" style="color: {p_col}; border: 1px solid {p_col};">{t.get("prioridad", "Media")}</span></div><div class="task-title">{t["titulo"]}</div><div class="task-meta"><span>📅 {t["fecha_limite"]}</span><b>👤 {t["asignado_a"]}</b></div></div>', unsafe_allow_html=True)
                b1, b2, b3 = st.columns([1,1,2])
                if i > 0:
                    if b1.button("⬅️", key=f"p_{t['id']}"): supabase.table("clivi_tareas_marketing").update({"estado": estados[i-1]}).eq("id", t['id']).execute(); st.cache_data.clear(); st.rerun()
                if i < 3:
                    if b2.button("➡️", key=f"n_{t['id']}"): supabase.table("clivi_tareas_marketing").update({"estado": estados[i+1]}).eq("id", t['id']).execute(); st.cache_data.clear(); st.rerun()
                else:
                    if b2.button("🗑️", key=f"trash_{t['id']}"): move_to_trash(t['id']); st.rerun()
                if b3.button("Detalles", key=f"d_{t['id']}", use_container_width=True): st.session_state.editing_task_id = t['id']; st.rerun()
else: st.info("Tablero vacío.")