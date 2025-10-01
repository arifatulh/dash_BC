# pages/Ketidaksesuaian
import math
import io, base64

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp

from sklearn.feature_extraction.text import CountVectorizer

#st.title("📝 Survei GBST (Offline & Online)")

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



all_df = {}
for sheet in sheet_names:
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
        df = pd.read_csv(url)
        all_df[sheet] = df
        # kalau pakai Excel
    except Exception as e:
        st.error(f"Gagal load sheet {sheet}: {e}")

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
            data_dict[sheet] = df
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


    # Ambil data survei
dt_online = all_df.get("Survei_Online", pd.DataFrame())
dt_offline = all_df.get("Survei_Offline", pd.DataFrame())
df_survey = pd.concat([dt_online, dt_offline], ignore_index=True)
st.markdown(
    """
    <h1 style="font-size:24px; color:#000000; font-weight:bold; margin-bottom:0.5px;">
    📝 Ketidaksesuaian Pengelolaan Sampah
    </h1>
    """,
    unsafe_allow_html=True
)

@st.cache_data(ttl=60)
def load_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(url)
# pages/ketidaksesuaian.py
# pages/ketidaksesuaian.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==================== LOAD DATA ====================
# Pastikan data sudah ada di session_state
if "data" in st.session_state and isinstance(st.session_state["data"], dict):
    df = st.session_state["data"].get("Ketidaksesuaian", pd.DataFrame())
else:
    df = st.session_state.get("Ketidaksesuaian", pd.DataFrame())

if df.empty:
    st.warning("❌ Data `Ketidaksesuaian` tidak ditemukan di session_state.")
    st.stop()

# ==================== NORMALISASI KOLOM ====================
# Samakan nama kolom supaya konsisten
df.columns = df.columns.astype(str).str.strip()

# Normalisasi kolom status
df["status_temuan"] = df["status_temuan"].astype(str).str.strip().str.title()

