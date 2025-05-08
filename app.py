import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Reporte de Sueldos", layout="wide")
st.title("Reporte Interactivo de Sueldos")

# Subir archivo Excel
st.sidebar.header("1. Subir archivo Excel")
uploaded_file = st.sidebar.file_uploader("Elige un archivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0)
    
    st.sidebar.header("2. Filtros")
    empresas = st.sidebar.multiselect("Empresa", df["Empresa"].dropna().unique())
    gerencias = st.sidebar.multiselect("Gerencia", df["Gerencia"].dropna().unique())
    seniorities = st.sidebar.multiselect("Seniority", df["seniority"].dropna().unique())

    df_filtered = df.copy()
    if empresas:
        df_filtered = df_filtered[df_filtered["Empresa"].isin(empresas)]
    if gerencias:
        df_filtered = df_filtered[df_filtered["Gerencia"].isin(gerencias)]
    if seniorities:
        df_filtered = df_filtered[df_filtered["seniority"].isin(seniorities)]

    st.subheader("Resumen General")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total personas", len(df_filtered))
    col2.metric("Sueldo Bruto Promedio", f"${df_filtered['Total sueldo bruto'].mean():,.0f}")
    col3.metric("Sueldo Bruto Total", f"${df_filtered['Total sueldo bruto'].sum():,.0f}")

    st.subheader("Distribución por Gerencia")
    chart = alt.Chart(df_filtered).mark_bar().encode(
        x=alt.X("Gerencia:N", sort="-y"),
        y="mean(Total sueldo bruto):Q",
        tooltip=["Gerencia", "mean(Total sueldo bruto):Q"]
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Tabla de Datos Filtrados")
    st.dataframe(df_filtered)

    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar datos filtrados como CSV",
        data=csv,
        file_name='sueldos_filtrados.csv',
        mime='text/csv',
    )

else:
    st.info("Por favor, sube un archivo Excel para comenzar.")
