import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np

# --- 1. SETUP & CONFIG ---
st.set_page_config(
    page_title="Mining Water Management",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .stContainer { border-radius: 10px; padding: 10px; border: 1px solid #f0f2f6; }
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
            hujan = np.random.choice([0, 0, 0, 0, 35, 12, 5])
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
    # Buat 2 Unit Pompa per Site agar dropdown terlihat fungsinya
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
                    "EWH": round(hm, 1) # Diganti jadi EWH
                })
    st.session_state.data_pompa = pd.DataFrame(data_p)

# Tipe data datetime
st.session_state.data_sump['Tanggal'] = pd.to_datetime(st.session_state.data_sump['Tanggal'])
st.session_state.data_pompa['Tanggal'] = pd.to_datetime(st.session_state.data_pompa['Tanggal'])

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("🌊 Control Panel")
    
    # A. FILTER LOKASI
    st.subheader("1. Lokasi")
    selected_site = st.selectbox("📍 Site:", ["All Sites"] + list(SITE_MAP.keys()))
    pit_options = ["All Pits"]
    if selected_site != "All Sites":
        pit_options += SITE_MAP[selected_site]
    selected_pit = st.selectbox("⛏️ Pit:", pit_options)
    
    st.divider()
    
    # B. FILTER PERIODE
    st.subheader("2. Periode Laporan")
    available_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True)
    selected_year = st.selectbox("📅 Tahun:", available_years)
    
    month_map = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
                 7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"}
    current_month_idx = date.today().month - 1
    selected_month_name = st.selectbox("🗓️ Bulan:", list(month_map.values()), index=current_month_idx)
    selected_month_int = [k for k, v in month_map.items() if v == selected_month_name][0]
    
    st.divider()
    st.info("Input data baru di Tab 'Input Harian'.")

# --- FILTER DATA ---
df_sump = st.session_state.data_sump.copy()
df_pompa = st.session_state.data_pompa.copy()

if selected_site != "All Sites":
    df_sump = df_sump[df_sump['Site'] == selected_site]
    df_pompa = df_pompa[df_pompa['Site'] == selected_site]
    if selected_pit != "All Pits":
        df_sump = df_sump[df_sump['Pit'] == selected_pit]
        df_pompa = df_pompa[df_pompa['Pit'] == selected_pit]

# Filter Waktu (Bulan & Tahun)
df_sump_filtered = df_sump[
    (df_sump['Tanggal'].dt.year == selected_year) & 
    (df_sump['Tanggal'].dt.month == selected_month_int)
].sort_values(by="Tanggal")

df_pompa_filtered = df_pompa[
    (df_pompa['Tanggal'].dt.year == selected_year) & 
    (df_pompa['Tanggal'].dt.month == selected_month_int)
].sort_values(by="Tanggal")

# --- 4. TABS SYSTEM ---
tab_dash, tab_input, tab_db = st.tabs(["📊 Dashboard Bulanan", "📝 Input Harian", "📂 Database & Download"])

