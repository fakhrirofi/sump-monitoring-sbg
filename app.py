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

# CSS Custom
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .stContainer { border-radius: 10px; padding: 10px; border: 1px solid #f0f2f6; }
    .stDownloadButton button { width: 100%; }
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
    # Generate 120 hari (4 Bulan) ke belakang
    for i in range(120):
        d = today - timedelta(days=i)
        for site in SITE_MAP.keys():
            pit = SITE_MAP[site][0] 
            # Simulasi Hujan & Naik Turun Air
            hujan = np.random.choice([0, 0, 0, 0, 35, 12, 5])
            # Pola gelombang agar terlihat naik turun
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
    for i in range(120):
        d = today - timedelta(days=i)
        for site in SITE_MAP.keys():
            pit = SITE_MAP[site][0]
            hm = np.random.uniform(10, 22)
            data_p.append({
                "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                "Unit Code": "WP-01", 
                "Debit Plan (m3/h)": 500, 
                "Debit Actual (m3/h)": np.random.randint(400, 480), 
                "HM Running": round(hm, 1)
            })
    st.session_state.data_pompa = pd.DataFrame(data_p)

# Pastikan tipe datetime
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
    
    # B. FILTER PERIODE (BULAN & TAHUN)
    st.subheader("2. Periode Laporan")
    
    # Ambil list tahun yang ada di data
    available_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True)
    selected_year = st.selectbox("📅 Tahun:", available_years)
    
    # Mapping Nama Bulan Indonesia
    month_map = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    
    # Default ke bulan saat ini
    current_month_idx = date.today().month - 1
    month_names = list(month_map.values())
    selected_month_name = st.selectbox("🗓️ Bulan:", month_names, index=current_month_idx)
    
    # Konversi nama bulan balik ke angka (int)
    selected_month_int = [k for k, v in month_map.items() if v == selected_month_name][0]
    
    st.divider()
    st.info("Ke Tab 'Input' untuk update data harian.")

# --- LOGIC FILTERING DATA ---
# 1. Filter Site/Pit dulu
df_sump = st.session_state.data_sump.copy()
df_pompa = st.session_state.data_pompa.copy()

if selected_site != "All Sites":
    df_sump = df_sump[df_sump['Site'] == selected_site]
    df_pompa = df_pompa[df_pompa['Site'] == selected_site]
    if selected_pit != "All Pits":
        df_sump = df_sump[df_sump['Pit'] == selected_pit]
        df_pompa = df_pompa[df_pompa['Pit'] == selected_pit]

