import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import io
from PIL import Image
from fpdf import FPDF
import base64
from matplotlib import pyplot as plt
import tempfile

st.set_page_config(page_title="Reporte de Sueldos", layout="wide")
st.title("Reporte Interactivo de Sueldos")

# Logo
logo = Image.open("logo-clusterciar.png")
st.image(logo, width=200)

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

promedio = df_filtered['Total sueldo bruto'].mean()
minimo = df_filtered['Total sueldo bruto'].min()
maximo = df_filtered['Total sueldo bruto'].max()
costo_total = df_filtered['Total sueldo bruto'].sum() * 1.245

# % empleados entre P25 y P75 usando columna '% BANDA SALARIAL'
if '% BANDA SALARIAL' in df_filtered.columns:
    en_banda = df_filtered[df_filtered['% BANDA SALARIAL'].between(0.15, 0.75)]
    porcentaje_en_banda = len(en_banda) / len(df_filtered) * 100 if len(df_filtered) > 0 else 0
else:
    porcentaje_en_banda = np.nan

# Métricas
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total personas", len(df_filtered))
col2.metric("Sueldo Bruto Promedio", f"${promedio:,.0f}")
col3.metric("Sueldo Mínimo / Máximo", f"${minimo:,.0f} / ${maximo:,.0f}")
col4.metric("Costo Laboral Total (24.5%)", f"${costo_total:,.0f}")

col5 = st.columns(1)[0]
col5.metric("% empleados entre P25 y P75", f"{porcentaje_en_banda:.1f}%")

st.markdown("### Conclusiones")
if len(df_filtered) > 0:
    st.markdown(f"- El sueldo bruto promedio es de **${promedio:,.0f}**.")
    st.markdown(f"- El rango va de **${minimo:,.0f}** a **${maximo:,.0f}**.")
    if not np.isnan(porcentaje_en_banda):
        st.markdown(f"- El **{porcentaje_en_banda:.1f}%** de los empleados está entre el 15% y el 75% de la banda salarial.")
    st.markdown(f"- El costo laboral total estimado asciende a **${costo_total:,.0f}**.")
else:
    st.info("No hay datos disponibles con los filtros actuales para generar conclusiones.")

# Gráfico de distribución
# Gráfico de distribución corregido
st.markdown("### Distribución de Sueldos Brutos")
hist = alt.Chart(df_filtered).mark_bar(opacity=0.8).encode(
    alt.X("Total sueldo bruto", bin=alt.Bin(maxbins=40), title="Sueldo Bruto"),
    y=alt.Y('count()', title='Cantidad de personas'),
    tooltip=[alt.Tooltip('count()', title='Cantidad')]
).properties(height=300)
st.altair_chart(hist, use_container_width=True)

# Comparación por categoría
st.markdown("### Comparación por Categoría")
agrupadores = ["Empresa", "CCT", "Grupo", "Comitente", "Puesto", "seniority", "Gerencia", "CVH", "Puesto tabla salarial", "Locacion"]
grupo_seleccionado = st.selectbox("Selecciona una categoría para agrupar", agrupadores, index=6)

chart = alt.Chart(df_filtered).mark_bar().encode(
    x=alt.X(f"{grupo_seleccionado}:N", sort="-y"),
    y="mean(Total sueldo bruto):Q",
    tooltip=["Apellido", "Nombre", "Puesto", grupo_seleccionado, "mean(Total sueldo bruto):Q"]
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

# Exportar a Excel
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df_filtered.to_excel(writer, index=False, sheet_name='Datos Filtrados')
    resumen = pd.DataFrame({
        'Total personas': [len(df_filtered)],
        'Promedio': [promedio],
        'Mínimo': [minimo],
        'Máximo': [maximo],
        'Costo laboral': [costo_total],
        '% empleados entre P25-P75': [porcentaje_en_banda],
    })
    resumen.to_excel(writer, index=False, sheet_name='Resumen')
excel_data = output.getvalue()
st.download_button(
    label="Descargar reporte en Excel",
    data=excel_data,
    file_name='reporte_sueldos.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
)

# Exportar a PDF (versión resumida)
if st.button("Generar reporte en PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.image("logo-clusterciar.png", x=10, y=8, w=50)
    pdf.ln(30)
    pdf.cell(200, 10, txt="Reporte de Sueldos - Clusterciar", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total personas: {len(df_filtered)}", ln=True)
    pdf.cell(200, 10, txt=f"Promedio: ${promedio:,.0f}", ln=True)
    pdf.cell(200, 10, txt=f"Mínimo / Máximo: ${minimo:,.0f} / ${maximo:,.0f}", ln=True)
    pdf.cell(200, 10, txt=f"Costo Laboral Total: ${costo_total:,.0f}", ln=True)
    pdf.cell(200, 10, txt=f"% empleados entre P25 y P75: {porcentaje_en_banda:.1f}%", ln=True)

    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmpfile.name)
    with open(tmpfile.name, "rb") as f:
        st.download_button("Descargar reporte en PDF", f.read(), file_name="reporte_sueldos.pdf", mime="application/pdf")
