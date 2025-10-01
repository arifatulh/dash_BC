# pages/3_Survei.py
import math
import io, base64

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp

from wordcloud import WordCloud
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

    # Ambil data survei
dt_online = all_df.get("Survei_Online", pd.DataFrame())
dt_offline = all_df.get("Survei_Offline", pd.DataFrame())
df_survey = pd.concat([dt_online, dt_offline], ignore_index=True)
st.markdown(
    """
    <h1 style="font-size:24px; color:#000000; font-weight:bold; margin-bottom:0.5px;">
    📝 Survei GBST (Offline & Online)
    </h1>
    """,
    unsafe_allow_html=True
)

@st.cache_data(ttl=60)
def load_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

# ========== 2) UTILITIES ==========
STOPWORDS_ID = {
    "yang","yg","dan","dengan","untuk","atau","serta","pada","dari","di","ke",
    "agar","karena","juga","adalah","akan","dalam","itu","sudah","belum",
    "sebagai","oleh","tidak","ada","ya","saya","kami","kita"
}

def show_wordcloud(texts: pd.Series, title: str, cmap: str = "viridis"):
    if texts is None or texts.empty or texts.isna().all():
        st.warning(f"Tidak ada jawaban untuk: {title}")
        return
    all_text = " ".join(texts.astype(str)).lower().strip()
    if not all_text:
        st.warning(f"Tidak ada kata yang bisa ditampilkan untuk: {title}")
        return
    try:
        wc = WordCloud(
            width=800, height=400,
            background_color="white",
            colormap=cmap,
            stopwords=STOPWORDS_ID
        ).generate(all_text)
    except ValueError:
        st.warning(f"⚠️ WordCloud gagal dibuat: {title}")
        return

    buf = io.BytesIO()
    wc.to_image().save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    st.subheader(title)
    st.markdown(f'<img src="data:image/png;base64,{img_b64}" width="100%">', unsafe_allow_html=True)

def get_top_phrases(texts: pd.Series, ngram_range=(2,2), top_n=10) -> pd.DataFrame:
    if texts is None:
        return pd.DataFrame(columns=["Frasa", "Frekuensi"])
    texts = texts.dropna().astype(str)
    if texts.empty:
        return pd.DataFrame(columns=["Frasa", "Frekuensi"])
    try:
        vec = CountVectorizer(ngram_range=ngram_range, stop_words=list(STOPWORDS_ID)).fit(texts)
        bag = vec.transform(texts)
        sum_words = bag.sum(axis=0)
        words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
        sorted_words = sorted(words_freq, key=lambda x: x[1], reverse=True)
        return pd.DataFrame(sorted_words[:top_n], columns=["Frasa", "Frekuensi"])
    except ValueError:
        return pd.DataFrame(columns=["Frasa", "Frekuensi"])

def make_insight(bi: pd.DataFrame, tri: pd.DataFrame) -> str:
    insights = []
    if not bi.empty:
        insights.append(f"Responden banyak menyinggung **'{bi.iloc[0]['Frasa']}'**.")
    if not tri.empty:
        insights.append(f"Selain itu, frasa **'{tri.iloc[0]['Frasa']}'** juga cukup dominan.")
    return " ".join(insights) if insights else "Tidak ada pola dominan yang muncul."

def gauge_figure(value: float, title: str, color_bar: str = "teal", w=350, h=320):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=float(value),
        title={"text": title},
        gauge={
            "axis": {"range": [1, 5]},
            "bar": {"color": color_bar},
            "steps": [
                {"range": [1,2], "color": "#ff9999"},
                {"range": [2,3], "color": "#ffcc99"},
                {"range": [3,4], "color": "#99ff99"},
                {"range": [4,5], "color": "#66ccff"},
            ],
        },
    ))
    fig.update_layout(height=h, width=w, margin=dict(t=80, r=40, b=40, l=40), showlegend=False)
    return fig

# ========== 3) LOAD ==========
#dt_offline, dt_online = None, None
#try: dt_offline = load_csv(dt_offline)
#except Exception as e: st.warning("Gagal memuat Survei Offline"); st.exception(e)
#try: dt_online = load_csv(dt_online)
#except Exception as e: st.warning("Gagal memuat Survei Online"); st.exception(e)

# ========== 4) PILIH TAB ==========
tab_choice = st.radio("Pilih Survei:", ["📋 Survei Offline", "🌐 Survei Online"], key="tab_choice", horizontal=True)