# 2. Filter Waktu (Berdasarkan Bulan & Tahun yg dipilih)
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
# TAB 1: DASHBOARD BULANAN (DAILY DETAIL)
# =========================================
with tab_dash:
    st.title(f"Laporan: {selected_month_name} {selected_year}")
    st.caption(f"Lokasi: {selected_site} | {selected_pit}")
    
    if df_sump_filtered.empty:
        st.warning(f"⚠️ Tidak ada data ditemukan untuk bulan {selected_month_name} {selected_year}.")
    else:
        # A. KARTU RINGKASAN BULANAN
        # Status Terakhir (Last Entry di Bulan tsb)
        last_entry = df_sump_filtered.iloc[-1] 
        # Total Hujan Bulan Ini
        total_rain = df_sump_filtered['Curah Hujan (mm)'].sum()
        # Rata-rata Elevasi Bulan Ini
        avg_elev = df_sump_filtered['Elevasi Air (m)'].mean()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.container(border=True).metric("Elevasi Terakhir", f"{last_entry['Elevasi Air (m)']} m", f"Avg: {avg_elev:.1f} m", delta_color="off")
        with c2:
            st.container(border=True).metric("Volume Terakhir", f"{last_entry['Volume Air Survey (m3)']:,.0f} m³")
        with c3:
            st.container(border=True).metric("Total Hujan", f"{total_rain:.1f} mm", "Akumulasi Bulan Ini")
        with c4:
            color = "red" if last_entry['Status'] == "BAHAYA" else "green"
            st.container(border=True).markdown(f"**Status Akhir:**\n## :{color}[{last_entry['Status']}]")
        
        st.divider()

        # B. GRAFIK TREN HARIAN (DI BULAN TERPILIH)
        st.subheader(f"Tren Harian ({selected_month_name} {selected_year})")
        
        # Aggregate jika All Sites dipilih agar grafik tidak error (sum volume, mean elevasi)
        chart_df = df_sump_filtered.groupby('Tanggal').agg({
            'Elevasi Air (m)': 'mean',
            'Volume Air Survey (m3)': 'sum',
            'Critical Elevation (m)': 'mean',
            'Curah Hujan (mm)': 'sum'
        }).reset_index()

        fig = go.Figure()

        # Bar: Volume
        fig.add_trace(go.Bar(
            x=chart_df['Tanggal'], y=chart_df['Volume Air Survey (m3)'],
            name='Volume (m3)', marker_color='#A7C7E7', opacity=0.6, yaxis='y2'
        ))
        
        # Bar: Hujan (Terbalik dari atas atau kecil di bawah) -> Kita taruh di bawah biasa
        # Opsional: Jika ingin hujan terlihat distinct
        
        # Line: Critical
        fig.add_trace(go.Scatter(
            x=chart_df['Tanggal'], y=chart_df['Critical Elevation (m)'],
            name='Critical Level', mode='lines', 
            line=dict(color='#FF6961', width=2, dash='dash')
        ))
        
        # Line: Elevasi Aktual
        fig.add_trace(go.Scatter(
            x=chart_df['Tanggal'], y=chart_df['Elevasi Air (m)'],
            name='Elevasi (m)', mode='lines+markers',
            line=dict(color='#0047AB', width=3)
        ))

        fig.update_layout(
            yaxis=dict(title="Elevasi (m)", side="left"),
            yaxis2=dict(title="Volume (m3)", side="right", overlaying="y", showgrid=False),
            xaxis=dict(
                title="Tanggal",
                tickformat="%d %b", # Format tgl: 01 Jan, 02 Jan
                dtick="D1" # Interval per hari
            ),
            legend=dict(orientation="h", y=1.1),
            hovermode="x unified",
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)

        # C. GRAFIK HUJAN HARIAN
        with st.expander("Lihat Detail Curah Hujan Harian"):
            fig_rain = px.bar(chart_df, x='Tanggal', y='Curah Hujan (mm)', title="Curah Hujan Harian")
            fig_rain.update_xaxes(tickformat="%d %b")
            st.plotly_chart(fig_rain, use_container_width=True)

        # D. PERFORMA POMPA BULAN INI
        st.subheader("Performa Pompa (Bulan Ini)")
        if not df_pompa_filtered.empty:
            # Kita ambil Rata-rata performa unit selama bulan ini
            pump_stats = df_pompa_filtered.groupby('Unit Code').agg({
                'Debit Plan (m3/h)': 'mean',
                'Debit Actual (m3/h)': 'mean',
                'HM Running': 'mean' # Rata-rata jam jalan per hari
            }).reset_index()
            
            fig_pump = go.Figure()
            fig_pump.add_trace(go.Bar(x=pump_stats['Unit Code'], y=pump_stats['Debit Plan (m3/h)'], name='Plan (Avg)', marker_color='lightgrey'))
            fig_pump.add_trace(go.Bar(x=pump_stats['Unit Code'], y=pump_stats['Debit Actual (m3/h)'], name='Actual (Avg)', marker_color='#2E8B57'))
            fig_pump.add_trace(go.Scatter(
                x=pump_stats['Unit Code'], y=pump_stats['HM Running'], 
                name='Avg Jam Kerja (HM/Day)', mode='markers+text',
                marker=dict(color='orange', size=15, symbol='diamond'),
                text=pump_stats['HM Running'].round(1), textposition="top center",
                yaxis='y2'
            ))

            fig_pump.update_layout(
                yaxis=dict(title="Debit (m3/h)"),
                yaxis2=dict(title="Jam Kerja (HM)", overlaying="y", side="right", showgrid=False),
                barmode='group', legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig_pump, use_container_width=True)
        else:
            st.info("Tidak ada data pompa di bulan ini.")

