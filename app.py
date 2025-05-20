import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import io
from PIL import Image
from fpdf import FPDF
import tempfile
from datetime import datetime

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
@st.cache_data
def load_data():
    return pd.read_excel("SUELDOS PARA INFORMES.xlsx", sheet_name=0)

try:
    df = load_data()
except FileNotFoundError:
    st.error("No se encontró el archivo SUELDOS_PARA_INFORMES.xlsx")
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

# Convertir columnas de fecha y calcular Edad y Antigüedad si no están presentes
date_columns = ['Fecha_de_Ingreso', 'Fecha_de_nacimiento']
for col in date_columns:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# Calcular Edad y Antigüedad si no están en el Excel
current_date = datetime(2025, 5, 20)
if 'Edad' not in df.columns and 'Fecha_de_nacimiento' in df.columns:
    df['Edad'] = (current_date - df['Fecha_de_nacimiento']).dt.days // 365
if 'Antigüedad' not in df.columns and 'Fecha_de_Ingreso' in df.columns:
    df['Antigüedad'] = (current_date - df['Fecha_de_Ingreso']).dt.days // 365

# Normalizar Porcentaje_Banda_Salarial (asegurar que esté entre 0 y 1)
if 'Porcentaje_Banda_Salarial' in df.columns:
    df['Porcentaje_Banda_Salarial'] = pd.to_numeric(df['Porcentaje_Banda_Salarial'], errors='coerce')
    # Si está en porcentaje (ej., 25), convertir a decimal (0.25)
    df['Porcentaje_Banda_Salarial'] = df['Porcentaje_Banda_Salarial'].apply(lambda x: x / 100 if x > 1 else x)

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
    # Calcular métricas
    promedio_edad = df_filtered['Edad'].mean() if 'Edad' in df_filtered.columns else 0
    promedio_antiguedad = df_filtered['Antigüedad'].mean() if 'Antigüedad' in df_filtered.columns else 0
    promedio_sueldo = df_filtered['Total_sueldo_bruto'].mean()
    minimo_sueldo = df_filtered['Total_sueldo_bruto'].min()
    maximo_sueldo = df_filtered['Total_sueldo_bruto'].max()
    dispersion_sueldo = maximo_sueldo - minimo_sueldo
    dispersion_porcentaje = (dispersion_sueldo / minimo_sueldo * 100) if minimo_sueldo > 0 else 0
    costo_total = df_filtered['Costo_laboral'].sum()

    # Distribución de Especialidad
    especialidad_dist = df_filtered['Especialidad'].value_counts(normalize=True) * 100
    especialidad_dist = especialidad_dist.reset_index()
    especialidad_dist.columns = ['Especialidad', 'Porcentaje']

    # Distribución de Bandas Salariales
    banda_25 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.25]) / len(df_filtered) * 100
    banda_50 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.50]) / len(df_filtered) * 100
    banda_75 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.75]) / len(df_filtered) * 100
    banda_arriba_75 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] >= 0.75]) / len(df_filtered) * 100

    # Métricas en columnas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Personas", len(df_filtered))
    col2.metric("Edad Promedio", f"{promedio_edad:.1f} años")
    col3.metric("Antigüedad Promedio", f"{promedio_antiguedad:.1f} años")
    col4.metric("Sueldo Bruto Promedio", f"${promedio_sueldo:,.0f}")

    col5, col6, col7 = st.columns(3)
    col5.metric("Sueldo Mínimo", f"${minimo_sueldo:,.0f}")
    col6.metric("Sueldo Máximo", f"${maximo_sueldo:,.0f}")
    col7.metric("Dispersión Salarial", f"${dispersion_sueldo:,.0f} ({dispersion_porcentaje:.1f}%)")

    # Distribución de Especialidad
    st.markdown("### Distribución de Especialidad")
    especialidad_chart = alt.Chart(especialidad_dist).mark_bar().encode(
        x=alt.X('Porcentaje:Q', title='Porcentaje (%)'),
        y=alt.Y('Especialidad:N', title='Especialidad', sort='-x'),
        tooltip=['Especialidad', alt.Tooltip('Porcentaje:Q', format='.1f')]
    ).properties(height=300)
    st.altair_chart(especialidad_chart, use_container_width=True)

    # Distribución de Bandas Salariales
    st.markdown("### Distribución de Bandas Salariales")
    banda_data = pd.DataFrame({
        'Categoría': ['< 25%', '25-50%', '50-75%', '≥ 75%'],
        'Porcentaje': [
            banda_25,
            banda_50 - banda_25,
            banda_75 - banda_50,
            banda_arriba_75
        ]
    })
    banda_chart = alt.Chart(banda_data).mark_arc().encode(
        theta=alt.Theta('Porcentaje:Q', stack=True),
        color=alt.Color('Categoría:N', legend=alt.Legend(title="Banda Salarial")),
        tooltip=['Categoría', alt.Tooltip('Porcentaje:Q', format='.1f')]
    ).properties(width=300, height=300)
    st.altair_chart(banda_chart, use_container_width=True)

    # Mostrar porcentajes de bandas
    st.markdown("**Porcentajes por Banda Salarial**:")
    st.write(f"- Debajo del 25%: {banda_25:.1f}%")
    st.write(f"- Debajo del 50%: {banda_50:.1f}%")
    st.write(f"- Debajo del 75%: {banda_75:.1f}%")
    st.write(f"- Arriba del 75%: {banda_arriba_75:.1f}%")

