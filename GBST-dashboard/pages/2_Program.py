import streamlit as st
import pandas as pd
import altair as alt

st.markdown('<p style="text-align: left;font-weight: bold;">♻️ Program Pengurangan & Pengolahan</p>',unsafe_allow_html=True)


import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============================
# Load Data dari Google Sheets
# =============================
sheet_url = "https://docs.google.com/spreadsheets/d/1cw3xMomuMOaprs8mkmj_qnib-Zp_9n68rYMgiRZZqBE/edit?usp=sharing"
sheet_id = sheet_url.split("/")[5]
sheet_name = ["Timbulan","Program","Survei_Online","Ketidaksesuaian","Survei_Offline","CCTV"]

all_df = {}
for sheet in sheet_name:
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
        df = pd.read_csv(url)
        all_df[sheet] = df
    except Exception as e:
        st.error(f"Gagal load sheet {sheet}: {e}")


# Ambil sheet timbulan dan program
    dt_timbulan = all_df.get("Timbulan", pd.DataFrame())
    df_timbulan = all_df.get("Timbulan", pd.DataFrame())
    dt_program = all_df.get("Program", pd.DataFrame())
    dt_online = all_df.get("Survei_Online", pd.DataFrame())
    df_program = all_df.get("Program", pd.DataFrame())
    # =============================
    # FILTER LOKAL (HANYA PAGE INI)
    # =============================
    st.sidebar.subheader("Filter Data")
    site_list = sorted(dt_program["Site"].dropna().unique()) if "Site" in dt_timbulan.columns else []
    site_sel = st.sidebar.multiselect("Pilih Site", site_list, default=site_list[:4] if site_list else [])

    perusahaan_list = sorted(dt_program["Perusahaan"].dropna().unique()) if "Perusahaan" in dt_timbulan.columns else []
    perusahaan_sel = st.sidebar.multiselect("Pilih Perusahaan", perusahaan_list, default=perusahaan_list[:6] if perusahaan_list else [])

    # Apply filter lokal
    df_filtered = dt_program.copy()
    if site_sel:
        df_filtered= df_filtered[df_filtered["Site"].isin(site_sel)]
    if perusahaan_sel:
        df_filtered = df_filtered[df_filtered["Perusahaan"].isin(perusahaan_sel)]

    # =============================
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

    # =============================
    # METRICS 4 KOLOM
    # =============================
    col1, col2, col3, col4 = st.columns(4)

    # 1. Jumlah Program
    df_program["Total_calc"] = pd.to_numeric(df_program["Total_calc"].astype(str).str.replace(",", "."), errors="coerce")
    jumlah_program = df_program["Nama program"].count()
    jumlah_program = df_program["Nama program"].dropna().shape[0]
    #col1.metric("Jumlah Program", jumlah_program)

    # 2. Jumlah Program Pengurangan
    jmlprog_pengurangan = df_filtered[df_filtered["Kategori"]=="Program Pengurangan"]["Nama program"].nunique()
    #col2.metric("Program Pengurangan", jmlprog_pengurangan)

    # 3. Jumlah Program Pengelolaan
    jmlprog_pengelolaan = df_filtered[df_filtered["Kategori"]=="Program Pengelolaan"]["Nama program"].nunique()
    #col3.metric("Program Pengelolaan", jmlprog_pengelolaan)
    days_period = 609
    # 4. Perusahaan-Site dengan Program Pengelolaan Teroptimal
    df_optimal = df_filtered[df_filtered["Kategori"]=="Program Pengelolaan"]
    optimal_site = df_optimal.groupby(["Perusahaan","Site"])["Total_calc"].sum().idxmax()
    optimal_value = df_optimal.groupby(["Perusahaan","Site"])["Total_calc"].sum().max()/days_period
    #col4.metric("Program Pengelolaan Teroptimal", f"{optimal_site[0]} - {optimal_site[1]} ({optimal_value:.0f})")

     # ===============================
        # TAMPILKAN METRIC
        # ===============================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Total Program</h6>
                        <p></p>
                    <p style="font-size:40px;  margin:0;margin-top:0;">{jumlah_program:,.0f}</p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;">per Agustus 2025</p>
                </div>
            """, unsafe_allow_html=True)
    with col2:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Program Pengurangan</h6>
                    <p style="font-size:40px; margin:0;margin-top:0;">{jmlprog_pengurangan}</p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;">(Reduce)</p>
                </div>
            """, unsafe_allow_html=True)
    with col3:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;"> Program Pengolahan</h6>
                        <p></p>
                    <p style="font-size:40px;  margin:0;margin-top:0;">{jmlprog_pengelolaan}</p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;">(Reuse & Recycle)</p>
                </div>
            """, unsafe_allow_html=True)
    with col4:
            st.markdown(f"""
                <div style="text-align:left; padding:0.5px; border-radius:2px;">
                    <h6 style="margin-bottom:0;margin-top:0;font-weight:normal;margin:0;">Pengolahan Teroptimal</h6>
                    <p style="font-size:40px; margin:0;margin-top:0;">{optimal_site[0]}</p>
                    <p style="font-size:14px; margin-top:0; color:#3BB143;">Site <strong>{optimal_site[1]}</strong> dengan {optimal_value:.0f} kg/hari </p>
                </div>
            """, unsafe_allow_html=True)
        



    with st.container():
    # =============================
    # PROPORSI BERDASARKAN KATEGORI
    # =============================
        col1,col2 = st.columns([0.35,0.65])
        with col1 : 
            st.markdown('<p style="text-align: left;font-weight: bold;">📊 Proporsi Program</p>',unsafe_allow_html=True)
            df_prop = df_filtered.groupby(["Kategori","Jenis Sampah"])["Nama program"].count().reset_index()
            df_prop.rename(columns={"Nama program":"Count"}, inplace=True)
            fig_prop = px.pie(df_prop, values='Count', names='Jenis Sampah', color='Jenis Sampah',
                        color_discrete_map={"Organik":"green","Anorganik":"yellow"})
                        # Buat efek "jarak antar slice"
            fig_prop.update_traces(pull=[0.01]*len(df_prop), textposition='inside', textinfo='percent+label', 
                                   hovertemplate=(
                        "<b>Jenis Sampah:</b> %{label}<br>" +
                        "<b>Kategori:</b> %{customdata[0]}<br>" +
                        "<b>Total Program:</b> %{value}<br>" +
                        "<extra></extra>"),
                                    customdata=df_prop[["Kategori"]].values  )
            

            # Perbesar chart
            fig_prop.update_layout(
                margin=dict(t=50, b=20, l=20, r=20),
                width=400,  # bisa disesuaikan
                height=400, showlegend = False
            )
            st.plotly_chart(fig_prop, use_container_width=True)

    # =============================
    # TREN SAMPAH TERKELOLA & TERKURANGI
    # =============================
        with col2 :
            st.markdown('<p style="text-align: left;font-weight: bold;">📈 Tren Sampah Terkelola & Terkurangi</p>',unsafe_allow_html=True)
            months = ["Januari 2024","Februari 2024","Maret 2024","April 2024","Mei 2024","Juni 2024",
                    "Juli 2024","Agustus 2024","September 2024","Oktober 2024","November 2024","Desember 2024",
                    "Januari 2025","Februari 2025","Maret 2025","April 2025","Mei 2025","Juni 2025","Juli 2025","Agustus 2025"]

            df_trend = df_filtered.groupby("Kategori")[months].sum().T
            df_trend.reset_index(inplace=True)
            df_trend.rename(columns={"index":"Bulan"}, inplace=True)

            fig_trend = go.Figure()
            for kategori in df_filtered["Kategori"].unique():
                fig_trend.add_trace(go.Scatter(x=df_trend["Bulan"], y=df_trend[kategori], mode='lines+markers', name=kategori))
            fig_trend.update_layout(
                                    xaxis_title="Bulan", yaxis_title="Total (kg/hari)",
                                    legend=dict(
                                    orientation="h",    # horizontal
                                    yanchor="top",   # posisi y legend
                                    y=1.1,             # geser ke bawah
                                    xanchor="center",
                                    x=0.5),
                                    margin=dict(t=50, b=100))
            st.plotly_chart(fig_trend, use_container_width=True)

    # =============================
    # PROPORSI PER PERUSAHAAN-SITE
    # =============================
    st.subheader("🏢 Proporsi per Perusahaan-Site")

    # Pastikan kolom Timbulan numerik
    df_timbulan["Timbulan"] = pd.to_numeric(
        df_timbulan["Timbulan"].astype(str).str.replace(",", "."),
        errors="coerce"
    )

    # Hitung rata-rata perhari untuk Program Pengelolaan
    df_pengelolaan = df_filtered[df_filtered["Kategori"]=="Program Pengelolaan"].copy()
    #df_pengelolaan["Avg_perhari"] = df_pengelolaan[months].mean(axis=1)
    df_pengelolaan["Avg_perhari"] = df_pengelolaan[months].sum(axis=1) / days_period

    # Hitung rata-rata perhari untuk Program Pengurangan
    df_pengurangan = df_filtered[df_filtered["Kategori"]=="Program Pengurangan"].copy()
    df_pengurangan["Avg_perhari_reduce"] = df_pengurangan[months].sum(axis=1) / days_period

    # Filter timbulan sesuai site/perusahaan
    df_timbulan_filtered = df_timbulan.copy()
    if site_sel:
        df_timbulan_filtered = df_timbulan_filtered[df_timbulan_filtered["Site"].isin(site_sel)]
    if perusahaan_sel:
        df_timbulan_filtered = df_timbulan_filtered[df_timbulan_filtered["Perusahaan"].isin(perusahaan_sel)]

    # Jumlahkan Timbulan per Perusahaan-Site
    df_timbulan_sum = df_timbulan_filtered.groupby(["Perusahaan","Site"])["Timbulan"].sum().reset_index()

    # Jumlahkan Avg_perhari Program Pengelolaan per Perusahaan-Site
    df_pengelolaan_sum = df_pengelolaan.groupby(["Perusahaan","Site"])["Avg_perhari"].sum().reset_index()
    df_pengurangan_sum = df_pengurangan.groupby(["Perusahaan","Site"])["Avg_perhari_reduce"].sum().reset_index()

    # Merge data
    df_merge = df_timbulan_sum \
    .merge(df_pengelolaan_sum, on=["Perusahaan","Site"], how="left") \
    .merge(df_pengurangan_sum, on=["Perusahaan","Site"], how="left")

    df_merge["Sampah_Terkelola"] = df_merge["Avg_perhari"].fillna(0)
    df_merge["Sampah_Tidak_Terkelola"] = df_merge["Timbulan"] - df_merge["Sampah_Terkelola"]
    df_merge["Reduce_Sampah"] = df_merge["Avg_perhari_reduce"].fillna(0)  # asumsi sama dengan Avg_perhari

    # Buat chart
    fig_bar = go.Figure()
    # Hitung persentase terkelola dan tidak terkelola
    df_merge["Pct_Terkelola"] = (df_merge["Sampah_Terkelola"] / df_merge["Timbulan"]) * 100
    df_merge["Pct_Tidak_Terkelola"] = (df_merge["Sampah_Tidak_Terkelola"] / df_merge["Timbulan"]) * 100
    df_merge["Pct_Reduce"] = (df_merge["Reduce_Sampah"] / df_merge["Timbulan"]) * 100

    fig_bar.add_trace(go.Bar(
        x=df_merge["Perusahaan"]+" - "+df_merge["Site"], 
        y=df_merge["Timbulan"], 
        name="Timbulan (kg/hari)",
        hovertemplate="<b>%{x}</b><br>Timbulan: %{y:,.0f}<extra></extra>"

    ))
    fig_bar.add_trace(go.Bar(
        x=df_merge["Perusahaan"]+" - "+df_merge["Site"], 
        y=df_merge["Sampah_Terkelola"], 
        name="Sampah Terkelola",
        hovertemplate="<b>%{x}</b><br>Terkelola: %{y:,.0f} kg/hari<br>%{customdata:.1f}% dari Timbulan<extra></extra>",
        customdata=df_merge["Pct_Terkelola"]
    ))
    fig_bar.add_trace(go.Bar(
        x=df_merge["Perusahaan"]+" - "+df_merge["Site"], 
        y=df_merge["Sampah_Tidak_Terkelola"], 
        name="Sampah Tidak Terkelola",
        hovertemplate="<b>%{x}</b><br>Tidak Terkelola: %{y:,.0f} kg/hari<br>%{customdata:.1f}% dari Timbulan<extra></extra>",
        customdata=df_merge["Pct_Terkelola"]
    ))
    fig_bar.add_trace(go.Bar(
        x=df_merge["Perusahaan"]+" - "+df_merge["Site"], 
        y=df_merge["Reduce_Sampah"], 
        name="Reduce Sampah",
        hovertemplate="<b>%{x}</b><br>Reduce: %{y:,.0f} kg/hari<extra></extra>",
        customdata=df_merge["Pct_Reduce"]
    ))

    fig_bar.update_layout(
        barmode='group',  # side-by-side, tidak bertumpuk
        xaxis_title="Perusahaan - Site",
        yaxis_title="Kg/hari",
        xaxis_tickangle=-45,
        legend=dict(
                                    orientation="h",    # horizontal
                                    yanchor="top",   # posisi y legend
                                    y=1,             # geser ke bawah
                                    xanchor="center",
                                    x=0.5),
                                    margin=dict(t=50, b=100)
    )
    unique_sites = df_merge["Perusahaan"] + " - " + df_merge["Site"]
    for i in range(0, len(unique_sites), 2):  
        fig_bar.add_vrect(
        x0=i-0.5, x1=i+0.5,   # posisi berdasarkan index kategori
        fillcolor="lightgray", opacity=0.3,
        layer="below", line_width=0
    )

    st.plotly_chart(fig_bar, use_container_width=True)


