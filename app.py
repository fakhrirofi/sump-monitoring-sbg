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

# Agar Data Dummy STABIL
np.random.seed(42)

# CSS Styling
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e0e0e0;
        padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .analysis-box {
        background-color: #e8f6f3; padding: 15px; border-radius: 10px; border-left: 5px solid #1abc9c;
    }
    .rec-box {
        background-color: #fef9e7; padding: 15px; border-radius: 10px; border-left: 5px solid #f1c40f;
    }
    .danger-box {
        background-color: #fdedec; padding: 15px; border-radius: 10px; border-left: 5px solid #e74c3c;
    }
    .wb-alert {
        background-color: #ffcccc; color: #cc0000; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 10px; border: 1px solid #ff0000;
    }
    .date-header {
        font-size: 1.2rem; font-weight: bold; color: #2c3e50; margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FILE MANAGEMENT SYSTEM (V10) ---
FILE_SUMP = "db_sump_v10.csv"   
FILE_POMPA = "db_pompa_v10.csv"

def load_or_init_data():
    # 1. LOAD DATA SUMP
    if os.path.exists(FILE_SUMP):
        df_s = pd.read_csv(FILE_SUMP)
        df_s['Tanggal'] = pd.to_datetime(df_s['Tanggal'])
    else:
        # Generate Dummy Data
        data = []
        today = date.today()
        init_map = {
            "Lais Coal Mine (LCM)": ["Sump Wijaya Barat", "Sump Wijaya Timur"],
            "Wiraduta Sejahtera Langgeng (WSL)": ["Sump F01", "Sump F02"],
            "Nusantara Energy (NE)": ["Sump S8"]
        }
        for i in range(30): # 30 Hari terakhir
            d = today - timedelta(days=i)
            for site in init_map.keys():
                for pit in init_map[site]:
                    elev = 10.0 + (np.sin(i/10) * 2) 
                    data.append({
                        "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                        "Elevasi Air (m)": round(elev, 2), "Critical Elevation (m)": 13.0,
                        "Volume Air Survey (m3)": int(elev * 5000),
                        "Plan Curah Hujan (mm)": 20.0, 
                        "Curah Hujan (mm)": np.random.randint(0, 40),      
                        "Actual Catchment (Ha)": 25.0,
                        "Groundwater (m3)": 0.0, # Kolom Baru
                        "Status": "BAHAYA" if elev > 13.0 else "AMAN"
                    })
        df_s = pd.DataFrame(data).sort_values(by=["Site", "Pit", "Tanggal"])
        df_s.to_csv(FILE_SUMP, index=False)

    # 2. LOAD DATA POMPA
    if os.path.exists(FILE_POMPA):
        df_p = pd.read_csv(FILE_POMPA)
        df_p['Tanggal'] = pd.to_datetime(df_p['Tanggal'])
    else:
        data_p = []
        today = date.today()
        init_map = {
            "Lais Coal Mine (LCM)": ["Sump Wijaya Barat", "Sump Wijaya Timur"],
            "Wiraduta Sejahtera Langgeng (WSL)": ["Sump F01", "Sump F02"],
            "Nusantara Energy (NE)": ["Sump S8"]
        }
        units = ["WP-01", "WP-02"] 
        for i in range(30):
            d = today - timedelta(days=i)
            for site in init_map.keys():
                for pit in init_map[site]:
                    for u in units:
                        data_p.append({
                            "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                            "Unit Code": u, 
                            "Debit Plan (m3/h)": 500, # Default Plan
                            "Debit Actual (m3/h)": np.random.randint(400, 500), 
                            "EWH Plan": 20.0, 
                            "EWH Actual": round(np.random.uniform(15, 20), 1)
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
    # --- LOGO HANDLING (RESTORED) ---
    logo_filename = "1.bara tama wijaya.jpg"
    if os.path.exists(logo_filename):
        st.image(logo_filename, use_container_width=True)
    else:
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

    # UNIT SELECTION
    unit_options = ["All Units"]
    if selected_pit != "All Sumps":
        raw_p = st.session_state.data_pompa
        avail_units_list = raw_p[(raw_p['Site'] == selected_site) & (raw_p['Pit'] == selected_pit)]['Unit Code'].unique().tolist()
        avail_units_list.sort()
        unit_options += avail_units_list
    selected_unit = st.selectbox("🚜 Pilih Unit Pompa", unit_options)
    
    st.caption("FILTER WAKTU")
    avail_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True)
    sel_year = st.selectbox("📅 Tahun", avail_years)
    month_map = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
    curr_m = date.today().month
    sel_month_name = st.selectbox("🗓️ Bulan", list(month_map.values()), index=curr_m-1)
    sel_month_int = [k for k,v in month_map.items() if v==sel_month_name][0]

# --- 5. MAIN LOGIC (WATER BALANCE CALC) ---
def save_to_csv():
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

# 1. Prepare Data for Pump Graph
if selected_unit != "All Units":
    df_p_display = df_p_filt[df_p_filt['Unit Code'] == selected_unit].sort_values(by="Tanggal")
    title_suffix = f"Unit: {selected_unit}"
else:
    df_p_display = df_p_filt.groupby('Tanggal')[['Debit Plan (m3/h)', 'Debit Actual (m3/h)', 'EWH Plan', 'EWH Actual']].mean().reset_index()
    title_suffix = "Rata-rata Semua Unit"

# 2. WATER BALANCE CALCULATION (Termasuk Groundwater)
df_p_total = df_p_filt.copy()
df_p_total['Volume Out'] = df_p_total['Debit Actual (m3/h)'] * df_p_total['EWH Actual']
daily_out = df_p_total.groupby(['Site', 'Pit', 'Tanggal'])['Volume Out'].sum().reset_index()

df_wb = pd.merge(df_s_filt, daily_out, on=['Site', 'Pit', 'Tanggal'], how='left')
df_wb['Volume Out'] = df_wb['Volume Out'].fillna(0)

# Inflow: Rain & Groundwater
df_wb['Volume In (Rain)'] = df_wb['Curah Hujan (mm)'] * df_wb['Actual Catchment (Ha)'] * 10
df_wb['Volume In (GW)'] = df_wb['Groundwater (m3)'].fillna(0)

df_wb = df_wb.sort_values(by="Tanggal")
df_wb['Volume Kemarin'] = df_wb['Volume Air Survey (m3)'].shift(1)

# RUMUS WATER BALANCE UPDATE
df_wb['Volume Teoritis'] = df_wb['Volume Kemarin'] + df_wb['Volume In (Rain)'] + df_wb['Volume In (GW)'] - df_wb['Volume Out']
df_wb['Diff Volume'] = df_wb['Volume Air Survey (m3)'] - df_wb['Volume Teoritis']
df_wb['Error %'] = (df_wb['Diff Volume'].abs() / df_wb['Volume Air Survey (m3)']) * 100
df_wb_dash = df_wb 

# --- FUNGSI LOGIN ---
def render_login_form(unique_key):
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

# --- 6. DISPLAY TABS ---
st.markdown(f"## 🏢 Bara Tama Wijaya: {selected_site}")

tab_dash, tab_input, tab_db, tab_admin = st.tabs(["📊 Dashboard", "📝 Input (Admin)", "📂 Database", "⚙️ Setting"])

# TAB 1: DASHBOARD
with tab_dash:
    if df_wb_dash.empty:
        st.warning("⚠️ Data belum tersedia untuk filter ini.")
    else:
        last = df_wb_dash.iloc[-1]
        
        # --- HEADER TANGGAL HARI INI ---
        st.markdown(f"<div class='date-header'>📅 Dashboard Status per Tanggal: {last['Tanggal'].strftime('%d %B %Y')}</div>", unsafe_allow_html=True)

        # --- METRICS SECTION ---
        c1, c2, c3, c4, c5 = st.columns(5)
        
        c1.metric("Elevasi Air", f"{last['Elevasi Air (m)']} m", f"Crit: {last['Critical Elevation (m)']}")
        c2.metric("Vol Survey", f"{last['Volume Air Survey (m3)']:,.0f} m³")
        
        # RAINFALL TODAY VS MTD
        rain_today = last['Curah Hujan (mm)']
        rain_mtd = df_wb_dash['Curah Hujan (mm)'].sum()
        c3.metric("Rain Today", f"{rain_today} mm")
        c4.metric("Rain MTD", f"{rain_mtd} mm")
        
        status_txt = "AMAN"; clr = "#27ae60"
        if last['Status'] == "BAHAYA": clr = "#e74c3c"; status_txt = "BAHAYA"
        c5.markdown(f"<div style='background-color:{clr};color:white;padding:20px;border-radius:5px;text-align:center;font-weight:bold;'>{status_txt}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- 1. WATER BALANCE & RAINFALL ANALYSIS ---
        st.subheader("⚖️ Water Balance & Rainfall Analysis")
        
        last_error = last['Error %']
        is_wb_critical = False
        if last_error > 5.0 or pd.isna(last_error):
            is_wb_critical = True
            st.markdown(f"""
            <div class="wb-alert">
                ⚠️ PERINGATAN WATER BALANCE: Error {last_error:.1f}% (Melebihi Toleransi 5%)<br>
                Selisih Volume: {last['Diff Volume']:,.0f} m³
            </div>
            """, unsafe_allow_html=True)
        
        col_wb1, col_wb2 = st.columns(2)
        
        with col_wb1:
            # CHART RAINFALL PLAN VS ACTUAL
            fig_rain = go.Figure()
            fig_rain.add_trace(go.Bar(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Curah Hujan (mm)'], 
                name='Act Rain (mm)', marker_color='#3498db',
                text=df_wb_dash['Curah Hujan (mm)'], textposition='auto'
            ))
            fig_rain.add_trace(go.Scatter(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Plan Curah Hujan (mm)'], 
                name='Plan Rain (mm)', mode='lines+markers',
                line=dict(color='#e74c3c', dash='dot')
            ))
            fig_rain.update_layout(title="Rainfall: Plan vs Actual (mm)", height=350, margin=dict(t=30), legend=dict(orientation='h', y=1.1))
            st.plotly_chart(fig_rain, use_container_width=True)

        with col_wb2:
            # CHART WATER BALANCE
            fig_wb = go.Figure()
            # Stacked Inflow
            fig_wb.add_trace(go.Bar(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume In (Rain)'], 
                name='In (Rain)', marker_color='#3498db'
            ))
            fig_wb.add_trace(go.Bar(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume In (GW)'], 
                name='In (Groundwater)', marker_color='#9b59b6'
            ))
            # Outflow - LABEL "TOTAL ALL PUMPS"
            fig_wb.add_trace(go.Bar(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Out'], 
                name='Out (Total All Pumps)', marker_color='#e74c3c',
                text=df_wb_dash['Volume Out'], texttemplate='%{text:.0f}', textposition='auto'
            ))
            fig_wb.update_layout(title="Volume Flow (m³): In vs Out", barmode='group', height=350, margin=dict(t=30), legend=dict(orientation='h', y=1.1))
            st.plotly_chart(fig_wb, use_container_width=True)
            
        # TABEL VALIDASI
        with st.expander("📋 Lihat Detail Angka Water Balance"):
            df_show = df_wb_dash[['Tanggal', 'Volume Air Survey (m3)', 'Volume Teoritis', 'Diff Volume', 'Error %']].copy()
            df_show['Tanggal'] = df_show['Tanggal'].dt.strftime('%d-%m-%Y')
            st.dataframe(df_show.style.format({'Volume Air Survey (m3)': '{:,.0f}','Volume Teoritis': '{:,.0f}', 'Diff Volume': '{:,.0f}','Error %': '{:.1f}%'}), hide_index=True, use_container_width=True)

        # --- 2. GRAFIK ELEVASI ---
        st.markdown("---")
        st.subheader("🌊 Tren Elevasi Sump")
        fig_s = go.Figure()
        fig_s.add_trace(go.Bar(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Air Survey (m3)'], name='Vol', 
            marker_color='#95a5a6', opacity=0.3, yaxis='y2'
        ))
        fig_s.add_trace(go.Scatter(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Elevasi Air (m)'], name='Elevasi', 
            mode='lines+markers+text',
            line=dict(color='#e67e22', width=3),
            text=df_wb_dash['Elevasi Air (m)'], texttemplate='%{text:.2f}', textposition='top center'
        ))
        fig_s.add_trace(go.Scatter(x=df_wb_dash['Tanggal'], y=df_wb_dash['Critical Elevation (m)'], name='Limit', line=dict(color='red', dash='dash')))
        fig_s.update_layout(
            yaxis2=dict(overlaying='y', side='right', showgrid=False, title="Volume (m3)"),
            yaxis=dict(title="Elevasi (m)"), legend=dict(orientation='h', y=1.1), height=400, margin=dict(t=30)
        )
        st.plotly_chart(fig_s, use_container_width=True)

        # --- 3. PERFORMA POMPA ---
        st.markdown("---")
        st.subheader(f"⚙️ Performa Pompa ({title_suffix})")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.caption(f"**Debit: Plan vs Actual (m3/h)**")
            fig_d = go.Figure()
            fig_d.add_trace(go.Bar(
                x=df_p_display['Tanggal'], y=df_p_display['Debit Actual (m3/h)'], name='Act', marker_color='#2ecc71',
                text=df_p_display['Debit Actual (m3/h)'], texttemplate='%{text:.0f}', textposition='auto'
            ))
            fig_d.add_trace(go.Scatter(x=df_p_display['Tanggal'], y=df_p_display['Debit Plan (m3/h)'], name='Plan', line=dict(color='#2c3e50', dash='dash')))
            fig_d.update_layout(legend=dict(orientation='h', y=1.1), height=300, margin=dict(t=20))
            st.plotly_chart(fig_d, use_container_width=True)
        with col_p2:
            st.caption(f"**EWH: Plan vs Actual (Jam)**")
            fig_e = go.Figure()
            fig_e.add_trace(go.Bar(
                x=df_p_display['Tanggal'], y=df_p_display['EWH Actual'], name='Act', marker_color='#d35400',
                text=df_p_display['EWH Actual'], texttemplate='%{text:.1f}', textposition='auto'
            ))
            fig_e.add_trace(go.Scatter(x=df_p_display['Tanggal'], y=df_p_display['EWH Plan'], name='Plan', line=dict(color='#2c3e50', dash='dash')))
            fig_e.update_layout(legend=dict(orientation='h', y=1.1), height=300, margin=dict(t=20))
            st.plotly_chart(fig_e, use_container_width=True)

        # --- 4. ANALISA & REKOMENDASI ---
        st.markdown("---")
        st.subheader("🧠 Analisa & Rekomendasi")
        
        col_an, col_rec = st.columns(2)
        if is_wb_critical:
            style_box = "danger-box"; header_text = "🚨 PERINGATAN: DATA TIDAK BALANCE"
        elif last['Elevasi Air (m)'] >= last['Critical Elevation (m)']:
            style_box = "danger-box"; header_text = "🚨 BAHAYA: ELEVASI TINGGI"
        else:
            style_box = "analysis-box"; header_text = "✅ KONDISI AMAN"

        with col_an:
            st.markdown(f"""
            <div class="{style_box}">
                <h4>{header_text}</h4>
                <ul>
                    <li><b>Status Water Balance:</b> Error {last_error:.1f}%.</li>
                    <li><b>Curah Hujan Hari Ini:</b> {rain_today} mm.</li>
                    <li><b>Status Elevasi:</b> {last['Elevasi Air (m)']} m.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_rec:
            st.markdown('<div class="rec-box"><h4>🛠️ REKOMENDASI</h4>', unsafe_allow_html=True)
            rec_list = []
            
            # REKOMENDASI WATER BALANCE
            if is_wb_critical:
                rec_list.append("🔴 <b>CEK INPUT DATA (HUMAN ERROR):</b> Pastikan angka Elevasi, Debit, dan Hujan yang diinput sudah benar.")
                rec_list.append("🔴 <b>Cek Groundwater:</b> Apakah ada air tanah/rembesan besar yang belum diinput di kolom Groundwater?")
                rec_list.append("🔴 <b>Cek Debit Pompa:</b> Verifikasi flowmeter pompa.")
            
            if last['Elevasi Air (m)'] >= last['Critical Elevation (m)']:
                rec_list.append("⛔ <b>STOP OPERASI & EVAKUASI UNIT.</b>")
            
            if not rec_list: st.markdown("- ✅ Data Valid & Operasi Aman.")
            for r in rec_list: st.markdown(f"- {r}", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: INPUT
with tab_input:
    if not st.session_state['logged_in']:
        render_login_form(unique_key="input_tab")
    else:
        st.info("Input Data Harian")
        with st.expander("➕ Input Harian Baru", expanded=True):
            d_in = st.date_input("Tanggal", date.today())
            p_in = st.selectbox("Sump", st.session_state['site_map'].get(selected_site, []), key="pi")
            
            cl, cr = st.columns(2)
            with cl:
                with st.form("fs"):
                    st.markdown("<b>Data Sump, Hujan & Groundwater</b>", unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    e_a = c1.number_input("Elevasi (m)", format="%.2f")
                    v_a = c2.number_input("Volume Survey (m3)", step=100)
                    r_p = c1.number_input("Rain Plan (mm)", value=20.0)
                    r_a = c2.number_input("Rain Act (mm)", 0.0)
                    gw_v = st.number_input("Groundwater/Seepage Volume (m3)", 0.0, help="Air masuk selain hujan")
                    
                    if st.form_submit_button("Simpan Sump"):
                        new = {
                            "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                            "Elevasi Air (m)": e_a, "Critical Elevation (m)": 13.0,
                            "Volume Air Survey (m3)": v_a, "Plan Curah Hujan (mm)": r_p,
                            "Curah Hujan (mm)": r_a, "Actual Catchment (Ha)": 25.0,
                            "Groundwater (m3)": gw_v,
                            "Status": "BAHAYA" if e_a > 13 else "AMAN"
                        }
                        st.session_state.data_sump = pd.concat([pd.DataFrame([new]), st.session_state.data_sump], ignore_index=True)
                        save_to_csv(); st.success("Sump Saved!")
            with cr:
                with st.form("fp"):
                    st.markdown("<b>Data Pompa (Plan vs Act)</b>", unsafe_allow_html=True)
                    uc = st.text_input("Unit Code (e.g., WP-01)")
                    c_dp, c_da = st.columns(2)
                    dp = c_dp.number_input("Debit Plan (m3/h)", value=500)
                    da = c_da.number_input("Debit Actual (m3/h)", 0)
                    ea = st.number_input("EWH Actual (Jam)", 0.0)
                    if st.form_submit_button("Simpan Pompa"):
                        newp = {
                            "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                            "Unit Code": uc, "Debit Plan (m3/h)": dp, "Debit Actual (m3/h)": da,
                            "EWH Plan": 20.0, "EWH Actual": ea
                        }
                        st.session_state.data_pompa = pd.concat([pd.DataFrame([newp]), st.session_state.data_pompa], ignore_index=True)
                        save_to_csv(); st.success("Pompa Saved!")

        st.divider()
        t1, t2 = st.tabs(["Edit Sump", "Edit Pompa"])
        with t1:
            ed_s = st.data_editor(st.session_state.data_sump[st.session_state.data_sump['Site']==selected_site], num_rows="dynamic", key="es")
            if st.button("Save Sump Changes"):
                st.session_state.data_sump = pd.concat([st.session_state.data_sump[st.session_state.data_sump['Site']!=selected_site], ed_s], ignore_index=True)
                save_to_csv(); st.rerun()
        with t2:
            ed_p = st.data_editor(st.session_state.data_pompa[st.session_state.data_pompa['Site']==selected_site], num_rows="dynamic", key="ep")
            if st.button("Save Pump Changes"):
                st.session_state.data_pompa = pd.concat([st.session_state.data_pompa[st.session_state.data_pompa['Site']!=selected_site], ed_p], ignore_index=True)
                save_to_csv(); st.rerun()

# TAB 3 & 4 (Database & Admin)
with tab_db:
    c1, c2 = st.columns(2)
    c1.download_button("Download Sump CSV", st.session_state.data_sump.to_csv(index=False), "sump_v10.csv")
    c2.download_button("Download Pompa CSV", st.session_state.data_pompa.to_csv(index=False), "pompa_v10.csv")
    st.dataframe(st.session_state.data_sump)

with tab_admin:
    if st.session_state['logged_in']:
        ns = st.text_input("New Site Name")
        if st.button("Add Site") and ns: st.session_state['site_map'][ns] = []
    else: render_login_form("adm")
