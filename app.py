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
    .stAlert { font-weight: bold; border: 1px solid #ddd; }
    section[data-testid="stSidebar"] { background-color: #ffffff; }
    .analysis-box {
        background-color: #e8f6f3; padding: 15px; border-radius: 10px; border-left: 5px solid #1abc9c;
    }
    .rec-box {
        background-color: #fef9e7; padding: 15px; border-radius: 10px; border-left: 5px solid #f1c40f;
    }
    .danger-box {
        background-color: #fdedec; padding: 15px; border-radius: 10px; border-left: 5px solid #e74c3c;
    }
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
        units = ["WP-01", "WP-02", "WP-03"] # Tambah unit dummy
        for i in range(60):
            d = today - timedelta(days=i)
            for site in init_map.keys():
                for pit in init_map[site]:
                    for u in units:
                        data_p.append({
                            "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                            "Unit Code": u, 
                            "Debit Plan (m3/h)": 500, "Debit Actual (m3/h)": np.random.randint(350, 520), 
                            "EWH Plan": 20.0, "EWH Actual": round(np.random.uniform(10, 22), 1)
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
    avail_units_list = []
    
    if selected_site and selected_site in st.session_state['site_map']: 
        pit_options += st.session_state['site_map'][selected_site]
    selected_pit = st.selectbox("💧 Pilih Sump", pit_options)

    # --- NEW: UNIT SELECTION ---
    unit_options = ["All Units"]
    if selected_pit != "All Sumps":
        # Ambil unit yang tersedia di Pit tersebut
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

# --- 5. MAIN LOGIC ---
def save_to_csv():
    st.session_state.data_sump.to_csv(FILE_SUMP, index=False)
    st.session_state.data_pompa.to_csv(FILE_POMPA, index=False)

df_s = st.session_state.data_sump.copy()
df_p = st.session_state.data_pompa.copy()

# Filter Base Data
if selected_site:
    df_s = df_s[df_s['Site'] == selected_site]
    df_p = df_p[df_p['Site'] == selected_site]

if selected_pit != "All Sumps":
    df_s = df_s[df_s['Pit'] == selected_pit]
    df_p = df_p[df_p['Pit'] == selected_pit]

df_s_filt = df_s[(df_s['Tanggal'].dt.year == sel_year) & (df_s['Tanggal'].dt.month == sel_month_int)].sort_values(by="Tanggal")
df_p_filt = df_p[(df_p['Tanggal'].dt.year == sel_year) & (df_p['Tanggal'].dt.month == sel_month_int)].sort_values(by="Tanggal")

# --- DATA PREPARATION FOR GRAPHS (UNIT FILTERING) ---
# Untuk Grafik Pompa, kita filter berdasarkan Unit yang dipilih
if selected_unit != "All Units":
    df_p_display = df_p_filt[df_p_filt['Unit Code'] == selected_unit].sort_values(by="Tanggal")
    # Tidak perlu mean() karena sudah spesifik per unit per hari
    title_suffix = f"Unit: {selected_unit}"
else:
    # Jika All Units, kita ambil rata-rata harian dari semua unit
    df_p_display = df_p_filt.groupby('Tanggal')[['Debit Plan (m3/h)', 'Debit Actual (m3/h)', 'EWH Plan', 'EWH Actual']].mean().reset_index()
    title_suffix = "Rata-rata Semua Unit"

# --- WATER BALANCE CALCULATION (ALWAYS ALL UNITS) ---
# Water balance harus menghitung TOTAL volume keluar dari SEMUA pompa, tidak boleh difilter per unit
df_p_total = df_p_filt.copy()
df_p_total['Volume Out'] = df_p_total['Debit Actual (m3/h)'] * df_p_total['EWH Actual']
daily_out = df_p_total.groupby(['Site', 'Pit', 'Tanggal'])['Volume Out'].sum().reset_index()

df_wb = pd.merge(df_s_filt, daily_out, on=['Site', 'Pit', 'Tanggal'], how='left')
df_wb['Volume Out'] = df_wb['Volume Out'].fillna(0)
df_wb['Volume In (Rain)'] = df_wb['Curah Hujan (mm)'] * df_wb['Actual Catchment (Ha)'] * 10
df_wb = df_wb.sort_values(by="Tanggal")
df_wb['Volume Kemarin'] = df_wb['Volume Air Survey (m3)'].shift(1)
df_wb['Volume Teoritis'] = df_wb['Volume Kemarin'] + df_wb['Volume In (Rain)'] - df_wb['Volume Out']
df_wb['Diff Volume'] = df_wb['Volume Air Survey (m3)'] - df_wb['Volume Teoritis']
df_wb['Error %'] = (df_wb['Diff Volume'].abs() / df_wb['Volume Air Survey (m3)']) * 100
df_wb_dash = df_wb # Data for dashboard

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

# --- 6. TABS LAYOUT ---
st.markdown(f"## 🏢 Bara Tama Wijaya: {selected_site}")
tab_dash, tab_input, tab_db, tab_admin = st.tabs(["📊 Dashboard", "📝 Input (Admin)", "📂 Database", "⚙️ Setting"])

# TAB 1: DASHBOARD
with tab_dash:
    if df_wb_dash.empty:
        st.warning("⚠️ Data belum tersedia.")
    else:
        last = df_wb_dash.iloc[-1]
        
        # METRICS
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Elevasi", f"{last['Elevasi Air (m)']} m", f"Crit: {last['Critical Elevation (m)']}")
        c2.metric("Vol Survey", f"{last['Volume Air Survey (m3)']:,.0f}")
        c3.metric("Rain (Act)", f"{df_wb_dash['Curah Hujan (mm)'].sum()} mm")
        clr = "#e74c3c" if last['Status'] == "BAHAYA" else "#27ae60"
        c4.markdown(f"<div style='background-color:{clr};color:white;padding:10px;border-radius:5px;text-align:center;'>{last['Status']}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 1. GRAFIK ELEVASI & VOLUME
        st.subheader("🌊 Tren Elevasi & Volume Sump")
        fig_s = go.Figure()
        fig_s.add_trace(go.Bar(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Air Survey (m3)'], name='Vol', 
            marker_color='#95a5a6', opacity=0.6, yaxis='y2',
            text=df_wb_dash['Volume Air Survey (m3)'], texttemplate='%{text:.2s}', textposition='inside'
        ))
        fig_s.add_trace(go.Scatter(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Elevasi Air (m)'], name='Elevasi', mode='lines+markers+text',
            line=dict(color='#e67e22', width=3),
            text=df_wb_dash['Elevasi Air (m)'], texttemplate='%{text:.2f}', textposition='top center'
        ))
        fig_s.add_trace(go.Scatter(x=df_wb_dash['Tanggal'], y=df_wb_dash['Critical Elevation (m)'], name='Limit', line=dict(color='red', dash='dash')))
        fig_s.update_layout(
            yaxis2=dict(overlaying='y', side='right', showgrid=False, title="Volume (m3)"),
            yaxis=dict(title="Elevasi (m)"), legend=dict(orientation='h', y=1.1), height=450, margin=dict(t=30)
        )
        st.plotly_chart(fig_s, use_container_width=True)

        # 2. GRAFIK CURAH HUJAN
        st.subheader("🌧️ Curah Hujan: Plan vs Actual")
        fig_r = go.Figure()
        fig_r.add_trace(go.Bar(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Curah Hujan (mm)'], name='Actual', marker_color='#3498db',
            text=df_wb_dash['Curah Hujan (mm)'], textposition='auto'
        ))
        fig_r.add_trace(go.Scatter(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Plan Curah Hujan (mm)'], name='Plan', mode='lines+markers',
            line=dict(color='#e74c3c', width=2, dash='dot')
        ))
        fig_r.update_layout(yaxis=dict(title="Curah Hujan (mm)"), legend=dict(orientation='h', y=1.1), height=350, margin=dict(t=20))
        st.plotly_chart(fig_r, use_container_width=True)

        # 3. GRAFIK POMPA (DYNAMIC UNIT)
        st.markdown("---")
        st.subheader(f"⚙️ Performa Pompa ({title_suffix})")
        
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            st.caption(f"**Debit: Plan vs Actual (m3/h) - {selected_unit}**")
            fig_d = go.Figure()
            fig_d.add_trace(go.Bar(
                x=df_p_display['Tanggal'], y=df_p_display['Debit Actual (m3/h)'], name='Act Debit', marker_color='#2ecc71',
                text=df_p_display['Debit Actual (m3/h)'], texttemplate='%{text:.0f}', textposition='auto'
            ))
            fig_d.add_trace(go.Scatter(
                x=df_p_display['Tanggal'], y=df_p_display['Debit Plan (m3/h)'], name='Plan Debit', mode='lines',
                line=dict(color='#2c3e50', width=2, dash='dash')
            ))
            fig_d.update_layout(legend=dict(orientation='h', y=1.1), height=300, margin=dict(t=20))
            st.plotly_chart(fig_d, use_container_width=True)
            
        with col_p2:
            st.caption(f"**EWH: Plan vs Actual (Jam) - {selected_unit}**")
            fig_e = go.Figure()
            fig_e.add_trace(go.Bar(
                x=df_p_display['Tanggal'], y=df_p_display['EWH Actual'], name='Act EWH', marker_color='#d35400',
                text=df_p_display['EWH Actual'], texttemplate='%{text:.1f}', textposition='auto'
            ))
            fig_e.add_trace(go.Scatter(
                x=df_p_display['Tanggal'], y=df_p_display['EWH Plan'], name='Plan EWH', mode='lines',
                line=dict(color='#2c3e50', width=2, dash='dash')
            ))
            fig_e.update_layout(legend=dict(orientation='h', y=1.1), height=300, margin=dict(t=20))
            st.plotly_chart(fig_e, use_container_width=True)

        # 4. ANALISA & REKOMENDASI
        st.markdown("---")
        st.subheader("🧠 Analisa & Rekomendasi Cerdas")
        
        last_date = last['Tanggal']
        last_elev = last['Elevasi Air (m)']
        crit_elev = last['Critical Elevation (m)']
        last_rain = last['Curah Hujan (mm)']
        
        # Analisa Pompa (Specific Unit / Average)
        last_pump_data = df_p_display[df_p_display['Tanggal'] == last_date]
        if not last_pump_data.empty:
            avg_debit_act = last_pump_data['Debit Actual (m3/h)'].mean()
            avg_debit_plan = last_pump_data['Debit Plan (m3/h)'].mean()
            avg_ewh_act = last_pump_data['EWH Actual'].mean()
            avg_ewh_plan = last_pump_data['EWH Plan'].mean()
        else:
            avg_debit_act = 0; avg_debit_plan = 500; avg_ewh_act = 0; avg_ewh_plan = 20

        col_an, col_rec = st.columns(2)
        
        with col_an:
            if last_elev >= crit_elev:
                style_box = "danger-box"; header_text = "🚨 KONDISI KRITIS (BAHAYA)"
            elif last_elev >= (crit_elev - 1.0):
                style_box = "rec-box"; header_text = "⚠️ KONDISI WARNING (SIAGA)"
            else:
                style_box = "analysis-box"; header_text = "✅ KONDISI AMAN"
            
            content_html = f"""
            <div class="{style_box}">
                <h4>{header_text}</h4>
                <ul>
                    <li><b>Status Level Air:</b> Saat ini elevasi {last_elev} m (Limit: {crit_elev} m).</li>
            """
            if last_rain > 50:
                content_html += f"<li><b>Curah Hujan Tinggi:</b> Terjadi hujan deras ({last_rain} mm).</li>"
            
            debit_eff = (avg_debit_act / avg_debit_plan) * 100 if avg_debit_plan > 0 else 0
            unit_text = "Unit ini" if selected_unit != "All Units" else "Rata-rata Unit"
            if debit_eff < 80:
                content_html += f"<li><b>Performa {unit_text} Rendah:</b> Efisiensi Debit hanya {debit_eff:.1f}%.</li>"
            else:
                content_html += f"<li><b>Performa {unit_text} Baik:</b> Efisiensi Debit {debit_eff:.1f}%.</li>"
            content_html += "</ul></div>"
            st.markdown(content_html, unsafe_allow_html=True)

        with col_rec:
            st.markdown('<div class="rec-box"><h4>🛠️ REKOMENDASI ENGINEERING</h4>', unsafe_allow_html=True)
            rec_list = []
            if last_elev >= crit_elev:
                rec_list.append("⛔ <b>STOP OPERASI</b> di area pit terdampak. Lakukan evakuasi unit.")
                rec_list.append("🚀 <b>Maksimalkan Pompa:</b> Nyalakan semua unit pompa yang standby.")
            elif last_elev >= (crit_elev - 1.0):
                rec_list.append("👀 <b>Monitor Ketat:</b> Cek elevasi setiap 1 jam.")
            
            if avg_debit_act < (avg_debit_plan * 0.85):
                rec_list.append(f"🔧 <b>Cek {selected_unit}:</b> Debit rendah. Periksa RPM, impeller, atau kebocoran.")
            
            if avg_ewh_act < (avg_ewh_plan - 2) and last_elev > (crit_elev - 2):
                rec_list.append("⏳ <b>Tingkatkan Jam Jalan:</b> Kurangi waktu standby/delay.")

            if not rec_list:
                rec_list.append("✅ <b>Pertahankan Operasi:</b> Kondisi aman.")
            
            for rec in rec_list:
                st.markdown(f"- {rec}", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: INPUT
with tab_input:
    if not st.session_state['logged_in']:
        render_login_form(unique_key="input_tab")
    else:
        st.info("💾 Setiap data yang disimpan akan otomatis ditulis ke file CSV (Permanen).")
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
                    uc = st.text_input("Unit Code (e.g. WP-01)")
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
        t_es, t_ep = st.tabs(["Edit Sump", "Edit Pompa"])
        with t_es:
            edt_s = st.data_editor(st.session_state.data_sump[st.session_state.data_sump['Site']==selected_site], num_rows="dynamic", key="ed_s")
            if st.button("Simpan Perubahan Sump"):
                base = st.session_state.data_sump[st.session_state.data_sump['Site']!=selected_site]
                st.session_state.data_sump = pd.concat([base, edt_s], ignore_index=True)
                save_to_csv()
                st.success("Updated & Saved!"); st.rerun()
        with t_ep:
            edt_p = st.data_editor(st.session_state.data_pompa[st.session_state.data_pompa['Site']==selected_site], num_rows="dynamic", key="ed_p")
            if st.button("Simpan Perubahan Pompa"):
                base = st.session_state.data_pompa[st.session_state.data_pompa['Site']!=selected_site]
                st.session_state.data_pompa = pd.concat([base, edt_p], ignore_index=True)
                save_to_csv()
                st.success("Updated & Saved!"); st.rerun()

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
        render_login_form(unique_key="admin_tab")
    else:
        st.write("⚙️ Pengaturan Site")
        ns = st.text_input("Tambah Site Baru")
        if st.button("Add Site"):
            if ns and ns not in st.session_state['site_map']:
                st.session_state['site_map'][ns] = []
                st.success(f"Site {ns} added")