# ========== 5) FUNCTION ANALISIS (SUPAYA TIDAK DUPLIKASI) ==========
def analisis_survei(df: pd.DataFrame, label: str, key_prefix: str):
    st.subheader(f"Hasil {label}")
    st.dataframe(df, use_container_width=True)

    id_cols = [
        "Kode SID","Perusahaan Area Kerja Tambang","Site / Lokasi Kerja",
        "Jabatan","Kategori Jabatan","Level Jabatan","Masa Kerja","Masa Kerja (BULAN)"
    ]
    site_col, corp_col = "Site / Lokasi Kerja", "Perusahaan Area Kerja Tambang"

    question_cols = [c for c in df.columns if c not in id_cols]
    question_cols_general = question_cols[:-5] if len(question_cols) > 5 else question_cols

    # Filter
    fcol = st.columns(2)
    with fcol[0]:
        sites = sorted(df[site_col].dropna().unique()) if site_col in df.columns else []
        sel_sites = st.multiselect("Filter Site", sites, default=sites[:3] if sites else [], key=f"{key_prefix}_sites")
    with fcol[1]:
        corps = sorted(df[corp_col].dropna().unique()) if corp_col in df.columns else []
        sel_corps = st.multiselect("Filter Perusahaan", corps, default=[], key=f"{key_prefix}_corps")

    df_f = df.copy()
    if sel_sites and site_col in df_f.columns:
        df_f = df_f[df_f[site_col].isin(sel_sites)]
    if sel_corps and corp_col in df_f.columns:
        df_f = df_f[df_f[corp_col].isin(sel_corps)]
    st.caption(f"Total respon (setelah filter): **{len(df_f)}**")

    # Distribusi umum
    c1, c2, c3 = st.columns(3)
    with c1: per_page = st.slider("Pertanyaan per halaman", 1, 8, 4, key=f"{key_prefix}_per_page")
    with c2: ncols = st.radio("Grafik per baris", [1, 2, 3], index=1, key=f"{key_prefix}_ncols")
    with c3:
        total = len(question_cols_general)
        pages = max(1, math.ceil(total / per_page))
        page = st.number_input("Halaman", min_value=1, max_value=pages, value=1, step=1, key=f"{key_prefix}_page")

    start, end = (page - 1) * per_page, min(page * per_page, total)
    questions = question_cols_general[start:end]

    nrows = max(1, math.ceil(len(questions) / ncols))
    fig = sp.make_subplots(rows=nrows, cols=ncols,
        subplot_titles=[q[:60] + ("..." if len(q) > 60 else "") for q in questions])

    for i, q in enumerate(questions):
        row, col = i // ncols + 1, i % ncols + 1
        counts = df_f[q].dropna().astype(str).value_counts()
        fig.add_trace(go.Bar(
            x=list(counts.index), y=list(counts.values),
            marker_color=px.colors.qualitative.Set2,
            hovertemplate="Pilihan = %{x}<br>Respon = %{y}<extra></extra>",
            showlegend=False
        ), row=row, col=col)

    fig.update_layout(barmode="group", height=max(350, 320*nrows),
                      title_text=f"Distribusi Jawaban (Hal {page}/{pages})", title_x=0.5)
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_dist")

    # Multi-jawaban
    for col_multi in [
        "Jika pernah, membuang sampah sembarangan, alasannya?",
        "Jika pernah tidak memilah sampah , alasannya?"
    ]:
        if col_multi in df_f.columns:
            multi = df_f[col_multi].dropna().astype(str).str.split(",").explode().str.strip()
            alasan_counts = multi.value_counts().reset_index()
            alasan_counts.columns = ["Alasan", "Jumlah"]
            st.subheader(f"📌 {col_multi}")
            st.dataframe(alasan_counts, use_container_width=True)
            fig2 = px.bar(alasan_counts, x="Jumlah", y="Alasan", orientation="h", color="Jumlah",
                          color_continuous_scale="orrd", text="Jumlah")
            fig2.update_layout(yaxis=dict(categoryorder="total ascending"), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True, key=f"{key_prefix}_{col_multi}")

    # Analisis Q2
    q2_col = "2. Seberapa optimal program GBST berjalan selama ini di perusahaan Anda?"
    if q2_col in df_f.columns:
        st.markdown("---"); st.header(f"⭐ Analisis Khusus Q2 — {label}")
        q2_vals = pd.to_numeric(df_f[q2_col], errors="coerce").dropna()
        if q2_vals.empty: st.warning("Belum ada data numerik untuk Q2")
        else:
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Mean", f"{q2_vals.mean():.2f}")
            c2.metric("Median", f"{q2_vals.median():.2f}")
            mode_val = q2_vals.mode().iat[0] if not q2_vals.mode().empty else "-"
            c3.metric("Modus", f"{mode_val}")
            c4.metric("Std. Dev", f"{q2_vals.std():.2f}")
            c5.metric("n", f"{len(q2_vals)}")
            st.plotly_chart(gauge_figure(q2_vals.mean(), "Rata-rata Optimalitas GBST"), use_container_width=True, key=f"{key_prefix}_gauge")

    # Open-ended
    st.markdown("---"); st.header(f"📊 Analisis Pertanyaan Terbuka ({label})")
    OPEN_QS = {
        "1. Apa hambatan yang dialami dalam melaksanakan program GBST?": "viridis",
        "3. Menurut Anda, Bagaimana cara membuat pekerja lebih disiplin dalam menjalankan GBST?": "cividis",
        "4. Bagaimana fasilitas pengelolaan sampah di area Anda?": "inferno",
        "5. Menurut Anda, Apa bentuk dukungan tambahan yang Anda perlukan untuk menjalankan atau mendukung program GBST?": "magma"
    }
    for q_col, cmap in OPEN_QS.items():
        if q_col in df_f.columns:
            q_text = df_f[q_col].dropna().astype(str)
            if q_text.empty: continue
            show_wordcloud(q_text, f"WordCloud - {q_col}", cmap=cmap)
            top_bi, top_tri = get_top_phrases(q_text,(2,2)), get_top_phrases(q_text,(3,3))
            c1,c2 = st.columns(2)
            with c1: st.plotly_chart(px.bar(top_bi, x="Frekuensi", y="Frasa", orientation="h",
                                            color="Frekuensi", color_continuous_scale="blues", text="Frekuensi"),
                                     use_container_width=True, key=f"{key_prefix}_{q_col}_bi")
            with c2: st.plotly_chart(px.bar(top_tri, x="Frekuensi", y="Frasa", orientation="h",
                                            color="Frekuensi", color_continuous_scale="greens", text="Frekuensi"),
                                     use_container_width=True, key=f"{key_prefix}_{q_col}_tri")
            st.info(make_insight(top_bi, top_tri))

# ========== 6) CALL ==========
if tab_choice == "📋 Survei Offline" and dt_offline is not None:
    analisis_survei(dt_offline, "Survei Offline", "offline")
elif tab_choice == "🌐 Survei Online" and dt_online is not None:
    analisis_survei(dt_online, "Survei Online", "online")
