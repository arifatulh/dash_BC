import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math
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

logo = "assets/4logo.png"
#st.sidebar.image("assets/4logo.png", use_column_width=True)

st.logo(logo, icon_image=logo, size="large")


# ===============================
# HEADER DENGAN LOGO
# ===============================

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
def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    """lowercase + strip + underscore untuk nama kolom."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    return df

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

sheet_url = "https://docs.google.com/spreadsheets/d/1cw3xMomuMOaprs8mkmj_qnib-Zp_9n68rYMgiRZZqBE/edit?usp=sharing"

# ambil ID file dari link
sheet_id = sheet_url.split("/")[5]

# daftar sheet yang ingin dibaca
sheet_names = ["Timbulan", "Program", "Ketidaksesuaian", "Survei_Online", "Survei_Offline", "CCTV"]

all_df = {}
for sheet in sheet_names:
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
        df = pd.read_csv(url)
        all_df[sheet] = df
        # kalau pakai Excel
    except Exception as e:
        st.error(f"Gagal load sheet {sheet}: {e}")
# ===============================
# DATA TIMBULAN (contoh ringkas)
# ===============================
#url = "https://docs.google.com/spreadsheets/d/1o3fP4QyjmWGAUQaJ-xXlkQJ8EGte-tYq_cVEKstZouA/edit?usp=sharing#gid=2116345303"

@st.cache_data(ttl=60)
def load_data(url):
    return pd.read_csv(url)


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



# Cara akses di halaman mana pun
dt_timbulan = st.session_state["data"].get("Timbulan", pd.DataFrame())
dt_program = st.session_state["data"].get("Program", pd.DataFrame())
dt_online = st.session_state["data"].get("Survei_Online", pd.DataFrame())
dt_ketidaksesuaian = st.session_state["data"].get("Ketidaksesuaian", pd.DataFrame())
dt_offline = st.session_state["data"].get("Survei_Offline", pd.DataFrame())
dt_cctv = st.session_state["data"].get("CCTV", pd.DataFrame())
dt_koordinat= st.session_state["data"].get("Koordinat_UTM", pd.DataFrame())
df_koordinat = all_df.get("Koordinat_UTM", pd.DataFrame()).copy()
df_koordinat = norm_cols(df_koordinat)

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
df_timbulan = norm_cols(df_timbulan)
df_program = norm_cols(df_program)
df_ketidaksesuaian = norm_cols(df_ketidaksesuaian)
df_online = norm_cols(df_online)
df_offline = norm_cols(df_offline)
df_koordinat = norm_cols(df_koordinat)


# ===============================
# PASTIKAN KOLOM ADA
# ===============================

tab1, tab2 = st.tabs(["Overview", "Data Quality Check"])
with tab1:
    try:
        # ambil data dari all_df
        df_timbulan = all_df.get("Timbulan", pd.DataFrame())
        df_program = all_df.get("Program", pd.DataFrame())
        df_ketidaksesuaian = all_df.get("Ketidaksesuaian", pd.DataFrame())

        # --- col1: Total Timbulan ---
        if "Timbulan" in df_timbulan.columns:
            df_timbulan["Timbulan"] = pd.to_numeric(
                df_timbulan["Timbulan"].astype(str).str.replace(",", "."),
                errors="coerce"
            )
            total_timbulan = df_timbulan["Timbulan"].sum()
            total_timbulan_all = df_timbulan["data_input_total"].sum()

            # Ambil nilai unik dari kolom "Man Power"
            manpower_unique = pd.to_numeric(
                pd.Series(df_timbulan["Man Power"].unique()).astype(str).str.replace(",", "."),
                errors="coerce"
            )

            # Jumlahkan nilai unik manpower
            total_manpower = manpower_unique.sum()

            # Rasio timbulan terhadap total manpower
            rasio_manpower = total_timbulan / total_manpower if total_manpower > 0 else 0
        else:
            total_timbulan = 0
            total_manpower = 0
            rasio_manpower = 0


            # program sheet juga pastikan numeric
        if "Nama program" in df_program.columns:
            df_program["Total_calc"] = pd.to_numeric(df_program["Total_calc"].astype(str).str.replace(",", "."), errors="coerce")
            jumlah_program = df_program["Nama program"].count()
            jumlah_program = df_program["Nama program"].dropna().shape[0]
        else:
            jumlah_program = 0
        # --- col3: Total Ketidaksesuaian Valid ---
        if "status_temuan" in df_ketidaksesuaian.columns:
            total_ketidaksesuaian = df_ketidaksesuaian.query("status_temuan == 'Valid'").shape[0]
            temuan_masuk = df_ketidaksesuaian["status_temuan"].count()
        else:
            total_ketidaksesuaian = 0

            # pastikan numeric dulu
        if "Total_calc" in df_program.columns:
            df_program["Total_calc"] = pd.to_numeric(
                df_program["Total_calc"].astype(str).str.replace(",", ".").str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            )
            total_program = df_program["Total_calc"].sum()
        else:
            total_program = 0

        # --- col4: Persentase rata-rata sampah yang terkelola/terkurangi ---
        days_period = 609  # periode Jan 2024 - Agustus 2025
        if "Total_calc" in df_program.columns and total_timbulan > 0:
            total_program = df_program["Total_calc"].sum()
            avg_timbulan_perhari = total_timbulan 
            avg_program_perhari = total_program / days_period
            persentase_terkelola = (avg_program_perhari / avg_timbulan_perhari) * 100
        else:
            persentase_terkelola = 0

        # ===============================
        # TAMPILKAN METRIC
        # ===============================
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Total Timbulan          (kg)</h6>
                    <p style="font-size:40px;  margin:0;margin-top:0;">{total_timbulan_all:,.0f}</p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;">per 8 dari <strong>{total_manpower:,}</strong> manpower</p>
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
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Jumlah Program Existing               </h6>
                    <p style="font-size:40px;  margin:0;margin-top:0;">{jumlah_program}</p>
                </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Jumlah Ketidaksesuaian Valid</h6>
                    <p style="font-size:40px; margin:0;margin-top:0;">{total_ketidaksesuaian:,}</p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;">dari <strong>{temuan_masuk} </strong>temuan masuk</p>
                </div>
            """, unsafe_allow_html=True)
        


    except Exception as e:
        st.error("Gagal menghitung metric.")
        st.exception(e)

        # ========== PENGOLAHAN & PENGURANGAN ==========

        total_program = df_program["Total_calc"].sum()
        avg_timbulan_perhari = total_timbulan 
        avg_program_perhari = total_program / days_period
        persentase_terkelola = (avg_program_perhari / avg_timbulan_perhari) * 100    
    # --- Pengolahan Sampah ---
    if "Kategori" in df_program.columns:
        df_pengolahan = df_program[df_program["Kategori"] == "Program Pengelolaan"]
        total_pengolahan = df_pengolahan["Total_calc"].sum()/days_period
        persen_pengolahan = (total_pengolahan / total_timbulan * 100) if total_timbulan > 0 else 0
    else:
        total_pengolahan, persen_pengolahan = 0, 0

    # --- Pengurangan Sampah ---
    if "Kategori" in df_program.columns:
        df_pengurangan = df_program[df_program["Kategori"] == "Program Pengurangan"]
        total_pengurangan = df_pengurangan["Total_calc"].sum()/days_period
        persen_pengurangan = (total_pengurangan / total_timbulan * 100) if total_timbulan > 0 else 0
    else:
        total_pengurangan, persen_pengurangan = 0, 0
    # --- Sisa Timbulan ---
    total_sisa = total_timbulan - total_pengolahan
    persen_sisa = (total_sisa / total_timbulan * 100)
    persen_sisa = max(persen_sisa, 0)  # jangan negatif
    persen_sisa = min(persen_sisa, 100)  # jangan lebih dari 100%
    persen_pengolahan = min(persen_pengolahan, 100)
    persen_pengurangan = min(persen_pengurangan, 100)


    # ===============================
        # CSS untuk card-box 3D
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
            color: #257d0a; /* hijau untuk kesan environment */
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

    # TAMPILKAN BOX
    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown(
            f"""
            <div class="card">
                <h3>Pengurangan Sampah (Reduce)</h3>
                <h2>{total_pengurangan:,.0f} </h2>
                <p>kg/hari</p>
            </div>
            """
            ,
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
        # UTILITIES
        # ===============================
        
    def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
            """lowercase + strip + underscore untuk nama kolom."""
            df = df.copy()
            df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
            return df

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
    

    df_koordinat = all_df.get("Koordinat_UTM", pd.DataFrame()).copy()

    st.markdown('<p style="text-align: center;font-weight: bold;">🗺️ Peta Lokasi Site & Timbulan Sampah</p>',unsafe_allow_html=True)

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

    dt_timbulan = all_df.get("Timbulan", pd.DataFrame())
    dt_program = all_df.get("Program", pd.DataFrame())


    col1, col2 = st.columns([0.5, 0.5])

    # Pilih palette yang sama seperti pie chart (Viridis)
    if not dt_timbulan.empty and "jenis_timbulan" in dt_timbulan.columns:
        jenis_unique = dt_timbulan["jenis_timbulan"].unique()
        colors = px.colors.sequential.Viridis[:len(jenis_unique)]  # sesuaikan jumlah warna
        color_map = {j: c for j, c in zip(jenis_unique, colors)}

    with col1:
        st.markdown('<p style="text-align: center;font-weight: bold;">🥧 Proporsi Timbulan Berdasarkan Jenis</p>', unsafe_allow_html=True)
        if "jenis_timbulan" in dt_timbulan.columns and not dt_timbulan.empty:
            jenis_sum = dt_timbulan.groupby("jenis_timbulan")["Timbulan"].sum()
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

        if not dt_timbulan.empty and "jenis_timbulan" in dt_timbulan.columns:
            total_site = dt_timbulan.groupby(["Site", "jenis_timbulan"], as_index=False)["Timbulan"].sum()
                # Hitung total per Site per jenis
            total_site = dt_timbulan.groupby(["Site", "jenis_timbulan"], as_index=False)["Timbulan"].sum()

            # Urutkan tiap Site berdasarkan jumlah timbulan descending
            total_site = total_site.sort_values(by=["Site", "Timbulan"], ascending=[True, False])
            fig1 = px.bar(
                total_site,
                y="Site",
                x="Timbulan",
                color="jenis_timbulan",
                orientation='h',
                text="Timbulan",
                labels={"Timbulan": "Total Timbulan (kg)", "jenis_timbulan": "Jenis Timbulan"},
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
        else:
            st.warning("Data kosong atau kolom 'jenis_timbulan' tidak ditemukan.")

    # ===============================
    import streamlit as st
    import pandas as pd
    import plotly.graph_objects as go

    # Ambil data survei
    dt_online = all_df.get("Survei_Online", pd.DataFrame())
    dt_offline = all_df.get("Survei_Offline", pd.DataFrame())
    df_survey = pd.concat([dt_online, dt_offline], ignore_index=True)

    # Kolom pertanyaan
    col_q = "2. Seberapa optimal program GBST berjalan selama ini di perusahaan Anda?"

    if col_q in df_survey.columns:
        df_survey[col_q] = pd.to_numeric(df_survey[col_q], errors="coerce")
        df_survey = df_survey.dropna(subset=[col_q])

        if not df_survey.empty:
            col1, col2 = st.columns([0.4, 0.6])  # sama besar
            with st.container():
            # --- Col1: Gauge rata-rata ---
                with col2:
                     # --- Gauge Indeks Optimalisasi ---
                    #if "Kategori Subketidaksesuaian" in df_valid.columns and not df_valid.empty:

                        st.markdown("<p style='font-weight: bold; text-align: center;'>🎖️Indeks Optimalisasi GBST </p>", unsafe_allow_html=True)
                        avg_score = df_survey[col_q].mean()
                        max_score = df_survey[col_q].max()
                        max_score = max(max_score, 1)

                        gauge_fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=avg_score,
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

                # --- Col2: Bar chart ranking ---
                with col1:
                    
                    # ---------------- COL2: Bawah - Proporsi Pengurangan/Pengelolaan/Sisa ----------------
                # Ambil dataframe ketidaksesuaian
                    df_ketidaksesuaian = all_df.get("Ketidaksesuaian", pd.DataFrame())

                    # Filter hanya Valid
                    df_valid = df_ketidaksesuaian[df_ketidaksesuaian["status_temuan"] == "Valid"]

                    # Pastikan kolom Subketidaksesuaian ada
                    if "Kategori Subketidaksesuaian" in df_valid.columns and not df_valid.empty:
                        st.markdown("<p style='font-weight: bold; text-align: center;'>⚠️ Proporsi Ketidaksesuaian Perilaku / Non-Perilaku</p>", unsafe_allow_html=True)

                        proporsi = df_valid["Kategori Subketidaksesuaian"].value_counts()
                        
                        fig = px.pie(
                            names=proporsi.index,
                            values=proporsi.values,
                            hole=0.4,
                            color=proporsi.index,
                            color_discrete_map={
                                "Perilaku": "#347829",
                                "Non Perilaku": "#78b00a"
                            },
                            template="plotly_white"
                        )
                        fig.update_traces(textinfo="percent+label", pull=[0.01]*len(proporsi))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Data Ketidaksesuaian Valid kosong atau kolom 'Kategori Subketidaksesuaian' tidak ditemukan.")            
        else:
            st.warning(f"Kolom '{col_q}' tidak ditemukan dalam data survei.")

            


with tab2:
    st.subheader("📋 Preview Data Timbulan")
    if not df_timbulan.empty:
        st.dataframe(df_timbulan.head(100))  # tampil 100 baris pertama
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