# =========================================
# TAB 2: INPUT HARIAN (Tetap Hari Ini)
# =========================================
with tab_input:
    st.header("📝 Input Data Harian")
    st.caption("Input data baru di sini (Tanggal bebas dipilih).")
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        date_in = st.date_input("Tanggal Data", date.today())
    with col_in2:
        site_in = st.selectbox("Site", list(SITE_MAP.keys()), key="s_in")
        pit_in = st.selectbox("Pit", SITE_MAP[site_in], key="p_in")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    # FORM SUMP
    with c1:
        with st.container(border=True):
            st.subheader("1. Data Air (Sump)")
            with st.form("f_sump"):
                e_act = st.number_input("Elevasi Aktual (m)", format="%.2f")
                e_crit = st.number_input("Critical Level (m)", value=12.0)
                vol = st.number_input("Volume Survey (m3)", step=100)
                rain = st.number_input("Curah Hujan (mm)", format="%.1f")
                catch = st.number_input("Catchment Area (Ha)", format="%.2f")
                
                if st.form_submit_button("Simpan Data Sump", type="primary"):
                    status = "BAHAYA" if e_act > e_crit else "AMAN"
                    new_row = {
                        "Tanggal": pd.to_datetime(date_in), 
                        "Site": site_in, "Pit": pit_in,
                        "Elevasi Air (m)": e_act, "Critical Elevation (m)": e_crit,
                        "Volume Air Survey (m3)": vol, "Curah Hujan (mm)": rain,
                        "Actual Catchment (Ha)": catch, "Status": status
                    }
                    st.session_state.data_sump = pd.concat([pd.DataFrame([new_row]), st.session_state.data_sump], ignore_index=True)
                    st.success("✅ Data Sump Tersimpan!")

    # FORM POMPA
    with c2:
        with st.container(border=True):
            st.subheader("2. Data Pompa")
            with st.form("f_pump"):
                u_code = st.text_input("Kode Unit (misal: WP01)")
                d_plan = st.number_input("Debit Plan (m3/h)")
                d_act = st.number_input("Debit Actual (m3/h)")
                hm_run = st.number_input("Jam Jalan (HM)", max_value=24.0, format="%.1f")
                
                if st.form_submit_button("Simpan Data Pompa", type="primary"):
                    new_p = {
                        "Tanggal": pd.to_datetime(date_in), "Site": site_in, "Pit": pit_in,
                        "Unit Code": u_code, "Debit Plan (m3/h)": d_plan,
                        "Debit Actual (m3/h)": d_act, "HM Running": hm_run
                    }
                    st.session_state.data_pompa = pd.concat([pd.DataFrame([new_p]), st.session_state.data_pompa], ignore_index=True)
                    st.success(f"✅ Unit {u_code} Tersimpan!")

# =========================================
# TAB 3: DATABASE & DOWNLOAD
# =========================================
with tab_db:
    st.header("📂 Database Master")
    
    st.subheader("⬇️ Download Laporan")
    dl_site = st.selectbox("Pilih Site:", list(SITE_MAP.keys()), key="dl_select")
    
    df_dl_sump = st.session_state.data_sump[st.session_state.data_sump['Site'] == dl_site]
    df_dl_pompa = st.session_state.data_pompa[st.session_state.data_pompa['Site'] == dl_site]
    
    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        if not df_dl_sump.empty:
            st.download_button("Download CSV Sump", df_dl_sump.to_csv(index=False).encode('utf-8'), f"Sump_{dl_site}.csv", "text/csv", type="primary")
        else:
            st.warning("Data Sump Kosong")
    with c_dl2:
        if not df_dl_pompa.empty:
            st.download_button("Download CSV Pompa", df_dl_pompa.to_csv(index=False).encode('utf-8'), f"Pompa_{dl_site}.csv", "text/csv", type="primary")
        else:
            st.warning("Data Pompa Kosong")
            
    st.divider()
    
    with st.expander("Edit Data Master (Full)", expanded=False):
        st.subheader("Data Sump")
        ed_sump = st.data_editor(st.session_state.data_sump, num_rows="dynamic", use_container_width=True, key="mk_sump")
        if st.button("Simpan Sump"): 
            st.session_state.data_sump = ed_sump
            st.rerun()
            
        st.subheader("Data Pompa")
        ed_pump = st.data_editor(st.session_state.data_pompa, num_rows="dynamic", use_container_width=True, key="mk_pump")
        if st.button("Simpan Pompa"): 
            st.session_state.data_pompa = ed_pump
            st.rerun()
