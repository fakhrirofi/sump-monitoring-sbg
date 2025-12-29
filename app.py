import streamlit as st
import pandas as pd
import numpy as np

# --- 1. SETUP DATA DUMMY (MENGGANTIKAN DATABASE SEMENTARA) ---
# Struktur data dictionary untuk 3 Site
sites_data = {
    "Lais Coal Mine": {
        "pits": ["Pit Utara", "Pit Selatan"],
        "pumps": ["WP1203 (Multiflo)", "WP1005 (KSB)"],
        "critical_level": 12.0
    },
    "Wiraduta Sejahtera Langgeng": {
        "pits": ["Pit A", "Pit B1"],
        "pumps": ["WP2001 (Sykes)", "WP2002 (Sykes)"],
        "critical_level": 45.0
    },
    "Nusantara Energy": {
        "pits": ["Pit Garuda"],
        "pumps": ["WP3001 (Multiflo)"],
        "critical_level": 8.5
    }
}

# --- 2. LAYOUT DASHBOARD ---
st.set_page_config(page_title="Mining Water Management", layout="wide")

# Sidebar Navigasi
st.sidebar.title("🌊 Water Management")
selected_site = st.sidebar.selectbox("Pilih Site:", list(sites_data.keys()))

# Ambil data berdasarkan site yang dipilih
current_site_info = sites_data[selected_site]
selected_pit = st.sidebar.selectbox("Pilih Lokasi (Sump):", current_site_info["pits"])

# --- 3. KONTEN UTAMA ---
st.title(f"Dashboard: {selected_site}")
st.markdown(f"**Monitoring Sump:** {selected_pit}")

# Baris Metrik Atas (KPI)
col1, col2, col3, col4 = st.columns(4)

# Simulasi angka acak agar terlihat hidup
elevasi_aktual = np.random.uniform(5, 14) 
is_danger = elevasi_aktual > current_site_info['critical_level']
status_color = "🔴 BAHAYA" if is_danger else "🟢 AMAN"

with col1:
    st.metric("Status Keselamatan", status_color)
with col2:
    st.metric("Curah Hujan (Hari Ini)", "45 mm", "+12mm")
with col3:
    st.metric("Elevasi Air", f"{elevasi_aktual:.2f} m", f"Batas: {current_site_info['critical_level']} m")
with col4:
    st.metric("Total Pompa Running", f"{len(current_site_info['pumps'])} Unit")

st.divider()

# --- 4. VISUALISASI GRAFIK ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Tren Elevasi Air vs Batas Kritis")
    # Membuat data dummy chart
    dates = pd.date_range(start="2025-12-01", periods=10)
    chart_data = pd.DataFrame({
        'Tanggal': dates,
        'Elevasi Aktual': np.random.uniform(8, 13, 10),
        'Critical Level': [current_site_info['critical_level']] * 10
    })
    st.line_chart(chart_data, x='Tanggal', y=['Elevasi Aktual', 'Critical Level'], color=["#0000FF", "#FF0000"])

with c2:
    st.subheader("Performa Pompa (Hari Ini)")
    # Menampilkan grid status pompa
    pump_df = pd.DataFrame({
        "Unit Code": current_site_info['pumps'],
        "Flowrate Plan (m3/h)": [500, 450] if len(current_site_info['pumps']) > 1 else [500],
        "Actual (m3/h)": [480, 200] if len(current_site_info['pumps']) > 1 else [480],
    })
    # Hitung efisiensi
    pump_df["Efisiensi"] = (pump_df["Actual (m3/h)"] / pump_df["Flowrate Plan (m3/h)"]) * 100
    
    st.dataframe(pump_df.style.highlight_between(left=0, right=50, subset="Efisiensi", color="#ffcccc"))
    st.caption("*Merah: Efisiensi di bawah 50% (Perlu Cek Mekanik)")

# --- 5. LOGIC WARNING ---
if elevasi_aktual > current_site_info['critical_level']:
    st.error(f"⚠️ PERINGATAN: Air di {selected_pit} sudah melewati batas aman! Segera aktifkan pompa cadangan.")
