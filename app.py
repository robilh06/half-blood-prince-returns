import streamlit as st
import mysql.connector
from mysql.connector import Error
import plotly.express as px
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="ChronoWeaver", layout="wide", page_icon="⏳")

# --- DATABASE MANAGER ---
def get_db_connection():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',       # CHANGE THIS
            password='Root@123', # CHANGE THIS
            database='chronoweaver'
        )
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

def run_query(query, params=None, fetch=False):
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return True
    except Error as e:
        st.error(f"Database Error: {e}")
        return None
    finally:
        conn.close()

# --- CUSTOM CSS ---
def local_css():
    st.markdown("""
    <style>
        .stApp { background-color: #050c16; }
        h1, h2, h3 { color: #3b82f6 !important; font-family: 'Helvetica Neue', sans-serif; }
        p, div, span, label { color: #e2e8f0; }
        
        /* Input Fields */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stNumberInput > div > div > input {
            background-color: #1e293b; color: white; border: 1px solid #3b82f6;
        }
        .stSelectbox > div > div > div {
            background-color: #1e293b; color: white;
        }
        
        /* Cards */
        .custom-card {
            background-color: #0f172a; padding: 20px; border-radius: 10px;
            border: 1px solid #1e293b; margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .card-title { font-size: 18px; font-weight: bold; color: #a855f7; margin-bottom: 5px; }
        .card-sub { font-size: 12px; color: #94a3b8; margin-bottom: 10px; }
        .participant-tag { border: 1px solid #3b82f6; color: #93c5fd; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 5px; }
        .relation-tag { border: 1px solid #d946ef; color: #f0abfc; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 5px; }
        
        /* Button Styling */
        .stButton > button { width: 100%; background-color: #1e293b; color: white; border: 1px solid #3b82f6; }
        .stButton > button:hover { background-color: #3b82f6; border-color: white; }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'selected_timeline' not in st.session_state: st.session_state.selected_timeline = None

# --- DATA FETCHING ---
def get_timeline_data(t_id):
    events = run_query("SELECT * FROM events WHERE timeline_id = %s ORDER BY event_year ASC", (t_id,), fetch=True)
    chars = run_query("SELECT * FROM characters WHERE timeline_id = %s", (t_id,), fetch=True)
    locs = run_query("SELECT * FROM locations WHERE timeline_id = %s", (t_id,), fetch=True)
    
    # Enrich Events with Participants
    if events:
        for e in events:
            e['participants'] = run_query("""
                SELECT c.name, ec.role_note FROM characters c 
                JOIN event_characters ec ON c.id = ec.character_id 
                WHERE ec.event_id = %s""", (e['id'],), fetch=True)
            
    # Enrich Characters with Relationships
    if chars:
        for c in chars:
            c['relationships'] = run_query("""
                SELECT c.name, cr.relationship_type, 'outgoing' as direction FROM character_relationships cr JOIN characters c ON cr.char2_id = c.id WHERE cr.char1_id = %s
                UNION
                SELECT c.name, cr.relationship_type, 'incoming' as direction FROM character_relationships cr JOIN characters c ON cr.char1_id = c.id WHERE cr.char2_id = %s
            """, (c['id'], c['id']), fetch=True)
            
    return events, chars, locs

# --- CRUD FORMS ---
def manage_entity(entity_type, data_list, timeline_id):
    st.subheader(f"Manage {entity_type}")
    
    action = st.radio(f"Action for {entity_type}", ["Create New", "Edit Existing", "Delete"], horizontal=True, key=f"{entity_type}_action")
    
    # --- CREATE ---
    if action == "Create New":
        with st.form(f"create_{entity_type}"):
            name = st.text_input("Name/Title")
            desc = st.text_area("Description")
            
            extra_field = None
            if entity_type == "Events":
                extra_field = st.number_input("Year", value=0)
            elif entity_type == "Characters":
                extra_field = st.text_input("Role/Class")
                
            if st.form_submit_button(f"Create {entity_type[:-1]}"):
                if entity_type == "Events":
                    run_query("INSERT INTO events (timeline_id, title, event_year, description) VALUES (%s, %s, %s, %s)", (timeline_id, name, extra_field, desc))
                elif entity_type == "Characters":
                    run_query("INSERT INTO characters (timeline_id, name, role, bio) VALUES (%s, %s, %s, %s)", (timeline_id, name, extra_field, desc))
                elif entity_type == "Locations":
                    run_query("INSERT INTO locations (timeline_id, name, description) VALUES (%s, %s, %s)", (timeline_id, name, desc))
                st.success("Created!")
                st.rerun()

    # --- EDIT ---
    elif action == "Edit Existing":
        if not data_list:
            st.info("No data to edit.")
        else:
            # Create a dict for easy lookup
            options = {item['title'] if 'title' in item else item['name']: item for item in data_list}
            selected_name = st.selectbox(f"Select {entity_type[:-1]} to Edit", list(options.keys()))
            selected_item = options[selected_name]
            
            with st.form(f"edit_{entity_type}"):
                new_name = st.text_input("Name/Title", value=selected_item.get('title', selected_item.get('name')))
                new_desc = st.text_area("Description", value=selected_item['description'] if 'description' in selected_item else selected_item['bio'])
                
                new_extra = None
                if entity_type == "Events":
                    new_extra = st.number_input("Year", value=selected_item['event_year'])
                elif entity_type == "Characters":
                    new_extra = st.text_input("Role", value=selected_item['role'])
                
                if st.form_submit_button("Save Changes"):
                    if entity_type == "Events":
                        run_query("UPDATE events SET title=%s, event_year=%s, description=%s WHERE id=%s", (new_name, new_extra, new_desc, selected_item['id']))
                    elif entity_type == "Characters":
                        run_query("UPDATE characters SET name=%s, role=%s, bio=%s WHERE id=%s", (new_name, new_extra, new_desc, selected_item['id']))
                    elif entity_type == "Locations":
                        run_query("UPDATE locations SET name=%s, description=%s WHERE id=%s", (new_name, new_desc, selected_item['id']))
                    st.success("Updated!")
                    st.rerun()

    # --- DELETE ---
    elif action == "Delete":
        if not data_list:
            st.info("Nothing to delete.")
        else:
            options = {item['title'] if 'title' in item else item['name']: item for item in data_list}
            selected_name = st.selectbox(f"Select {entity_type[:-1]} to Delete", list(options.keys()))
            selected_id = options[selected_name]['id']
            
            if st.button(f"⚠️ Delete {selected_name}?"):
                table_map = {"Events": "events", "Characters": "characters", "Locations": "locations"}
                run_query(f"DELETE FROM {table_map[entity_type]} WHERE id = %s", (selected_id,))
                st.success("Deleted.")
                st.rerun()

# --- PAGE: HOME ---
def show_home():
    st.title("ChronoWeaver")
    st.markdown("### Select or Create a Timeline")
    
    # Create New Timeline Section
    with st.expander("➕ Create New Timeline", expanded=False):
        with st.form("create_timeline"):
            t_title = st.text_input("Timeline Title")
            t_desc = st.text_area("Description")
            if st.form_submit_button("Create World"):
                run_query("INSERT INTO timelines (title, description) VALUES (%s, %s)", (t_title, t_desc))
                st.success("New world created!")
                st.rerun()

    # List Existing Timelines
    timelines = run_query("SELECT * FROM timelines", fetch=True)
    if timelines:
        for t in timelines:
            with st.container():
                st.markdown(f"""
                <div class="custom-card">
                    <div style="color:#38bdf8; font-size: 24px; font-weight:bold;">{t['title']}</div>
                    <div style="margin-top:10px;">{t['description']}</div>
                </div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button(f"Enter", key=f"btn_{t['id']}"):
                        st.session_state.page = 'dashboard'
                        st.session_state.selected_timeline = t
                        st.rerun()
                with col2:
                    if st.button("Delete", key=f"del_{t['id']}"):
                        run_query("DELETE FROM timelines WHERE id = %s", (t['id'],))
                        st.rerun()

# --- PAGE: DASHBOARD ---
def show_dashboard():
    t_data = st.session_state.selected_timeline
    
    # Navigation
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.button("← Home"):
            st.session_state.page = 'home'
            st.rerun()
    with col2:
        st.title(t_data['title'])

    # Fetch all data for this timeline
    events, chars, locs = get_timeline_data(t_data['id'])

    # TABS: View vs Edit
    tab_view, tab_manage, tab_links = st.tabs(["📜 The Saga (View)", "🛠️ Dungeon Master (Edit)", "🕸️ Connections"])

    # --- TAB 1: VIEW MODE ---
    with tab_view:
        # Timeline Chart
        if events:
            df = pd.DataFrame(events)
            fig = px.scatter(df, x="event_year", y=[1]*len(df), text="title", hover_data=["description"], size=[10]*len(df), title="Timeline Chronology")
            fig.update_traces(textposition='top center', marker=dict(color='#3b82f6', size=15, line=dict(width=2, color='white')), textfont=dict(color='white'))
            fig.update_layout(plot_bgcolor='#0f172a', paper_bgcolor='#0f172a', font_color='white', xaxis=dict(showgrid=False, zeroline=True, zerolinecolor='#334155'), yaxis=dict(visible=False), height=250, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        col_e, col_c, col_l = st.columns(3)
        with col_e:
            st.markdown("### 🕒 Events")
            if events:
                for e in events:
                    part_html = ""
                    if e['participants']:
                        part_html = "<br><small>Participants:</small><br>" + "".join([f"<span class='participant-tag'>{p['name']}</span>" for p in e['participants']])
                    st.markdown(f"<div class='custom-card'><div class='card-title'>{e['title']}</div><div class='card-sub'>{e['event_year']}</div>{e['description']}{part_html}</div>", unsafe_allow_html=True)
        
        with col_c:
            st.markdown("### 👤 Characters")
            if chars:
                for c in chars:
                    rel_html = ""
                    if c['relationships']:
                        rel_html = "<br><small>Connections:</small><br>" + "".join([f"<span class='relation-tag'>{r['relationship_type']} {r['name']}</span>" for r in c['relationships']])
                    st.markdown(f"<div class='custom-card'><div class='card-title'>{c['name']}</div><div class='card-sub'>{c['role']}</div>{c['bio']}{rel_html}</div>", unsafe_allow_html=True)

        with col_l:
            st.markdown("### ⛩️ Locations")
            if locs:
                for l in locs:
                    st.markdown(f"<div class='custom-card'><div class='card-title'>{l['name']}</div>{l['description']}</div>", unsafe_allow_html=True)

    # --- TAB 2: MANAGE DATA (CRUD) ---
    with tab_manage:
        st.info("Here you can Add, Edit, or Delete specific entries.")
        m_event, m_char, m_loc = st.tabs(["Events", "Characters", "Locations"])
        
        with m_event:
            manage_entity("Events", events, t_data['id'])
        with m_char:
            manage_entity("Characters", chars, t_data['id'])
        with m_loc:
            manage_entity("Locations", locs, t_data['id'])

    # --- TAB 3: CONNECTIONS (Linking Logic) ---
    with tab_links:
        st.subheader("🔗 Weave Fate")
        link_col1, link_col2 = st.columns(2)
        
        with link_col1:
            st.write("**Link Character to Event**")
            with st.form("link_event"):
                if events and chars:
                    e_sel = st.selectbox("Event", [e['title'] for e in events])
                    c_sel = st.selectbox("Character", [c['name'] for c in chars])
                    role = st.text_input("Role in Event")
                    if st.form_submit_button("Link"):
                        eid = next(e['id'] for e in events if e['title'] == e_sel)
                        cid = next(c['id'] for c in chars if c['name'] == c_sel)
                        run_query("INSERT INTO event_characters (event_id, character_id, role_note) VALUES (%s, %s, %s)", (eid, cid, role))
                        st.success("Linked!")
                        st.rerun()
        
        with link_col2:
            st.write("**Link Character to Character**")
            with st.form("link_chars"):
                if len(chars) >= 2:
                    c1_sel = st.selectbox("Character 1", [c['name'] for c in chars], key="c1")
                    c2_sel = st.selectbox("Character 2", [c['name'] for c in chars], key="c2")
                    rel = st.text_input("Relationship (e.g. Rival)")
                    if st.form_submit_button("Connect"):
                        if c1_sel != c2_sel:
                            id1 = next(c['id'] for c in chars if c['name'] == c1_sel)
                            id2 = next(c['id'] for c in chars if c['name'] == c2_sel)
                            run_query("INSERT INTO character_relationships (char1_id, char2_id, relationship_type) VALUES (%s, %s, %s)", (id1, id2, rel))
                            st.success("Connected!")
                            st.rerun()

# --- MAIN APP ---
def main():
    if st.session_state.page == 'home':
        show_home()
    elif st.session_state.page == 'dashboard':
        if st.session_state.selected_timeline:
            show_dashboard()
        else:
            st.session_state.page = 'home'
            st.rerun()

if __name__ == "__main__":
    main()
