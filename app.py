import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np
import os

# --- 1. SETUP & CONFIG ---
st.set_page_config(
    page_title="Bara Tama Wijaya Water Management",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e0e0e0;
        padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stAlert { font-weight: bold; }
    section[data-testid="stSidebar"] { background-color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# --- 2. FILE MANAGEMENT SYSTEM (AUTO-SAVE) ---
FILE_SUMP = "db_sump.csv"
FILE_POMPA = "db_pompa.csv"

def load_or_init_data():
    # 1. LOAD DATA SUMP
    if os.path.exists(FILE_SUMP):
        df_s = pd.read_csv(FILE_SUMP)
        df_s['Tanggal'] = pd.to_datetime(df_s['Tanggal'])
    else:
        # Generate Dummy Data Awal
        data = []
        today = date.today()
        init_map = {
            "Lais Coal Mine (LCM)": ["Sump Wijaya Barat", "Sump Wijaya Timur"],
            "Wiraduta Sejahtera Langgeng (WSL)": ["Sump F01", "Sump F02"],
            "Nusantara Energy (NE)": ["Sump S8"]
        }
        for i in range(60): 
            d = today - timedelta(days=i)
            for site in init_map.keys():
                for pit in init_map[site]:
                    elev = 10.0 + (np.sin(i/15) * 3) + np.random.uniform(0, 0.5)
                    data.append({
                        "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                        "Elevasi Air (m)": round(elev, 2), "Critical Elevation (m)": 13.0,
                        "Volume Air Survey (m3)": int(elev * 5000),
                        "Plan Curah Hujan (mm)": np.random.choice([10, 20, 30]), 
                        "Curah Hujan (mm)": np.random.choice([0, 5, 15, 60]),         
                        "Actual Catchment (Ha)": 25.0, 
                        "Status": "BAHAYA" if elev > 13.0 else "AMAN"
                    })
        df_s = pd.DataFrame(data).sort_values(by=["Site", "Pit", "Tanggal"])
        df_s.to_csv(FILE_SUMP, index=False)

    # 2. LOAD DATA POMPA
    if os.path.exists(FILE_POMPA):
        df_p = pd.read_csv(FILE_POMPA)
        df_p['Tanggal'] = pd.to_datetime(df_p['Tanggal'])
    else:
        # Generate Dummy Data Awal
        data_p = []
        today = date.today()
        init_map = {
            "Lais Coal Mine (LCM)": ["Sump Wijaya Barat", "Sump Wijaya Timur"],
            "Wiraduta Sejahtera Langgeng (WSL)": ["Sump F01", "Sump F02"],
            "Nusantara Energy (NE)": ["Sump S8"]
        }
        units = ["WP-01", "WP-02"]
        for i in range(60):
            d = today - timedelta(days=i)
            for site in init_map.keys():
                for pit in init_map[site]:
                    for u in units:
                        data_p.append({
                            "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                            "Unit Code": u, 
                            "Debit Plan (m3/h)": 500, "Debit Actual (m3/h)": np.random.randint(400, 480), 
                            "EWH Plan": 20.0, "EWH Actual": round(np.random.uniform(15, 22), 1)
                        })
        df_p = pd.DataFrame(data_p)
        df_p.to_csv(FILE_POMPA, index=False)

    return df_s, df_p

# --- 3. INITIALIZE SESSION STATE ---
if 'data_sump' not in st.session_state or 'data_pompa' not in st.session_state:
    df_s, df_p = load_or_init_data()
    st.session_state['data_sump'] = df_s
    st.session_state['data_pompa'] = df_p

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

# Site Map Dynamic
if 'site_map' not in st.session_state:
    existing_sites = st.session_state.data_sump['Site'].unique()
    current_map = {}
    for s in existing_sites:
        pits = st.session_state.data_sump[st.session_state.data_sump['Site'] == s]['Pit'].unique().tolist()
        current_map[s] = pits
    st.session_state['site_map'] = current_map

USERS = {"englcm": "eng123", "engwsl": "eng123", "engne": "eng123", "admin": "eng123"}

# --- 4. SIDEBAR ---
with st.sidebar:
    # --- LOGO HANDLING ---
    logo_filename = "1.bara tama wijaya.jpg"
    
    if os.path.exists(logo_filename):
        st.image(logo_filename, use_container_width=True)
    else:
        # Fallback teks jika gambar belum diupload
        st.markdown("## 🏢 BARA TAMA WIJAYA")
        st.caption("⚠️ Upload file logo ke folder repository agar gambar muncul.")
    
    st.markdown("<h3 style='text-align: center;'>Water Management</h3>", unsafe_allow_html=True)
    st.divider()
    
    if st.session_state['logged_in']:
        st.success(f"👤 Login: {st.session_state['username']}")
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
    else:
        st.info("👀 Mode: View Only")

    st.divider()
    current_sites = list(st.session_state['site_map'].keys())
    selected_site = st.selectbox("📍 Pilih Site", current_sites) if current_sites else None
    
    pit_options = ["All Sumps"]
    if selected_site and selected_site in st.session_state['site_map']: 
        pit_options += st.session_state['site_map'][selected_site]
    selected_pit = st.selectbox("💧 Pilih Sump", pit_options)
    
    st.caption("FILTER WAKTU")
    avail_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True)
    sel_year = st.selectbox("📅 Tahun", avail_years)
    month_map = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
    curr_m = date.today().month
    sel_month_name = st.selectbox("🗓️ Bulan", list(month_map.values()), index=curr_m-1)
    sel_month_int = [k for k,v in month_map.items() if v==sel_month_name][0]

# --- 5. MAIN LOGIC ---
def save_to_csv():
    """Helper to save current state to CSV"""
    st.session_state.data_sump.to_csv(FILE_SUMP, index=False)
    st.session_state.data_pompa.to_csv(FILE_POMPA, index=False)

df_s = st.session_state.data_sump.copy()
df_p = st.session_state.data_pompa.copy()

if selected_site:
    df_s = df_s[df_s['Site'] == selected_site]
    df_p = df_p[df_p['Site'] == selected_site]

if selected_pit != "All Sumps":
    df_s = df_s[df_s['Pit'] == selected_pit]
    df_p = df_p[df_p['Pit'] == selected_pit]

df_s_filt = df_s[(df_s['Tanggal'].dt.year == sel_year) & (df_s['Tanggal'].dt.month == sel_month_int)].sort_values(by="Tanggal")
df_p_filt = df_p[(df_p['Tanggal'].dt.year == sel_year) & (df_p['Tanggal'].dt.month == sel_month_int)].sort_values(by="Tanggal")

# Water Balance Calc
df_p_daily = df_p.copy()
df_p_daily['Volume Out'] = df_p_daily['Debit Actual (m3/h)'] * df_p_daily['EWH Actual']
daily_out = df_p_daily.groupby(['Site', 'Pit', 'Tanggal'])['Volume Out'].sum().reset_index()
df_wb = pd.merge(df_s, daily_out, on=['Site', 'Pit', 'Tanggal'], how='left')
df_wb['Volume Out'] = df_wb['Volume Out'].fillna(0)
df_wb['Volume In (Rain)'] = df_wb['Curah Hujan (mm)'] * df_wb['Actual Catchment (Ha)'] * 10
df_wb = df_wb.sort_values(by=['Site', 'Pit', 'Tanggal'])
df_wb['Volume Kemarin'] = df_wb.groupby(['Site', 'Pit'])['Volume Air Survey (m3)'].shift(1)
df_wb['Volume Teoritis'] = df_wb['Volume Kemarin'] + df_wb['Volume In (Rain)'] - df_wb['Volume Out']
df_wb['Diff Volume'] = df_wb['Volume Air Survey (m3)'] - df_wb['Volume Teoritis']
df_wb['Error %'] = (df_wb['Diff Volume'].abs() / df_wb['Volume Air Survey (m3)']) * 100
df_wb_dash = df_wb[(df_wb['Tanggal'].dt.year == sel_year) & (df_wb['Tanggal'].dt.month == sel_month_int)].sort_values(by="Tanggal")

# --- FUNGSI LOGIN FIX (ANTI ERROR DUPLICATE ID) ---
def render_login_form(unique_key):
    # Menggunakan unique_key agar tidak bentrok antar Tabs
    with st.form(key=f"login_form_{unique_key}"):
        st.subheader("🔒 Area Terbatas")
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if user in USERS and USERS[user] == pwd:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user
                st.rerun()
            else:
                st.error("Gagal Login")

# --- 6. TABS LAYOUT ---
st.markdown(f"## 🏢 Bara Tama Wijaya: {selected_site}")
tab_dash, tab_input, tab_db, tab_admin = st.tabs(["📊 Dashboard", "📝 Input (Admin)", "📂 Database", "⚙️ Setting"])

# TAB 1: DASHBOARD
with tab_dash:
    if df_wb_dash.empty:
        st.warning("⚠️ Data belum tersedia.")
    else:
        last = df_wb_dash.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Elevasi", f"{last['Elevasi Air (m)']} m", f"Crit: {last['Critical Elevation (m)']}")
        c2.metric("Vol Survey", f"{last['Volume Air Survey (m3)']:,.0f}")
        c3.metric("Rain (Act)", f"{df_wb_dash['Curah Hujan (mm)'].sum()} mm")
        clr = "#e74c3c" if last['Status'] == "BAHAYA" else "#27ae60"
        c4.markdown(f"<div style='background-color:{clr};color:white;padding:10px;border-radius:5px;text-align:center;'>{last['Status']}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        # Grafik Sump
        fig_s = go.Figure()
        fig_s.add_trace(go.Bar(x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Air Survey (m3)'], name='Vol', marker_color='#95a5a6', opacity=0.6, yaxis='y2'))
        fig_s.add_trace(go.Scatter(x=df_wb_dash['Tanggal'], y=df_wb_dash['Elevasi Air (m)'], name='Elevasi', line=dict(color='#e67e22', width=3)))
        fig_s.add_trace(go.Scatter(x=df_wb_dash['Tanggal'], y=df_wb_dash['Critical Elevation (m)'], name='Limit', line=dict(color='red', dash='dash')))
        fig_s.update_layout(yaxis2=dict(overlaying='y', side='right', showgrid=False), legend=dict(orientation='h', y=1.1), height=400, margin=dict(t=10))
        st.plotly_chart(fig_s, use_container_width=True)

        # Water Balance
        st.subheader("⚖️ Water Balance")
        wb = last
        w1, w2, w3, w4, w5 = st.columns(5)
        w1.metric("Vol Kemarin", f"{wb['Volume Kemarin']:,.0f}")
        w2.metric("In (Rain)", f"{wb['Volume In (Rain)']:,.0f}")
        w3.metric("Out (Pump)", f"{wb['Volume Out']:,.0f}")
        w4.metric("Teoritis", f"{wb['Volume Teoritis']:,.0f}")
        w5.metric("Actual", f"{wb['Volume Air Survey (m3)']:,.0f}")
        if pd.notna(wb['Error %']) and wb['Error %'] > 5:
            st.error(f"🚨 Selisih Tinggi: {wb['Error %']:.1f}%")
        else:
            st.success(f"✅ Valid (Diff: {wb['Error %']:.1f}%)")

# TAB 2: INPUT
with tab_input:
    if not st.session_state['logged_in']:
        # Panggil fungsi login dengan KUNCI UNIK 'input'
        render_login_form(unique_key="input_tab")
    else:
        st.info("💾 Setiap data yang disimpan akan otomatis ditulis ke file CSV (Permanen).")
        
        # ADD NEW
        with st.expander("➕ Input Harian Baru", expanded=True):
            with st.container():
                d_in = st.date_input("Tanggal", date.today())
                p_in = st.selectbox("Sump", st.session_state['site_map'].get(selected_site, []), key="pi")
                
            cl, cr = st.columns(2)
            with cl:
                with st.form("fs"):
                    st.markdown("**Sump Data**")
                    c1, c2 = st.columns(2)
                    e_a = c1.number_input("Elevasi", format="%.2f")
                    v_a = c2.number_input("Volume", step=100)
                    r_p = c1.number_input("Rain Plan", 0.0)
                    r_a = c2.number_input("Rain Act", 0.0)
                    if st.form_submit_button("Simpan Sump"):
                        new = {
                            "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                            "Elevasi Air (m)": e_a, "Critical Elevation (m)": 13.0,
                            "Volume Air Survey (m3)": v_a, "Plan Curah Hujan (mm)": r_p,
                            "Curah Hujan (mm)": r_a, "Actual Catchment (Ha)": 25.0,
                            "Status": "BAHAYA" if e_a > 13 else "AMAN"
                        }
                        st.session_state.data_sump = pd.concat([pd.DataFrame([new]), st.session_state.data_sump], ignore_index=True)
                        save_to_csv()
                        st.success("Tersimpan!")
            with cr:
                with st.form("fp"):
                    st.markdown("**Pompa Data**")
                    uc = st.text_input("Unit Code")
                    da = st.number_input("Debit Act", 0)
                    ea = st.number_input("EWH Act", 0.0)
                    if st.form_submit_button("Simpan Pompa"):
                        newp = {
                            "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                            "Unit Code": uc, "Debit Plan (m3/h)": 500, "Debit Actual (m3/h)": da,
                            "EWH Plan": 20.0, "EWH Actual": ea
                        }
                        st.session_state.data_pompa = pd.concat([pd.DataFrame([newp]), st.session_state.data_pompa], ignore_index=True)
                        save_to_csv()
                        st.success("Tersimpan!")

        st.divider()
        # EDIT MODE
        t_es, t_ep = st.tabs(["Edit Sump", "Edit Pompa"])
        with t_es:
            edt_s = st.data_editor(st.session_state.data_sump[st.session_state.data_sump['Site']==selected_site], num_rows="dynamic", key="ed_s")
            if st.button("Simpan Perubahan Sump"):
                base = st.session_state.data_sump[st.session_state.data_sump['Site']!=selected_site]
                st.session_state.data_sump = pd.concat([base, edt_s], ignore_index=True)
                save_to_csv()
                st.success("Updated & Saved!")
                st.rerun()
        with t_ep:
            edt_p = st.data_editor(st.session_state.data_pompa[st.session_state.data_pompa['Site']==selected_site], num_rows="dynamic", key="ed_p")
            if st.button("Simpan Perubahan Pompa"):
                base = st.session_state.data_pompa[st.session_state.data_pompa['Site']!=selected_site]
                st.session_state.data_pompa = pd.concat([base, edt_p], ignore_index=True)
                save_to_csv()
                st.success("Updated & Saved!")
                st.rerun()

# TAB 3: DOWNLOAD
with tab_db:
    st.subheader("📂 Download & Backup")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Download CSV Sump", st.session_state.data_sump.to_csv(index=False).encode('utf-8'), "db_sump.csv", "text/csv")
        st.dataframe(st.session_state.data_sump.head())
    with c2:
        st.download_button("⬇️ Download CSV Pompa", st.session_state.data_pompa.to_csv(index=False).encode('utf-8'), "db_pompa.csv", "text/csv")
        st.dataframe(st.session_state.data_pompa.head())

# TAB 4: SETTING
with tab_admin:
    if not st.session_state['logged_in']:
        # Panggil fungsi login dengan KUNCI UNIK 'admin'
        render_login_form(unique_key="admin_tab")
    else:
        st.write("⚙️ Pengaturan Site")
        ns = st.text_input("Tambah Site Baru")
        if st.button("Add Site"):
            if ns and ns not in st.session_state['site_map']:
                st.session_state['site_map'][ns] = []
                st.success(f"Site {ns} added")