# Normalisasi kolom kategori subketidaksesuaian
df["kategori_subketidaksesuaian"] = (
    df["kategori_subketidaksesuaian"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
    .str.title()
)

# ==================== HITUNG METRICS ====================
total_reports = len(df)

# Filter valid
df_valid = df[df["status_temuan"] == "Valid"].copy()
total_valid = len(df_valid)
pct_valid = (total_valid / total_reports * 100) if total_reports > 0 else 0

# Hitung jumlah Perilaku / Non Perilaku
count_perilaku = (df_valid["kategori_subketidaksesuaian"] == "Perilaku").sum()
count_nonperilaku = (df_valid["kategori_subketidaksesuaian"] == "Non Perilaku").sum()

pct_perilaku = (count_perilaku / total_valid * 100) if total_valid > 0 else 0
pct_nonperilaku = (count_nonperilaku / total_valid * 100) if total_valid > 0 else 0

# ==================== TAMPILKAN METRICS ====================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div style="text-align:left; padding:0.5px; border-radius:2px;">
            <h6 style="margin-bottom:0;font-weight:normal;">Jumlah Laporan</h6>
            <p style="font-size:40px; margin:0;">{total_reports:,}</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div style="text-align:left; padding:0.5px; border-radius:2px;">
            <h6 style="margin-bottom:0;font-weight:normal;">Laporan Valid</h6>
            <p style="font-size:40px; margin:0;">{total_valid:,}</p>
            <p style="font-size:14px; color:#3BB143;">{pct_valid:.1f}% dari total</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div style="text-align:left; padding:0.5px; border-radius:2px;">
            <h6 style="margin-bottom:0;font-weight:normal;">Kategori Perilaku</h6>
            <p style="font-size:40px; margin:0;">{count_perilaku:,}</p>
            <p style="font-size:14px; color:#3BB143;">{pct_perilaku:.1f}% dari valid</p>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div style="text-align:left; padding:0.5px; border-radius:2px;">
            <h6 style="margin-bottom:0;font-weight:normal;">Kategori Non Perilaku</h6>
            <p style="font-size:40px; margin:0;">{count_nonperilaku:,}</p>
            <p style="font-size:14px; color:#3BB143;">{pct_nonperilaku:.1f}% dari valid</p>
        </div>
    """, unsafe_allow_html=True)


# ========== DUA METRIC KIRI: Tren & Proporsi Sub-ketidaksesuaian ==========
#colA, colB = st.columns(2)

# --- Tren Perilaku vs Non Perilaku (hanya valid)
    # --- Tren Perilaku vs Non Perilaku (hanya valid)
#with colA:
st.subheader("📈 Tren: Perilaku vs Non-Perilaku (Valid)")

col_tgl = "tanggallapor"  # pakai kolom TanggalLapor (sudah dinormalisasi)
    
if col_tgl in df_valid.columns:
        try:
            df_valid[col_tgl] = pd.to_datetime(df_valid[col_tgl], errors="coerce")
        except Exception:
            df_valid[col_tgl] = pd.to_datetime(df_valid[col_tgl].astype(str), errors="coerce")

        # buat agregasi per bulan
        df_valid["period_month"] = df_valid[col_tgl].dt.to_period("M")

        if "kategori_subketidaksesuaian" in df_valid.columns:
            trend = (
                df_valid.groupby(["period_month", "kategori_subketidaksesuaian"])
                .size().reset_index(name="count")
            )
            if trend.empty:
                st.info("Tidak ada data tanggal yang valid untuk membuat tren.")
            else:
                pivot = trend.pivot(
                    index="period_month", 
                    columns="kategori_subketidaksesuaian", 
                    values="count"
                ).fillna(0)
                pivot.index = pivot.index.to_timestamp()

                fig = go.Figure()
                for col in pivot.columns:
                    fig.add_trace(go.Scatter(
                        x=pivot.index, y=pivot[col],
                        mode="lines+markers", name=col
                    ))
                fig.update_layout(
                    height=350,
                    xaxis_title="Bulan",
                    yaxis_title="Jumlah Laporan (Valid)",
                    legend_title=""
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Kolom kategori_subketidaksesuaian tidak ditemukan.")
else:
        st.info("Kolom 'TanggalLapor' tidak ditemukan di data.")

   
# --- Proporsi berdasarkan sub-ketidaksesuaian (hanya valid)
#with colB:
st.subheader("📊 Proporsi berdasarkan Sub-Ketidaksesuaian (Valid)")

import plotly.express as px

# Definisi kategori
perilaku_list = [
    "[ENV] Sampah tidak terpilah",
    "[ENV] Sampah dibuang tidak pada tempat sampah"
]

non_perilaku_list = [
    "[ENV] Tidak terdapat jadwal pengangkutan sampah",
    "[ENV] Tidak ada tempat sampah sesuai jenis sampah",
    "[ENV] Pengangkutan sampah tidak sesuai jadwal",
    "[ENV] Pengangkutan sampah tidak terpilah",
    "[ENV] Tempat sampah penuh",
    "[ENV] Tidak ada logbook pencatatan timbulan sampah"
]

# Filter hanya valid
df_valid = df[df["status_temuan"].str.lower() == "valid"].copy()

if not df_valid.empty:
    # Mapping kategori sub-ketidaksesuaian
    def map_kategori(x):
        if x in perilaku_list:
            return "Perilaku"
        elif x in non_perilaku_list:
            return "Non Perilaku"
        else:
            return "Lainnya"   # jaga-jaga kalau ada sub baru

    df_valid["kategori_subketidaksesuaian"] = df_valid["sub_ketidaksesuaian"].apply(map_kategori)

    # Hitung jumlah
    sub_counts = (
        df_valid.groupby(["kategori_subketidaksesuaian", "sub_ketidaksesuaian"])
        .size()
        .reset_index(name="Jumlah")
    )

    # Buat sunburst chart
    fig = px.sunburst(
        sub_counts,
        path=["kategori_subketidaksesuaian", "sub_ketidaksesuaian"],
        values="Jumlah",
        color="kategori_subketidaksesuaian",
        color_discrete_map={
            "Perilaku": "#ffcc00",
            "Non Perilaku": "#00cc96",
            "Lainnya": "#cccccc"
        },
        labels={"Jumlah": "Jumlah Laporan"}
    )

    fig.update_traces(textinfo="label+percent entry+value")  # tampilkan label + persen + jumlah
    fig.update_layout(title="🔍 Distribusi Sub-Ketidaksesuaian (Valid)", height=600)
    st.plotly_chart(fig, use_container_width=True)

    
st.markdown("---")

## ================================
# 📊 Jumlah Sub-Ketidaksesuaian per Perusahaan-Site (Valid Only) - Horizontal
# ================================
st.subheader("🔍 Jumlah Sub-Ketidaksesuaian per Site - Perusahaan (Valid)")

if df.empty:
    st.info("Tidak ada data untuk dianalisis.")
else:
    # Filter hanya status_temuan valid
    df_valid = df[df["status_temuan"].str.lower() == "valid"].copy()

    if df_valid.empty:
        st.info("Tidak ada data valid.")
    else:
        # Pastikan kolom perusahaan & site ada
        if "perusahaan" not in df_valid.columns or "site" not in df_valid.columns:
            st.error("Kolom 'perusahaan' atau 'site' tidak ditemukan di dataset.")
        else:
            # Gabungkan jadi company_site
            df_valid["company_site"] = (
                df_valid["perusahaan"].astype(str).str.strip()
                + " - "
                + df_valid["site"].astype(str).str.strip()
            )

            # Hitung jumlah sub ketidaksesuaian per company_site
            grp = (
                df_valid.groupby(["company_site", "sub_ketidaksesuaian"])
                .size()
                .reset_index(name="count")
            )

            # Pivot untuk stacked bar (pakai count langsung)
            pivot_cs = (
                grp.pivot(
                    index="company_site",
                    columns="sub_ketidaksesuaian",
                    values="count",
                )
                .fillna(0)
            )

            # Buat stacked bar chart horizontal
            fig = go.Figure()
            for col in pivot_cs.columns:
                fig.add_trace(
                    go.Bar(
                        y=pivot_cs.index,
                        x=pivot_cs[col],
                        name=col,
                        orientation="h",
                        text=pivot_cs[col].astype(int),
                        textposition="inside"
                    )
                )

            fig.update_layout(
                barmode="stack",
                height=600,
                xaxis_title="Jumlah Temuan (Valid)",
                yaxis_title="Perusahaan - Site",
                legend_title="Sub Ketidaksesuaian",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.05,
                    xanchor="center",
                    x=0.5
                )
            )

            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(grp)


# ========== BAGIAN 0.7 / 0.3: Proporsi per site-perusahaan dan Top 3 site ==========
col_left, col_right = st.columns([0.7, 0.3])

with col_left:
    st.subheader("📍 Proporsi Perilaku vs Non-Perilaku per Site - Perusahaan (Valid)")
    if df_valid.empty:
        st.info("Tidak ada data valid.")
    else:
        # Pastikan ada kolom site & perusahaan; jika tidak, coba gabungkan kolom lain
        if not col_site:
            df_valid["site"] = df_valid.get("lokasi", "Unknown")
        else:
            df_valid["site"] = df_valid[col_site].astype(str)
        if not col_perusahaan:
            df_valid["perusahaan"] = df_valid.get("company", "Unknown")
        else:
            df_valid["perusahaan"] = df_valid[col_perusahaan].astype(str)

        df_valid["company_site"] = df_valid["perusahaan"].str.strip() + " - " + df_valid["site"].str.strip()
        # hitung proporsi per company_site
        grp = df_valid.groupby(["company_site", "Kategori Subketidaksesuaian"]).size().reset_index(name="count")
        total_by_cs = grp.groupby("company_site")["count"].sum().reset_index(name="total")
        merged = grp.merge(total_by_cs, on="company_site")
        merged["proporsi"] = merged["count"] / merged["total"]

        # Pivot untuk stacked bar (ambil top 30 site by total)
        top_sites = total_by_cs.sort_values("total", ascending=False).head(30)["company_site"].tolist()
        pivot_cs = merged[merged["company_site"].isin(top_sites)].pivot(index="company_site", columns="Kategori Subketidaksesuaian", values="proporsi").fillna(0)
        pivot_cs = pivot_cs.sort_values(by=pivot_cs.columns.tolist(), ascending=False)
        if pivot_cs.empty:
            st.info("Data per site-perusahaan tidak cukup untuk visualisasi.")
        else:
            fig3 = go.Figure()
            # buat stacked bar (proporsi)
            for col in pivot_cs.columns:
                fig3.add_trace(go.Bar(x=pivot_cs.index, y=pivot_cs[col], name=col))
            fig3.update_layout(barmode='stack', xaxis_tickangle=-45, height=420,
                               yaxis_title="Proporsi (Valid)", xaxis_title="Perusahaan - Site")
            st.plotly_chart(fig3, use_container_width=True)

with col_right:
    st.subheader("🏆 Top 3 Site dengan Ketidaksesuaian Valid")
    if df_valid.empty:
        st.info("Tidak ada data valid.")
    else:
        top3 = df_valid.groupby(["perusahaan", "site"]).size().reset_index(name="count").sort_values("count", ascending=False).head(3)
        # tampilkan list sederhana
        for i, row in top3.iterrows():
            st.markdown(f"**{int(row['count'])}** — {row['perusahaan']} · {row['site']}")
        st.write("")  # spasi
        st.dataframe(top3.style.format({"count":"{:,}"}), height=220)

st.markdown("---")



# ========== Proporsi sub ketidaksesuaian per site-perusahaan (sunburst atau stacked) ==========
st.subheader("🔍 Proporsi Sub-Ketidaksesuaian per Site - Perusahaan (Valid)")
if df_valid.empty:
    st.info("Tidak ada data valid untuk analisis ini.")
else:
    # Ambil top N company_site untuk readability
    df_valid["company_site"] = df_valid["perusahaan"].str.strip() + " - " + df_valid["site"].str.strip()
    top_m = 12
    top_cs = df_valid.groupby("company_site").size().reset_index(name="total").sort_values("total", ascending=False).head(top_m)["company_site"].tolist()
    df_sb = df_valid[df_valid["company_site"].isin(top_cs)].copy()
    # Buat sunburst: perusahaan -> site -> sub_ketidaksesuaian_norm
    try:
        fig4 = px.sunburst(df_sb, path=["perusahaan", "site", "sub_ketidaksesuaian_norm"], values=None, color="Kategori Subketidaksesuaian", title="Sunburst: Perusahaan > Site > Sub-Ketidaksesuaian")
        fig4.update_layout(height=600)
        st.plotly_chart(fig4, use_container_width=True)
    except Exception as e:
        st.error(f"Gagal membuat sunburst: {e}")
        st.dataframe(df_sb[["perusahaan","site","sub_ketidaksesuaian_norm","Kategori Subketidaksesuaian"]].value_counts().reset_index(name="count"))

# Footer: export CSV tombol
st.markdown("---")
st.subheader("📥 Ekspor Data (opsional)")
if not df_valid.empty:
    csv = df_valid.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV Laporan Valid (Ketidaksesuaian)", data=csv, file_name="ketidaksesuaian_valid.csv", mime="text/csv")
else:
    st.info("Tidak ada file untuk diunduh (tidak ada laporan valid).")


# ========== TOP METRICS (4 kolom) ==========
#c1, c2, c3, c4 = st.columns(4)
#c1.metric("🔢 Jumlah Laporan Ketidaksesuaian", f"{total_reports:,}")
#c2.metric("✅ Laporan Valid (%)", f"{total_valid:,} ({pct_valid:.1f}%)", help="Persentase dari total laporan")
#c3.metric("🧍‍♂️ Perilaku (Valid)", f"{count_perilaku:,}")
#c4.metric("🏗️ Non Perilaku (Valid)", f"{count_nonperilaku:,}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div style="text-align:left; padding:0.5px; border-radius:2px;">
            <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Jumlah Laporan</h6>
            <p style="font-size:40px; margin:0;margin-top:0;">{total_reports:,}</p>
            
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div style="text-align:left; padding:0.5px; border-radius:2px;">
            <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Laporan Valid</h6>
            <p style="font-size:40px; margin:0;margin-top:0;">{total_valid:,}</p>
            <p style="font-size:14px; margin-top:0; color:#3BB143;">{pct_valid:.1f}% dari total</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div style="text-align:left; padding:0.5px; border-radius:2px;">
            <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;"> Kategori Perilaku</h6>
            <p style="font-size:40px; margin:0;margin-top:0;">{count_perilaku:,}</p>
            <p style="font-size:14px; margin-top:0; color:#3BB143;">{pct_perilaku:.1f}% dari total valid</p>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div style="text-align:left; padding:0.5px; border-radius:2px;">
            <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;"> Kategori Non Perilaku</h6>
            <p style="font-size:40px; margin:0;margin-top:0;">{count_nonperilaku:,}</p>
            <p style="font-size:14px; margin-top:0; color:#3BB143;">{pct_nonperilaku:.1f}% dari total valid</p>
        </div>
    """, unsafe_allow_html=True)


