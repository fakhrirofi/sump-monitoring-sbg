import streamlit as st
import pandas as pd
from datetime import date
import os

# Import Modules
import database as db
import processing as proc
import ui

# --- 1. CONFIG & SETUP ---
st.set_page_config(
    page_title="Bara Tama Wijaya Water Management",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)
ui.load_css()

# --- 2. SESSION STATE & DATA LOADING ---
if 'data_sump' not in st.session_state or 'data_pompa' not in st.session_state:
    try:
        df_s, df_p = db.load_data()
        st.session_state['data_sump'] = df_s
        st.session_state['data_pompa'] = df_p
    except Exception as e:
        st.error(f"Gagal koneksi ke Neon DB: {e}")
        st.stop()

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'username' not in st.session_state: st.session_state['username'] = ''
if 'site_map' not in st.session_state:
    # Build dynamic site map from DB data
    if not st.session_state.data_sump.empty:
        existing_sites = st.session_state.data_sump['Site'].unique()
        current_map = {}
        for s in existing_sites:
            pits = st.session_state.data_sump[st.session_state.data_sump['Site'] == s]['Pit'].unique().tolist()
            current_map[s] = pits
        st.session_state['site_map'] = current_map
    else:
        st.session_state['site_map'] = {}

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("## 🏢 BARA TAMA WIJAYA")
    if st.session_state['logged_in']:
        st.success(f"👤 Login: {st.session_state['username']}")
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
    else:
        st.info("👀 Mode: View Only")
    
    st.divider()
    
    # FILTERS
    current_sites = list(st.session_state['site_map'].keys())
    selected_site = st.selectbox("📍 Pilih Site", current_sites) if current_sites else None
    
    pit_options = ["All Sumps"]
    if selected_site and selected_site in st.session_state['site_map']: 
        pit_options += st.session_state['site_map'][selected_site]
    selected_pit = st.selectbox("💧 Pilih Sump", pit_options)

    # Unit Filter Logic
    unit_options = ["All Units"]
    if selected_pit != "All Sumps" and not st.session_state.data_pompa.empty:
        raw_p = st.session_state.data_pompa
        avail_units = raw_p[(raw_p['Site'] == selected_site) & (raw_p['Pit'] == selected_pit)]['Unit Code'].unique().tolist()
        unit_options += sorted(avail_units)
    selected_unit = st.selectbox("🚜 Pilih Unit Pompa", unit_options)
    
    # Date Filter
    avail_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True) if not st.session_state.data_sump.empty else [date.today().year]
    sel_year = st.selectbox("📅 Tahun", avail_years)
    month_map = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
    curr_m = date.today().month
    sel_month_name = st.selectbox("🗓️ Bulan", list(month_map.values()), index=curr_m-1)
    sel_month_int = [k for k,v in month_map.items() if v==sel_month_name][0]

# --- 4. DATA PROCESSING ---
df_wb_dash, df_p_display, title_suffix = proc.process_water_balance(
    st.session_state.data_sump, st.session_state.data_pompa,
    selected_site, selected_pit, selected_unit, sel_year, sel_month_int
)

# --- 5. TABS ---
st.markdown(f"## 🏢 Bara Tama Wijaya: {selected_site}")
tab_dash, tab_input, tab_db, tab_admin = st.tabs(["📊 Dashboard", "📝 Input (Admin)", "📂 Database", "⚙️ Setting"])

