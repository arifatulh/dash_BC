# pages/4_📋_Preview_Data.py

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Preview Data",
    page_icon="📋",
    layout="wide"
)

# Ambil data dari session_state (supaya konsisten antar page)
df_timbulan = st.session_state.get("df_timbulan", pd.DataFrame())
df_program = st.session_state.get("df_program", pd.DataFrame())
df_ketidaksesuaian = st.session_state.get("df_ketidaksesuaian", pd.DataFrame())

st.title("📋 Preview Semua Data")

# --- Preview Timbulan ---
st.subheader("📊 Preview Data Timbulan")
if not df_timbulan.empty:
    st.dataframe(df_timbulan.head(100), use_container_width=True)
else:
    st.warning("Data Timbulan kosong.")

# --- Preview Program ---
st.subheader("🗂️ Preview Data Program")
if not df_program.empty:
    st.dataframe(df_program.head(100), use_container_width=True)
else:
    st.warning("Data Program kosong.")

# --- Preview Ketidaksesuaian ---
st.subheader("⚠️ Preview Data Ketidaksesuaian")
if not df_ketidaksesuaian.empty:
    st.dataframe(df_ketidaksesuaian.head(100), use_container_width=True)
else:
    st.warning("Data Ketidaksesuaian kosong.")

# --- Survey Kepuasan ---
st.subheader("😊 Preview Data Survey")
df_survey = st.session_state.get("df_survey", pd.DataFrame())
if not df_survey.empty:
    st.dataframe(df_survey.head(100), use_container_width=True)
else:
    st.warning("Data Survey kosong.")
    tab1, tab2 = st.tabs(["Survei Online", "Survei Offline"])
    with tab1:
        df_survey_online = df_survey[df_survey["jenis_survey"] == "Online"]
        if not df_survey_online.empty:
            st.dataframe(df_survey_online.head(100), use_container_width=True)
        else:
            st.warning("Data Survei Online kosong.")
    with tab2:
        df_survey_offline = df_survey[df_survey["jenis_survey"] == "Offline"]
        if not df_survey_offline.empty:
            st.dataframe(df_survey_offline.head(100), use_container_width=True)
        else:
            st.warning("Data Survei Offline kosong.")