# ========== DUA METRIC KIRI: Tren & Proporsi Sub-ketidaksesuaian ==========
colA, colB = st.columns(2)

# --- Tren Perilaku vs Non Perilaku (hanya valid)
with colA:
    st.subheader("📈 Tren: Perilaku vs Non-Perilaku (Valid)")
    if col_tgl:
        # parse tanggal
        try:
            df_valid[col_tgl] = pd.to_datetime(df_valid[col_tgl], errors="coerce")
        except Exception:
            df_valid[col_tgl] = pd.to_datetime(df_valid[col_tgl].astype(str), errors="coerce")
        # buat agregasi per bulan
        df_valid["period_month"] = df_valid[col_tgl].dt.to_period("M")
        trend = df_valid.groupby(["period_month", "Kategori Subketidaksesuaian"]).size().reset_index(name="count")
        if trend.empty:
            st.info("Tidak ada data tanggal yang valid untuk membuat tren. Pastikan kolom tanggal tersedia dan terformat.")
        else:
            # pivot
            pivot = trend.pivot(index="period_month", columns="Kategori Subketidaksesuaian", values="count").fillna(0)
            pivot.index = pivot.index.to_timestamp()
            fig = go.Figure()
            for col in pivot.columns:
                fig.add_trace(go.Scatter(x=pivot.index, y=pivot[col], mode="lines+markers", name=col))
            fig.update_layout(height=350, xaxis_title="Bulan", yaxis_title="Jumlah Laporan (Valid)", legend_title="")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Kolom tanggal tidak terdeteksi (cari nama seperti 'tanggal_laporan', 'tanggal', 'date'). Tren tidak dapat ditampilkan.")

