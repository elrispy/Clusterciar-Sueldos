import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import io
from PIL import Image
from fpdf import FPDF
import tempfile

# Configuración de la página
st.set_page_config(page_title="Reporte de Sueldos", layout="wide")
st.title("Reporte Interactivo de Sueldos")

# Cargar logo
try:
    logo = Image.open("logo-clusterciar.png")
    st.image(logo, width=200)
except FileNotFoundError:
    st.warning("No se encontró el archivo logo-clusterciar.png")

# Cargar archivo Excel
try:
    df = pd.read_excel("SUELDOS PARA INFORMES.xlsx", sheet_name=0)
except FileNotFoundError:
    st.error("No se encontró el archivo SUELDOS PARA INFORMES.xlsx")
    st.stop()

# Limpiar nombres de columnas
df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('%_BANDA_SALARIAL', 'Porcentaje_Banda_Salarial')

# Convertir columnas categóricas a string y manejar valores inválidos
categorical_columns = [
    'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
    'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior'
]
for col in categorical_columns:
    if col in df.columns:
        df[col] = df[col].astype(str).replace(['#Ref', 'nan'], '')

# Convertir columnas de fecha
date_columns = ['Fecha_de_Ingreso', 'Fecha_de_nacimiento']
for col in date_columns:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# Filtros en la barra lateral
st.sidebar.header("Filtros")
filtros = {
    "Empresa": st.sidebar.multiselect("Empresa", df["Empresa"].unique()),
    "CCT": st.sidebar.multiselect("CCT", df["CCT"].unique()),
    "Grupo": st.sidebar.multiselect("Grupo", df["Grupo"].unique()),
    "Comitente": st.sidebar.multiselect("Comitente", df["Comitente"].unique()),
    "Puesto": st.sidebar.multiselect("Puesto", df["Puesto"].unique()),
    "seniority": st.sidebar.multiselect("Seniority", df["seniority"].unique()),
    "Gerencia": st.sidebar.multiselect("Gerencia", df["Gerencia"].unique()),
    "CVH": st.sidebar.multiselect("CVH", df["CVH"].unique()),
    "Puesto_tabla_salarial": st.sidebar.multiselect("Puesto tabla salarial", df["Puesto_tabla_salarial"].unique()),
    "Locacion": st.sidebar.multiselect("Locación", df["Locacion"].unique()),
    "Centro_de_Costos": st.sidebar.multiselect("Centro de Costos", df["Centro_de_Costos"].unique()),
    "Especialidad": st.sidebar.multiselect("Especialidad", df["Especialidad"].unique()),
    "Superior": st.sidebar.multiselect("Superior", df["Superior"].unique())
}

# Aplicar filtros
df_filtered = df.copy()
for key, values in filtros.items():
    if values:
        df_filtered = df_filtered[df_filtered[key].isin(values)]

# Resumen General
st.subheader("Resumen General")

if len(df_filtered) > 0:
    promedio = df_filtered['Total_sueldo_bruto'].mean()
    minimo = df_filtered['Total_sueldo_bruto'].min()
    maximo = df_filtered['Total_sueldo_bruto'].max()
    costo_total = df_filtered['Costo_laboral'].sum()

    # Porcentaje de empleados entre P25 y P75
    en_banda = df_filtered[df_filtered['Porcentaje_Banda_Salarial'].between(0.15, 0.75)]
    porcentaje_en_banda = len(en_banda) / len(df_filtered) * 100 if len(df_filtered) > 0 else 0

    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total personas", len(df_filtered))
    col2.metric("Sueldo Bruto Promedio", f"${promedio:,.0f}")
    col3.metric("Sueldo Mínimo / Máximo", f"${minimo:,.0f} / ${maximo:,.0f}")
    col4.metric("Costo Laboral Total", f"${costo_total:,.0f}")

    col5 = st.columns(1)[0]
    col5.metric("% empleados entre P25 y P75", f"{porcentaje_en_banda:.1f}%")

    # Conclusiones
    st.markdown("### Conclusiones")
    st.markdown(f"- El sueldo bruto promedio es de **${promedio:,.0f}**.")
    st.markdown(f"- El rango va de **${minimo:,.0f}** a **${maximo:,.0f}**.")
    st.markdown(f"- El **{porcentaje_en_banda:.1f}%** de los empleados está entre el 15% y el 75% de la banda salarial.")
    st.markdown(f"- El costo laboral total asciende a **${costo_total:,.0f}**.")
else:
    st.info("No hay datos disponibles con los filtros actuales para generar conclusiones.")
    promedio, minimo, maximo, costo_total, porcentaje_en_banda = 0, 0, 0, 0, 0

# Gráfico de distribución
st.markdown("### Distribución de Sueldos Brutos")
if len(df_filtered) > 0:
    hist = alt.Chart(df_filtered).mark_bar(opacity=0.8).encode(
        alt.X("Total_sueldo_bruto", bin=alt.Bin(maxbins=40), title="Sueldo Bruto"),
        y=alt.Y('count()', title='Cantidad de personas'),
        tooltip=[alt.Tooltip('count()', title='Cantidad')]
    ).properties(height=300)
    st.altair_chart(hist, use_container_width=True)
else:
    st.warning("No hay datos para mostrar en el gráfico de distribución.")

# Comparación por categoría
st.markdown("### Comparación por Categoría")
agrupadores = [
    'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
    'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior'
]
# Filtrar agrupadores para incluir solo columnas existentes
agrupadores = [col for col in agrupadores if col in df.columns]
grupo_seleccionado = st.selectbox("Selecciona una categoría para agrupar", agrupadores, index=agrupadores.index('Gerencia') if 'Gerencia' in agrupadores else 0)

if len(df_filtered) > 0:
    # Calcular la media por grupo y limpiar datos
    grouped_data = df_filtered.groupby(grupo_seleccionado)['Total_sueldo_bruto'].mean().reset_index()
    grouped_data = grouped_data.dropna(subset=[grupo_seleccionado, 'Total_sueldo_bruto'])
    grouped_data[grupo_seleccionado] = grouped_data[grupo_seleccionado].astype(str)

    chart = alt.Chart(grouped_data).mark_bar().encode(
        x=alt.X(f"{grupo_seleccionado}:N", title=grupo_seleccionado, sort="-y"),
        y=alt.Y("Total_sueldo_bruto:Q", title="Sueldo Bruto Promedio"),
        tooltip=[alt.Tooltip(grupo_seleccionado, title=grupo_seleccionado), alt.Tooltip("Total_sueldo_bruto:Q", title="Sueldo Promedio", format=",.0f")]
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)
else:
    st.warning("No hay datos para mostrar en el gráfico de comparación por categoría.")

# Tabla de datos filtrados
st.subheader("Tabla de Datos Filtrados")
st.dataframe(df_filtered)

# Exportar a CSV
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
        'Total_personas': [len(df_filtered)],
        'Promedio': [promedio],
        'Mínimo': [minimo],
        'Máximo': [maximo],
        'Costo_laboral': [costo_total],
        'Porcentaje_empleados_entre_P25-P75': [porcentaje_en_banda],
    })
    resumen.to_excel(writer, index=False, sheet_name='Resumen')
excel_data = output.getvalue()
st.download_button(
    label="Descargar reporte en Excel",
    data=excel_data,
    file_name='reporte_sueldos.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
)

# Exportar a PDF
if st.button("Generar reporte en PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    try:
        pdf.image("logo-clusterciar.png", x=10, y=8, w=50)
    except:
        pdf.cell(200, 10, txt="Logo no disponible", ln=True, align='C')
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
