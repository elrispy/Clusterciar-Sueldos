import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import io
from PIL import Image
from fpdf import FPDF
import tempfile
from datetime import datetime
import os

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

# Configuración de la página
st.set_page_config(page_title="Reporte de Sueldos", layout="wide")

# Cargar logo
try:
    logo = Image.open("logo-clusterciar.png")
    st.image(logo, width=200)
except FileNotFoundError:
    st.warning("No se encontró el archivo logo-clusterciar.png")

# Menú principal para seleccionar la página
st.sidebar.header("Menú Principal")
page = st.sidebar.selectbox("Selecciona una página", ["Reporte de Sueldos", "Tabla Salarial"])

# --- Página: Reporte de Sueldos ---
if page == "Reporte de Sueldos":
    st.title("Reporte Interactivo de Sueldos")

    # Selección del dataset en la barra lateral
    st.sidebar.header("Selección de Dataset")
    dataset_options = {
        "Sueldos para Informes": "SUELDOS PARA INFORMES.xlsx",
        "Otro Excel": "OTRO_EXCEL.xlsx"
    }
    selected_dataset = st.sidebar.selectbox("Selecciona el archivo a analizar", list(dataset_options.keys()))

    # Cargar el archivo Excel seleccionado
    @st.cache_data
    def load_data(file_name):
        return pd.read_excel(file_name, sheet_name=0)

    try:
        df = load_data(dataset_options[selected_dataset])
    except FileNotFoundError:
        st.error(f"No se encontró el archivo {dataset_options[selected_dataset]}")
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
    st.subheader(f"Resumen General - {selected_dataset}")

    if len(df_filtered) > 0:
        # Calcular métricas
        promedio_edad = df_filtered['Edad'].mean() if 'Edad' in df_filtered.columns else 0
        promedio_antiguedad = df_filtered['Antigüedad'].mean() if 'Antigüedad' in df_filtered.columns else 0
        promedio_sueldo = df_filtered['Total_sueldo_bruto'].mean() if 'Total_sueldo_bruto' in df_filtered.columns else 0
        minimo_sueldo = df_filtered['Total_sueldo_bruto'].min() if 'Total_sueldo_bruto' in df_filtered.columns else 0
        maximo_sueldo = df_filtered['Total_sueldo_bruto'].max() if 'Total_sueldo_bruto' in df_filtered.columns else 0
        dispersion_sueldo = maximo_sueldo - minimo_sueldo
        dispersion_porcentaje = (dispersion_sueldo / minimo_sueldo * 100) if minimo_sueldo > 0 else 0
        costo_total = df_filtered['Costo_laboral'].sum() if 'Costo_laboral' in df_filtered.columns else 0

        # Distribución de Especialidad
        if 'Especialidad' in df_filtered.columns:
            especialidad_dist = df_filtered['Especialidad'].value_counts(normalize=True) * 100
            especialidad_dist = especialidad_dist.reset_index()
            especialidad_dist.columns = ['Especialidad', 'Porcentaje']
        else:
            especialidad_dist = pd.DataFrame()

        # Distribución de Bandas Salariales
        if 'Porcentaje_Banda_Salarial' in df_filtered.columns:
            banda_25 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.25]) / len(df_filtered) * 100
            banda_50 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.50]) / len(df_filtered) * 100
            banda_75 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.75]) / len(df_filtered) * 100
            banda_arriba_75 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] >= 0.75]) / len(df_filtered) * 100
        else:
            banda_25 = banda_50 = banda_75 = banda_arriba_75 = 0

        # Métricas en columnas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Personas", len(df_filtered))
        col2.metric("Edad Promedio", f"{promedio_edad:.1f} años")
        col3.metric("Antigüedad Promedio", f"{promedio_antiguedad:.1f} años")
        col4.metric("Sueldo Bruto Promedio", f"${promedio_sueldo:,.0f}")

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Sueldo Mínimo", f"${minimo_sueldo:,.0f}")
        col6.metric("Sueldo Máximo", f"${maximo_sueldo:,.0f}")
        col7.metric("Dispersión Salarial", f"${dispersion_sueldo:,.0f} ({dispersion_porcentaje:.1f}%)")
        col8.metric("Costo Laboral Total", f"${costo_total:,.0f}")

        # Distribución de Especialidad
        if 'Especialidad' in df_filtered.columns:
            st.markdown("### Distribución de Especialidad")
            especialidad_chart = alt.Chart(especialidad_dist).mark_bar().encode(
                x=alt.X('Porcentaje:Q', title='Porcentaje (%)'),
                y=alt.Y('Especialidad:N', title='Especialidad', sort='-x'),
                tooltip=['Especialidad', alt.Tooltip('Porcentaje:Q', format='.1f')]
            ).properties(height=300)
            st.altair_chart(especialidad_chart, use_container_width=True)

        # Distribución de Bandas Salariales
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
    grupo_seleccionado = st.selectbox("Selecciona una categoría para agrupar", agrupadores, index=agrupadores.index('Puesto_tabla_salarial') if 'Puesto_tabla_salarial' in agrupadores else 0)

    if len(df_filtered) > 0:
        # Calcular métricas por grupo
        if 'Total_sueldo_bruto' in df_filtered.columns:
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

        # Si se selecciona Puesto_tabla_salarial, mostrar distribución de Seniority
        if grupo_seleccionado == 'Puesto_tabla_salarial' and 'Puesto_tabla_salarial' in df_filtered.columns and 'seniority' in df_filtered.columns:
            st.markdown("### Distribución de Seniority por Puesto Tabla Salarial")
            puesto_seleccionado = st.selectbox("Selecciona un Puesto Tabla Salarial", df_filtered['Puesto_tabla_salarial'].unique())
            df_puesto = df_filtered[df_filtered['Puesto_tabla_salarial'] == puesto_seleccionado]
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
                if 'Total_sueldo_bruto' in df_puesto.columns:
                    sueldo_stats = df_puesto['Total_sueldo_bruto'].agg(['min', 'mean', 'max']).round(0)
                    st.markdown(f"**Sueldos para {puesto_seleccionado}**:")
                    st.write(f"- Mínimo: ${sueldo_stats['min']:,.0f}")
                    st.write(f"- Promedio: ${sueldo_stats['mean']:,.0f}")
                    st.write(f"- Máximo: ${sueldo_stats['max']:,.0f}")
            else:
                st.warning("No hay datos para el puesto tabla salarial seleccionado.")

        # Si se selecciona Seniority, mostrar sueldos
        if grupo_seleccionado == 'seniority' and 'seniority' in df_filtered.columns and 'Total_sueldo_bruto' in df_filtered.columns:
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
        file_name=f'sueldos_filtrados_{selected_dataset.lower().replace(" ", "_")}.csv',
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
        file_name=f'reporte_sueldos_{selected_dataset.lower().replace(" ", "_")}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

    # Exportar a PDF
    if st.button("Generar reporte en PDF"):
        pdf = FPDF()
        pdf.add_page()

        # Usar Arial como fuente (PDF no soporta Red Hat Display directamente)
        pdf.set_font("Arial", size=12)

        # Agregar logo
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                logo.save(tmpfile.name)
                pdf.image(tmpfile.name, x=10, y=8, w=50)
            os.unlink(tmpfile.name)
        except Exception as e:
            pdf.cell(200, 10, txt="Logo no disponible", ln=True, align='C')

        pdf.ln(30)
        # Limpiar texto para evitar caracteres no soportados
        def clean_text(text):
            return ''.join(c for c in str(text) if ord(c) < 128)

        pdf.cell(200, 10, txt=clean_text(f"Reporte de Sueldos - {selected_dataset}"), ln=True, align='C')
        pdf.ln(10)
        pdf.cell(200, 10, txt=clean_text(f"Total personas: {len(df_filtered)}"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Edad promedio: {promedio_edad:.1f} años"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Antigüedad promedio: {promedio_antiguedad:.1f} años"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Sueldo promedio: ${promedio_sueldo:,.0f}"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Sueldo mínimo / máximo: ${minimo_sueldo:,.0f} / ${maximo_sueldo:,.0f}"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Dispersión salarial: ${dispersion_sueldo:,.0f} ({dispersion_porcentaje:.1f}%)"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Costo laboral total: ${costo_total:,.0f}"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Porcentaje <25%: {banda_25:.1f}%"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Porcentaje <50%: {banda_50:.1f}%"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Porcentaje <75%: {banda_75:.1f}%"), ln=True)
        pdf.cell(200, 10, txt=clean_text(f"Porcentaje ≥75%: {banda_arriba_75:.1f}%"), ln=True)

        # Guardar PDF
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                pdf.output(tmpfile.name)
                with open(tmpfile.name, "rb") as f:
                    st.download_button(
                        label="Descargar reporte en PDF",
                        data=f.read(),
                        file_name=f"reporte_sueldos_{selected_dataset.lower().replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
            os.unlink(tmpfile.name)
        except Exception as e:
            st.error(f"Error al generar el PDF: {str(e)}")

    # Conclusión Final
    st.markdown("### Conclusión Final")
    if len(df_filtered) > 0:
        conclusion = f"""
        - Se analizaron **{len(df_filtered)}** empleados con una edad promedio de **{promedio_edad:.1f} años** y una antigüedad promedio de **{promedio_antiguedad:.1f} años**.
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

    # Cargar el archivo de tabla salarial
    @st.cache_data
    def load_tabla_salarial():
        return pd.read_excel("tabla salarial.xlsx", sheet_name=0)

    try:
        df_tabla = load_tabla_salarial()
    except FileNotFoundError:
        st.error("No se encontró el archivo tabla salarial.xlsx")
        st.stop()

    # Limpiar nombres de columnas
    df_tabla.columns = df_tabla.columns.str.strip().str.replace(' ', '_')

    # Obtener listas únicas de Puesto, Seniority y Locación
    puestos = sorted(df_tabla['Puesto'].unique())
    seniorities = sorted(df_tabla['Seniority'].unique())
    locaciones = sorted(df_tabla['Locacion'].unique())

    # Selección de Puesto, Seniority y Locación
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_puesto = st.selectbox("Selecciona un Puesto", puestos)
    with col2:
        selected_seniority = st.selectbox("Selecciona un Seniority", seniorities)
    with col3:
        selected_locacion = st.selectbox("Selecciona una Locación", locaciones)

    # Filtrar los datos según la selección
    df_selected = df_tabla[
        (df_tabla['Puesto'] == selected_puesto) &
        (df_tabla['Seniority'] == selected_seniority) &
        (df_tabla['Locacion'] == selected_locacion)
    ]

    # Mostrar los valores Q1 a Q5
    if not df_selected.empty:
        st.subheader(f"Valores Salariales para {selected_puesto} - {selected_seniority} - {selected_locacion}")
        valores = df_selected[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].iloc[0]
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Q1", f"${valores['Q1']:,.0f}")
        col2.metric("Q2", f"${valores['Q2']:,.0f}")
        col3.metric("Q3", f"${valores['Q3']:,.0f}")
        col4.metric("Q4", f"${valores['Q4']:,.0f}")
        col5.metric("Q5", f"${valores['Q5']:,.0f}")

        # Gráfico de barras para visualizar Q1 a Q5
        st.markdown("### Visualización de Rangos Salariales")
        df_plot = pd.DataFrame({
            'Quintil': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'],
            'Sueldo': [valores['Q1'], valores['Q2'], valores['Q3'], valores['Q4'], valores['Q5']]
        })
        chart = alt.Chart(df_plot).mark_bar().encode(
            x=alt.X('Quintil:N', title='Quintil'),
            y=alt.Y('Sueldo:Q', title='Sueldo ($)'),
            tooltip=[alt.Tooltip('Quintil:N'), alt.Tooltip('Sueldo:Q', format=",.0f")]
        ).properties(width=400, height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning(f"No se encontraron datos para {selected_puesto} con Seniority {selected_seniority} en Locación {selected_locacion}.")

    # Opción para descargar la tabla salarial completa
    csv = df_tabla.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar tabla salarial completa como CSV",
        data=csv,
        file_name='tabla_salarial.csv',
        mime='text/csv',
    )
