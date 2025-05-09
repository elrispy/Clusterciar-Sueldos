import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from PIL import Image

st.set_page_config(page_title="Reporte de Sueldos", layout="wide")
st.title("Reporte Interactivo de Sueldos")

# Logo
logo = Image.open("07 (1).png")
st.image(logo, width=150)

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
costo_total = df_filtered['Total sueldo bruto'].sum() * 1.245

# % empleados entre P25 y P75 basado en columna '% BANDA SALARIAL'
if '% BANDA SALARIAL' in df_filtered.columns:
    entre_banda = df_filtered[df_filtered['% BANDA SALARIAL'].between(0.15, 0.75)]
    porcentaje_en_banda = len(entre_banda) / len(df_filtered) * 100 if len(df_filtered) > 0 else 0
else:
    porcentaje_en_banda = np.nan

# Métricas visibles
col1, col2, col3 = st.columns(3)
col1.metric("Total personas", len(df_filtered))
col2.metric("Sueldo Bruto Promedio", f"${promedio:,.0f}")
col3.metric("Sueldo Mínimo / Máximo", f"${minimo:,.0f} / ${maximo:,.0f}")

col4, col5 = st.columns(2)
col4.metric("% empleados entre P25 y P75", f"{porcentaje_en_banda:.1f}%")
col5.metric("Costo Laboral Total (24.5%)", f"${costo_total:,.0f}")

# Interpretaciones automáticas
st.markdown("### Conclusiones")
if len(df_filtered) > 0:
    st.markdown(f"- El sueldo bruto promedio es de **${promedio:,.0f}**.")
    st.markdown(f"- El rango de sueldos va desde **${minimo:,.0f}** hasta **${maximo:,.0f}**.")
    if not np.isnan(porcentaje_en_banda):
        st.markdown(f"- El **{porcentaje_en_banda:.1f}%** de las personas están dentro de la banda salarial entre el percentil 25 y 75 (según '% BANDA SALARIAL'), lo cual {'es adecuado' if porcentaje_en_banda > 50 else 'podría indicar desvíos salariales'}.")
    st.markdown(f"- El costo laboral total estimado (sueldo + 24.5%) asciende a **${costo_total:,.0f}**.")
else:
    st.info("No hay datos disponibles con los filtros actuales para generar conclusiones.")

# Gráfico de distribución
st.markdown("### Distribución de Sueldos Brutos")
hist = alt.Chart(df_filtered).mark_bar(opacity=0.8).encode(
    alt.X("Total sueldo bruto", bin=alt.Bin(maxbins=40), title="Sueldo Bruto"),
    y='count()',
    tooltip=['Apellido', 'Nombre', 'Puesto', 'Total sueldo bruto']
).properties(height=300)
st.altair_chart(hist, use_container_width=True)

# Comparación por categoría
st.markdown("### Comparación por Categoría")
agrupadores = ["Empresa", "CCT", "Grupo", "Comitente", "Puesto", "seniority", "Gerencia", "CVH", "Puesto tabla salarial", "Locacion"]
grupo_seleccionado = st.selectbox("Selecciona una categoría para agrupar", agrupadores, index=6)

chart = alt.Chart(df_filtered).mark_bar().encode(
    x=alt.X(f"{grupo_seleccionado}:N", sort="-y"),
    y="mean(Total sueldo bruto):Q",
    tooltip=[grupo_seleccionado, "mean(Total sueldo bruto):Q", "Apellido", "Nombre", "Puesto"]
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
