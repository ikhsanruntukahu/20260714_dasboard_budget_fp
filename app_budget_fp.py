from PIL import Image
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- PALET WARNA (khusus tampilan) ---
C_PRIMARY = "#1f4e79"
C_ACCENT = "#6baed6"
C_BAR = "#2b6cb0"
C_LINE = "#242a85"
C_TEXT = "#1f2d3d"
C_GRID = "#e6eaf0"
FONT_FAMILY = "Inter, 'Segoe UI', Arial, sans-serif"


# --- FORMAT ANGKA INDONESIA (titik = ribuan, koma = desimal) ---
def fmt_id(v, dec=0):
    s_ = f"{float(v):,.{dec}f}"
    return s_.replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_rp(v):
    return "Rp " + fmt_id(v)

def fmt_pct(v):
    return fmt_id(v, 2) + "%"

# LANDING PAGE
try:
    logo = Image.open("_ MDPI Primary Logo.png")
    st.set_page_config(page_title="Dashboard Budget FP-MDPI", page_icon=logo, layout="wide", initial_sidebar_state="expanded")
except:
    st.set_page_config(page_title="Dashboard Budget FP-MDPI", layout="wide", initial_sidebar_state="expanded")


# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    }

    /* Latar halaman & lebar konten */
    .stApp { background: #f3f6fa; }
    [data-testid="stMainBlockContainer"], .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* Judul utama */
    h1 {
        color: #ffffff !important;
        background: linear-gradient(90deg, #1f4e79 0%, #2b6cb0 100%);
        padding: 1.1rem 1.5rem !important;
        border-radius: 14px;
        font-weight: 800 !important;
        font-size: 2rem !important;
        letter-spacing: .2px;
        box-shadow: 0 6px 18px rgba(31, 78, 121, .25);
        margin-bottom: .5rem;
    }

    /* Sub-judul seksi */
    h2 { color: #1f4e79 !important; font-weight: 700 !important; }
    [data-testid="stMainBlockContainer"] h3 {
        color: #1f4e79 !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        border-left: 5px solid #6baed6;
        padding-left: .7rem;
        margin-bottom: .6rem;
    }

    /* Kartu (container ber-border) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border: 1px solid #e3e8ef !important;
        border-radius: 14px !important;
        box-shadow: 0 2px 10px rgba(31, 45, 61, .06);
        padding: .4rem .5rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1f3a52 0%, #2b3e50 100%);
    }
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] h3 {
        border-bottom: 2px solid #6baed6;
        padding-bottom: .4rem;
        margin-bottom: .8rem;
    }
    /* Pastikan area checkbox di sidebar tetap gelap (bukan kartu putih) */
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] button svg,
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    /* Tombol di sidebar (Buat & Download laporan) */
    [data-testid="stSidebar"] .stButton button,
    [data-testid="stSidebar"] .stDownloadButton button {
        background: #6baed6;
        border: none;
        border-radius: 10px;
        padding: .5rem 1rem;
    }
    [data-testid="stSidebar"] .stButton button *,
    [data-testid="stSidebar"] .stDownloadButton button * {
        color: #10283f !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] .stButton button:hover,
    [data-testid="stSidebar"] .stDownloadButton button:hover {
        background: #8cc3e6;
    }

    /* Tabel */
    [data-testid="stDataFrame"] {
        border: 1px solid #e3e8ef;
        border-radius: 10px;
        overflow: hidden;
    }
    th {
        color: black !important;
        font-weight: bold !important;
    }

    /* Garis pemisah */
    hr { margin: 1.2rem 0; border-top: 1px solid #d9dee7; }

    /* Teks kecil di atas tabel */
    [data-testid="stMarkdownContainer"] strong { color: #1f4e79; }
</style>
""", unsafe_allow_html=True)


# --- HELPER TAMPILAN GRAFIK ---
def style_bar(fig, height):
    fig.update_traces(
        marker_color=C_BAR,
        hovertemplate="<b>%{y}</b><br>Rp %{x:,.0f}<extra></extra>"
    )
    fig.update_layout(
        height=height, margin=dict(l=10, r=20, t=10, b=10),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family=FONT_FAMILY, color=C_TEXT, size=12),
        bargap=0.35,
        separators=',.',
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(title="Total Expense (Rp)", showgrid=True, gridcolor=C_GRID, zeroline=False, tickformat='.2s')
    fig.update_yaxes(title="", showgrid=False, automargin=True)
    return fig


# --- MAIN TITLE ---
st.title("Dashboard Budget FP")

# --- LOAD & CLEAN DATA ---
@st.cache_data(ttl=60) 
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/1-IU5pot4Ir7HLBDxmf2KEK9CCMvVxXIYKq5FvVqJcWM/export?format=xlsx"
    
    try:
        dfs = pd.read_excel(sheet_url, sheet_name=None)
        
        df_alloc = dfs.get('Allocation')
        df_key = dfs.get('key_activity')
        df_req = dfs.get('Request Budget')
        
        for df in [df_alloc, df_key, df_req]:
            if df is not None:
                df.columns = df.columns.str.strip()

        def clean_currency(col):
            if col.dtype == 'object':
                return pd.to_numeric(col.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
            return pd.to_numeric(col, errors='coerce').fillna(0)

        df_alloc['Allocation'] = clean_currency(df_alloc['Allocation'])
        df_req['Total Expense'] = clean_currency(df_req['Total Expense'])
        
        # Konversi Date & Ekstrak Quarter dan Week
        df_req['Date'] = pd.to_datetime(df_req['Date'], errors='coerce')
        df_req['Quarter'] = 'Q' + df_req['Date'].dt.quarter.astype(str).str.replace('.0', '', regex=False)
        df_req['Week'] = df_req['Date'].dt.isocalendar().week

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

if 'donor_list' not in st.session_state:
    st.session_state.donor_list = sorted([str(d) for d in df_alloc_master['Donor'].unique() if pd.notna(d)])

if 'select_all' not in st.session_state:
    st.session_state.select_all = True
    for donor in st.session_state.donor_list:
        st.session_state[f"donor_{donor}"] = True

def abaikan_atau_pilih_semua():
    for donor in st.session_state.donor_list:
        st.session_state[f"donor_{donor}"] = st.session_state.select_all

def periksa_status_donor():
    st.session_state.select_all = all(st.session_state[f"donor_{d}"] for d in st.session_state.donor_list)

st.sidebar.checkbox("Select all", key="select_all", on_change=abaikan_atau_pilih_semua)

selected_donors = []
for donor in st.session_state.donor_list:
    if st.sidebar.checkbox(donor, key=f"donor_{donor}", on_change=periksa_status_donor):
        selected_donors.append(donor)

if not selected_donors:
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
col1, col2 = st.columns(2)

def create_gauge(val, maximum, title):
    max_val = maximum if maximum > 0 else 1
    percentage = (val / max_val) * 100 if maximum > 0 else 0
    
    center_number = fmt_id(val / 1000000, 2) + "M"
    min_label = "0,00M"
    max_label = fmt_id(max_val / 1000000, 2) + "M"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge", 
        value = val,
        domain = {'x': [0, 1], 'y': [0.1, 0.95]},
        gauge = {
            'axis': {'range': [0, max_val], 'showticklabels': False},
            'bar': {'color': "#86ef5d", 'thickness': 0.8}, 
            'bgcolor': "#e5e7eb",
            'borderwidth': 0,
        }
    ))
    
    fig.update_layout(
        height=240, margin=dict(l=35, r=35, t=45, b=15), paper_bgcolor=C_PRIMARY,
        font=dict(family=FONT_FAMILY),
        annotations=[
            dict(text=title, x=0.001, y=1.25, showarrow=False, font={'size': 13, 'color': 'white', 'weight': 'bold'}, xref="paper", yref="paper"),
            dict(text=center_number, x=0.5, y=0.19, showarrow=False, font={'size': 20, 'color': '#ffffff', 'family': 'Arial Black'}, xref="paper", yref="paper"),
            dict(text=min_label, x=0.0, y=0.0, showarrow=False, font={'size': 10, 'color': '#dbe7f3', 'family': 'Arial'}, xref="paper", yref="paper"),
            dict(text=fmt_pct(percentage), x=0.5, y=0.02, showarrow=False, font={'size': 16, 'color': '#86ef5d', 'family': 'Arial Black'}, xref="paper", yref="paper"),
            dict(text=max_label, x=1.0, y=0.0, showarrow=False, font={'size': 10, 'color': '#dbe7f3', 'family': 'Arial'}, xref="paper", yref="paper")
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

st.markdown("<br>", unsafe_allow_html=True)

# --- EXPENSE OVER TIME ---
# 1. Total Expense by Week
with st.container(border=True):
    st.markdown("### Total Expense by Week")
    if 'Date' in df_req.columns and not df_req.empty:
        df_req_clean = df_req.dropna(subset=['Date']).copy()
        df_req_clean['Date'] = pd.to_datetime(df_req_clean['Date'])
        df_req_clean['Total Expense'] = pd.to_numeric(df_req_clean['Total Expense'], errors='coerce').fillna(0)
        
        df_req_clean['Start of Week'] = df_req_clean['Date'] - pd.to_timedelta(df_req_clean['Date'].dt.dayofweek, unit='d')
        weekly_exp = df_req_clean.groupby('Start of Week')['Total Expense'].sum().reset_index().sort_values('Start of Week')
        
        weekly_exp['Label'] = weekly_exp['Total Expense'].apply(lambda x: f"{x/1000000:.0f}M" if x > 0 else "0M")

        x_data = weekly_exp['Start of Week'].tolist()
        y_data = weekly_exp['Total Expense'].astype(float).tolist()
        text_data = weekly_exp['Label'].tolist()

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=x_data, y=y_data, mode='lines+markers+text', text=text_data, textposition='top center',
            textfont=dict(size=11, color=C_TEXT),
            line=dict(shape='spline', color=C_LINE, width=3),
            marker=dict(size=8, color='white', line=dict(color=C_LINE, width=2)),
            fill='tozeroy', fillcolor='rgba(36, 42, 133, 0.08)',
            hovertemplate="Minggu mulai %{x|%d %b %Y}<br>Rp %{y:,.0f}<extra></extra>"
        ))

        fig_line.update_layout(
            height=350, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family=FONT_FAMILY, color=C_TEXT, size=12),
            hoverlabel=dict(bgcolor="white", font_size=12),
            separators=',.',
            xaxis=dict(title="", tickformat="%b %Y", showgrid=False),
            yaxis=dict(type='linear', showgrid=True, gridcolor=C_GRID, gridwidth=1, griddash='dot', zeroline=False, tickformat='.2s')
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Data tanggal belum tersedia untuk menampilkan grafik mingguan.")

st.markdown("<br>", unsafe_allow_html=True)

# 2. Total Expense by Quarter
with st.container(border=True):
    st.markdown("### Total Expense by Quarter")
    if 'Quarter' in df_req.columns and not df_req.empty:
        # Hanya filter baris yang tanggalnya tidak kosong agar 'Qnan' tidak terdeteksi
        df_req_q = df_req.dropna(subset=['Date']).copy()

        # Menghitung agregat per Quarter
        quarterly_exp = (
            df_req_q.groupby('Quarter')['Total Expense']
            .sum()
            .reset_index()
        )
        quarterly_exp['Total Expense'] = pd.to_numeric(quarterly_exp['Total Expense'], errors='coerce').fillna(0)

        quarterly_exp['Quarter Order'] = quarterly_exp['Quarter'].str.extract(r'Q(\d+)').astype(int)
        quarterly_exp = quarterly_exp.sort_values(['Quarter Order', 'Quarter']).drop(columns=['Quarter Order'])
        quarterly_exp['Percent'] = quarterly_exp['Total Expense'] / total_filtered_allocation * 100 if total_filtered_allocation > 0 else 0
        quarterly_exp['Percent'] = quarterly_exp['Percent'].fillna(0)

        st.markdown("**Tabel Rincian Kuartal**")
        st.dataframe(
            quarterly_exp[['Quarter', 'Total Expense', 'Percent']].style.format({
                'Total Expense': fmt_rp,
                'Percent': fmt_pct
            }).set_table_styles([{'selector': 'th', 'props': [('color', 'black'), ('font-weight', 'bold')]}]),
            use_container_width=True
        )

        # Tambahkan baris TOTAL di bawah tabel
        tot_exp_q = quarterly_exp['Total Expense'].sum()
        df_tot_q = pd.DataFrame([{
            'Quarter': 'TOTAL',
            'Total Expense': tot_exp_q,
            'Percent': (tot_exp_q / total_filtered_allocation * 100) if total_filtered_allocation > 0 else 0
        }])
        st.dataframe(
            df_tot_q.style.format({'Total Expense': fmt_rp, 'Percent': fmt_pct}).set_table_styles([{'selector': 'th', 'props': [('display', 'none')]}]),
            use_container_width=True
        )
    else:
        st.info("Data kuartal belum tersedia.")

st.markdown("<br>", unsafe_allow_html=True)


# --- BAR CHART & TABLE SECTIONS ---
# === BARIS 1: GOALS & PROVINCE ===
col_goals, col_prov = st.columns([1, 1.2])

with col_goals:
    with st.container(border=True):
        st.markdown("### Total Expense by Goals")
        if 'Goals' in df_req.columns:
            goals_exp = df_req.groupby('Goals')['Total Expense'].sum().reset_index().sort_values(by='Total Expense', ascending=True)
            fig_bar1 = go.Figure(go.Bar(
                x=goals_exp['Total Expense'].astype(float).tolist(),
                y=goals_exp['Goals'].astype(str).tolist(),
                orientation='h'
            ))
            style_bar(fig_bar1, 280)
            st.plotly_chart(fig_bar1, use_container_width=True)

with col_prov:
    with st.container(border=True):
        st.markdown("### Details by Province")
        if 'Provinsi' in df_req.columns:
            # Samakan penulisan provinsi (spasi & huruf besar/kecil) agar tidak terhitung ganda
            df_prov = df_req.dropna(subset=['Provinsi']).copy()
            prov_clean = df_prov['Provinsi'].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
            prov_key = prov_clean.str.lower()
            # Nama yang ditampilkan = penulisan yang paling sering muncul di data
            prov_display = prov_clean.groupby(prov_key).agg(lambda x: x.value_counts().idxmax())
            df_prov['Provinsi'] = prov_key.map(prov_display)
            prov_summary = df_prov.groupby('Provinsi')['Total Expense'].sum().reset_index()
            prov_summary.rename(columns={'Provinsi': 'Province'}, inplace=True)
            prov_summary['Absorption (%)'] = (prov_summary['Total Expense'] / total_filtered_allocation) * 100 if total_filtered_allocation > 0 else 0
            prov_summary = prov_summary.sort_values(by='Total Expense', ascending=False)
            
            st.dataframe(prov_summary.style.format({'Total Expense': fmt_rp, 'Absorption (%)': fmt_pct}).set_table_styles([{'selector': 'th', 'props': [('color', 'black'), ('font-weight', 'bold')]}]), use_container_width=True)
            
            tot_exp_prov = prov_summary['Total Expense'].sum()
            tot_abs_prov = (tot_exp_prov / total_filtered_allocation) * 100 if total_filtered_allocation > 0 else 0
            df_tot_prov = pd.DataFrame([{'Province': 'TOTAL', 'Total Expense': tot_exp_prov, 'Absorption (%)': tot_abs_prov}])
            
            st.dataframe(df_tot_prov.style.format({'Total Expense': fmt_rp, 'Absorption (%)': fmt_pct}).set_table_styles([{'selector': 'th', 'props': [('display', 'none')]}]), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# === BUDGET HOLDER ===
col_bh_chart, col_bh_table = st.columns([1, 1.2])

if 'Budget Holder' in df_req.columns and not df_req.empty:
    # Samakan penulisan nama (spasi berlebih & huruf besar/kecil) agar tidak terhitung ganda
    df_bh = df_req.dropna(subset=['Budget Holder']).copy()
    df_bh['Budget Holder'] = (
        df_bh['Budget Holder'].astype(str)
        .str.strip()
        .str.replace(r'\s+', ' ', regex=True)
        .str.title()
    )
    bh_summary = df_bh.groupby('Budget Holder')['Total Expense'].sum().reset_index()
    bh_summary = bh_summary.sort_values(by='Total Expense', ascending=False).reset_index(drop=True)
    total_bh_exp = bh_summary['Total Expense'].sum()
    bh_summary['Share (%)'] = (bh_summary['Total Expense'] / total_bh_exp) * 100 if total_bh_exp > 0 else 0

    with col_bh_chart:
        with st.container(border=True):
            st.markdown("### Total Expense by Budget Holder")
            bh_top = bh_summary.head(15).sort_values(by='Total Expense', ascending=True)
            fig_bh = go.Figure(go.Bar(
                x=bh_top['Total Expense'].astype(float).tolist(),
                y=bh_top['Budget Holder'].astype(str).tolist(),
                orientation='h'
            ))
            style_bar(fig_bh, max(300, 40 * len(bh_top) + 60))
            st.plotly_chart(fig_bh, use_container_width=True)

    with col_bh_table:
        with st.container(border=True):
            st.markdown("### Details by Budget Holder")
            st.dataframe(bh_summary.style.format({'Total Expense': fmt_rp, 'Share (%)': fmt_pct}).set_table_styles([{'selector': 'th', 'props': [('color', 'black'), ('font-weight', 'bold')]}]), use_container_width=True, height=400)

            df_tot_bh = pd.DataFrame([{'Budget Holder': 'TOTAL', 'Total Expense': total_bh_exp, 'Share (%)': 100.0 if total_bh_exp > 0 else 0}])
            st.dataframe(df_tot_bh.style.format({'Total Expense': fmt_rp, 'Share (%)': fmt_pct}).set_table_styles([{'selector': 'th', 'props': [('display', 'none')]}]), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

# === BARIS 2: SEKSI AKTIVITAS ===
with st.container(border=True):
    st.markdown("### Details by Activity")
    if 'Goals' in df_alloc.columns and 'Activity' in df_alloc.columns:
        alloc_grouped = df_alloc.groupby(['Goals', 'Activity'])['Allocation'].sum().reset_index()
        exp_grouped = df_req.groupby(['Goals', 'Activity'])['Total Expense'].sum().reset_index() if ('Goals' in df_req.columns and 'Activity' in df_req.columns) else pd.DataFrame(columns=['Goals', 'Activity', 'Total Expense'])
        
        act_summary = pd.merge(alloc_grouped, exp_grouped, on=['Goals', 'Activity'], how='left').fillna(0)
        act_summary['Remaining Budget'] = act_summary['Allocation'] - act_summary['Total Expense']
        act_summary['Absorption (%)'] = (act_summary['Total Expense'] / act_summary['Allocation']) * 100
        act_summary['Absorption (%)'] = act_summary['Absorption (%)'].replace([np.inf, -np.inf], 0).fillna(0)
        
        st.dataframe(act_summary.style.format({
            'Allocation': fmt_rp, 'Total Expense': fmt_rp, 'Remaining Budget': fmt_rp, 'Absorption (%)': fmt_pct
        }).set_table_styles([{'selector': 'th', 'props': [('color', 'black'), ('font-weight', 'bold')]}]), use_container_width=True, height=300)
        
        tot_alloc_act = act_summary['Allocation'].sum()
        tot_exp_act = act_summary['Total Expense'].sum()
        tot_rem_act = act_summary['Remaining Budget'].sum()
        tot_abs_act = (tot_exp_act / tot_alloc_act) * 100 if tot_alloc_act > 0 else 0
        df_tot_act = pd.DataFrame([{
            'Goals': 'TOTAL', 'Activity': '', 'Allocation': tot_alloc_act, 
            'Total Expense': tot_exp_act, 'Remaining Budget': tot_rem_act, 'Absorption (%)': tot_abs_act
        }])
        
        st.dataframe(df_tot_act.style.format({
            'Allocation': fmt_rp, 'Total Expense': fmt_rp, 'Remaining Budget': fmt_rp, 'Absorption (%)': fmt_pct
        }).set_table_styles([{'selector': 'th', 'props': [('display', 'none')]}]), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### Total Expense by Activity")
    if 'Activity' in df_req.columns:
        act_exp = df_req.groupby('Activity')['Total Expense'].sum().reset_index().sort_values(by='Total Expense', ascending=True)
        act_exp_top = act_exp.tail(15)
        fig_bar2 = go.Figure(go.Bar(
            x=act_exp_top['Total Expense'].astype(float).tolist(),
            y=act_exp_top['Activity'].astype(str).tolist(),
            orientation='h'
        ))
        style_bar(fig_bar2, 500)
        st.plotly_chart(fig_bar2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# === BARIS 3: GOALS SUMMARY TABLE ===
with st.container(border=True):
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
            'Allocation': fmt_rp, 'Total Expense': fmt_rp, 'Remaining Budget': fmt_rp, 'Absorption (%)': fmt_pct
        }).set_table_styles([{'selector': 'th', 'props': [('color', 'black'), ('font-weight', 'bold')]}]), use_container_width=True)

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
            'Allocation': fmt_rp, 'Total Expense': fmt_rp, 'Remaining Budget': fmt_rp, 'Absorption (%)': fmt_pct
        }).set_table_styles([{'selector': 'th', 'props': [('display', 'none')]}]), use_container_width=True)


# =====================================================================
# --- LAPORAN (HTML / CETAK PDF) ---
# =====================================================================
# BEGIN REPORT
def build_html_report(ctx):
    import base64
    import io
    from datetime import datetime
    from html import escape
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import FuncFormatter

    df_alloc_r = ctx['df_alloc']
    df_req_r = ctx['df_req']
    selected = ctx['selected_donors']
    total_alloc = float(ctx['total_alloc'])
    total_exp = float(df_req_r['Total Expense'].sum()) if len(df_req_r) else 0.0

    fmt_m = FuncFormatter(lambda x, _: fmt_id(x / 1e6, 0) + "M")

    def has(df):
        return df is not None and len(df) > 0

    def fig_to_img(fig):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f'<img class="chart-img" src="data:image/png;base64,{b64}">'

    def style_ax(ax):
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        ax.tick_params(axis='both', labelsize=8, colors='#333333')

    def chart_barh(names, values):
        names = [(n if len(n) <= 42 else n[:40] + '...') for n in names]
        n = len(names)
        fig, ax = plt.subplots(figsize=(8.5, max(1.8, 0.36 * n + 0.8)))
        bars = ax.barh(names, values, color=C_BAR, height=0.65)
        ax.xaxis.set_major_formatter(fmt_m)
        ax.set_xlabel("Total Expense (juta Rp)", fontsize=8, color='#555555')
        style_ax(ax)
        ax.grid(axis='x', color='#e6eaf0', linewidth=0.8)
        ax.set_axisbelow(True)
        mx = max(values) if len(values) and max(values) > 0 else 1
        for b, v in zip(bars, values):
            ax.text(v + mx * 0.01, b.get_y() + b.get_height() / 2, fmt_id(v / 1e6, 1) + "M",
                    va='center', fontsize=7, color='#333333')
        ax.set_xlim(0, mx * 1.14)
        fig.tight_layout()
        return fig_to_img(fig)

    def chart_line(x, y):
        fig, ax = plt.subplots(figsize=(8.5, 3.2))
        ax.plot(x, y, color=C_LINE, linewidth=2, marker='o', markersize=4, markerfacecolor='white')
        ax.fill_between(x, y, color=C_LINE, alpha=0.08)
        ax.yaxis.set_major_formatter(fmt_m)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.set_ylabel("Total Expense (juta Rp)", fontsize=8, color='#555555')
        style_ax(ax)
        ax.grid(axis='y', color='#e6eaf0', linewidth=0.8, linestyle=':')
        fig.tight_layout()
        return fig_to_img(fig)

    def html_table(header, rows, num_cols=(), total=None, kpi_col=None):
        def td(i, v, is_total=False):
            cls = []
            if i in num_cols:
                cls.append("num")
            if kpi_col is not None and i == kpi_col:
                cls.append("kpi kpi-" + str(v))
            c = f' class="{" ".join(cls)}"' if cls else ""
            return f"<td{c}>{escape(str(v))}</td>"
        out = ["<table><thead><tr>"]
        out += [f"<th>{escape(h)}</th>" for h in header]
        out.append("</tr></thead><tbody>")
        for r in rows:
            out.append("<tr>" + "".join(td(i, v) for i, v in enumerate(r)) + "</tr>")
        if total is not None:
            out.append('<tr class="total">' + "".join(td(i, v, True) for i, v in enumerate(total)) + "</tr>")
        out.append("</tbody></table>")
        return "".join(out)

    parts = []
    counter = {'n': 0}

    def section(title, note=None):
        counter['n'] += 1
        parts.append(f"<h2>{counter['n']}. {escape(title)}</h2>")
        if note:
            parts.append(f'<p class="note">{escape(note)}</p>')

    # ---------- RINGKASAN ----------
    remaining = total_alloc - total_exp
    absorption = (total_exp / total_alloc * 100) if total_alloc > 0 else 0
    donor_text = ", ".join(selected) if selected else "Tidak ada donor dipilih"
    metrics = [("Total Allocation", fmt_rp(total_alloc)), ("Total Expense", fmt_rp(total_exp)),
               ("Remaining Budget", fmt_rp(remaining)), ("Absorption", fmt_pct(absorption))]
    cards = "".join(f'<div class="metric"><div class="mv">{escape(v)}</div><div class="ml">{escape(l)}</div></div>'
                    for l, v in metrics)
    parts.append(f'<div class="metrics">{cards}</div>')

    # ---------- 1. RINGKASAN PER DONOR ----------
    if has(df_alloc_r) and 'Donor' in df_alloc_r.columns:
        section("Ringkasan per Donor", "Alokasi dan realisasi expense untuk donor yang dipilih.")
        alloc_by = df_alloc_r.groupby('Donor')['Allocation'].sum()
        exp_by = df_req_r.groupby('Donor')['Total Expense'].sum() if 'Donor' in df_req_r.columns else pd.Series(dtype=float)
        rows = []
        for d, a in alloc_by.items():
            e = float(exp_by.get(d, 0))
            rows.append([str(d), fmt_rp(a), fmt_rp(e), fmt_rp(a - e), fmt_pct(e / a * 100 if a > 0 else 0)])
        ta, te = alloc_by.sum(), exp_by.sum()
        tot = ['TOTAL', fmt_rp(ta), fmt_rp(te), fmt_rp(ta - te), fmt_pct(te / ta * 100 if ta > 0 else 0)]
        parts.append(html_table(["Donor", "Allocation", "Total Expense", "Remaining Budget", "Absorption (%)"],
                                rows, num_cols=(1, 2, 3, 4), total=tot))

    # ---------- 2. PER MINGGU ----------
    weekly = ctx.get('weekly_exp')
    if has(weekly):
        section("Total Expense per Minggu", "Tren pengeluaran mingguan (minggu dimulai hari Senin).")
        parts.append(chart_line(list(weekly['Start of Week'].dt.to_pydatetime()),
                                weekly['Total Expense'].astype(float).tolist()))

    # ---------- 3. PER KUARTAL ----------
    quarterly = ctx.get('quarterly_exp')
    if has(quarterly):
        section("Total Expense per Kuartal")
        rows = [[r['Quarter'], fmt_rp(r['Total Expense']), fmt_pct(r['Percent'])] for _, r in quarterly.iterrows()]
        tq = quarterly['Total Expense'].sum()
        tot = ['TOTAL', fmt_rp(tq), fmt_pct(tq / total_alloc * 100 if total_alloc > 0 else 0)]
        parts.append(html_table(["Quarter", "Total Expense", "Percent"], rows, num_cols=(1, 2), total=tot))

    # ---------- 4. GOALS ----------
    goals_exp_r = ctx.get('goals_exp')
    goals_sum_r = ctx.get('goals_summary')
    if has(goals_exp_r) or has(goals_sum_r):
        section("Expense berdasarkan Goals")
        if has(goals_exp_r):
            parts.append(chart_barh(goals_exp_r['Goals'].astype(str).tolist(),
                                    goals_exp_r['Total Expense'].astype(float).tolist()))
        if has(goals_sum_r):
            rows = [[str(r['Goals']), fmt_rp(r['Allocation']), fmt_rp(r['Total Expense']),
                     fmt_rp(r['Remaining Budget']), fmt_pct(r['Absorption (%)']), r['KPI']]
                    for _, r in goals_sum_r.iterrows()]
            ta, te = goals_sum_r['Allocation'].sum(), goals_sum_r['Total Expense'].sum()
            tab = (te / ta * 100) if ta > 0 else 0
            tk = 'Overspan' if tab > 100 else 'Low' if tab < 50 else 'Medium' if tab < 70 else 'Good'
            tot = ['TOTAL', fmt_rp(ta), fmt_rp(te), fmt_rp(ta - te), fmt_pct(tab), tk]
            parts.append('<h3>Goals Summary</h3>')
            parts.append(html_table(["Goals", "Allocation", "Total Expense", "Remaining Budget", "Absorption (%)", "KPI"],
                                    rows, num_cols=(1, 2, 3, 4), total=tot, kpi_col=5))
            parts.append('<p class="note">Keterangan KPI: Low &lt; 50%, Medium 50-70%, Good &ge; 70%, Overspan &gt; 100%.</p>')

    # ---------- 5. PROVINSI ----------
    prov = ctx.get('prov_summary')
    if has(prov):
        section("Details by Province")
        rows = [[str(r['Province']), fmt_rp(r['Total Expense']), fmt_pct(r['Absorption (%)'])] for _, r in prov.iterrows()]
        te = prov['Total Expense'].sum()
        tot = ['TOTAL', fmt_rp(te), fmt_pct(te / total_alloc * 100 if total_alloc > 0 else 0)]
        parts.append(html_table(["Province", "Total Expense", "Absorption (%)"], rows, num_cols=(1, 2), total=tot))

    # ---------- 6. BUDGET HOLDER ----------
    bh = ctx.get('bh_summary')
    if has(bh):
        section("Expense berdasarkan Budget Holder", "Grafik menampilkan 15 Budget Holder dengan expense terbesar.")
        top = bh.head(15).sort_values('Total Expense', ascending=True)
        parts.append(chart_barh(top['Budget Holder'].astype(str).tolist(), top['Total Expense'].astype(float).tolist()))
        rows = [[str(r['Budget Holder']), fmt_rp(r['Total Expense']), fmt_pct(r['Share (%)'])] for _, r in bh.iterrows()]
        te = bh['Total Expense'].sum()
        tot = ['TOTAL', fmt_rp(te), fmt_pct(100 if te > 0 else 0)]
        parts.append(html_table(["Budget Holder", "Total Expense", "Share (%)"], rows, num_cols=(1, 2), total=tot))

    # ---------- 7. ACTIVITY ----------
    act = ctx.get('act_summary')
    act_exp_r = ctx.get('act_exp')
    if has(act) or has(act_exp_r):
        section("Expense berdasarkan Activity")
        if has(act_exp_r):
            parts.append('<p class="note">15 aktivitas dengan expense terbesar.</p>')
            top = act_exp_r.tail(15)
            parts.append(chart_barh(top['Activity'].astype(str).tolist(), top['Total Expense'].astype(float).tolist()))
        if has(act):
            parts.append('<h3>Details by Activity</h3>')
            rows = [[str(r['Goals']), str(r['Activity']), fmt_rp(r['Allocation']), fmt_rp(r['Total Expense']),
                     fmt_rp(r['Remaining Budget']), fmt_pct(r['Absorption (%)'])] for _, r in act.iterrows()]
            ta, te = act['Allocation'].sum(), act['Total Expense'].sum()
            tot = ['TOTAL', '', fmt_rp(ta), fmt_rp(te), fmt_rp(ta - te), fmt_pct(te / ta * 100 if ta > 0 else 0)]
            parts.append(html_table(["Goals", "Activity", "Allocation", "Total Expense", "Remaining Budget", "Absorption (%)"],
                                    rows, num_cols=(2, 3, 4, 5), total=tot))

    body = "\n".join(parts)
    now_txt = datetime.now().strftime('%d-%m-%Y %H:%M')

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Laporan Budget FP - MDPI</title>
<style>
    @page {{ size: A4; margin: 12mm; }}
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 30px; color: #1f2d3d; line-height: 1.55; background: #f3f6fa; }}
    .container {{ max-width: 980px; margin: auto; background: #fff; padding: 35px; border-radius: 10px; box-shadow: 0 0 12px rgba(0,0,0,.1); }}
    .header {{ background: linear-gradient(90deg, {C_PRIMARY} 0%, {C_BAR} 100%); color: #fff; padding: 22px 26px; border-radius: 10px; margin-bottom: 18px; }}
    .header h1 {{ margin: 0 0 4px 0; font-size: 26px; }}
    .header p {{ margin: 2px 0; font-size: 13px; color: #dbe7f3; }}
    .metrics {{ display: flex; gap: 12px; margin-bottom: 8px; }}
    .metric {{ flex: 1; background: #f4f7fb; border: 1px solid #d9dee7; border-radius: 8px; padding: 12px 10px; text-align: center; }}
    .mv {{ font-size: 16px; font-weight: 700; color: {C_PRIMARY}; }}
    .ml {{ font-size: 11px; color: #6b7280; margin-top: 2px; }}
    h2 {{ color: {C_PRIMARY}; font-size: 18px; border-bottom: 2px solid {C_PRIMARY}; padding-bottom: 4px; margin-top: 30px; page-break-after: avoid; }}
    h3 {{ color: {C_PRIMARY}; font-size: 14px; margin: 16px 0 4px 0; page-break-after: avoid; }}
    .note {{ font-size: 12px; font-style: italic; color: #6b7280; margin: 4px 0 8px 0; }}
    table {{ width: 100%; border-collapse: collapse; margin: 8px 0 14px 0; font-size: 12.5px; }}
    th, td {{ border: 1px solid #d9dee7; padding: 6px 10px; text-align: left; }}
    th {{ background: {C_PRIMARY}; color: #fff; text-align: center; }}
    thead {{ display: table-header-group; }}
    tr {{ page-break-inside: avoid; }}
    tbody tr:nth-child(even) {{ background: #f4f7fb; }}
    td.num {{ text-align: right; white-space: nowrap; }}
    tr.total td {{ background: #e3edf7; font-weight: 700; border-top: 2px solid {C_PRIMARY}; }}
    td.kpi {{ text-align: center; font-weight: 700; }}
    .kpi-Low {{ color: red; }} .kpi-Medium {{ color: #ff9900; }} .kpi-Good {{ color: green; }} .kpi-Overspan {{ color: purple; }}
    .chart-img {{ width: 100%; max-width: 900px; display: block; margin: 10px auto; page-break-inside: avoid; }}
    .print-btn {{ text-align: center; margin-bottom: 18px; }}
    .btn {{ background: {C_PRIMARY}; color: #fff; padding: 10px 22px; border: none; border-radius: 6px; font-size: 14px; font-weight: 700; cursor: pointer; }}
    .btn:hover {{ background: #163a5c; }}
    .footer {{ text-align: center; font-size: 12px; color: #888; margin-top: 34px; border-top: 1px solid #ddd; padding-top: 12px; }}
    @media print {{
        body {{ background: #fff; margin: 0; }}
        .container {{ max-width: 100%; box-shadow: none; padding: 0; }}
        .no-print {{ display: none !important; }}
        * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    }}
</style>
</head>
<body>
<div class="container">
    <div class="print-btn no-print">
        <button class="btn" onclick="window.print()">Cetak / Simpan sebagai PDF</button>
    </div>
    <div class="header">
        <h1>Laporan Budget FP</h1>
        <p>Yayasan MDPI &nbsp;|&nbsp; Donor: {escape(donor_text)}</p>
        <p>Dibuat pada {now_txt}</p>
    </div>
    {body}
    <div class="footer">&copy; 2026 Yayasan MDPI. Hak Cipta Dilindungi. <i>Happy People Many Fish</i>.</div>
</div>
</body>
</html>"""
# END REPORT


# --- TOMBOL DOWNLOAD LAPORAN (SIDEBAR) ---
@st.cache_data(show_spinner="Menyusun laporan...")
def get_report_html(ctx):
    return build_html_report(ctx)

st.sidebar.markdown("---")
st.sidebar.markdown("### Laporan")

_ctx = dict(
    df_alloc=df_alloc, df_req=df_req, selected_donors=selected_donors,
    total_alloc=total_filtered_allocation,
    weekly_exp=globals().get('weekly_exp'),
    quarterly_exp=globals().get('quarterly_exp'),
    goals_exp=globals().get('goals_exp'),
    goals_summary=globals().get('goals_summary'),
    prov_summary=globals().get('prov_summary'),
    bh_summary=globals().get('bh_summary'),
    act_summary=globals().get('act_summary'),
    act_exp=globals().get('act_exp'),
)
try:
    st.sidebar.download_button(
        "Download Laporan (HTML / Cetak PDF)",
        data=get_report_html(_ctx),
        file_name=f"Laporan_Budget_FP_{pd.Timestamp.now().strftime('%Y%m%d')}.html",
        mime="text/html",
        use_container_width=True,
    )
except Exception as e:
    st.sidebar.error(f"Gagal membuat laporan: {e}")