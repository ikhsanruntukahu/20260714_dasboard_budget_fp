from PIL import Image
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# LANDING PAGE
try:
    logo = Image.open("_ MDPI Primary Logo.png")
    st.set_page_config(page_title="Dashbard Budget FP-MDPI", page_icon=logo, layout="wide", initial_sidebar_state="expanded")
except:
    st.set_page_config(page_title="Dashbard Budget FP-MDPI", layout="wide", initial_sidebar_state="expanded")


# --- CUSTOM CSS ---
st.markdown("""
<style>
    .reportview-container { background: #f0f2f6; }
    .sidebar .sidebar-content { background-color: #2b3e50; color: white; }
    h1, h2, h3 { color: #2b3e50; }
    
    /* Memaksa header tabel menjadi hitam tebal untuk kompatibilitas HTML */
    th {
        color: black !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# --- MAIN TITLE (TAMBAHKAN INI DI SINI) ---
# ==========================================================
st.title("Dashboard Budget FP")
st.markdown("---") # Garis pembatas

# --- LOAD & CLEAN DATA ---
@st.cache_data(ttl=60) # Cache otomatis refresh setiap 1 menit
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/1-IU5pot4Ir7HLBDxmf2KEK9CCMvVxXIYKq5FvVqJcWM/export?format=xlsx"
    
    try:
        # Membaca seluruh sheet menjadi dictionary DataFrames
        dfs = pd.read_excel(sheet_url, sheet_name=None)
        
        df_alloc = dfs.get('Allocation')
        df_key = dfs.get('key_activity')
        df_req = dfs.get('Request Budget')
        
        # Bersihkan spasi tersembunyi pada nama kolom
        for df in [df_alloc, df_key, df_req]:
            if df is not None:
                df.columns = df.columns.str.strip()

        # Fungsi pembersih angka (rupiah ke integer/float)
        def clean_currency(col):
            if col.dtype == 'object':
                return pd.to_numeric(col.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
            return pd.to_numeric(col, errors='coerce').fillna(0)

        # Terapkan pembersihan angka
        df_alloc['Allocation'] = clean_currency(df_alloc['Allocation'])
        df_req['Total Expense'] = clean_currency(df_req['Total Expense'])
        
        # Konversi Date & Ekstrak Quarter dan Week
        df_req['Date'] = pd.to_datetime(df_req['Date'], errors='coerce')
        df_req['Quarter'] = 'Q' + df_req['Date'].dt.quarter.astype(str).str.replace('.0', '', regex=False)
        df_req['Week'] = df_req['Date'].dt.isocalendar().week

        # Memasukkan kolom 'Donor' ke tabel Request Budget dari key_activity
        if 'Key Activity' in df_req.columns and 'Key Activity' in df_key.columns:
            mapping = df_key[['Key Activity', 'Donor']].dropna().drop_duplicates()
            df_req = df_req.merge(mapping, on='Key Activity', how='left')
        
        return df_alloc, df_req

    except Exception as e:
        st.error(f"Gagal memuat atau memproses data: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_alloc_master, df_req_master = load_data()

if df_alloc_master.empty or df_req_master.empty:
    st.warning("Data belum berhasil dimuat. Pastikan URL Google Sheets dapat diakses dan format sheet sesuai.")
    st.stop()

# --- SIDEBAR / FILTER ---
st.sidebar.markdown("### Pilih Donor")

# 1. Simpan daftar donor unik di dalam session state agar persisten
if 'donor_list' not in st.session_state:
    st.session_state.donor_list = sorted([str(d) for d in df_alloc_master['Donor'].unique() if pd.notna(d)])

# 2. Set status centang awal (default semuanya bernilai True saat pertama kali dibuka)
if 'select_all' not in st.session_state:
    st.session_state.select_all = True
    for donor in st.session_state.donor_list:
        st.session_state[f"donor_{donor}"] = True

# 3. Fungsi pembantu (Callback) ketika "Select all" diklik
def abaikan_atau_pilih_semua():
    for donor in st.session_state.donor_list:
        st.session_state[f"donor_{donor}"] = st.session_state.select_all

# 4. Fungsi pembantu (Callback) ketika salah satu donor diubah centangnya
def periksa_status_donor():
    # Jika seluruh donor bernilai True, maka "Select all" otomatis True. 
    # Jika ada satu saja yang False (di-uncheck), maka "Select all" otomatis ikut False.
    st.session_state.select_all = all(st.session_state[f"donor_{d}"] for d in st.session_state.donor_list)

# 5. Render widget checkbox di sidebar dengan mengunci nilainya menggunakan key
st.sidebar.checkbox("Select all", key="select_all", on_change=abaikan_atau_pilih_semua)

selected_donors = []
for donor in st.session_state.donor_list:
    if st.sidebar.checkbox(donor, key=f"donor_{donor}", on_change=periksa_status_donor):
        selected_donors.append(donor)

# 6. Filter DataFrames berdasarkan pilihan donor
if not selected_donors:
    # Antisipasi jika semua dikosongkan agar dashboard tidak crash karena data kosong
    df_alloc = df_alloc_master.iloc[0:0]
    df_req = df_req_master.iloc[0:0]
else:
    df_alloc = df_alloc_master[df_alloc_master['Donor'].isin(selected_donors)]
    if 'Donor' in df_req_master.columns:
        df_req = df_req_master[df_req_master['Donor'].isin(selected_donors)]
    else:
        df_req = df_req_master

total_filtered_allocation = df_alloc['Allocation'].sum()

# --- METRICS & GAUGES ---
st.markdown("## Overview")
col1, col2, col3 = st.columns([1, 1, 2])

def create_gauge(val, maximum, title):
    max_val = maximum if maximum > 0 else 1
    percentage = (val / max_val) * 100 if maximum > 0 else 0
    
    # 1. Format teks angka tengah & maksimum secara dinamis (contoh: 520M atau 92.48M)
    center_number = f"{val/1000000:,.2f}M".rstrip('0').rstrip('.')
    if center_number.endswith('.'): 
        center_number = center_number[:-1]
        
    min_label = "0.00M"
    max_label = f"{max_val/1000000:,.2f}M".rstrip('0').rstrip('.')
    if max_label.endswith('.'): 
        max_label = max_label[:-1]
    
    fig = go.Figure(go.Indicator(
        mode = "gauge", # KUNCI: Diubah menjadi 'gauge' saja untuk mematikan angka bawaan Plotly yang rusak
        value = val,
        domain = {'x': [0, 1], 'y': [0.1, 0.95]}, # Memberikan ruang proporsional
        gauge = {
            'axis': {
                'range': [0, max_val], 
                'showticklabels': False # Sembunyikan tick otomatis agar bersih
            },
            'bar': {'color': "#86ef5d"}, 
            'bgcolor': "#e5e7eb",
        }
    ))
    
    # 2. Atur posisi 5 elemen teks secara absolut berbasis kanvas (Koordinat 0 sampai 1)
    fig.update_layout(
        height=240, 
        margin=dict(l=35, r=35, t=45, b=15),
        paper_bgcolor="#6baed6",
        annotations=[
            # Judul Chart (Atas Kiri)
            dict(
                text=title,
                x=0.001, y=1.25,
                showarrow=False,
                font={'size': 12, 'color': 'white', 'weight': 'bold'},
                xref="paper", yref="paper"
            ),
            # Angka Utama Besar (Tepat di Tengah-Tengah di dalam Arc)
            dict(
                text=center_number,
                x=0.5, y=0.45, 
                showarrow=False,
                font={'size': 18, 'color': 'white', 'family': 'Arial Black'},
                xref="paper", yref="paper"
            ),
            # Label Batas Minimum (Bawah Kiri)
            dict(
                text=min_label,
                x=0.0, y=0.0,
                showarrow=False,
                font={'size': 10, 'color': 'white', 'family': 'Arial'},
                xref="paper", yref="paper"
            ),
            # Teks Persentase Realisasi (Bawah Tengah)
            dict(
                text=f"{percentage:.2f}%",
                x=0.5, y=0.1,
                showarrow=False,
                font={'size': 16, 'color': '#374151', 'family': 'Arial Black'},
                xref="paper", yref="paper"
            ),
            # Label Total Alokasi / Maksimum (Bawah Kanan)
            dict(
                text=max_label,
                x=1.0, y=0.0,
                showarrow=False,
                font={'size': 10, 'color': 'white', 'family': 'Arial'},
                xref="paper", yref="paper"
            )
        ]
    )
    return fig

with col1:
    walton_alloc = df_alloc_master[df_alloc_master['Donor']=='Walton 5']['Allocation'].sum()
    walton_exp = df_req_master[df_req_master['Donor']=='Walton 5']['Total Expense'].sum() if 'Donor' in df_req_master.columns else 0
    st.plotly_chart(create_gauge(walton_exp, walton_alloc, "Walton 5 Expense (Rp)"), use_container_width=True)

with col2:
    packard_alloc = df_alloc_master[df_alloc_master['Donor']=='Packard 4']['Allocation'].sum()
    packard_exp = df_req_master[df_req_master['Donor']=='Packard 4']['Total Expense'].sum() if 'Donor' in df_req_master.columns else 0
    st.plotly_chart(create_gauge(packard_exp, packard_alloc, "Packard 4 Expense (Rp)"), use_container_width=True)

with col3:
    st.empty() # Spacing samping


# --- LAYOUT SECTIONS ---
# Line Chart: Total Expense by Week
st.markdown("### Total Expense by Week")

if 'Date' in df_req.columns and not df_req.empty:
    # 1. Bersihkan data
    df_req_clean = df_req.dropna(subset=['Date']).copy()
    df_req_clean['Date'] = pd.to_datetime(df_req_clean['Date'])
    df_req_clean['Total Expense'] = pd.to_numeric(df_req_clean['Total Expense'], errors='coerce').fillna(0)
    
    # 2. Cari Start of Week (Senin)
    df_req_clean['Start of Week'] = df_req_clean['Date'] - pd.to_timedelta(df_req_clean['Date'].dt.dayofweek, unit='d')
    
    # 3. Groupby dan pastikan diurutkan berdasarkan tanggal
    weekly_exp = df_req_clean.groupby('Start of Week')['Total Expense'].sum().reset_index()
    weekly_exp = weekly_exp.sort_values('Start of Week') # Pastikan urutan waktu benar
    
    # 4. Buat label teks
    weekly_exp['Label'] = weekly_exp['Total Expense'].apply(
        lambda x: f"{x/1000000:.0f}M" if x > 0 else "0M"
    )

    # 5. UBAH KE LIST MURNI (Ini kunci utamanya agar Plotly tidak salah baca index)
    x_data = weekly_exp['Start of Week'].tolist()
    y_data = weekly_exp['Total Expense'].astype(float).tolist()
    text_data = weekly_exp['Label'].tolist()

    # 6. Buat grafik dengan data list murni
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=x_data, 
        y=y_data,
        mode='lines+markers+text',
        text=text_data,
        textposition='top center',
        line=dict(shape='spline', color='#242a85', width=3), 
        marker=dict(size=8, color='#242a85')
    ))

    # 7. Layout
    fig_line.update_layout(
        height=350, 
        margin=dict(l=10, r=10, t=20, b=10),
        plot_bgcolor='rgba(0,0,0,0)', 
        xaxis=dict(
            title="",
            tickformat="%b %Y",       
            showgrid=False
        ),
        yaxis=dict(
            type='linear', # Paksa sumbu Y menjadi linear numerik
            showgrid=True,
            gridcolor='#e6e6e6',
            gridwidth=1,
            griddash='dot',           
            zeroline=False,
            tickformat='.2s'          
        )
    )

    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Data tanggal belum tersedia untuk menampilkan grafik mingguan.")

# --- BAR CHART & TABLE SECTIONS ---

# === BARIS 1: GOALS & PROVINCE (Tetap Berdampingan karena Ringkas) ===
col_goals, col_prov = st.columns([1, 1.2])

with col_goals:
    # Bar Chart: Goals
    st.markdown("### Total Expense by Goals")
    if 'Goals' in df_req.columns:
        goals_exp = df_req.groupby('Goals')['Total Expense'].sum().reset_index().sort_values(by='Total Expense', ascending=True)
        fig_bar1 = px.bar(goals_exp, x='Total Expense', y='Goals', orientation='h', color_discrete_sequence=['black'])
        fig_bar1.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_bar1, use_container_width=True)

with col_prov:
    # 1. Tabel Details by Province
    st.markdown("### Details by Province")
    if 'Provinsi' in df_req.columns:
        prov_summary = df_req.groupby('Provinsi')['Total Expense'].sum().reset_index()
        prov_summary.rename(columns={'Provinsi': 'Province'}, inplace=True)
        prov_summary['Absorption (%)'] = (prov_summary['Total Expense'] / total_filtered_allocation) * 100 if total_filtered_allocation > 0 else 0
        prov_summary = prov_summary.sort_values(by='Total Expense', ascending=False)
        
        st.dataframe(prov_summary.style.format({'Total Expense': 'Rp {:,.0f}', 'Absorption (%)': '{:.2f}%'}).set_table_styles([{'selector': 'th', 'props': [('color', 'black'), ('font-weight', 'bold')]}]), use_container_width=True)
        
        tot_exp_prov = prov_summary['Total Expense'].sum()
        tot_abs_prov = (tot_exp_prov / total_filtered_allocation) * 100 if total_filtered_allocation > 0 else 0
        df_tot_prov = pd.DataFrame([{'Province': 'TOTAL', 'Total Expense': tot_exp_prov, 'Absorption (%)': tot_abs_prov}])
        
        st.dataframe(df_tot_prov.style.format({'Total Expense': 'Rp {:,.0f}', 'Absorption (%)': '{:.2f}%'}).set_table_styles([{'selector': 'th', 'props': [('display', 'none')]}]), use_container_width=True)

st.markdown("---")

# === BARIS 2: SEKSI AKTIVITAS (Menumpuk: Tabel di Atas, Grafik di Bawah) ===

# 2. Tabel Details by Activity (DI ATAS - FULL WIDTH)
st.markdown("### Details by Activity")
if 'Goals' in df_alloc.columns and 'Activity' in df_alloc.columns:
    alloc_grouped = df_alloc.groupby(['Goals', 'Activity'])['Allocation'].sum().reset_index()
    exp_grouped = df_req.groupby(['Goals', 'Activity'])['Total Expense'].sum().reset_index() if ('Goals' in df_req.columns and 'Activity' in df_req.columns) else pd.DataFrame(columns=['Goals', 'Activity', 'Total Expense'])
    
    act_summary = pd.merge(alloc_grouped, exp_grouped, on=['Goals', 'Activity'], how='left').fillna(0)
    act_summary['Remaining Budget'] = act_summary['Allocation'] - act_summary['Total Expense']
    act_summary['Absorption (%)'] = (act_summary['Total Expense'] / act_summary['Allocation']) * 100
    act_summary['Absorption (%)'] = act_summary['Absorption (%)'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Render Tabel Utama Aktivitas
    st.dataframe(act_summary.style.format({
        'Allocation': 'Rp {:,.0f}', 'Total Expense': 'Rp {:,.0f}', 'Remaining Budget': 'Rp {:,.0f}', 'Absorption (%)': '{:.2f}%'
    }).set_table_styles([{'selector': 'th', 'props': [('color', 'black'), ('font-weight', 'bold')]}]), use_container_width=True, height=300)
    
    # Render Baris Total Aktivitas
    tot_alloc_act = act_summary['Allocation'].sum()
    tot_exp_act = act_summary['Total Expense'].sum()
    tot_rem_act = act_summary['Remaining Budget'].sum()
    tot_abs_act = (tot_exp_act / tot_alloc_act) * 100 if tot_alloc_act > 0 else 0
    df_tot_act = pd.DataFrame([{
        'Goals': 'TOTAL', 'Activity': '', 'Allocation': tot_alloc_act, 
        'Total Expense': tot_exp_act, 'Remaining Budget': tot_rem_act, 'Absorption (%)': tot_abs_act
    }])
    
    st.dataframe(df_tot_act.style.format({
        'Allocation': 'Rp {:,.0f}', 'Total Expense': 'Rp {:,.0f}', 'Remaining Budget': 'Rp {:,.0f}', 'Absorption (%)': '{:.2f}%'
    }).set_table_styles([{'selector': 'th', 'props': [('display', 'none')]}]), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Bar Chart: Activity (DI BAWAH - FULL WIDTH)
st.markdown("### Total Expense by Activity")
if 'Activity' in df_req.columns:
    act_exp = df_req.groupby('Activity')['Total Expense'].sum().reset_index().sort_values(by='Total Expense', ascending=True)
    # Membuat grafik lebih tinggi (height=500) agar label sumbu Y yang panjang tidak bertumpuk
    fig_bar2 = px.bar(act_exp.tail(15), x='Total Expense', y='Activity', orientation='h', color_discrete_sequence=['black'])
    fig_bar2.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_bar2, use_container_width=True)


# === BARIS 3: GOALS SUMMARY TABLE (Paling Bawah) ===
st.markdown("---")
st.markdown("### Goals Summary Table")
if 'Goals' in df_alloc.columns:
    goal_alloc = df_alloc.groupby('Goals')['Allocation'].sum().reset_index()
    goal_exp = df_req.groupby('Goals')['Total Expense'].sum().reset_index() if 'Goals' in df_req.columns else pd.DataFrame(columns=['Goals', 'Total Expense'])

    goals_summary = pd.merge(goal_alloc, goal_exp, on='Goals', how='left').fillna(0)
    goals_summary['Remaining Budget'] = goals_summary['Allocation'] - goals_summary['Total Expense']
    goals_summary['Absorption (%)'] = (goals_summary['Total Expense'] / goals_summary['Allocation']) * 100
    goals_summary['Absorption (%)'] = goals_summary['Absorption (%)'].replace([np.inf, -np.inf], 0).fillna(0)
    
    conditions = [
        goals_summary['Absorption (%)'] > 100,
        goals_summary['Absorption (%)'] < 50,
        goals_summary['Absorption (%)'] < 70
    ]
    choices = ['Overspan', 'Low', 'Medium']
    goals_summary['KPI'] = np.select(conditions, choices, default='Good')

    def color_kpi(val):
        if val == 'Low': color = 'red'
        elif val == 'Medium': color = '#ff9900'
        elif val == 'Good': color = 'green'
        elif val == 'Overspan': color = 'purple'
        else: color = 'black'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(goals_summary.style.map(color_kpi, subset=['KPI']).format({
        'Allocation': 'Rp {:,.0f}', 'Total Expense': 'Rp {:,.0f}', 'Remaining Budget': 'Rp {:,.0f}', 'Absorption (%)': '{:.2f}%'
    }).set_table_styles([{'selector': 'th', 'props': [('color', 'black'), ('font-weight', 'bold')]}]), use_container_width=True)

    # Tabel Total untuk Goals Summary Table
    tot_alloc_goals = goals_summary['Allocation'].sum()
    tot_exp_goals = goals_summary['Total Expense'].sum()
    tot_rem_goals = goals_summary['Remaining Budget'].sum()
    tot_abs_goals = (tot_exp_goals / tot_alloc_goals) * 100 if tot_alloc_goals > 0 else 0
    
    if tot_abs_goals > 100: tot_kpi_goals = 'Overspan'
    elif tot_abs_goals < 50: tot_kpi_goals = 'Low'
    elif tot_abs_goals < 70: tot_kpi_goals = 'Medium'
    else: tot_kpi_goals = 'Good'

    df_tot_goals = pd.DataFrame([{
        'Goals': 'TOTAL', 'Allocation': tot_alloc_goals, 
        'Total Expense': tot_exp_goals, 'Remaining Budget': tot_rem_goals, 
        'Absorption (%)': tot_abs_goals, 'KPI': tot_kpi_goals
    }])

    st.dataframe(df_tot_goals.style.map(color_kpi, subset=['KPI']).format({
        'Allocation': 'Rp {:,.0f}', 'Total Expense': 'Rp {:,.0f}', 'Remaining Budget': 'Rp {:,.0f}', 'Absorption (%)': '{:.2f}%'
    }).set_table_styles([{'selector': 'th', 'props': [('display', 'none')]}]), use_container_width=True)