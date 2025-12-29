import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np

# --- 1. SETUP & MODERN UI CONFIG ---
st.set_page_config(
    page_title="Mining Water Management",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS UNTUK TAMPILAN MODERN ---
st.markdown("""
<style>
    /* Background Halaman */
    .stApp {
        background-color: #f4f6f9;
    }
    
    /* Styling Kartu Metrik (Cards) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        color: #333;
    }
    
    /* Styling Header */
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Tombol Download Modern */
    .stDownloadButton button {
        background-color: #2c3e50;
        color: white;
        border-radius: 8px;
        height: 50px;
        width: 100%;
        border: none;
        font-weight: bold;
    }
    .stDownloadButton button:hover {
        background-color: #34495e;
        color: white;
    }
    
    /* Container Grafik */
    .chart-container {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# CONFIG SITE
SITE_MAP = {
    "Lais Coal Mine (LCM)": ["Pit Wijaya Barat", "Pit Wijaya Timur"],
    "Wiraduta Sejahtera Langgeng (WSL)": ["Pit F01", "Pit F02"],
    "Nusantara Energy (NE)": ["Pit S8"]
}

# --- 2. DATA GENERATOR (DUMMY 4 BULAN) ---
if 'data_sump' not in st.session_state:
    data = []
    today = date.today()
    for i in range(120):
        d = today - timedelta(days=i)
        for site in SITE_MAP.keys():
            pit = SITE_MAP[site][0] 
            hujan = np.random.choice([0, 0, 0, 0, 35, 12, 5, 60])
            elev = 10.0 + (np.sin(i/15) * 3) + np.random.uniform(0, 0.5)
            data.append({
                "Tanggal": pd.to_datetime(d), 
                "Site": site, "Pit": pit,
                "Elevasi Air (m)": round(elev, 2), 
                "Critical Elevation (m)": 13.0,
                "Volume Air Survey (m3)": int(elev * 500), 
                "Curah Hujan (mm)": hujan,
                "Actual Catchment (Ha)": 25.0, 
                "Status": "BAHAYA" if elev > 13.0 else "AMAN"
            })
    st.session_state.data_sump = pd.DataFrame(data)

if 'data_pompa' not in st.session_state:
    data_p = []
    today = date.today()
    units = ["WP-01", "WP-02"] 
    for i in range(120):
        d = today - timedelta(days=i)
        for site in SITE_MAP.keys():
            pit = SITE_MAP[site][0]
            for u in units:
                hm = np.random.uniform(10, 22) if u == "WP-01" else np.random.uniform(5, 15)
                debit_act = np.random.randint(400, 480) if u == "WP-01" else np.random.randint(200, 300)
                data_p.append({
                    "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                    "Unit Code": u, 
                    "Debit Plan (m3/h)": 500 if u == "WP-01" else 350, 
                    "Debit Actual (m3/h)": debit_act, 
                    "EWH": round(hm, 1)
                })
    st.session_state.data_pompa = pd.DataFrame(data_p)

# Ensure Datetime
st.session_state.data_sump['Tanggal'] = pd.to_datetime(st.session_state.data_sump['Tanggal'])
st.session_state.data_pompa['Tanggal'] = pd.to_datetime(st.session_state.data_pompa['Tanggal'])

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("## 🌊 Water Management")
    st.markdown("---")
    
    # A. FILTER LOKASI
    st.caption("FILTER LOKASI")
    selected_site = st.selectbox("📍 Site Area", ["All Sites"] + list(SITE_MAP.keys()))
    
    pit_options = ["All Pits"]
    if selected_site != "All Sites":
        pit_options += SITE_MAP[selected_site]
    selected_pit = st.selectbox("⛏️ Pit Area", pit_options)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # B. FILTER PERIODE
    st.caption("FILTER PERIODE")
    available_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True)
    selected_year = st.selectbox("📅 Tahun", available_years)
    
    month_map = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
                 7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"}
    current_month_idx = date.today().month - 1
    selected_month_name = st.selectbox("🗓️ Bulan", list(month_map.values()), index=current_month_idx)
    selected_month_int = [k for k, v in month_map.items() if v == selected_month_name][0]
    
    st.markdown("---")
    st.info("💡 Tip: Gunakan Tab 'Download' untuk menarik laporan gabungan.")

# --- FILTER DATA LOGIC ---
df_sump = st.session_state.data_sump.copy()
df_pompa = st.session_state.data_pompa.copy()

if selected_site != "All Sites":
    df_sump = df_sump[df_sump['Site'] == selected_site]
    df_pompa = df_pompa[df_pompa['Site'] == selected_site]
    if selected_pit != "All Pits":
        df_sump = df_sump[df_sump['Pit'] == selected_pit]
        df_pompa = df_pompa[df_pompa['Pit'] == selected_pit]

# Filter Waktu
df_sump_filtered = df_sump[
    (df_sump['Tanggal'].dt.year == selected_year) & 
    (df_sump['Tanggal'].dt.month == selected_month_int)
].sort_values(by="Tanggal")

df_pompa_filtered = df_pompa[
    (df_pompa['Tanggal'].dt.year == selected_year) & 
    (df_pompa['Tanggal'].dt.month == selected_month_int)
].sort_values(by="Tanggal")

# --- 4. TABS SYSTEM ---
tab_dash, tab_input, tab_db = st.tabs(["📊 Dashboard Executive", "📝 Input Data", "📂 Download Center"])

# =========================================
# TAB 1: DASHBOARD MODERN
# =========================================
with tab_dash:
    st.title(f"{selected_month_name} {selected_year}")
    st.markdown(f"**Site:** {selected_site} | **Pit:** {selected_pit}")
    st.markdown("---")
    
    if df_sump_filtered.empty:
        st.warning("⚠️ Data belum tersedia untuk periode ini.")
    else:
        # A. KARTU METRIK UTAMA (Styled by CSS)
        last_entry = df_sump_filtered.iloc[-1] 
        total_rain = df_sump_filtered['Curah Hujan (mm)'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Elevasi Akhir", f"{last_entry['Elevasi Air (m)']} m", f"Batas: {last_entry['Critical Elevation (m)']} m", delta_color="off")
        with col2:
            st.metric("Volume Air", f"{last_entry['Volume Air Survey (m3)']:,.0f} m³", "Est. Volume")
        with col3:
            st.metric("Total Hujan", f"{total_rain:.1f} mm", "Akumulasi Bulan Ini")
        with col4:
            status_text = last_entry['Status']
            # Custom HTML untuk status agar berwarna
            color_hex = "#e74c3c" if status_text == "BAHAYA" else "#27ae60"
            st.markdown(f"""
            <div style="background-color:{color_hex}; color:white; padding:10px; border-radius:8px; text-align:center;">
                <h3 style="margin:0; color:white;">{status_text}</h3>
                <small>Status Terkini</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # B. LAYOUT GRAFIK (GRID SYSTEM)
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.markdown("### 📈 Tren Hidrologi Harian")
            chart_sump = df_sump_filtered.groupby('Tanggal').agg({
                'Elevasi Air (m)': 'mean', 'Volume Air Survey (m3)': 'sum', 'Critical Elevation (m)': 'mean'
            }).reset_index()

            fig = go.Figure()
            # Area Volume (Background)
            fig.add_trace(go.Bar(x=chart_sump['Tanggal'], y=chart_sump['Volume Air Survey (m3)'], name='Volume', marker_color='#d6eaf8', opacity=0.8, yaxis='y2'))
            # Line Elevasi
            fig.add_trace(go.Scatter(x=chart_sump['Tanggal'], y=chart_sump['Elevasi Air (m)'], name='Elevasi', mode='lines+markers', line=dict(color='#2980b9', width=3)))
            # Line Critical
            fig.add_trace(go.Scatter(x=chart_sump['Tanggal'], y=chart_sump['Critical Elevation (m)'], name='Critical', line=dict(color='#e74c3c', dash='dash')))
            
            fig.update_layout(
                yaxis=dict(title="Elevasi (m)", side="left"),
                yaxis2=dict(title="Volume (m3)", side="right", overlaying="y", showgrid=False),
                xaxis=dict(tickformat="%d", title="Tanggal", showgrid=False),
                legend=dict(orientation="h", y=1.1, x=0),
                margin=dict(l=20, r=20, t=20, b=20),
                height=380,
                paper_bgcolor='rgba(0,0,0,0)', # Transparent
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)

        with c_right:
            st.markdown("### 🌧️ Curah Hujan")
            # Bar Chart Hujan Simpel
            fig_rain = px.bar(df_sump_filtered, x='Tanggal', y='Curah Hujan (mm)', color_discrete_sequence=['#34495e'])
            fig_rain.update_layout(
                xaxis=dict(tickformat="%d", title=None),
                yaxis=dict(title="mm"),
                height=380,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_rain, use_container_width=True)

        # C. DETAIL POMPA (FULL WIDTH)
        st.markdown("### ⚙️ Analisis Performa Pompa")
        
        if not df_pompa_filtered.empty:
            unit_list = df_pompa_filtered['Unit Code'].unique()
            selected_unit_graph = st.selectbox("Pilih Unit:", unit_list, label_visibility="collapsed")
            
            df_pump_daily = df_pompa_filtered[df_pompa_filtered['Unit Code'] == selected_unit_graph].sort_values(by="Tanggal")
            
            fig_p_day = go.Figure()
            # Bar Debit
            fig_p_day.add_trace(go.Bar(
                x=df_pump_daily['Tanggal'], y=df_pump_daily['Debit Actual (m3/h)'],
                name='Debit Actual', marker_color='#27ae60'
            ))
            # Line EWH
            fig_p_day.add_trace(go.Scatter(
                x=df_pump_daily['Tanggal'], y=df_pump_daily['EWH'],
                name='EWH (Jam)', mode='lines+markers',
                marker=dict(size=8, color='#f39c12'),
                line=dict(width=3, color='#f39c12'), yaxis='y2'
            ))

            fig_p_day.update_layout(
                yaxis=dict(title="Flowrate (m3/h)", showgrid=True, gridcolor='#f0f0f0'),
                yaxis2=dict(title="EWH (Jam)", overlaying="y", side="right", showgrid=False, range=[0, 24]),
                xaxis=dict(tickformat="%d %b", dtick="D1", showgrid=False),
                legend=dict(orientation="h", y=1.1),
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_p_day, use_container_width=True)

# =========================================
# TAB 2: INPUT HARIAN (Clean Form)
# =========================================
with tab_input:
    st.subheader("📝 Form Input Data")
    
    with st.container():
        c_date, c_site, c_pit = st.columns(3)
        date_in = c_date.date_input("Tanggal", date.today())
        site_in = c_site.selectbox("Site", list(SITE_MAP.keys()), key="s_in")
        pit_in = c_pit.selectbox("Pit", SITE_MAP[site_in], key="p_in")
    
    st.markdown("---")
    
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.markdown("#### 1. Data Sump (Air)")
        with st.form("f_sump"):
            c1, c2 = st.columns(2)
            e_act = c1.number_input("Elevasi Aktual (m)", format="%.2f")
            e_crit = c2.number_input("Critical Level (m)", value=12.0)
            vol = c1.number_input("Volume (m3)", step=100)
            catch = c2.number_input("Catchment (Ha)", format="%.2f")
            rain = st.number_input("Curah Hujan (mm)", format="%.1f")
            
            if st.form_submit_button("💾 Simpan Data Sump", use_container_width=True):
                st.session_state.data_sump = pd.concat([pd.DataFrame([{
                    "Tanggal": pd.to_datetime(date_in), "Site": site_in, "Pit": pit_in,
                    "Elevasi Air (m)": e_act, "Critical Elevation (m)": e_crit,
                    "Volume Air Survey (m3)": vol, "Curah Hujan (mm)": rain,
                    "Actual Catchment (Ha)": catch, "Status": "BAHAYA" if e_act > e_crit else "AMAN"
                }]), st.session_state.data_sump], ignore_index=True)
                st.success("Data Sump tersimpan!")

    with col_r:
        st.markdown("#### 2. Data Pompa")
        with st.form("f_pump"):
            u_code = st.text_input("Kode Unit (e.g., WP-01)")
            c3, c4 = st.columns(2)
            d_plan = c3.number_input("Debit Plan", value=500)
            d_act = c4.number_input("Debit Actual", value=450)
            ewh_in = st.number_input("Jam Jalan (EWH)", max_value=24.0, format="%.1f")
            
            if st.form_submit_button("💾 Simpan Data Pompa", use_container_width=True):
                st.session_state.data_pompa = pd.concat([pd.DataFrame([{
                    "Tanggal": pd.to_datetime(date_in), "Site": site_in, "Pit": pit_in,
                    "Unit Code": u_code, "Debit Plan (m3/h)": d_plan,
                    "Debit Actual (m3/h)": d_act, "EWH": ewh_in
                }]), st.session_state.data_pompa], ignore_index=True)
                st.success("Data Pompa tersimpan!")

# =========================================
# TAB 3: DOWNLOAD CENTER (COMBINED CSV)
# =========================================
with tab_db:
    st.subheader("📂 Download Center")
    st.info("Download data gabungan (Sump & Pompa) dalam satu file CSV.")
    
    # 1. Pilih Site
    dl_site = st.selectbox("Pilih Site untuk Download:", list(SITE_MAP.keys()))
    
    # 2. Logic Penggabungan Data (Merge)
    # Filter dulu berdasarkan Site
    df_s_raw = st.session_state.data_sump[st.session_state.data_sump['Site'] == dl_site]
    df_p_raw = st.session_state.data_pompa[st.session_state.data_pompa['Site'] == dl_site]
    
    if not df_s_raw.empty:
        # Lakukan Merge (Outer Join agar data yang tidak ada pasangan tetap muncul)
        # Kunci: Tanggal, Site, Pit
        df_combined = pd.merge(
            df_s_raw, 
            df_p_raw, 
            on=['Tanggal', 'Site', 'Pit'], 
            how='outer',
            suffixes=('_Sump', '_Pompa')
        )
        
        # Sortir biar rapi
        df_combined = df_combined.sort_values(by=['Tanggal', 'Pit', 'Unit Code'])
        
        # Tampilkan Preview
        st.markdown("### Preview Data Gabungan")
        st.dataframe(df_combined.head(), use_container_width=True)
        
        # Tombol Download
        csv_data = df_combined.to_csv(index=False).encode('utf-8')
        file_name = f"Master_Data_Combined_{dl_site.replace(' ', '_')}.csv"
        
        st.download_button(
            label="⬇️ DOWNLOAD FULL REPORT (CSV)",
            data=csv_data,
            file_name=file_name,
            mime='text/csv'
        )
    else:
        st.warning("Tidak ada data Sump ditemukan untuk site ini. Silakan input data terlebih dahulu.")

    st.divider()
    
    with st.expander("🛠️ Edit Data Mentah (Advanced)"):
        st.write("Data Sump")
        st.data_editor(st.session_state.data_sump, key="ed_s", num_rows="dynamic")
        st.write("Data Pompa")
        st.data_editor(st.session_state.data_pompa, key="ed_p", num_rows="dynamic")
