```python
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import io
from PIL import Image
from fpdf import FPDF
import tempfile
import os

# Configuración de la página (debe ser la primera llamada)
st.set_page_config(page_title="Reporte de Sueldos y Análisis de Legajos", layout="wide")

# CSS personalizado con fuente Red Hat Display y diseño responsive
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;700&display=swap');

    /* Aplicar Red Hat Display a todos los elementos */
    * {
        font-family: 'Red Hat Display', sans-serif !important;
    }

    /* Estilo general */
    .stApp {
        max-width: 100%;
        margin: 0 auto;
    }

    /* Menú lateral responsive */
    .sidebar .sidebar-content {
        padding: 10px;
    }
    @media (max-width: 768px) {
        .sidebar .sidebar-content {
            width: 100%;
            position: relative;
            height: auto;
            padding: 5px;
        }
        .sidebar .sidebar-content .stSelectbox {
            width: 90%;
            margin: 5px auto;
        }
        .sidebar .sidebar-content .stButton {
            width: 90%;
            margin: 5px auto;
        }
        .stApp [data-testid="stSidebar"] {
            width: 100% !important;
            position: relative;
        }
        /* Apilar columnas en móviles */
        .css-1d8v2e5 {
            flex-direction: column !important;
        }
        .css-1d8v2e5 > div {
            width: 100% !important;
            margin-bottom: 10px;
        }
        /* Ajustar tamaño de texto y gráficos */
        .stMetric {
            font-size: 14px !important;
        }
        .stMarkdown {
            font-size: 16px !important;
        }
        .altair-chart {
            width: 100% !important;
            height: auto !important;
        }
        /* Botones y selectores más grandes para touch */
        .stButton>button {
            padding: 10px 20px;
            font-size: 16px;
        }
        .stSelectbox>select {
            padding: 10px;
            font-size: 16px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Cargar logo
try:
    logo = Image.open("logo-clusterciar.png")
    st.image(logo, width=200)
except FileNotFoundError:
    st.warning("No se encontró el archivo logo-clusterciar.png")

# Menú principal para seleccionar la página
st.sidebar.header("Menú Principal")
page = st.sidebar.selectbox("Selecciona una página", ["Reporte de Sueldos", "Tabla Salarial", "Elegir Base de Datos"])

# --- Función para cargar datos de Análisis de Legajos ---
@st.cache_data
def load_legajos_data():
    try:
        df = pd.read_excel("Análisis de Legajos.xlsx")
        # Limpiar datos: reemplazar valores vacíos con cadenas vacías
        df = df.fillna('')
        return df
    except FileNotFoundError:
        st.error("No se encontró el archivo 'Análisis de Legajos.xlsx'. Asegúrate de que esté en el mismo directorio.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return pd.DataFrame()

# Inicializar estado de la sesión para los filtros de legajos
if 'legajos_filters' not in st.session_state:
    st.session_state.legajos_filters = {
        'Empresa': '',
        'Comitente': '',
        'Locacion': '',
        'Es cvh': '',
        'Convenio': '',
        'Centro de costo': ''
    }

# --- Página: Reporte de Sueldos ---
if page == "Reporte de Sueldos":
    st.title("Reporte Interactivo de Sueldos")

    # Cargar el archivo Excel fijo (sin selección de dataset)
    @st.cache_data
    def load_data():
        return pd.read_excel("SUELDOS PARA INFORMES.xlsx", sheet_name=0)

    try:
        df = load_data()
    except FileNotFoundError:
        st.error("No se encontró el archivo SUELDOS PARA INFORMES.xlsx")
        st.stop()

    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('%_BANDA_SALARIAL', 'Porcentaje_Banda_Salarial')

    # Convertir columnas categóricas a string y manejar valores inválidos
    categorical_columns = [
        'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
        'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior',
        'PersonaApellido', 'PersonaNombre'
    ]
    for col in categorical_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(['#Ref', 'nan'], '')

    # Convertir columnas de fecha
    date_columns = ['Fecha_de_Ingreso', 'Fecha_de_nacimiento']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Normalizar Porcentaje_Banda_Salarial
    if 'Porcentaje_Banda_Salarial' in df.columns:
        df['Porcentaje_Banda_Salarial'] = pd.to_numeric(df['Porcentaje_Banda_Salarial'], errors='coerce')
        df['Porcentaje_Banda_Salarial'] = df['Porcentaje_Banda_Salarial'].apply(lambda x: x / 100 if x > 1 else x)

    # Filtros en la barra lateral
    st.sidebar.header("Filtros")
    filtros = {}
    for col in ['Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
                'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior']:
        if col in df.columns:
            filtros[col] = st.sidebar.multiselect(col.replace('_', ' ').title(), df[col].unique())
        else:
            filtros[col] = []

    # Aplicar filtros
    df_filtered = df.copy()
    for key, values in filtros.items():
        if values:
            df_filtered = df_filtered[df_filtered[key].isin(values)]

    # Resumen General
    st.subheader("Resumen General - Sueldos para Informes")

    if len(df_filtered) > 0:
        promedio_sueldo = df_filtered['Total_sueldo_bruto'].mean() if 'Total_sueldo_bruto' in df_filtered.columns else 0
        minimo_sueldo = df_filtered['Total_sueldo_bruto'].min() if 'Total_sueldo_bruto' in df_filtered.columns else 0
        maximo_sueldo = df_filtered['Total_sueldo_bruto'].max() if 'Total_sueldo_bruto' in df_filtered.columns else 0
        dispersion_sueldo = maximo_sueldo - minimo_sueldo
        dispersion_porcentaje = (dispersion_sueldo / minimo_sueldo * 100) if minimo_sueldo > 0 else 0
        costo_total = df_filtered['Costo_laboral'].sum() if 'Costo_laboral' in df_filtered.columns else 0

        if 'Especialidad' in df_filtered.columns:
            especialidad_dist = df_filtered['Especialidad'].value_counts(normalize=True) * 100
            especialidad_dist = especialidad_dist.reset_index()
            especialidad_dist.columns = ['Especialidad', 'Porcentaje']
        else:
            especialidad_dist = pd.DataFrame()

        if 'Porcentaje_Banda_Salarial' in df_filtered.columns:
            banda_25 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.25]) / len(df_filtered) * 100
            banda_50 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.50]) / len(df_filtered) * 100
            banda_75 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.75]) / len(df_filtered) * 100
            banda_arriba_75 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] >= 0.75]) / len(df_filtered) * 100
        else:
            banda_25 = banda_50 = banda_75 = banda_arriba_75 = 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Personas", len(df_filtered))
        col2.metric("Sueldo Bruto Promedio", f"${promedio_sueldo:,.0f}")
        col3.metric("Sueldo Mínimo", f"${minimo_sueldo:,.0f}")
        col4.metric("Sueldo Máximo", f"${maximo_sueldo:,.0f}")

        col5, col6 = st.columns(2)
        col5.metric("Dispersión Salarial", f"${dispersion_sueldo:,.0f} ({dispersion_porcentaje:.1f}%)")
        col6.metric("Costo Laboral Total", f"${costo_total:,.0f}")

        if 'Especialidad' in df_filtered.columns:
            st.markdown("### Distribución de Especialidad")
            especialidad_chart = alt.Chart(especialidad_dist).mark_bar().encode(
                x=alt.X('Porcentaje:Q', title='Porcentaje (%)'),
                y=alt.Y('Especialidad:N', title='Especialidad', sort='-x'),
                tooltip=['Especialidad', alt.Tooltip('Porcentaje:Q', format='.1f')]
            ).properties(height=300)
            st.altair_chart(especialidad_chart, use_container_width=True)

        if 'Porcentaje_Banda_Salarial' in df_filtered.columns:
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

            st.markdown("**Porcentajes por Banda Salarial**:")
            st.write(f"- Debajo del 25%: {banda_25:.1f}%")
            st.write(f"- Debajo del 50%: {banda_50:.1f}%")
            st.write(f"- Debajo del 75%: {banda_75:.1f}%")
            st.write(f"- Arriba del 75%: {banda_arriba_75:.1f}%")

    else:
        st.info("No hay datos disponibles con los filtros actuales.")
        promedio_sueldo = minimo_sueldo = maximo_sueldo = dispersion_sueldo = dispersion_porcentaje = costo_total = 0
        banda_25 = banda_50 = banda_75 = banda_arriba_75 = 0
        especialidad_dist = pd.DataFrame()

    # Comparación por Categoría
    st.markdown("### Comparación por Categoría")
    agrupadores = [
        'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
        'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior'
    ]
    agrupadores = [col for col in agrupadores if col in df.columns]
    grupo_seleccionado = st.selectbox("Selecciona una categoría para agrupar", agrupadores, index=agrupadores.index('Puesto_tabla_salarial') if 'Puesto_tabla_salarial' in agrupadores else 0)

    if len(df_filtered) > 0 and 'Total_sueldo_bruto' in df_filtered.columns:
        grouped_data = df_filtered.groupby(grupo_seleccionado).agg({
            'Total_sueldo_bruto': ['mean', 'min', 'max'],
            'seniority': 'count'
        }).reset_index()
        grouped_data.columns = [grupo_seleccionado, 'Sueldo_Promedio', 'Sueldo_Mínimo', 'Sueldo_Máximo', 'Cantidad']
        grouped_data = grouped_data.dropna(subset=[grupo_seleccionado, 'Sueldo_Promedio'])
        grouped_data[grupo_seleccionado] = grouped_data[grupo_seleccionado].astype(str)

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

        if grupo_seleccionado == 'Puesto_tabla_salarial' and 'seniority' in df_filtered.columns:
            st.markdown("### Distribución de Seniority por Puesto Tabla Salarial")
            puesto_seleccionado = st.selectbox("Selecciona un Puesto Tabla Salarial", df_filtered['Puesto_tabla_salarial'].unique())
            df_puesto = df_filtered[df_filtered['Puesto_tabla_salarial'] == puesto_seleccionado]
            if len(df_puesto) > 0 and 'Total_sueldo_bruto' in df_puesto.columns:
                seniority_dist = df_puesto['seniority'].value_counts(normalize=True) * 100
                seniority_dist = seniority_dist.reset_index()
                seniority_dist.columns = ['Seniority', 'Porcentaje']
                seniority_chart = alt.Chart(seniority_dist).mark_arc().encode(
                    theta=alt.Theta('Porcentaje:Q', stack=True),
                    color=alt.Color('Seniority:N', legend=alt.Legend(title="Seniority")),
                    tooltip=['Seniority', alt.Tooltip('Porcentaje:Q', format='.1f')]
                ).properties(width=300, height=300)
                st.altair_chart(seniority_chart, use_container_width=True)

                sueldo_stats = df_puesto['Total_sueldo_bruto'].agg(['min', 'mean', 'max']).round(0)
                st.markdown(f"**Sueldos para {puesto_seleccionado}**:")
                st.write(f"- Mínimo: ${sueldo_stats['min']:,.0f}")
                st.write(f"- Promedio: ${sueldo_stats['mean']:,.0f}")
                st.write(f"- Máximo: ${sueldo_stats['max']:,.0f}")
            else:
                st.warning("No hay datos para el puesto tabla salarial seleccionado.")

        if grupo_seleccionado == 'seniority':
            sueldo_stats = grouped_data[['seniority', 'Sueldo_Mínimo', 'Sueldo_Promedio', 'Sueldo_Máximo']]
            st.markdown("**Sueldos por Seniority**:")
            st.dataframe(sueldo_stats)

    else:
        st.warning("No hay datos para mostrar en el gráfico de comparación por categoría.")

    st.subheader("Tabla de Datos Filtrados")
    st.dataframe(df_filtered)

    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar datos filtrados como CSV",
        data=csv,
        file_name='sueldos_filtrados.csv',
        mime='text/csv',
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='Datos Filtrados')
        resumen = pd.DataFrame({
            'Total_personas': [len(df_filtered)],
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

    if st.button("Generar reporte en PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                logo.save(tmpfile.name)
                pdf.image(tmpfile.name, x=10, y=8, w=50)
            os.unlink(tmpfile.name)
        except Exception as e:
            pdf.cell(200, 10, txt="Logo no disponible", ln=True, align='C')

        pdf.ln(30)
        def clean_text(text):
            return ''.join(c for c in str(text) if ord(c) < 128)

        pdf.cell(200, 10, txt=clean_text("Reporte de Sueldos - Sueldos para Informes"), ln=True, align='C')
        pdf.ln(10)
        pdf.cell(200, 10, txt=clean_text(f"Total personas: {len(df_filtered)}"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Sueldo promedio: ${promedio_sueldo:,.0f}"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Sueldo mínimo / máximo: ${minimo_sueldo:,.0f} / ${maximo_sueldo:,.0f}"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Dispersión salarial: ${dispersion_sueldo:,.0f} ({dispersion_porcentaje:.1f}%)"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Costo laboral total: ${costo_total:,.0f}"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Porcentaje <25%: {banda_25:.1f}%"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Porcentaje <50%: {banda_50:.1f}%"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Porcentaje <75%: {banda_75:.1f}%"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Porcentaje ≥75%: {banda_arriba_75:.1f}%"), ln=True)

        if len(df_filtered) < 20 and all(col in df_filtered.columns for col in ['PersonaApellido', 'PersonaNombre', 'Puesto', 'Seniority', 'Porcentaje_Banda_Salarial', 'Total_sueldo_bruto']):
            pdf.ln(20)
            pdf.set_font("Arial", size=10)
            pdf.cell(200, 10, txt="Detalles de Personas (ordenado por Total Sueldo Bruto descendente)", ln=True, align='C')
            pdf.ln(5)
            columns = ['PersonaApellido', 'PersonaNombre', 'Puesto', 'Seniority', 'Porcentaje_Banda_Salarial', 'Total_sueldo_bruto']
            df_table = df_filtered[columns].sort_values(by='Total_sueldo_bruto', ascending=False)
            pdf.set_font("Arial", size=8)
            for col in columns:
                pdf.cell(33, 10, clean_text(col.replace('_', ' ').title()), border=1, align='C')
            pdf.ln()
            for index, row in df_table.iterrows():
                pdf.cell(33, 10, clean_text(str(row['PersonaApellido'])), border=1)
                pdf.cell(33, 10, clean_text(str(row['PersonaNombre'])), border=1)
                pdf.cell(33, 10, clean_text(str(row['Puesto'])), border=1)
                pdf.cell(33, 10, clean_text(str(row['Seniority'])), border=1)
                pdf.cell(33, 10, clean_text(f"{row['Porcentaje_Banda_Salarial']*100:.1f}%"), border=1)
                pdf.cell(35, 10, clean_text(f"${row['Total_sueldo_bruto']:,.0f}"), border=1)
                pdf.ln()

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                pdf.output(tmpfile.name)
                with open(tmpfile.name, "rb") as f:
                    st.download_button(
                        label="Descargar reporte en PDF",
                        data=f.read(),
                        file_name="reporte_sueldos.pdf",
                        mime="application/pdf"
                    )
            os.unlink(tmpfile.name)
        except Exception as e:
            st.error(f"Error al generar el PDF: {str(e)}")

    st.markdown("### Conclusión Final")
    if len(df_filtered) > 0:
        conclusion = f"""
        - Se analizaron **{len(df_filtered)}** empleados.
        - El sueldo bruto promedio es **${promedio_sueldo:,.0f}**.
        - El costo laboral total asciende a **${costo_total:,.0f}**.
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

# --- Página: Tabla Salarial ---
elif page == "Tabla Salarial":
    st.title("Consulta de Tabla Salarial")

    @st.cache_data
    def load_tabla_salarial():
        return pd.read_excel("tabla salarial.xlsx", sheet_name=0)

    try:
        df_tabla = load_tabla_salarial()
    except FileNotFoundError:
        st.error("No se encontró el archivo tabla salarial.xlsx")
        st.stop()

    df_tabla.columns = df_tabla.columns.str.strip().str.replace(' ', '_')

    puestos = sorted(df_tabla['Puesto'].unique())
    seniorities = sorted(df_tabla['Seniority'].unique())
    locaciones = sorted(df_tabla['Locacion'].unique())

    st.subheader("Comparativa de Valores Salariales")

    st.markdown("**Primera Selección**")
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_puesto_1 = st.selectbox("Selecciona un Puesto (1)", puestos, key="puesto_1")
    with col2:
        selected_seniority_1 = st.selectbox("Selecciona un Seniority (1)", seniorities, key="seniority_1")
    with col3:
        selected_locacion_1 = st.selectbox("Selecciona una Locación (1)", locaciones, key="locacion_1")

    df_selected_1 = df_tabla[
        (df_tabla['Puesto'] == selected_puesto_1) &
        (df_tabla['Seniority'] == selected_seniority_1) &
        (df_tabla['Locacion'] == selected_locacion_1)
    ]

    if not df_selected_1.empty:
        st.markdown(f"**Valores Salariales para {selected_puesto_1} - {selected_seniority_1} - {selected_locacion_1}**")
        valores_1 = df_selected_1[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].iloc[0]
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Q1", f"${valores_1['Q1']:,.0f}")
        col2.metric("Q2", f"${valores_1['Q2']:,.0f}")
        col3.metric("Q3", f"${valores_1['Q3']:,.0f}")
        col4.metric("Q4", f"${valores_1['Q4']:,.0f}")
        col5.metric("Q5", f"${valores_1['Q5']:,.0f}")
    else:
        st.warning(f"No se encontraron datos para {selected_puesto_1} con Seniority {selected_seniority_1} en Locación {selected_locacion_1}.")
        valores_1 = None

    st.markdown("**Segunda Selección**")
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_puesto_2 = st.selectbox("Selecciona un Puesto (2)", puestos, key="puesto_2")
    with col2:
        selected_seniority_2 = st.selectbox("Selecciona un Seniority (2)", seniorities, key="seniority_2")
    with col3:
        selected_locacion_2 = st.selectbox("Selecciona una Locación (2)", locaciones, key="locacion_2")

    df_selected_2 = df_tabla[
        (df_tabla['Puesto'] == selected_puesto_2) &
        (df_tabla['Seniority'] == selected_seniority_2) &
        (df_tabla['Locacion'] == selected_locacion_2)
    ]

    if not df_selected_2.empty:
        st.markdown(f"**Valores Salariales para {selected_puesto_2} - {selected_seniority_2} - {selected_locacion_2}**")
        valores_2 = df_selected_2[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].iloc[0]
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Q1", f"${valores_2['Q1']:,.0f}")
        col2.metric("Q2", f"${valores_2['Q2']:,.0f}")
        col3.metric("Q3", f"${valores_2['Q3']:,.0f}")
        col4.metric("Q4", f"${valores_2['Q4']:,.0f}")
        col5.metric("Q5", f"${valores_2['Q5']:,.0f}")
    else:
        st.warning(f"No se encontraron datos para {selected_puesto_2} con Seniority {selected_seniority_2} en Locación {selected_locacion_2}.")
        valores_2 = None

    if valores_1 is not None and valores_2 is not None:
        st.markdown("### Comparativa de Sueldos")
        promedio_1 = valores_1[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].mean()
        promedio_2 = valores_2[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].mean()
        if promedio_1 != 0:
            porcentaje_diferencia = ((promedio_2 - promedio_1) / promedio_1) * 100
            st.markdown(f"**Diferencia porcentual (basada en el promedio de Q1-Q5):** {porcentaje_diferencia:.2f}%")
            if porcentaje_diferencia > 0:
                st.write(f"El promedio de la segunda selección es {porcentaje_diferencia:.2f}% mayor que el de la primera.")
            elif porcentaje_diferencia < 0:
                st.write(f"El promedio de la segunda selección es {abs(porcentaje_diferencia):.2f}% menor que el de la primera.")
            else:
                st.write("No hay diferencia entre los promedios de las dos selecciones.")
        else:
            st.warning("No se puede calcular el porcentaje de diferencia porque el promedio de la primera selección es 0.")
    elif valores_1 is None or valores_2 is None:
        st.warning("No se puede calcular la diferencia porque una o ambas selecciones no tienen datos.")

    st.markdown("### Descargar Tabla Salarial Completa")
    col1, col2 = st.columns(2)
    with col1:
        csv = df_tabla.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar tabla salarial completa como CSV",
            data=csv,
            file_name='tabla_salarial.csv',
            mime='text/csv',
        )
    with col2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_tabla.to_excel(writer, index=False, sheet_name='Tabla Salarial')
        excel_data = output.getvalue()
        st.download_button(
            label="Descargar tabla salarial completa como Excel",
            data=excel_data,
            file_name='tabla_salarial.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

# --- Página: Elegir Base de Datos (Análisis de Legajos) ---
elif page == "Elegir Base de Datos":
    st.title("Análisis de Legajos")
    
    # Cargar datos de Análisis de Legajos
    df_legajos = load_legajos_data()
    
    # Botón para regresar al menú principal
    if st.button("Volver al Menú Principal"):
        st.session_state.page = "main_menu"
    
    if df_legajos.empty:
        st.warning("No hay datos disponibles para analizar.")
        st.stop()
    
    # Filtros para segmentación
    st.markdown("### Filtros para Segmentación")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        empresas = ['Todos'] + sorted(df_legajos['Empresa'].unique().tolist())
        selected_empresa = st.selectbox("Empresa", empresas, index=empresas.index(st.session_state.legajos_filters['Empresa']) if st.session_state.legajos_filters['Empresa'] in empresas else 0)
        st.session_state.legajos_filters['Empresa'] = selected_empresa if selected_empresa != "Todos" else ""
    
    with col2:
        comitentes = ['Todos'] + sorted(df_legajos['Comitente'].unique().tolist())
        selected_comitente = st.selectbox("Comitente", comitentes, index=comitentes.index(st.session_state.legajos_filters['Comitente']) if st.session_state.legajos_filters['Comitente'] in comitentes else 0)
        st.session_state.legajos_filters['Comitente'] = selected_comitente if selected_comitente != "Todos" else ""
    
    with col3:
        locaciones = ['Todos'] + sorted(df_legajos['Locacion'].unique().tolist())
        selected_locacion = st.selectbox("Locación", locaciones, index=locaciones.index(st.session_state.legajos_filters['Locacion']) if st.session_state.legajos_filters['Locacion'] in locaciones else 0)
        st.session_state.legajos_filters['Locacion'] = selected_locacion if selected_locacion != "Todos" else ""
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        es_cvh_options = ['Todos'] + sorted(df_legajos['Es cvh'].unique().tolist())
        selected_es_cvh = st.selectbox("Es CVH", es_cvh_options, index=es_cvh_options.index(st.session_state.legajos_filters['Es cvh']) if st.session_state.legajos_filters['Es cvh'] in es_cvh_options else 0)
        st.session_state.legajos_filters['Es cvh'] = selected_es_cvh if selected_es_cvh != "Todos" else ""
    
    with col5:
        convenios = ['Todos'] + sorted(df_legajos['Convenio'].unique().tolist())
        selected_convenio = st.selectbox("Convenio", convenios, index=convenios.index(st.session_state.legajos_filters['Convenio']) if st.session_state.legajos_filters['Convenio'] in convenios else 0)
        st.session_state.legajos_filters['Convenio'] = selected_convenio if selected_convenio != "Todos" else ""
    
    with col6:
        centros = ['Todos'] + sorted(df_legajos['Centro de costo'].unique().tolist())
        selected_centro = st.selectbox("Centro de Costo", centros, index=centros.index(st.session_state.legajos_filters['Centro de costo']) if st.session_state.legajos_filters['Centro de costo'] in centros else 0)
        st.session_state.legajos_filters['Centro de costo'] = selected_centro if selected_centro != "Todos" else ""
    
    # Aplicar filtros y mostrar resultados
    filtered_legajos = df_legajos.copy()
    for key, value in st.session_state.legajos_filters.items():
        if value:
            filtered_legajos = filtered_legajos[filtered_legajos[key] == value]
    
    st.subheader("Datos Filtrados")
    st.dataframe(filtered_legajos)
    
    # Botón para aplicar filtros y regresar al menú principal
    if st.button("Aplicar Filtros y Ver Resumen"):
        st.session_state.page = "main_menu"

# --- Menú Principal (mostrar resumen de legajos) ---
if page == "main_menu" or page == "Reporte de Sueldos" or page == "Tabla Salarial":
    st.title("Panel Principal")
    
    # Mostrar resumen de Análisis de Legajos basado en filtros
    df_legajos = load_legajos_data()
    if not df_legajos.empty:
        st.markdown("### Resumen de Análisis de Legajos (según filtros)")
        filtered_legajos = apply_filters(df_legajos, st.session_state.legajos_filters)
        
        total_records = len(df_legajos)
        filtered_records = len(filtered_legajos)
        percentage = (filtered_records / total_records * 100) if total_records > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Registros", total_records)
        col2.metric("Registros Filtrados", filtered_records)
        col3.metric("Porcentaje del Total", f"{percentage:.2f}%")
        
        # Desglose por Empresa
        if filtered_records > 0:
            st.markdown("#### Desglose por Empresa")
            empresa_counts = filtered_legajos['Empresa'].value_counts()
            for empresa, count in empresa_counts.items():
                percentage_empresa = (count / filtered_records * 100)
                st.write(f"**{empresa}**: {count} ({percentage_empresa:.2f}%)")
        else:
            st.write("No hay datos para mostrar con los filtros actuales.")
    else:
        st.warning("No se pudo cargar el archivo Análisis de Legajos.xlsx para mostrar el resumen.")

# Función auxiliar para aplicar filtros
def apply_filters(df, filters):
    filtered_df = df.copy()
    for key, value in filters.items():
        if value:
            filtered_df = filtered_df[filtered_df[key] == value]
    return filtered_df

# Ajuste para navegación
if page not in ["Reporte de Sueldos", "Tabla Salarial", "Elegir Base de Datos"]:
    st.session_state.page = "main_menu"
```
