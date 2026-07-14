import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="Financial Dashboard", layout="wide", initial_sidebar_state="expanded")

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

# --- LOAD & CLEAN DATA ---
@st.cache_data(ttl=600) # Cache otomatis refresh setiap 10 menit
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/1yWpWdb-OSJg4b29mjazKZNqcvi6hMlEoXP5ZFuLQ5ks/export?format=xlsx"
    
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
st.sidebar.markdown("### Select Donor")
donor_list = [str(d) for d in df_alloc_master['Donor'].unique() if pd.notna(d)]
donor_list = sorted(donor_list)

select_all = st.sidebar.checkbox("Select all", value=True)
selected_donors = []

for donor in donor_list:
    if st.sidebar.checkbox(donor, value=select_all):
        selected_donors.append(donor)

# Filter DataFrames
if select_all or len(selected_donors) == len(donor_list):
    df_alloc = df_alloc_master
    df_req = df_req_master
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
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = val,
        number = {'valueformat': '.2s'}, 
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 14}},
        gauge = {
            'axis': {'range': [None, max_val]},
            'bar': {'color': "#a5d17f"},
            'steps': [{'range': [0, max_val], 'color': "#e1e4e8"}],
        }
    ))
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="#6baed6", font=dict(color="white"))
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
    st.empty() # Placeholder untuk jarak

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
col_charts, col_tables = st.columns([1, 1.2])

with col_charts:
    # Bar Chart: Goals
    st.markdown("### Total Expense by Goals")
    if 'Goals' in df_req.columns:
        goals_exp = df_req.groupby('Goals')['Total Expense'].sum().reset_index().sort_values(by='Total Expense', ascending=True)
        fig_bar1 = px.bar(goals_exp, x='Total Expense', y='Goals', orientation='h', color_discrete_sequence=['black'])
        fig_bar1.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_bar1, use_container_width=True)
    
    # Bar Chart: Activity
    st.markdown("### Total Expense by Activity")
    if 'Activity' in df_req.columns:
        act_exp = df_req.groupby('Activity')['Total Expense'].sum().reset_index().sort_values(by='Total Expense', ascending=True)
        fig_bar2 = px.bar(act_exp.tail(15), x='Total Expense', y='Activity', orientation='h', color_discrete_sequence=['black'])
        fig_bar2.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_bar2, use_container_width=True)

with col_tables:
    st.markdown("### Details by Province")
    if 'Provinsi' in df_req.columns:
        prov_summary = df_req.groupby('Provinsi')['Total Expense'].sum().reset_index()
        prov_summary.rename(columns={'Provinsi': 'Province'}, inplace=True)
        prov_summary['Absorption (%)'] = (prov_summary['Total Expense'] / total_filtered_allocation) * 100 if total_filtered_allocation > 0 else 0
        prov_summary = prov_summary.sort_values(by='Total Expense', ascending=False)
        st.dataframe(prov_summary.style.format({'Total Expense': 'Rp {:,.0f}', 'Absorption (%)': '{:.2f}%'}).set_table_styles([{'selector': 'th.col_heading', 'props': [('color', 'black'), ('font-weight', 'bold')]}, {'selector': 'th', 'props': [('color', 'black'), ('font-weight', 'bold')]}]).hide(axis="index"), use_container_width=True, hide_index=True)


    st.markdown("### Details by Activity")
    if 'Goals' in df_alloc.columns and 'Activity' in df_alloc.columns:
        alloc_grouped = df_alloc.groupby(['Goals', 'Activity'])['Allocation'].sum().reset_index()
        exp_grouped = df_req.groupby(['Goals', 'Activity'])['Total Expense'].sum().reset_index() if ('Goals' in df_req.columns and 'Activity' in df_req.columns) else pd.DataFrame(columns=['Goals', 'Activity', 'Total Expense'])
        
        act_summary = pd.merge(alloc_grouped, exp_grouped, on=['Goals', 'Activity'], how='left').fillna(0)
        act_summary['Remaining Budget'] = act_summary['Allocation'] - act_summary['Total Expense']
        act_summary['Absorption (%)'] = (act_summary['Total Expense'] / act_summary['Allocation']) * 100
        act_summary['Absorption (%)'] = act_summary['Absorption (%)'].replace([np.inf, -np.inf], 0).fillna(0)
        
        st.dataframe(act_summary.style.format({
            'Allocation': 'Rp {:,.0f}', 
            'Total Expense': 'Rp {:,.0f}', 
            'Remaining Budget': 'Rp {:,.0f}', 
            'Absorption (%)': '{:.2f}%'
        }).set_table_styles([{'selector': 'th.col_heading', 'props': [('color', 'black'), ('font-weight', 'bold')]}, {'selector': 'th', 'props': [('color', 'black'), ('font-weight', 'bold')]}]).hide(axis="index"), use_container_width=True, hide_index=True, height=350)



st.markdown("---")
st.markdown("### Goals Summary Table")
if 'Goals' in df_alloc.columns:
    goal_alloc = df_alloc.groupby('Goals')['Allocation'].sum().reset_index()
    goal_exp = df_req.groupby('Goals')['Total Expense'].sum().reset_index() if 'Goals' in df_req.columns else pd.DataFrame(columns=['Goals', 'Total Expense'])

    goals_summary = pd.merge(goal_alloc, goal_exp, on='Goals', how='left').fillna(0)
    goals_summary['Remaining Budget'] = goals_summary['Allocation'] - goals_summary['Total Expense']
    goals_summary['Absorption (%)'] = (goals_summary['Total Expense'] / goals_summary['Allocation']) * 100
    goals_summary['Absorption (%)'] = goals_summary['Absorption (%)'].replace([np.inf, -np.inf], 0).fillna(0)
    
    goals_summary['KPI'] = np.where(goals_summary['Absorption (%)'] < 20, 'Low', 'High')

    def color_kpi(val):
        color = 'red' if val == 'Low' else 'green'
        return f'color: {color}; font-weight: bold;'
        
    st.dataframe(goals_summary.style.map(color_kpi, subset=['KPI']).format({
        'Allocation': 'Rp {:,.0f}', 
        'Total Expense': 'Rp {:,.0f}', 
        'Remaining Budget': 'Rp {:,.0f}', 
        'Absorption (%)': '{:.2f}%'
    }).set_table_styles([{'selector': 'th.col_heading', 'props': [('color', 'black'), ('font-weight', 'bold')]}, {'selector': 'th', 'props': [('color', 'black'), ('font-weight', 'bold')]}]).hide(axis="index"), use_container_width=True, hide_index=True)