else:
    st.info("No hay datos disponibles con los filtros actuales.")
    promedio_edad = promedio_antiguedad = promedio_sueldo = minimo_sueldo = maximo_sueldo = dispersion_sueldo = dispersion_porcentaje = costo_total = 0
    banda_25 = banda_50 = banda_75 = banda_arriba_75 = 0
    especialidad_dist = pd.DataFrame()

# Comparación por Categoría
st.markdown("### Comparación por Categoría")
agrupadores = [
    'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
    'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior'
]
agrupadores = [col for col in agrupadores if col in df.columns]
grupo_seleccionado = st.selectbox("Selecciona una categoría para agrupar", agrupadores, index=agrupadores.index('Puesto') if 'Puesto' in agrupadores else 0)

if len(df_filtered) > 0:
    # Calcular métricas por grupo
    grouped_data = df_filtered.groupby(grupo_seleccionado).agg({
        'Total_sueldo_bruto': ['mean', 'min', 'max'],
        'seniority': 'count'
    }).reset_index()
    grouped_data.columns = [grupo_seleccionado, 'Sueldo_Promedio', 'Sueldo_Mínimo', 'Sueldo_Máximo', 'Cantidad']
    grouped_data = grouped_data.dropna(subset=[grupo_seleccionado, 'Sueldo_Promedio'])
    grouped_data[grupo_seleccionado] = grouped_data[grupo_seleccionado].astype(str)

    # Gráfico de sueldos promedio
    chart = alt.Chart(grouped_data).mark_bar().encode(
        x=alt.X(f"{grupo_seleccionado}:N", title=grupo_seleccionado, sort="-y"),
        y=alt.Y("Sueldo_Promedio:Q", title="Sueldo Bruto Promedio"),
        tooltip=[
            grupo_seleccionado,
            alt.Tooltip("Sueldo_Promedio:Q", title="Sueldo Promedio", format=",.0f"),
            alt.Tooltip("Sueldo_Mínimo:Q", title="Sueldo Mínimo", format=",.0f"),
            alt.Tooltip("Sueldo_Máximo:Q", title="Sueldo Máximo", format=",.0f")
        ]
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

    # Si se selecciona Puesto, mostrar distribución de Seniority
    if grupo_seleccionado == 'Puesto':
        st.markdown("### Distribución de Seniority por Puesto")
        puesto_seleccionado = st.selectbox("Selecciona un Puesto", df_filtered['Puesto'].unique())
        df_puesto = df_filtered[df_filtered['Puesto'] == puesto_seleccionado]
        if len(df_puesto) > 0:
            seniority_dist = df_puesto['seniority'].value_counts(normalize=True) * 100
            seniority_dist = seniority_dist.reset_index()
            seniority_dist.columns = ['Seniority', 'Porcentaje']
            seniority_chart = alt.Chart(seniority_dist).mark_arc().encode(
                theta=alt.Theta('Porcentaje:Q', stack=True),
                color=alt.Color('Seniority:N', legend=alt.Legend(title="Seniority")),
                tooltip=['Seniority', alt.Tooltip('Porcentaje:Q', format='.1f')]
            ).properties(width=300, height=300)
            st.altair_chart(seniority_chart, use_container_width=True)

            # Mostrar sueldos para el puesto seleccionado
            sueldo_stats = df_puesto['Total_sueldo_bruto'].agg(['min', 'mean', 'max']).round(0)
            st.markdown(f"**Sueldos para {puesto_seleccionado}**:")
            st.write(f"- Mínimo: ${sueldo_stats['min']:,.0f}")
            st.write(f"- Promedio: ${sueldo_stats['mean']:,.0f}")
            st.write(f"- Máximo: ${sueldo_stats['max']:,.0f}")
        else:
            st.warning("No hay datos para el puesto seleccionado.")

    # Si se selecciona Seniority, mostrar sueldos
    if grupo_seleccionado == 'seniority':
        sueldo_stats = grouped_data[['seniority', 'Sueldo_Mínimo', 'Sueldo_Promedio', 'Sueldo_Máximo']]
        st.markdown("**Sueldos por Seniority**:")
        st.dataframe(sueldo_stats)

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
        'Edad_Promedio': [promedio_edad],
        'Antigüedad_Promedio': [promedio_antiguedad],
        'Sueldo_Promedio': [promedio_sueldo],
        'Sueldo_Mínimo': [minimo_sueldo],
        'Sueldo_Máximo': [maximo_sueldo],
        'Dispersión_Salarial': [dispersion_sueldo],
        'Costo_laboral': [costo_total],
        'Porcentaje_<25%': [banda_25],
        'Porcentaje_<50%': [banda_50],
        'Porcentaje_<75%': [banda_75],
        'Porcentaje_≥75%': [banda_arriba_75]
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
    pdf.cell(200, 10, txt=f"Edad promedio: {promedio_edad:.1f} años", ln=True)
    pdf.cell(200, 10, txt=f"Antigüedad promedio: {promedio_antiguedad:.1f} años", ln=True)
    pdf.cell(200, 10, txt=f"Sueldo promedio: ${promedio_sueldo:,.0f}", ln=True)
    pdf.cell(200, 10, txt=f"Sueldo mínimo / máximo: ${minimo_sueldo:,.0f} / ${maximo_sueldo:,.0f}", ln=True)
    pdf.cell(200, 10, txt=f"Dispersión salarial: ${dispersion_sueldo:,.0f} ({dispersion_porcentaje:.1f}%)", ln=True)
    pdf.cell(200, 10, txt=f"Porcentaje <25%: {banda_25:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"Porcentaje <50%: {banda_50:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"Porcentaje <75%: {banda_75:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"Porcentaje ≥75%: {banda_arriba_75:.1f}%", ln=True)

    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmpfile.name)
    with open(tmpfile.name, "rb") as f:
        st.download_button("Descargar reporte en PDF", f.read(), file_name="reporte_sueldos.pdf", mime="application/pdf")

# Conclusión Final
st.markdown("### Conclusión Final")
if len(df_filtered) > 0:
    conclusion = f"""
    - Se analizaron **{len(df_filtered)}** empleados con una edad promedio de **{promedio_edad:.1f} años** y una antigüedad promedio de **{promedio_antiguedad:.1f} años**.
    - El sueldo bruto promedio es **${promedio_sueldo:,.0f}**, con un rango de **${minimo_sueldo:,.0f}** a **${maximo_sueldo:,.0f}**, lo que indica una dispersión de **${dispersion_sueldo:,.0f} ({dispersion_porcentaje:.1f}%)**.
    - La distribución de bandas salariales muestra que:
      - **{banda_25:.1f}%** está por debajo del 25% de la banda.
      - **{banda_50:.1f}%** está por debajo del 50%.
      - **{banda_75:.1f}%** está por debajo del 75%.
      - **{banda_arriba_75:.1f}%** está por encima del 75%.
    - Las especialidades más comunes son **{especialidad_dist.iloc[0]['Especialidad'] if not especialidad_dist.empty else 'N/A'}** ({especialidad_dist.iloc[0]['Porcentaje']:.1f}% si aplica).
    - **Recomendación**: Revisar los puestos con alta dispersión salarial y seniority bajo para ajustar políticas de compensación.
    """
    st.markdown(conclusion)
else:
    st.markdown("No hay datos suficientes para generar una conclusión. Ajuste los filtros para incluir más datos.")
