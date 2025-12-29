import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import date

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Mining Sump Monitor", layout="wide")

# --- FUNGSI DATABASE SEDERHANA (CSV) ---
DB_FILE = 'sump_database.csv'

def init_db():
    """Membuat file database jika belum ada"""
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=[
            'Date', 'Elevation', 'Rainfall', 'Volume', 
            'Pump1_HM_Start', 'Pump1_HM_End', 'Pump1_Hours',
            'Pump2_HM_Start', 'Pump2_HM_End', 'Pump2_Hours',
            'Total_Outflow_Est'
        ])
        df.to_csv(DB_FILE, index=False)

def load_data():
    """Load data dari CSV"""
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame()

def save_data(new_entry):
    """Menyimpan data baru ke CSV"""
    df = load_data()
    # Mengubah new_entry menjadi DataFrame
    new_df = pd.DataFrame([new_entry])
    # Menggabungkan dan menyimpan
    if not df.empty:
        df = pd.concat([df, new_df], ignore_index=True)
    else:
        df = new_df
    df.to_csv(DB_FILE, index=False)
    return df

# Inisialisasi Database
init_db()

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("🔧 Navigasi")
menu = st.sidebar.radio("Pilih Halaman:", ["📊 Dashboard", "📝 Input Daily Data"])

# ==============================================================================
# HALAMAN 1: INPUT DATA (FORMULIR)
# ==============================================================================
if menu == "📝 Input Daily Data":
    st.title("📝 Input Data Harian Sump")
    st.markdown("---")
    
    with st.form("daily_input_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("1. Kondisi Lingkungan")
            input_date = st.date_input("Tanggal", date.today())
            input_elevasi = st.number_input("Elevasi Aktual (m)", min_value=0.0, format="%.3f")
            input_ch = st.number_input("Curah Hujan (mm)", min_value=0.0, format="%.1f")
            # Volume bisa dibuat otomatis hitung berdasarkan elevasi jika ada tabel kurva, 
            # untuk sekarang kita buat manual input
            input_vol = st.number_input("Volume Air Survey (m³)", min_value=0.0)

        with col2:
            st.subheader("2. Operasional Pompa")
            st.markdown("**Pompa 1 (WP1203 - MF420)**")
            p1_start = st.number_input("HM Awal WP1203", min_value=0.0)
            p1_end = st.number_input("HM Akhir WP1203", min_value=0.0)
            
            st.markdown("**Pompa 2 (WP1002)**")
            p2_start = st.number_input("HM Awal WP1002", min_value=0.0)
            p2_end = st.number_input("HM Akhir WP1002", min_value=0.0)

        # Tombol Submit
        submitted = st.form_submit_button("💾 Simpan Data")
        
        if submitted:
            # --- VALIDASI DATA (Kunci dari Opsi 3) ---
            error = False
            
            # Cek HM Logic
            if p1_end < p1_start:
                st.error("❌ Error: HM Akhir WP1203 lebih kecil dari HM Awal!")
                error = True
            if p2_end < p2_start:
                st.error("❌ Error: HM Akhir WP1002 lebih kecil dari HM Awal!")
                error = True
                
            if not error:
                # Kalkulasi Otomatis (Backend Logic)
                p1_hours = p1_end - p1_start
                p2_hours = p2_end - p2_start
                
                # Estimasi Flowrate (Misal asumsi: WP1203=250 m3/jam, WP1002=250 m3/jam)
                # Angka ini bisa disesuaikan dengan actual flowrate
                est_outflow = (p1_hours * 250) + (p2_hours * 250)
                
                new_data = {
                    'Date': input_date,
                    'Elevation': input_elevasi,
                    'Rainfall': input_ch,
                    'Volume': input_vol,
                    'Pump1_HM_Start': p1_start,
                    'Pump1_HM_End': p1_end,
                    'Pump1_Hours': p1_hours,
                    'Pump2_HM_Start': p2_start,
                    'Pump2_HM_End': p2_end,
                    'Pump2_Hours': p2_hours,
                    'Total_Outflow_Est': est_outflow
                }
                
                save_data(new_data)
                st.success(f"✅ Data tanggal {input_date} berhasil disimpan!")
                st.balloons()

# ==============================================================================
# HALAMAN 2: DASHBOARD
# ==============================================================================
elif menu == "📊 Dashboard":
    st.title("🌊 Dashboard Monitoring Sump")
    
    df = load_data()
    
    if df.empty:
        st.warning("Belum ada data. Silakan input data di menu sebelah kiri.")
    else:
        # Sort data berdasarkan tanggal
        df = df.sort_values(by='Date')
        
        # --- TOP KPI CARDS ---
        latest = df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Elevasi Terkini", f"{latest['Elevation']} m")
        col2.metric("Curah Hujan Terakhir", f"{latest['Rainfall']} mm")
        col3.metric("Volume Air", f"{latest['Volume']:,.0f} m³")
        col4.metric("Total Outflow (Est)", f"{latest['Total_Outflow_Est']:,.0f} m³")
        
        st.markdown("---")

        # --- CHART 1: COMBO CHART (HUJAN vs ELEVASI) ---
        st.subheader("🌧️ Analisis Hujan & Elevasi Air")
        
        fig_combo = go.Figure()
        # Bar Hujan
        fig_combo.add_trace(go.Bar(
            x=df['Date'], y=df['Rainfall'],
            name='Curah Hujan (mm)', marker_color='#3498db', opacity=0.6, yaxis='y'
        ))
        # Line Elevasi
        fig_combo.add_trace(go.Scatter(
            x=df['Date'], y=df['Elevation'],
            name='Elevasi (m)', mode='lines+markers',
            line=dict(color='#e74c3c', width=3), yaxis='y2'
        ))
        
        fig_combo.update_layout(
            yaxis=dict(title='Curah Hujan (mm)', side='right', showgrid=False),
            yaxis2=dict(title='Elevasi (m)', side='left', overlaying='y', showgrid=True),
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_combo, use_container_width=True)
        
        # --- CHART 2: PERFORMA POMPA (JAM KERJA) ---
        st.subheader("⚙️ Jam Operasi Pompa (Running Hours)")
        
        # Melt dataframe untuk format grafik bar chart grouped
        df_pump = df[['Date', 'Pump1_Hours', 'Pump2_Hours']].melt(
            id_vars='Date', var_name='Pompa', value_name='Jam Operasi'
        )
        
        fig_pump = px.bar(
            df_pump, x='Date', y='Jam Operasi', color='Pompa',
            barmode='group',
            color_discrete_map={'Pump1_Hours': '#2ecc71', 'Pump2_Hours': '#f1c40f'}
        )
        st.plotly_chart(fig_pump, use_container_width=True)

        # --- DATA TABLE ---
        with st.expander("Lihat Data Mentah"):
            st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True)