# =========================================
# TAB 1: DASHBOARD
# =========================================
with tab_dash:
    st.title(f"Laporan: {selected_month_name} {selected_year}")
    
    if df_sump_filtered.empty:
        st.warning("⚠️ Tidak ada data untuk periode ini.")
    else:
        # A. SUMMARY CARDS
        last_entry = df_sump_filtered.iloc[-1] 
        total_rain = df_sump_filtered['Curah Hujan (mm)'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.container(border=True).metric("Elevasi Akhir", f"{last_entry['Elevasi Air (m)']} m")
        with c2: st.container(border=True).metric("Volume Akhir", f"{last_entry['Volume Air Survey (m3)']:,.0f} m³")
        with c3: st.container(border=True).metric("Total Hujan", f"{total_rain:.1f} mm")
        with c4:
            clr = "red" if last_entry['Status'] == "BAHAYA" else "green"
            st.container(border=True).markdown(f"**Status:** :{clr}[{last_entry['Status']}]")
        
        st.divider()

        # B. GRAFIK ELEVASI & VOLUME (HARIAN)
        st.subheader(f"Tren Hidrologi Harian")
        chart_sump = df_sump_filtered.groupby('Tanggal').agg({
            'Elevasi Air (m)': 'mean', 'Volume Air Survey (m3)': 'sum', 'Critical Elevation (m)': 'mean'
        }).reset_index()

        fig = go.Figure()
        fig.add_trace(go.Bar(x=chart_sump['Tanggal'], y=chart_sump['Volume Air Survey (m3)'], name='Volume', marker_color='#A7C7E7', opacity=0.6, yaxis='y2'))
        fig.add_trace(go.Scatter(x=chart_sump['Tanggal'], y=chart_sump['Critical Elevation (m)'], name='Critical', line=dict(color='red', dash='dash')))
        fig.add_trace(go.Scatter(x=chart_sump['Tanggal'], y=chart_sump['Elevasi Air (m)'], name='Elevasi', mode='lines+markers', line=dict(color='blue', width=3)))
        
        fig.update_layout(
            yaxis=dict(title="Elevasi (m)", side="left"),
            yaxis2=dict(title="Volume (m3)", side="right", overlaying="y", showgrid=False),
            xaxis=dict(tickformat="%d", title="Tanggal"),
            legend=dict(orientation="h", y=1.1),
            hovermode="x unified", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # C. ANALISIS POMPA (HARIAN PER UNIT)
        st.markdown("---")
        st.subheader("⚙️ Detail Harian Pompa (Debit & EWH)")
        
        if not df_pompa_filtered.empty:
            # 1. Pilihan Unit
            unit_list = df_pompa_filtered['Unit Code'].unique()
            col_sel, col_empty = st.columns([1, 3])
            with col_sel:
                selected_unit_graph = st.selectbox("🔎 Pilih Unit Pompa:", unit_list)
            
            # 2. Filter Data Harian Unit Terpilih
            df_pump_daily = df_pompa_filtered[df_pompa_filtered['Unit Code'] == selected_unit_graph].sort_values(by="Tanggal")
            
            # 3. Grafik Combo (Bar & Line)
            fig_p_day = go.Figure()
            
            # Bar: Debit Actual
            fig_p_day.add_trace(go.Bar(
                x=df_pump_daily['Tanggal'], 
                y=df_pump_daily['Debit Actual (m3/h)'],
                name='Debit Actual',
                marker_color='#2E8B57'
            ))
            
            # Line: Debit Plan (Optional, sebagai referensi)
            fig_p_day.add_trace(go.Scatter(
                x=df_pump_daily['Tanggal'],
                y=df_pump_daily['Debit Plan (m3/h)'],
                name='Plan Cap.',
                line=dict(color='grey', dash='dot')
            ))

            # Line/Scatter: EWH (Secondary Axis)
            fig_p_day.add_trace(go.Scatter(
                x=df_pump_daily['Tanggal'], 
                y=df_pump_daily['EWH'],
                name='EWH (Jam)',
                mode='lines+markers',
                marker=dict(size=8, color='orange'),
                line=dict(width=3, color='orange'),
                yaxis='y2'
            ))

            fig_p_day.update_layout(
                title=f"Tren Harian Unit: {selected_unit_graph}",
                yaxis=dict(title="Flowrate (m3/h)"),
                yaxis2=dict(title="EWH (Jam)", overlaying="y", side="right", showgrid=False, range=[0, 24]),
                xaxis=dict(tickformat="%d %b", dtick="D1"), # Tampilkan per hari
                legend=dict(orientation="h", y=1.1),
                hovermode="x unified"
            )
            st.plotly_chart(fig_p_day, use_container_width=True)
            
        else:
            st.info("Tidak ada data pompa bulan ini.")

# =========================================
# TAB 2: INPUT HARIAN
# =========================================
with tab_input:
    st.header("📝 Form Input Data")
    
    col_in1, col_in2 = st.columns(2)
    with col_in1: date_in = st.date_input("Tanggal", date.today())
    with col_in2: 
        site_in = st.selectbox("Site", list(SITE_MAP.keys()), key="s_in")
        pit_in = st.selectbox("Pit", SITE_MAP[site_in], key="p_in")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    # INPUT SUMP
    with c1:
        with st.container(border=True):
            st.subheader("1. Data Air")
            with st.form("f_sump"):
                e_act = st.number_input("Elevasi Aktual (m)", format="%.2f")
                e_crit = st.number_input("Critical Level (m)", value=12.0)
                vol = st.number_input("Volume (m3)", step=100)
                rain = st.number_input("Curah Hujan (mm)", format="%.1f")
                catch = st.number_input("Catchment (Ha)", format="%.2f")
                if st.form_submit_button("Simpan Sump", type="primary"):
                    st.session_state.data_sump = pd.concat([pd.DataFrame([{
                        "Tanggal": pd.to_datetime(date_in), "Site": site_in, "Pit": pit_in,
                        "Elevasi Air (m)": e_act, "Critical Elevation (m)": e_crit,
                        "Volume Air Survey (m3)": vol, "Curah Hujan (mm)": rain,
                        "Actual Catchment (Ha)": catch, "Status": "BAHAYA" if e_act > e_crit else "AMAN"
                    }]), st.session_state.data_sump], ignore_index=True)
                    st.success("Tersimpan!")

    # INPUT POMPA
    with c2:
        with st.container(border=True):
            st.subheader("2. Data Pompa")
            with st.form("f_pump"):
                u_code = st.text_input("Kode Unit")
                d_plan = st.number_input("Debit Plan (m3/h)")
                d_act = st.number_input("Debit Actual (m3/h)")
                ewh_in = st.number_input("EWH / Jam Jalan", max_value=24.0, format="%.1f") # Label EWH
                if st.form_submit_button("Simpan Pompa", type="primary"):
                    st.session_state.data_pompa = pd.concat([pd.DataFrame([{
                        "Tanggal": pd.to_datetime(date_in), "Site": site_in, "Pit": pit_in,
                        "Unit Code": u_code, "Debit Plan (m3/h)": d_plan,
                        "Debit Actual (m3/h)": d_act, "EWH": ewh_in
                    }]), st.session_state.data_pompa], ignore_index=True)
                    st.success("Tersimpan!")

# =========================================
# TAB 3: DOWNLOAD & EDIT
# =========================================
with tab_db:
    st.header("📂 Database")
    
    dl_site = st.selectbox("Pilih Site Download:", list(SITE_MAP.keys()))
    
    df_dl_sump = st.session_state.data_sump[st.session_state.data_sump['Site'] == dl_site]
    df_dl_pompa = st.session_state.data_pompa[st.session_state.data_pompa['Site'] == dl_site]
    
    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        if not df_dl_sump.empty:
            st.download_button("Download CSV Sump", df_dl_sump.to_csv(index=False).encode('utf-8'), f"Sump_{dl_site}.csv", "text/csv", type="primary")
    with c_dl2:
        if not df_dl_pompa.empty:
            st.download_button("Download CSV Pompa", df_dl_pompa.to_csv(index=False).encode('utf-8'), f"Pompa_{dl_site}.csv", "text/csv", type="primary")
            
    st.divider()
    with st.expander("Edit Data Master"):
        st.data_editor(st.session_state.data_sump, key="ed1", use_container_width=True)
        st.data_editor(st.session_state.data_pompa, key="ed2", use_container_width=True)
