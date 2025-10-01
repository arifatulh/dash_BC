import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyproj import Transformer
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import math


# ===============================
# CONFIG DASHBOARD
# ===============================
st.set_page_config(
    page_title="Dashboard GBST",
    page_icon="🌍",
    layout="wide"
)

# ===============================
# LOGO + HEADER
# ===============================
logo = "assets/4logo.png"
st.logo(logo, icon_image=logo, size="large")

sheet_url = "https://docs.google.com/spreadsheets/d/1cw3xMomuMOaprs8mkmj_qnib-Zp_9n68rYMgiRZZqBE/edit?usp=sharing"

# daftar sheet yang ingin dibaca
sheet_names = ["Timbulan", "Program", "Ketidaksesuaian", "Survei_Online", "Survei_Offline", "CCTV"]
# ambil ID file dari link
sheet_id = sheet_url.split("/")[5]

# Load data sekali dan simpan di session_state
if "data" not in st.session_state:
    data_dict = {}
    for sheet in sheet_names:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
        try:
            df = pd.read_csv(url)
            # normalisasi kolom: string, strip, lower, replace spasi
            df.columns = df.columns.astype(str)
            df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
            data_dict[sheet.lower()] = df
        except Exception as e:
            st.error(f"Gagal load sheet {sheet}: {e}")
            data_dict[sheet] = pd.DataFrame()
    st.session_state["data"] = data_dict

# ===============================
# LOAD DATA GOOGLE SHEETS
# ===============================
sheet_url = "https://docs.google.com/spreadsheets/d/1cw3xMomuMOaprs8mkmj_qnib-Zp_9n68rYMgiRZZqBE/edit?usp=sharing"
sheet_id = sheet_url.split("/")[5]
sheet_names = ["Timbulan", "Program", "Ketidaksesuaian", "Survei_Online", "Survei_Offline", "CCTV", "Koordinat_UTM"]

all_df = {}
for sheet in sheet_names:
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
        df = pd.read_csv(url)
        all_df[sheet] = df
    except Exception as e:
        st.error(f"Gagal load sheet {sheet}: {e}")
        all_df[sheet] = pd.DataFrame()


# Cara akses di halaman mana pun
df_timbulan = st.session_state["data"].get("Timbulan", pd.DataFrame())
df_program = st.session_state["data"].get("Program", pd.DataFrame())
df_online = st.session_state["data"].get("Survei_Online", pd.DataFrame())
df_ketidaksesuaian = st.session_state["data"].get("Ketidaksesuaian", pd.DataFrame())
df_offline = st.session_state["data"].get("Survei_Offline", pd.DataFrame())
df_cctv = st.session_state["data"].get("CCTV", pd.DataFrame())
df_koordinat= st.session_state["data"].get("Koordinat_UTM", pd.DataFrame())
df_program = st.session_state["data"].get("Program", pd.DataFrame())


# Dataset
df_timbulan = all_df.get("Timbulan", pd.DataFrame()).copy()
df_program = all_df.get("Program", pd.DataFrame()).copy()
df_ketidaksesuaian = all_df.get("Ketidaksesuaian", pd.DataFrame()).copy()
df_online = all_df.get("Survei_Online", pd.DataFrame()).copy()
df_offline = all_df.get("Survei_Offline", pd.DataFrame()).copy()
df_cctv = all_df.get("CCTV", pd.DataFrame()).copy()
df_koordinat = all_df.get("Koordinat_UTM", pd.DataFrame()).copy()

# ===============================
# NORMALISASI DASAR
# ===============================

