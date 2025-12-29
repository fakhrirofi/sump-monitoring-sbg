import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# --- CONFIG & DUMMY DATA SETUP ---
st.set_page_config(page_title="Sump Monitor - Input System", layout="wide")

# Simulasi Database Awal (Hasil Import dari Excel Anda)
if 'db_sump_logs' not in st.session_state:
    # Ini ceritanya data yang sudah di-import dari Excel kemarin
    data_awal = {
        'Tanggal': [date(2025, 12, 24), date(2025, 12, 25)],
        'Site': ['Lais Coal Mine', 'Lais Coal Mine'],
        'Sump': ['Pit Utara', 'Pit Utara'],
        'Curah Hujan (mm)': [69.0, 0.0],
        'Elevasi (m)': [11.7, 12.0],
        'Volume Air (m3)': [7739, 8500],
        'Status': ['Safe', 'Warning']
    }
    st.session_state.db_sump_logs = pd.DataFrame(data_awal)

# --- SIDEBAR MENU ---
menu = st.sidebar.radio("Menu", ["Dashboard", "Input Data Harian", "Edit Data (History)"])

# --- 1. MENU DASHBOARD (Read) ---
if menu == "Dashboard":
    st.title("📊 Monitoring Overview")
    st.info("Data di bawah ini berasal dari database yang Anda input.")
    # Tampilkan Grafik
    df = st.session_state.db_sump_logs
    st.line_chart(df, x='Tanggal', y='Elevasi (m)')
    st.dataframe(df, use_container_width=True)

# --- 2. MENU INPUT HARIAN (Create) ---
elif menu == "Input Data Harian":
    st.title("📝 Input Data Harian")
    
    with st.form("input_form"):
        c1, c2 = st.columns(2)
        with c1:
            input_site = st.selectbox("Pilih Site", ["Lais Coal Mine", "Wiraduta", "Nusantara"])
            input_sump = st.selectbox("Pilih Sump", ["Pit Utara", "Pit Selatan"])
        with c2:
            input_date = st.date_input("Tanggal", date.today())
        
        st.subheader("Data Hidrologi")
        c3, c4 = st.columns(2)
        in_ch = c3.number_input("Curah Hujan (mm)", min_value=0.0)
        in_elev = c4.number_input("Elevasi Aktual (m)", min_value=0.0)
        
        # Tombol Submit
        submitted = st.form_submit_button("Simpan Data")
        
        if submitted:
            # Logika Simpan ke Database
            new_data = {
                'Tanggal': input_date,
                'Site': input_site,
                'Sump': input_sump,
                'Curah Hujan (mm)': in_ch,
                'Elevasi (m)': in_elev,
                'Volume Air (m3)': in_elev * 1000, # Rumus dummy
                'Status': 'Safe' if in_elev < 12 else 'Danger'
            }
            # Tambahkan ke session state (Database sementara)
            st.session_state.db_sump_logs = pd.concat([
                pd.DataFrame([new_data]), 
                st.session_state.db_sump_logs
            ], ignore_index=True)
            
            st.success("✅ Data berhasil disimpan!")

# --- 3. MENU EDIT DATA / KOREKSI (Update) ---
elif menu == "Edit Data (History)":
    st.title("✏️ Koreksi Data (Excel Mode)")
    st.markdown("Klik langsung pada sel tabel di bawah untuk mengedit kesalahan input.")
    
    # Fitur Data Editor (Mirip Excel)
    edited_df = st.data_editor(
        st.session_state.db_sump_logs,
        num_rows="dynamic", # Bisa tambah baris
        use_container_width=True,
        key="data_editor"
    )
    
    # Tombol untuk commit perubahan permanen
    if st.button("Simpan Perubahan Koreksi"):
        # Di sini logic update ke SQL Database
        st.session_state.db_sump_logs = edited_df
        
        # Validasi sederhana
        st.session_state.db_sump_logs['Status'] = np.where(
            st.session_state.db_sump_logs['Elevasi (m)'] > 12, 'Danger', 'Safe'
        )
        
        st.success("✅ Database telah diperbarui dengan data koreksi Anda.")
        st.rerun()