# --- Proporsi berdasarkan sub-ketidaksesuaian (hanya valid)
with colB:
    st.subheader("📊 Proporsi berdasarkan Sub-Ketidaksesuaian (Valid)")
    if df_valid.empty:
        st.info("Tidak ada laporan valid untuk dianalisis.")
    else:
        # Hitung top subcategories
        subcounts = df_valid.groupby("sub_ketidaksesuaian_norm").size().reset_index(name="count").sort_values("count", ascending=False)
        # Tampilkan bar chart horizontal top 20
        top_n = 20
        subtop = subcounts.head(top_n)
        fig2 = px.bar(subtop, x="count", y="sub_ketidaksesuaian_norm", orientation="h", labels={"count":"Jumlah","sub_ketidaksesuaian_norm":"Sub Ketidaksesuaian"})
        fig2.update_layout(height=350, yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ========== BAGIAN 0.7 / 0.3: Proporsi per site-perusahaan dan Top 3 site ==========
col_left, col_right = st.columns([0.7, 0.3])

with col_left:
    st.subheader("📍 Proporsi Perilaku vs Non-Perilaku per Site - Perusahaan (Valid)")
    if df_valid.empty:
        st.info("Tidak ada data valid.")
    else:
        # Pastikan ada kolom site & perusahaan; jika tidak, coba gabungkan kolom lain
        if not col_site:
            df_valid["site"] = df_valid.get("lokasi", "Unknown")
        else:
            df_valid["site"] = df_valid[col_site].astype(str)
        if not col_perusahaan:
            df_valid["perusahaan"] = df_valid.get("company", "Unknown")
        else:
            df_valid["perusahaan"] = df_valid[col_perusahaan].astype(str)

        df_valid["company_site"] = df_valid["perusahaan"].str.strip() + " - " + df_valid["site"].str.strip()
        # hitung proporsi per company_site
        grp = df_valid.groupby(["company_site", "Kategori Subketidaksesuaian"]).size().reset_index(name="count")
        total_by_cs = grp.groupby("company_site")["count"].sum().reset_index(name="total")
        merged = grp.merge(total_by_cs, on="company_site")
        merged["proporsi"] = merged["count"] / merged["total"]

        # Pivot untuk stacked bar (ambil top 30 site by total)
        top_sites = total_by_cs.sort_values("total", ascending=False).head(30)["company_site"].tolist()
        pivot_cs = merged[merged["company_site"].isin(top_sites)].pivot(index="company_site", columns="Kategori Subketidaksesuaian", values="proporsi").fillna(0)
        pivot_cs = pivot_cs.sort_values(by=pivot_cs.columns.tolist(), ascending=False)
        if pivot_cs.empty:
            st.info("Data per site-perusahaan tidak cukup untuk visualisasi.")
        else:
            fig3 = go.Figure()
            # buat stacked bar (proporsi)
            for col in pivot_cs.columns:
                fig3.add_trace(go.Bar(x=pivot_cs.index, y=pivot_cs[col], name=col))
            fig3.update_layout(barmode='stack', xaxis_tickangle=-45, height=420,
                               yaxis_title="Proporsi (Valid)", xaxis_title="Perusahaan - Site")
            st.plotly_chart(fig3, use_container_width=True)

with col_right:
    st.subheader("🏆 Top 3 Site dengan Ketidaksesuaian Valid")
    if df_valid.empty:
        st.info("Tidak ada data valid.")
    else:
        top3 = df_valid.groupby(["perusahaan", "site"]).size().reset_index(name="count").sort_values("count", ascending=False).head(3)
        # tampilkan list sederhana
        for i, row in top3.iterrows():
            st.markdown(f"**{int(row['count'])}** — {row['perusahaan']} · {row['site']}")
        st.write("")  # spasi
        st.dataframe(top3.style.format({"count":"{:,}"}), height=220)

st.markdown("---")

# ========== Proporsi sub ketidaksesuaian per site-perusahaan (sunburst atau stacked) ==========
st.subheader("🔍 Proporsi Sub-Ketidaksesuaian per Site - Perusahaan (Valid)")
if df_valid.empty:
    st.info("Tidak ada data valid untuk analisis ini.")
else:
    # Ambil top N company_site untuk readability
    df_valid["company_site"] = df_valid["perusahaan"].str.strip() + " - " + df_valid["site"].str.strip()
    top_m = 12
    top_cs = df_valid.groupby("company_site").size().reset_index(name="total").sort_values("total", ascending=False).head(top_m)["company_site"].tolist()
    df_sb = df_valid[df_valid["company_site"].isin(top_cs)].copy()
    # Buat sunburst: perusahaan -> site -> sub_ketidaksesuaian_norm
    try:
        fig4 = px.sunburst(df_sb, path=["perusahaan", "site", "sub_ketidaksesuaian_norm"], values=None, color="Kategori Subketidaksesuaian", title="Sunburst: Perusahaan > Site > Sub-Ketidaksesuaian")
        fig4.update_layout(height=600)
        st.plotly_chart(fig4, use_container_width=True)
    except Exception as e:
        st.error(f"Gagal membuat sunburst: {e}")
        st.dataframe(df_sb[["perusahaan","site","sub_ketidaksesuaian_norm","Kategori Subketidaksesuaian"]].value_counts().reset_index(name="count"))

# Footer: export CSV tombol
st.markdown("---")
st.subheader("📥 Ekspor Data (opsional)")
if not df_valid.empty:
    csv = df_valid.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV Laporan Valid (Ketidaksesuaian)", data=csv, file_name="ketidaksesuaian_valid.csv", mime="text/csv")
else:
    st.info("Tidak ada file untuk diunduh (tidak ada laporan valid).")