def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    """lowercase + strip + underscore untuk nama kolom."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    return df
df_timbulan = norm_cols(df_timbulan)
df_program = norm_cols(df_program)
df_ketidaksesuaian = norm_cols(df_ketidaksesuaian)
df_online = norm_cols(df_online)
df_offline = norm_cols(df_offline)
df_koordinat = norm_cols(df_koordinat)

# Pastikan kolom numeric
if "timbulan" in df_timbulan.columns:
    df_timbulan["timbulan"] = pd.to_numeric(df_timbulan["timbulan"], errors='coerce').fillna(0)
if "total_calc" in df_program.columns:
    df_program["total_calc"] = pd.to_numeric(df_program["total_calc"], errors='coerce').fillna(0)

# =============================
# FILTER LOKAL (HANYA PAGE INI)
# =============================
import calendar
import re
st.sidebar.subheader("Filter Data")
site_list = sorted(df_timbulan["site"].dropna().unique()) if "site" in df_timbulan.columns else []
site_sel = st.sidebar.multiselect("Pilih Site", site_list, default=site_list[:4] if site_list else [])

perusahaan_list = sorted(df_timbulan["perusahaan"].dropna().unique()) if "perusahaan" in df_timbulan.columns else []
perusahaan_sel = st.sidebar.multiselect("Pilih Perusahaan", perusahaan_list, default=perusahaan_list[:6] if perusahaan_list else [])


# 1. Deteksi kolom bulan-tahun otomatis
pattern = r"^(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)_\d{4}$"
bulan_tahun_cols = [col for col in df_program.columns if re.match(pattern, str(col))]

# 2. Reshape wide → long
df_prog_long = df_program.melt(
    id_vars=[col for col in df_program.columns if col not in bulan_tahun_cols],
    value_vars=bulan_tahun_cols,
    var_name="Bulan-Tahun",
    value_name="Value"
)
#df_prog_long["tahun"] = df_prog_long["Bulan-Tahun"].apply(lambda x: int(x.split(" ")[1]))
#df_prog_long["bulan"] = df_prog_long["Bulan-Tahun"].apply(lambda x: x.split(" ")[0])

df_prog_long["tahun"] = df_prog_long["Bulan-Tahun"].apply(lambda x: int(x.split("_")[1]))
df_prog_long["bulan"] = df_prog_long["Bulan-Tahun"].apply(lambda x: x.split("_")[0].capitalize())


# 3. Mapping nama bulan ke angka
bulan_map = {
   "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
  "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
  "September": 9, "Oktober": 10, "November": 11, "Desember": 12
}


# 4. Bisa bikin kolom periode datetime (buat filter/plot)
import datetime

#df_prog_long["Periode"] = df_prog_long.apply(
#    lambda row: datetime.datetime(row["Tahun"], bulan_map[row["Bulan"]], 1),
#    axis=1
#)

#df_prog_long["periode"] = pd.to_datetime(
#    df_prog_long["tahun"].astype(int).astype(str) + "-" +
#    df_prog_long["bulan"].map(bulan_map).astype(str) + "-01"
#)

df_prog_long["periode"] = pd.to_datetime(
    df_prog_long["tahun"].astype(str) + "-" +
    df_prog_long["bulan"].map(bulan_map).astype(str) + "-01"
)

# ======================
# Filter Bulan & Tahun
# ======================
#df_ketidaksesuaian = all_df.get("Ketidaksesuaian", pd.DataFrame())
df_ketidaksesuaian["tanggallapor"] = pd.to_datetime(df_ketidaksesuaian["tanggallapor"], dayfirst=True, errors="coerce")
df_ketidaksesuaian["tahun"] = df_ketidaksesuaian["tanggallapor"].dt.year
df_ketidaksesuaian["bulan"] = df_ketidaksesuaian["tanggallapor"].dt.month
# Buat filter selectbox
# Pastikan pakai df_ketidaksesuaian yang sudah punya kolom Tahun & Bulan
tahun_tersedia = sorted(df_prog_long["tahun"].dropna().astype(int).unique())
#bulan_tersedia = [b for b in calendar.month_name[1:]]  # ['Januari', ..., 'Desember']
bulan_tersedia = list(bulan_map.keys())  


    #tahun_pilihan = st.selectbox("Pilih Tahun:", tahun_tersedia, index=len(tahun_tersedia)-1)
tahun_pilihan = st.sidebar.multiselect("Pilih Tahun:", tahun_tersedia, default=tahun_tersedia)

bulan_pilihan = st.sidebar.multiselect("Pilih Bulan:", bulan_tersedia, default=bulan_tersedia)

# Filter dataframe sesuai pilihan user
# Convert nama bulan ke angka untuk filter Ketidaksesuaian
bulan_pilihan_num = [bulan_map[b] for b in bulan_pilihan]
# =============================
# Apply Filter
# =============================
# Apply filter ke df_program
df_prog_filtered = df_prog_long[
    (df_prog_long["tahun"].isin(tahun_pilihan)) &
    (df_prog_long["bulan"].isin(bulan_pilihan))].sort_values(by=["tahun","periode"])
total_program_filtered = df_prog_filtered["Value"].sum()

# Apply filter ke df_ketidaksesuaian
df_ketidaksesuaian["tanggallapor"] = pd.to_datetime(df_ketidaksesuaian["tanggallapor"], dayfirst=True, errors="coerce")
df_ketidaksesuaian["tahun"] = df_ketidaksesuaian["tanggallapor"].dt.year
df_ketidaksesuaian["bulan"] = df_ketidaksesuaian["tanggallapor"].dt.month

df_ket_filtered = df_ketidaksesuaian[
    (df_ketidaksesuaian["tahun"].isin(tahun_pilihan)) &
    (df_ketidaksesuaian["bulan"].isin([bulan_map[b]for b in bulan_pilihan]))&
    (df_ketidaksesuaian["status_temuan"]=="Valid")
].sort_values(by=["tahun","bulan"])

# Filter Timbulan
df_timbulan_filtered = df_timbulan.copy()
if site_sel:
    df_timbulan_filtered = df_timbulan_filtered[df_timbulan_filtered["site"].isin(site_sel)]
if perusahaan_sel:
    df_timbulan_filtered = df_timbulan_filtered[df_timbulan_filtered["perusahaan"].isin(perusahaan_sel)]
total_timbulan = df_timbulan_filtered["timbulan"].sum()

df_timbulan_sum = df_timbulan_filtered.groupby(["perusahaan","site"])["timbulan"].sum().reset_index()
total_timbulan = df_timbulan_sum["timbulan"].sum()
total_program = df_prog_filtered["Value"].sum()
# =============================
# Info Jumlah Hari
# =============================
import calendar

# Hitung total hari dari semua kombinasi bulan & tahun yang dipilih
days_period = 0
for y in tahun_pilihan:
    for b in bulan_pilihan:
        month_num = bulan_map[b]
        days_period += calendar.monthrange(y, month_num)[1]

st.info(f"📅 Total jumlah hari periode filter: **{days_period} hari**")
# Apply filter lokal
#df_filtered = dt_timbulan.copy()
#if site_sel:
   # df_filtered= df_filtered[df_filtered["Site"].isin(site_sel)]
#if perusahaan_sel:
 #   df_filtered = df_filtered[df_filtered["Perusahaan"].isin(perusahaan_sel)]
# ==============================
# Fungsi filter global
# ==============================
def apply_site_perusahaan_filter(df, site_col="site", perusahaan_col="perusahaan"):
    df_filtered = df.copy()
    if site_sel and site_col in df_filtered.columns:
        df_filtered = df_filtered[df_filtered[site_col].isin(site_sel)]
    if perusahaan_sel and perusahaan_col in df_filtered.columns:
        df_filtered = df_filtered[df_filtered[perusahaan_col].isin(perusahaan_sel)]
    return df_filtered

# ==============================
# FILTER TAHUN & BULAN untuk Program
# ==============================
def apply_program_filter(df_prog_long, tahun_pilihan, bulan_pilihan):
    bulan_map = {
       "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
       "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
       "September": 9, "Oktober": 10, "November": 11, "Desember": 12
    }
    bulan_pilihan_num = [bulan_map[b] for b in bulan_pilihan]
    
    df_filtered = df_prog_long[
        (df_prog_long["tahun"].isin(tahun_pilihan)) &
        (df_prog_long["bulan"].map(bulan_map).isin(bulan_pilihan_num))
    ]
    
    # Filter site & perusahaan juga
    df_filtered = apply_site_perusahaan_filter(df_filtered)
    
    return df_filtered

# ==============================
# FILTER TAHUN & BULAN untuk Ketidaksesuaian
# ==============================
def apply_ketidaksesuaian_filter(df_ketidaksesuaian, tahun_pilihan, bulan_pilihan):
    bulan_map = {
       "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
       "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
       "September": 9, "Oktober": 10, "November": 11, "Desember": 12
    }
    bulan_pilihan_num = [bulan_map[b] for b in bulan_pilihan]

    # Pastikan kolom tanggallapor datetime
    df_ketidaksesuaian["tanggallapor"] = pd.to_datetime(df_ketidaksesuaian["tanggallapor"], dayfirst=True, errors="coerce")
    df_ketidaksesuaian["tahun"] = df_ketidaksesuaian["tanggallapor"].dt.year
    df_ketidaksesuaian["bulan"] = df_ketidaksesuaian["tanggallapor"].dt.month

    df_filtered = df_ketidaksesuaian[
        (df_ketidaksesuaian["tahun"].isin(tahun_pilihan)) &
        (df_ketidaksesuaian["bulan"].isin(bulan_pilihan_num)) &
        (df_ketidaksesuaian["status_temuan"] == "Valid")
    ]
    
    # Filter site & perusahaan juga
    df_filtered = apply_site_perusahaan_filter(df_filtered)
    
    return df_filtered

# ==============================
# Apply ke semua dataframe
# ==============================
df_timbulan_filtered = apply_site_perusahaan_filter(df_timbulan)
df_prog_filtered = apply_program_filter(df_prog_long, tahun_pilihan, bulan_pilihan)
df_ket_filtered = apply_ketidaksesuaian_filter(df_ketidaksesuaian, tahun_pilihan, bulan_pilihan)
df_online_filtered = apply_site_perusahaan_filter(df_online)
df_offline_filtered = apply_site_perusahaan_filter(df_offline)

df_cctv_filtered = apply_site_perusahaan_filter(df_cctv)
df_koordinat_filtered = apply_site_perusahaan_filter(df_koordinat)

# ==============================
# Hitung total setelah filter
# ==============================
total_timbulan = df_timbulan_filtered["timbulan"].sum() if "timbulan" in df_timbulan_filtered.columns else 0
total_program = df_prog_filtered["Value"].sum() if "Value" in df_prog_filtered.columns else 0

#=============================================================================================================


st.markdown(
    """
    <h1 style="font-size:24px; color:#000000; font-weight:bold; margin-bottom:0.5px;">
    📈Dashboard Gerakan Buang Sampah terpilah (GBST)
    </h1>
    """,
    unsafe_allow_html=True
)

# ===============================
# UTILITIES
# ===============================


def company_to_code(s: pd.Series) -> pd.Series:
    """
    Seragamkan nama perusahaan menjadi kode singkat.
    Contoh: 'PT PAMA' -> 'PAMA', 'PT BUMA' -> 'BUMA', 'FAD' -> 'FAD'
    """
    return (
        s.astype(str)
         .str.upper()
         .str.replace(r"[^A-Z ]", "", regex=True)
         .str.split()
         .apply(lambda t: t[-1] if len(t) else "")
    )

def combine_kapasitas(df: pd.DataFrame) -> pd.DataFrame:
    """Gabungkan seluruh kolom 'kapasitas*' menjadi 'kapasitas_total'."""
    kap_cols = [c for c in df.columns if c.startswith("kapasitas")]
    if kap_cols:
        df["kapasitas_total"] = df[kap_cols].apply(
            lambda row: pd.to_numeric(row, errors="coerce").fillna(0).sum(), axis=1
        )
    else:
        df["kapasitas_total"] = 0
    return df



# ===============================
# TAB
# ===============================
tab1, tab2 = st.tabs(["Overview", "Data Quality Check"])

with tab1:
    #try:
        # ---------- METRIC DASAR ----------
        if "timbulan" in df_timbulan_filtered.columns:
            df_timbulan_filtered["timbulan"] = pd.to_numeric(df_timbulan_filtered["timbulan"].astype(str).str.replace(",", "."), errors="coerce")
            total_timbulan = df_timbulan_filtered["timbulan"].sum()
            total_timbulan_all = pd.to_numeric(df_timbulan_filtered.get("data_input_total", 0), errors="coerce").sum()

            if "man_power" in df_timbulan_filtered.columns:
                manpower_unique = pd.to_numeric(pd.Series(df_timbulan_filtered["man_power"].unique()).astype(str).str.replace(",", "."), errors="coerce")
                total_manpower = manpower_unique.sum()
            else:
                total_manpower = 0
            rasio_manpower = (total_timbulan / total_manpower) if total_manpower > 0 else 0
        else:
            total_timbulan = total_timbulan_all = total_manpower = rasio_manpower = 0

        if "nama_program" in df_prog_filtered.columns:
            jumlah_program = df_prog_filtered["nama_program"].dropna().shape[0]
        elif "nama_program" not in df_prog_filtered.columns and "nama program" in all_df.get("Program", pd.DataFrame()).columns:
            # kalau header belum ternormalisasi
            jumlah_program = all_df["Program"]["Nama program"].dropna().shape[0]
        else:
            jumlah_program = 0

        if "status_temuan" in df_ket_filtered.columns:
            total_ketidaksesuaian = df_ket_filtered.query("status_temuan == 'Valid'").shape[0]
            temuan_masuk = df_ket_filtered["status_temuan"].count()
        else:
            total_ketidaksesuaian, temuan_masuk = 0, 0

        # ---------- TAMPILKAN METRIC ----------
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Total Timbulan (kg)</h6>
                    <p style="font-size:40px;  margin:0;margin-top:0;">{total_timbulan_all:,.0f}</p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;">per 8 dari <strong>{int(total_manpower):,}</strong> manpower</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Rata-rata Timbulan (kg/hari)</h6>
                    <p style="font-size:40px; margin:0;margin-top:0;">{total_timbulan:.2f}</p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;"> dengan <strong>{rasio_manpower:.2f}</strong> kg/hari/manpower</p>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Jumlah Program Existing</h6>
                    <p style="font-size:40px;  margin:0;margin-top:0;">{jumlah_program}</p>
                </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Jumlah Ketidaksesuaian Valid</h6>
                    <p style="font-size:40px; margin:0;margin-top:0;">{total_ketidaksesuaian:,}</p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;">dari <strong>{temuan_masuk}</strong> temuan masuk</p>
                </div>
            """, unsafe_allow_html=True)


        # ==========================================================
        #         ========== PENGOLAHAN & PENGURANGAN ==========
        # ==========================================================
        # Periode hari (silakan sesuaikan)
        days_period = 609

        # Pastikan kolom numeric untuk program
        if "total_calc" in df_prog_filtered.columns:
            df_prog_filtered["total_calc"] = pd.to_numeric(
                df_prog_filtered["total_calc"].astype(str).str.replace(",", ".").str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            ).fillna(0)
        elif "Total_calc" in all_df.get("Program", pd.DataFrame()).columns:
            # Jika nama kolom belum ternormalisasi
            df_prog_filtered["total_calc"] = pd.to_numeric(
                all_df["Program"]["Total_calc"].astype(str).str.replace(",", ".").str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            ).fillna(0)
        else:
            df_prog_filtered["total_calc"] = 0

        total_program = float(df_prog_filtered["total_calc"].sum())
        avg_timbulan_perhari = float(total_timbulan)
        avg_program_perhari = total_program / days_period if days_period > 0 else 0
        persentase_terkelola = (avg_program_perhari / avg_timbulan_perhari) * 100 if avg_timbulan_perhari > 0 else 0

        # --- Pengolahan Sampah ---
        if "kategori" in df_prog_filtered.columns:
            df_pengolahan = df_prog_filtered[df_prog_filtered["kategori"] == "Program Pengelolaan"]
            total_pengolahan = df_pengolahan["total_calc"].sum() / days_period if days_period > 0 else 0
            persen_pengolahan = (total_pengolahan / total_timbulan * 100) if total_timbulan > 0 else 0
        else:
            total_pengolahan, persen_pengolahan = 0, 0

        # --- Pengurangan Sampah ---
        if "kategori" in df_prog_filtered.columns:
            df_pengurangan = df_prog_filtered[df_prog_filtered["kategori"] == "Program Pengurangan"]
            total_pengurangan = df_pengurangan["total_calc"].sum() / days_period if days_period > 0 else 0
            persen_pengurangan = (total_pengurangan / total_timbulan * 100) if total_timbulan > 0 else 0
        else:
            total_pengurangan, persen_pengurangan = 0, 0

        # --- Sisa Timbulan ---
        total_sisa = total_timbulan - total_pengolahan
        persen_sisa = (total_sisa / total_timbulan * 100) if total_timbulan > 0 else 0
        persen_sisa = min(max(persen_sisa, 0), 100)
        persen_pengolahan = min(persen_pengolahan, 100)
        persen_pengurangan = min(persen_pengurangan, 100)

        # ---------- CSS Card ----------
        st.markdown("""
            <style>
            .card {
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
                background-color: #ffffff;
                box-shadow: 3px 3px 12px rgba(0,0,0,0.1);
                text-align: center;
                margin-bottom: 5px;
            }
            .card h3 {
                font-size: 20px;
                color: #333333;
                margin-bottom: 5px;
            }
            .card h2 {
                font-size: 40px;
                color: #257d0a;
                margin: 0;
                margin-bottom:0;
            }
            .card p {
                font-size: 20px;
                color: #666666;
                margin-top:0;
                margin-bottom:0;
            }
            </style>
        """, unsafe_allow_html=True)

        # ---------- TAMPILKAN CARD ----------
        colA, colB, colC = st.columns(3)
        with colA:
            st.markdown(
                f"""
                <div class="card">
                    <h3>Pengurangan Sampah (Reduce)</h3>
                    <h2>{total_pengurangan:,.0f}</h2>
                    <p>kg/hari</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with colB:
            st.markdown(
                f"""
                <div class="card">
                    <h3>Pengolahan Sampah</h3>
                    <h2>{persen_pengolahan:.2f}%</h2>
                    <p>{total_pengolahan:,.0f} kg/hari dari timbulan</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with colC:
            st.markdown(
                f"""
                <div class="card">
                    <h3>Timbulan Tidak Terkelola</h3>
                    <h2>{persen_sisa:.2f}%</h2>
                    <p>{total_sisa:,.0f} kg/hari</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        # ==========================================================
        #                      	   PETA
        # ==========================================================
    
        st.markdown('<p style="text-align: center;font-weight: bold;">🗺️ Peta Lokasi Site & Timbulan Sampah</p>', unsafe_allow_html=True)

        if not df_timbulan.empty and not df_koordinat.empty:
            # Normalisasi isi kolom penting
            for col in ["site", "perusahaan"]:
                if col in df_timbulan.columns:
                    df_timbulan[col] = df_timbulan[col].astype(str).str.strip()

            for col in ["site", "company"]:
                if col in df_koordinat.columns:
                    df_koordinat[col] = df_koordinat[col].astype(str).str.strip()

            # Company code agar match antar sheet
            df_timbulan["company_code"] = company_to_code(df_timbulan.get("perusahaan", ""))
            df_koordinat["company_code"] = company_to_code(df_koordinat.get("company", ""))

            # Gabung semua kapasitas -> kapasitas_total
            df_timbulan = combine_kapasitas(df_timbulan)

            # Agregasi per (site, company_code)
            agg = (
                df_timbulan.groupby(["site", "company_code"], as_index=False)
                .agg(
                    total_timbulan=("timbulan", "sum"),
                    sampah_terkelola=("kapasitas_total", "sum"),
                )
            )
            agg["sampah_tidak_terkelola"] = agg["total_timbulan"] - agg["sampah_terkelola"]

            # Koordinat numeric + drop NA
            if "x" in df_koordinat.columns and "y" in df_koordinat.columns:
                df_koordinat["x"] = pd.to_numeric(df_koordinat["x"], errors="coerce")
                df_koordinat["y"] = pd.to_numeric(df_koordinat["y"], errors="coerce")
                df_koordinat = df_koordinat.dropna(subset=["x", "y"])

            # Merge pakai (site, company_code) -> supaya titik tepat per perusahaan di tiap site
            df_map = df_koordinat.merge(agg, on=["site", "company_code"], how="left")

            if not df_map.empty:
                # Konversi UTM (EPSG:32650) -> WGS84
                transformer = Transformer.from_crs("epsg:32650", "epsg:4326", always_xy=True)
                lon, lat = transformer.transform(df_map["x"].values, df_map["y"].values)
                df_map["lon"] = lon
                df_map["lat"] = lat

                # Render peta
                center_lat = float(df_map["lat"].mean())
                center_lon = float(df_map["lon"].mean())
                fmap = folium.Map(location=[center_lat, center_lon], zoom_start=8)

                cluster = MarkerCluster().add_to(fmap)
                for _, r in df_map.iterrows():
                    perusahaan_display = ("PT " + r["company_code"]) if r.get("company_code", "") else "-"
                    popup_html = f"""
                    <b>Site:</b> {r.get('site','-')}<br>
                    <b>Perusahaan:</b> {perusahaan_display}<br>
                    <b>Total Timbulan:</b> {r.get('total_timbulan',0):,.0f} kg<br>
                    <b>Sampah Terkelola:</b> {r.get('sampah_terkelola',0):,.0f} kg<br>
                    <b>Sampah Tidak Terkelola:</b> {r.get('sampah_tidak_terkelola',0):,.0f} kg
                    """
                    folium.Marker(
                        location=[r["lat"], r["lon"]],
                        tooltip=f"{r['site']} - {perusahaan_display}",
                        popup=popup_html,
                        icon=folium.Icon(color="green", icon="trash", prefix="fa"),
                    ).add_to(cluster)

                st_folium(fmap, height=520, use_container_width=True)
            else:
                st.warning("⚠️ Data peta kosong setelah proses merge. Cek kecocokan site & perusahaan.")
        else:
            st.warning("⚠️ Data Timbulan atau Koordinat kosong.")

        # ===============================
        # GRAFIK & ANALISIS
        # ===============================
        import plotly.express as px
        import streamlit as st
        import pandas as pd
        import numpy as np
        import plotly.graph_objects as go
        import math

        #dt_timbulan = all_df.get("Timbulan", pd.DataFrame())
        #dt_program = all_df.get("Program", pd.DataFrame())


        col1, col2 = st.columns([0.5, 0.5])

        # Pilih palette yang sama seperti pie chart (Viridis)
        if not df_timbulan_filtered.empty and "jenis_timbulan" in df_timbulan_filtered.columns:
            jenis_unique = df_timbulan_filtered["jenis_timbulan"].unique()
            colors = px.colors.sequential.Viridis[:len(jenis_unique)]  # sesuaikan jumlah warna
            color_map = {j: c for j, c in zip(jenis_unique, colors)}

        with col1:
            st.markdown('<p style="text-align: center;font-weight: bold;">🥧 Proporsi Timbulan Berdasarkan Jenis</p>', unsafe_allow_html=True)
            if "jenis_timbulan" in df_timbulan_filtered.columns and not df_timbulan_filtered.empty:
                jenis_sum = df_timbulan_filtered.groupby("jenis_timbulan")["timbulan"].sum()
                fig2 = px.pie(
                    names=jenis_sum.index,
                    values=jenis_sum.values,
                    hole=0.4,
                    color=jenis_sum.index,
                    color_discrete_map=color_map,
                    template="plotly_white"
                )
                fig2.update_traces(
                    textinfo="percent+label",
                    showlegend=False,
                    pull=[0.01]*len(jenis_sum),
                    marker=dict(line=dict(color='white', width=1))
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("Kolom 'Jenis_Timbulan' tidak ditemukan atau data kosong.")

        with col2:
            st.markdown('<p style="text-align:center;font-weight: bold;">Proporsi Timbulan Per Site</p>', unsafe_allow_html=True)

            if not df_timbulan_filtered.empty and "jenis_timbulan" in df_timbulan_filtered.columns:
                total_site = df_timbulan_filtered.groupby(["site", "jenis_timbulan"], as_index=False)["timbulan"].sum()
                    # Hitung total per Site per jenis
                total_site = df_timbulan_filtered.groupby(["site", "jenis_timbulan"], as_index=False)["timbulan"].sum()

                # Urutkan tiap Site berdasarkan jumlah timbulan descending
                total_site = total_site.sort_values(by=["site", "timbulan"], ascending=[True, False])
                fig1 = px.bar(
                    total_site,
                    y="site",
                    x="timbulan",
                    color="jenis_timbulan",
                    orientation='h',
                    text="timbulan",
                    labels={"timbulan": "Total Timbulan (kg/hari)", "jenis_timbulan": "Jenis Timbulan"},
                    color_discrete_map=color_map,  # <--- jangan lupa koma
                    template="plotly_white",
                    height=400
                )
                
                fig1.update_traces(texttemplate='%{text:,.0f}', textposition="outside")
                fig1.update_layout(
                    barmode='stack',
                    margin=dict(t=30, b=30, l=100, r=20),
                    yaxis=dict(tickmode='linear'),
                    bargap=0.2,
                    legend=dict(orientation="h", y=-0.1, x=0.5, xanchor='center')
                )
                
                st.plotly_chart(fig1, use_container_width=True)
            
        # ===============================

        # =====================================================
        # 🔹 SURVEI & KETIDAKSESUAIAN
        # =====================================================
        #st.subheader("📊 Survei & Ketidaksesuaian")
        col1,col2 = st.columns(2)
        with col1:
        # Pie Ketidaksesuaian (Valid)
            if not df_ketidaksesuaian.empty and "kategori_subketidaksesuaian" in df_ketidaksesuaian.columns:
                df_valid = df_ketidaksesuaian[df_ketidaksesuaian["status_temuan"].str.lower() == "valid"]
                if not df_valid.empty:
                    prop = df_valid["kategori_subketidaksesuaian"].value_counts()
                    fig_ket = px.pie(
                        names=prop.index, values=prop.values, hole=0.4,
                        color=prop.index, template="plotly_white",
                        color_discrete_map={"Perilaku":"#347829","Non Perilaku":"#78b00a"}
                    )
                    fig_ket.update_traces(textinfo="percent+label")
                    st.markdown("<p style='font-weight:bold;text-align:center;'>⚠️ Proporsi Ketidaksesuaian</p>", unsafe_allow_html=True)
                    st.plotly_chart(fig_ket, use_container_width=True)
        with col2:
        # Gabung survei online+offline
            df_survey = pd.concat([df_online, df_offline], ignore_index=True)

        # Kolom pertanyaan (biarkan sesuai punyamu)
            col_q = "2. Seberapa optimal program GBST berjalan selama ini di perusahaan Anda?"

            if not df_survey.empty:
                # Kalau nama kolom sedikit berbeda, coba cari yang mirip
                if col_q not in df_survey.columns:
                    candidates = [c for c in df_survey.columns if "optimal" in c.lower() and "gbst" in c.lower()]
                    if candidates:
                        col_q = candidates[0]

            if col_q in df_survey.columns:
                df_survey[col_q] = pd.to_numeric(df_survey[col_q], errors="coerce")
                df_survey = df_survey.dropna(subset=[col_q])
                st.markdown("<p style='font-weight:bold;text-align:center;'>Indeks Optimalisasi GBST</p>", unsafe_allow_html=True)
                if not df_survey.empty:
                    avg_score = df_survey[col_q].mean()
                    max_score = df_survey[col_q].max()
                    max_score = max(max_score, 1)

                    gauge_fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=avg_score,
                        #title={"text": "Rata-rata Skor Optimalitas Program"},
                        gauge={
                            'axis': {'range': [0, max_score]},
                            'bar': {'color': "green"},
                            'steps': [
                                {'range': [0, max_score * 0.5], 'color': "#F58C62"},
                                {'range': [max_score * 0.5, max_score * 0.8], 'color': "#E1EF47"},
                                {'range': [max_score * 0.8, max_score], 'color': "#4CB817"}
                            ]
                        }
                    ))
                    st.plotly_chart(gauge_fig, use_container_width=True)
                else:
                    st.warning("Data survei kosong setelah konversi angka untuk kolom optimalitas.")
            else:
                st.warning(f"Kolom '{col_q}' tidak ditemukan dalam data survei.")

  
    #except Exception as e:
    #st.error("Gagal memproses Overview.")
    #st.exception(e)
        # =============================
        # PROPORSI KESELURUHAN (GROUP BAR)
        # =============================
        # --- Pengolahan Sampah ---
        if "kategori" in df_prog_filtered.columns:
            df_pengolahan = df_prog_filtered[df_prog_filtered["kategori"] == "Program Pengelolaan"]
            total_pengolahan = df_pengolahan["Value"].sum() / days_period if days_period > 0 else 0
            persen_pengolahan = (total_pengolahan / total_timbulan * 100) if total_timbulan > 0 else 0
        else:
            total_pengolahan, persen_pengolahan = 0, 0

            # --- Pengurangan Sampah ---
        if "kategori" in df_prog_filtered.columns:
            df_pengurangan = df_prog_filtered[df_prog_filtered["kategori"] == "Program Pengurangan"]
            total_pengurangan = df_pengurangan["Value"].sum() / days_period if days_period > 0 else 0
            persen_pengurangan = (total_pengurangan / total_timbulan * 100) if total_timbulan > 0 else 0
        else:
            total_pengurangan, persen_pengurangan = 0, 0

        st.markdown('<p style="text-align: center;font-weight: bold;">📊 Proporsi Keseluruhan Timbulan</p>', unsafe_allow_html=True)
        # =============================
        # PROPORSI KESELURUHAN (GROUP BAR)
        # =============================

        # Pastikan kolom numeric
        df_timbulan_filtered["timbulan"] = pd.to_numeric(
            df_timbulan_filtered["timbulan"].astype(str).str.replace(",", "."), errors="coerce"
        )

        # Total timbulan per perusahaan-site
        df_timbulan_sum = df_timbulan_filtered.groupby(["perusahaan", "site"])["timbulan"].sum().reset_index()
        total_timbulan = df_timbulan_sum["timbulan"].sum()

        # --- Filter program ---
        df_pengolahan = df_prog_filtered[df_prog_filtered["kategori"] == "Program Pengelolaan"]
        df_pengurangan = df_prog_filtered[df_prog_filtered["kategori"] == "Program Pengurangan"]

        # --- Hitung total per hari ---
        total_program = df_pengolahan["Value"].sum()
        avg_program_perhari = total_program / days_period if days_period > 0 else 0

        total_reduce = df_pengurangan["Value"].sum() / days_period if days_period > 0 else 0

        # Sampah tidak terkelola
        sampah_tidak_terkelola = total_timbulan - avg_program_perhari

        # =============================
        # Buat figure
        # =============================
        fig_total = go.Figure()

        # Timbulan total
        fig_total.add_trace(go.Bar(
            x=["Keseluruhan"],
            y=[total_timbulan],
            name="Timbulan (kg/hari)",
            hovertemplate="Timbulan: %{y:,.0f} kg/hari<extra></extra>"
        ))

        # Sampah terkelola
        fig_total.add_trace(go.Bar(
            x=["Keseluruhan"],
            y=[avg_program_perhari],
            name="Sampah Terkelola",
            hovertemplate="Terkelola: %{y:,.0f} kg/hari<br>%{customdata:.1f}%<extra></extra>",
            customdata=[(avg_program_perhari/total_timbulan)*100]
        ))

        # Sampah tidak terkelola
        fig_total.add_trace(go.Bar(
            x=["Keseluruhan"],
            y=[sampah_tidak_terkelola],
            name="Sampah Tidak Terkelola",
            hovertemplate="Tidak Terkelola: %{y:,.0f} kg/hari<br>%{customdata:.1f}%<extra></extra>",
            customdata=[(sampah_tidak_terkelola/total_timbulan)*100]
        ))

        # Reduce sampah
        fig_total.add_trace(go.Bar(
            x=["Keseluruhan"],
            y=[total_reduce],
            name="Reduce Sampah",
            hovertemplate="Reduce: %{y:,.0f} kg/hari<br>%{customdata:.1f}%<extra></extra>",
            customdata=[(total_reduce/total_timbulan)*100]
        ))

        # Layout
        fig_total.update_layout(
            barmode='group',
            xaxis_title="Kategori",
            yaxis_title="Kg/hari",
            legend=dict(
                orientation="h",
                yanchor="top",
                y=1,
                xanchor="center",
                x=0.5
            ),
            margin=dict(t=50, b=100)
        )

        #st.markdown('<p style="text-align: center;font-weight: bold;">📊 Proporsi Keseluruhan Timbulan</p>', unsafe_allow_html=True)
        st.plotly_chart(fig_total, use_container_width=True)

#except Exception as e: st.error("Terjadi error di Overview")
#st.exception(e) 
with tab2:
            st.subheader("📋 Preview Data Timbulan")
            if not df_timbulan.empty:
                st.dataframe(df_timbulan.head(100))
            else:
                st.warning("Data Timbulan kosong.")

            st.subheader("📋 Preview Data Program")
            if not df_program.empty:
                st.dataframe(df_program.head(100))
            else:
                st.warning("Data Program kosong.")

            st.subheader("📋 Preview Data Ketidaksesuaian")
            if not df_ketidaksesuaian.empty:
                st.dataframe(df_ketidaksesuaian.head(100))
            else:
                st.warning("Data Ketidaksesuaian kosong.")
