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
# TAB
# ===============================
tab1, tab2 = st.tabs(["Overview", "Data Quality Check"])

with tab1:
    try:
        # ---------- METRIC DASAR ----------
        if "timbulan" in df_timbulan.columns:
            df_timbulan["timbulan"] = pd.to_numeric(df_timbulan["timbulan"].astype(str).str.replace(",", "."), errors="coerce")
            total_timbulan = df_timbulan["timbulan"].sum()
            total_timbulan_all = pd.to_numeric(df_timbulan.get("data_input_total", 0), errors="coerce").sum()

            if "man_power" in df_timbulan.columns:
                manpower_unique = pd.to_numeric(pd.Series(df_timbulan["man_power"].unique()).astype(str).str.replace(",", "."), errors="coerce")
                total_manpower = manpower_unique.sum()
            else:
                total_manpower = 0
            rasio_manpower = (total_timbulan / total_manpower) if total_manpower > 0 else 0
        else:
            total_timbulan = total_timbulan_all = total_manpower = rasio_manpower = 0

        if "nama_program" in df_program.columns:
            jumlah_program = df_program["nama_program"].dropna().shape[0]
        elif "nama_program" not in df_program.columns and "nama program" in all_df.get("Program", pd.DataFrame()).columns:
            # kalau header belum ternormalisasi
            jumlah_program = all_df["Program"]["Nama program"].dropna().shape[0]
        else:
            jumlah_program = 0

        if "status_temuan" in df_ketidaksesuaian.columns:
            total_ketidaksesuaian = df_ketidaksesuaian.query("status_temuan == 'Valid'").shape[0]
            temuan_masuk = df_ketidaksesuaian["status_temuan"].count()
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
        if "total_calc" in df_program.columns:
            df_program["total_calc"] = pd.to_numeric(
                df_program["total_calc"].astype(str).str.replace(",", ".").str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            ).fillna(0)
        elif "Total_calc" in all_df.get("Program", pd.DataFrame()).columns:
            # Jika nama kolom belum ternormalisasi
            df_program["total_calc"] = pd.to_numeric(
                all_df["Program"]["Total_calc"].astype(str).str.replace(",", ".").str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            ).fillna(0)
        else:
            df_program["total_calc"] = 0

        total_program = float(df_program["total_calc"].sum())
        avg_timbulan_perhari = float(total_timbulan)
        avg_program_perhari = total_program / days_period if days_period > 0 else 0
        persentase_terkelola = (avg_program_perhari / avg_timbulan_perhari) * 100 if avg_timbulan_perhari > 0 else 0

        # --- Pengolahan Sampah ---
        if "kategori" in df_program.columns:
            df_pengolahan = df_program[df_program["kategori"] == "Program Pengelolaan"]
            total_pengolahan = df_pengolahan["total_calc"].sum() / days_period if days_period > 0 else 0
            persen_pengolahan = (total_pengolahan / total_timbulan * 100) if total_timbulan > 0 else 0
        else:
            total_pengolahan, persen_pengolahan = 0, 0

        # --- Pengurangan Sampah ---
        if "kategori" in df_program.columns:
            df_pengurangan = df_program[df_program["kategori"] == "Program Pengurangan"]
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
        st.subheader("🗺️ Peta Lokasi Site & Timbulan Sampah")

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

        # ==========================================================
        #                    GRAFIK & ANALISIS
        # ==========================================================
        dt_timbulan = all_df.get("Timbulan", pd.DataFrame()).copy()
        dt_program = all_df.get("Program", pd.DataFrame()).copy()
        dt_timbulan = norm_cols(dt_timbulan)

        col_left, col_right = st.columns([0.5, 0.5])

        # Pie Jenis Timbulan
        with col_left:
            st.markdown('<p style="text-align: center;font-weight: bold;">🥧 Proporsi Timbulan Berdasarkan Jenis</p>', unsafe_allow_html=True)
            if "jenis_timbulan" in dt_timbulan.columns and not dt_timbulan.empty:
                dt_timbulan["timbulan"] = pd.to_numeric(dt_timbulan["timbulan"].astype(str).str.replace(",", "."), errors="coerce")
                jenis_sum = dt_timbulan.groupby("jenis_timbulan")["timbulan"].sum()
                colors = px.colors.sequential.Viridis[:len(jenis_sum)]
                color_map = {j: c for j, c in zip(jenis_sum.index, colors)}
                fig2 = px.pie(
                    names=jenis_sum.index,
                    values=jenis_sum.values,
                    hole=0.4,
                    color=jenis_sum.index,
                    color_discrete_map=color_map,
                    template="plotly_white"
                )
                fig2.update_traces(textinfo="percent+label", showlegend=False, pull=[0.01]*len(jenis_sum))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("Kolom 'jenis_timbulan' tidak ditemukan atau data kosong.")

        # Bar Stacked per Site
        with col_right:
            st.markdown('<p style="text-align:center;font-weight: bold;">Proporsi Timbulan Per Site</p>', unsafe_allow_html=True)
            if not dt_timbulan.empty and "jenis_timbulan" in dt_timbulan.columns and "site" in dt_timbulan.columns:
                total_site = (
                    dt_timbulan.groupby(["site", "jenis_timbulan"], as_index=False)["timbulan"]
                    .sum()
                    .sort_values(by=["site", "timbulan"], ascending=[True, False])
                )
                colors = px.colors.sequential.Viridis[: total_site["jenis_timbulan"].nunique()]
                color_map = {j: c for j, c in zip(total_site["jenis_timbulan"].unique(), colors)}
                fig1 = px.bar(
                    total_site,
                    y="site",
                    x="timbulan",
                    color="jenis_timbulan",
                    orientation="h",
                    text="timbulan",
                    labels={"timbulan": "Total Timbulan (kg)", "jenis_timbulan": "Jenis Timbulan"},
                    color_discrete_map=color_map,
                    template="plotly_white",
                    height=420
                )
                fig1.update_traces(texttemplate='%{text:,.0f}', textposition="outside")
                fig1.update_layout(barmode='stack', margin=dict(t=30, b=30, l=100, r=20))
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("Data kosong atau kolom 'jenis_timbulan/site' tidak ditemukan.")

        # ====== SURVEI OPTIMALITAS (Gauge + Pie Ketidaksesuaian) ======
        dt_online = norm_cols(all_df.get("Survei_Online", pd.DataFrame()))
        dt_offline = norm_cols(all_df.get("Survei_Offline", pd.DataFrame()))
        df_survey = pd.concat([dt_online, dt_offline], ignore_index=True)

        col_q = "2._seberapa_optimal_program_gbst_berjalan_selama_ini_di_perusahaan_anda?"
        if col_q in df_survey.columns:
            vals = pd.to_numeric(df_survey[col_q], errors="coerce").dropna()
            if not vals.empty:
                c_gauge, c_ket = st.columns([0.5, 0.5])
                with c_gauge:
                    avg_score = float(vals.mean())
                    max_score = max(float(vals.max()), 1.0)
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

                with c_ket:
                    df_valid = df_ketidaksesuaian[df_ketidaksesuaian.get("status_temuan", "") == "Valid"]
                    if "kategori_subketidaksesuaian" in df_valid.columns and not df_valid.empty:
                        st.markdown("<p style='font-weight: bold; text-align: center;'>⚠️ Proporsi Ketidaksesuaian Perilaku / Non-Perilaku</p>", unsafe_allow_html=True)
                        proporsi = df_valid["kategori_subketidaksesuaian"].value_counts()
                        fig = px.pie(
                            names=proporsi.index,
                            values=proporsi.values,
                            hole=0.4,
                            color=proporsi.index,
                            color_discrete_map={"PERILAKU": "#347829", "NON PERILAKU": "#78b00a"},
                            template="plotly_white"
                        )
                        fig.update_traces(textinfo="percent+label", pull=[0.01]*len(proporsi))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Data Ketidaksesuaian Valid kosong atau kolom 'Kategori Subketidaksesuaian' tidak ditemukan.")
            else:
                st.warning("Data survei kosong.")
        else:
            st.warning(f"Kolom pertanyaan survei tidak ditemukan.")

    except Exception as e:
        st.error("Gagal memproses Overview.")
        st.exception(e)

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
