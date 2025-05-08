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

# Cálculos clave
promedio = df_filtered['Total sueldo bruto'].mean()
minimo = df_filtered['Total sueldo bruto'].min()
maximo = df_filtered['Total sueldo bruto'].max()
mediana = df_filtered['Total sueldo bruto'].median()
costo_total = df_filtered['Total sueldo bruto'].sum() * 1.245

# Porcentaje del sueldo en la banda salarial (entre 25% y 75%)
if 'Sueldo mínimo' in df_filtered.columns and 'Sueldo máximo' in df_filtered.columns:
    df_filtered['% en banda'] = (df_filtered['Total sueldo bruto'] - df_filtered['Sueldo mínimo']) / (df_filtered['Sueldo máximo'] - df_filtered['Sueldo mínimo']) * 100
    en_banda = df_filtered[df_filtered['% en banda'].between(25, 75)]
    porcentaje_en_banda = len(en_banda) / len(df_filtered) * 100 if len(df_filtered) > 0 else 0
else:
    porcentaje_en_banda = np.nan

# Métricas visibles
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total personas", len(df_filtered))
col2.metric("Sueldo Bruto Promedio", f"${promedio:,.0f}")
col3.metric("Sueldo Mínimo / Máximo", f"${minimo:,.0f} / ${maximo:,.0f}")
col4.metric("Mediana Sueldo Bruto", f"${mediana:,.0f}")

col5, col6 = st.columns(2)
col5.metric("% empleados entre P25 y P75", f"{porcentaje_en_banda:.1f}%")
col6.metric("Costo Laboral Total (24.5%)", f"${costo_total:,.0f}")

# Gráfico de distribución
st.markdown("### Distribución de Sueldos Brutos")
hist = alt.Chart(df_filtered).mark_bar(opacity=0.8).encode(
    alt.X("Total sueldo bruto", bin=alt.Bin(maxbins=40), title="Sueldo Bruto"),
    y='count()',
    tooltip=['count()']
).properties(height=300)
st.altair_chart(hist, use_container_width=True)

# Comparación por categoría
st.markdown("### Comparación por Categoría")
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