# TAB 1: DASHBOARD
with tab_dash:
    if df_wb_dash.empty:
        st.warning("⚠️ Data belum tersedia untuk filter ini. Silakan generate dummy data di tab Setting.")
    else:
        last = df_wb_dash.iloc[-1]
        st.markdown(f"<div class='date-header'>📅 Dashboard Status per Tanggal: {last['Tanggal'].strftime('%d %B %Y')}</div>", unsafe_allow_html=True)
        
        # Metrics
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Elevasi Air", f"{last['Elevasi Air (m)']} m", f"Crit: {last['Critical Elevation (m)']}")
        c2.metric("Vol Survey", f"{last['Volume Air Survey (m3)']:,.0f} m³")
        c3.metric("Rain Today", f"{last['Curah Hujan (mm)']} mm")
        c4.metric("Rain MTD", f"{df_wb_dash['Curah Hujan (mm)'].sum()} mm")
        status_clr = "#e74c3c" if last['Status'] == "BAHAYA" else "#27ae60"
        c5.markdown(f"<div style='background-color:{status_clr};color:white;padding:20px;border-radius:5px;text-align:center;'>{last['Status']}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        # Render Charts
        ui.render_charts(df_wb_dash, df_p_display, title_suffix)

# TAB 2: INPUT
with tab_input:
    if not st.session_state['logged_in']:
        ui.render_login_form("input")
    else:
        st.info("Input Data Harian (Saved to Neon Cloud)")
        with st.expander("➕ Input Harian Baru", expanded=True):
            d_in = st.date_input("Tanggal", date.today())
            
            # --- FIXED LOGIC FOR SUMP SELECTION ---
            # Get existing sumps for this site
            existing_sumps = st.session_state['site_map'].get(selected_site, [])
            
            p_in = None # Variable to hold the final chosen sump name
            
            # If no sumps exist (New Site), force Text Input
            if not existing_sumps:
                st.warning(f"Belum ada Sump di {selected_site}. Silakan buat baru.")
                p_in = st.text_input("Nama Sump Baru (Wajib Diisi)", placeholder="Contoh: Sump Utara")
            else:
                # If sumps exist, allow user to choose or create new
                mode_input = st.radio("Mode Input Sump:", ["Pilih Sump Ada", "Buat Sump Baru"], horizontal=True)
                
                if mode_input == "Pilih Sump Ada":
                    p_in = st.selectbox("Pilih Sump", existing_sumps)
                else:
                    p_in = st.text_input("Nama Sump Baru", placeholder="Contoh: Sump Selatan")

            # --- FORM INPUT ---
            # Only show forms if p_in is valid (not empty string)
            if p_in:
                cl, cr = st.columns(2)
                with cl:
                    with st.form("fs"):
                        st.markdown(f"<b>Data Sump: {p_in}</b>", unsafe_allow_html=True)
                        e_a = st.number_input("Elevasi (m)", format="%.2f")
                        v_a = st.number_input("Volume Survey (m3)", step=100)
                        r_p = st.number_input("Rain Plan (mm)", value=20.0)
                        r_a = st.number_input("Rain Act (mm)", 0.0)
                        gw_v = st.number_input("Groundwater (m3)", 0.0)
                        
                        if st.form_submit_button("Simpan Sump"):
                            new = {
                                "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                                "Elevasi Air (m)": e_a, "Critical Elevation (m)": 13.0,
                                "Volume Air Survey (m3)": v_a, "Plan Curah Hujan (mm)": r_p,
                                "Curah Hujan (mm)": r_a, "Actual Catchment (Ha)": 25.0,
                                "Groundwater (m3)": gw_v,
                                "Status": "BAHAYA" if e_a > 13 else "AMAN"
                            }
                            db.save_new_sump(new)
                            
                            # Refresh Data & Site Map immediately
                            st.session_state['data_sump'], _ = db.load_data()
                            # Rebuild map so the new sump appears in dropdowns next time
                            st.session_state.pop('site_map', None)
                            
                            st.success(f"Sump '{p_in}' Saved!")
                            st.rerun()

                with cr:
                    with st.form("fp"):
                        st.markdown(f"<b>Data Pompa: {p_in}</b>", unsafe_allow_html=True)
                        uc = st.text_input("Unit Code (e.g., WP-01)")
                        dp = st.number_input("Debit Plan (m3/h)", value=500)
                        da = st.number_input("Debit Actual (m3/h)", 0)
                        ea = st.number_input("EWH Actual (Jam)", 0.0)
                        
                        if st.form_submit_button("Simpan Pompa"):
                            newp = {
                                "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                                "Unit Code": uc, "Debit Plan (m3/h)": dp, "Debit Actual (m3/h)": da,
                                "EWH Plan": 20.0, "EWH Actual": ea
                            }
                            db.save_new_pompa(newp)
                            _, st.session_state['data_pompa'] = db.load_data() # Reload
                            st.success(f"Pompa for '{p_in}' Saved!")
                            st.rerun()
            else:
                if not existing_sumps:
                    st.info("Silakan ketik nama Sump baru di atas untuk memulai.")

        st.divider()
        st.markdown("### 🛠️ Bulk Edit (Delete Data here)")
        st.caption("Tips: Select rows and press 'Delete' on your keyboard to remove data. Click Update to save changes.")
        
        t1, t2 = st.tabs(["Edit Sump", "Edit Pompa"])
        with t1:
            # Sump Editor
            curr_s = st.session_state.data_sump[st.session_state.data_sump['Site']==selected_site]
            ed_s = st.data_editor(curr_s, num_rows="dynamic", key="es")
            
            if st.button("💾 UPDATE SUMP DB"):
                full_s = pd.concat([st.session_state.data_sump[st.session_state.data_sump['Site']!=selected_site], ed_s], ignore_index=True)
                db.overwrite_full_db(full_s, st.session_state.data_pompa)
                st.session_state['data_sump'] = full_s
                
                # Rebuild map in case sumps were renamed or deleted
                st.session_state.pop('site_map', None)
                st.success("Updated!"); st.rerun()
                
        with t2:
            # Pompa Editor
            curr_p = st.session_state.data_pompa[st.session_state.data_pompa['Site']==selected_site]
            ed_p = st.data_editor(curr_p, num_rows="dynamic", key="ep")
            
            if st.button("💾 UPDATE POMPA DB"):
                full_p = pd.concat([st.session_state.data_pompa[st.session_state.data_pompa['Site']!=selected_site], ed_p], ignore_index=True)
                db.overwrite_full_db(st.session_state.data_sump, full_p)
                st.session_state['data_pompa'] = full_p
                st.success("Updated!"); st.rerun()

# TAB 3: DATABASE
with tab_db:
    st.info("📂 Source: Neon PostgreSQL")
    c1, c2 = st.columns(2)
    c1.download_button("Download Sump CSV", st.session_state.data_sump.to_csv(index=False), "sump.csv")
    c2.download_button("Download Pompa CSV", st.session_state.data_pompa.to_csv(index=False), "pompa.csv")
    st.dataframe(st.session_state.data_sump)

# TAB 4: ADMIN / SETTINGS
with tab_admin:
    st.markdown("### ⚙️ System Settings")
    
    if st.session_state['logged_in']:
        # Section 1: Manage Sites
        st.markdown("#### 🏗️ Manage Sites")
        ns = st.text_input("New Site Name")
        if st.button("Add Site") and ns: st.session_state['site_map'][ns] = []
        
        st.divider()
        
        # Section 2: Developer Tools
        st.markdown("#### 🧪 Developer Tools")
        
        c_dev1, c_dev2 = st.columns(2)
        
        with c_dev1:
            st.info("Gunakan ini untuk mengisi data grafik.")
            if st.button("Generate Dummy Data", type="primary", use_container_width=True):
                try:
                    with st.spinner("Generating data..."):
                        db.generate_dummy_data()
                        # Reload Data
                        df_s, df_p = db.load_data()
                        st.session_state['data_sump'] = df_s
                        st.session_state['data_pompa'] = df_p
                        st.session_state.pop('site_map', None) 
                    st.success("Dummy data generated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.error("Tip: Try 'Reset Database' below if this fails.")
                
        with c_dev2:
            st.info("Hapus hanya data dummy.")
            if st.button("Delete Dummy Data", type="secondary", use_container_width=True):
                with st.spinner("Cleaning up..."):
                    db.delete_dummy_data()
                    df_s, df_p = db.load_data()
                    st.session_state['data_sump'] = df_s
                    st.session_state['data_pompa'] = df_p
                    st.session_state.pop('site_map', None) 
                st.warning("Dummy data deleted.")
                st.rerun()

        st.divider()
        st.markdown("#### ⚠️ Danger Zone")
        with st.expander("Reset Database (Fix Schema Errors)"):
            st.warning("This will DELETE ALL DATA (Real & Dummy) and recreate empty tables. Use this if you get 'ProgrammingError' or 'Column missing' errors.")
            if st.button("🔴 RESET DATABASE (DROP TABLES)", type="primary"):
                with st.spinner("Resetting Database..."):
                    db.reset_db()
                    st.session_state.clear() # Clear session to force full reload
                st.success("Database has been reset. Please refresh the page.")
                
    else:
        ui.render_login_form("adm")
