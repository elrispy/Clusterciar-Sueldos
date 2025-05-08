import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Reporte de Sueldos", layout="wide")
st.title("Reporte Interactivo de Sueldos")

# Cargar archivo Excel desde el proyecto
df = pd.read_excel("SUELDOS PARA INFORMES.xlsx", sheet_name=0)

st.sidebar.header("Filtros")
filtros = {
    "Empresa": st.sidebar.multiselect("Empresa", df["Empresa"].dropna().unique()),
    "CCT": st.sidebar.multiselect("CCT", df["CCT"].dropna().unique()),
    "Grupo": st.sidebar.multiselect("Grupo", df["Grupo"].dropna().unique()),
    "Comitente": st.sidebar.multiselect("Comitente", df["Comitente"].dropna().unique()),
    "Puesto": st.sidebar.multiselect("Puesto", df["Puesto"].dropna().unique()),
    "seniority": st.sidebar.multiselect("Seniority", df["seniority"].dropna().unique()),
    "Gerencia": st.sidebar.multiselect("Gerencia", df["Gerencia"].dropna().unique()),
    "CVH": st.sidebar.multiselect("CVH", df["CVH"].dropna().unique()),
    "Puesto tabla salarial": st.sidebar.multiselect("Puesto tabla salarial", df["Puesto tabla salarial"].dropna().unique()),
    "Locacion": st.sidebar.multiselect("Locacion", df["Locacion"].dropna().unique()),
}

df_filtered = df.copy()
for key, values in filtros.items():
    if values:
        df_filtered = df_filtered[df_filtered[key].isin(values)]

st.subheader("Resumen General")
col1, col2, col3 = st.columns(3)
col1.metric("Total personas", len(df_filtered))
col2.metric("Sueldo Bruto Promedio", f"${df_filtered['Total sueldo bruto'].mean():,.0f}")
col3.metric("Sueldo Bruto Total", f"${df_filtered['Total sueldo bruto'].sum():,.0f}")

st.subheader("Distribución de Sueldo Bruto")
agrupadores = ["Empresa", "CCT", "Grupo", "Comitente", "Puesto", "seniority", "Gerencia", "CVH", "Puesto tabla salarial", "Locacion"]
grupo_seleccionado = st.selectbox("Selecciona una categoría para agrupar", agrupadores, index=6)

chart = alt.Chart(df_filtered).mark_bar().encode(
    x=alt.X(f"{grupo_seleccionado}:N", sort="-y"),
    y="mean(Total sueldo bruto):Q",
    tooltip=[grupo_seleccionado, "mean(Total sueldo bruto):Q"]
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
