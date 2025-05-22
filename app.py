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
st.set_page_config(page_title="Reporte de Sueldos", layout="wide")

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
page = st.sidebar.selectbox("Selecciona una página", ["Reporte de Sueldos", "Tabla Salarial", "Análisis de Legajos", "Comparar Personas"])

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
        'Personaapellido', 'Personanombre'
    ]
    for col in categorical_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(['#Ref', 'nan'], '')

    # Convertir columnas de fecha (sin calcular Edad ni Antigüedad)
    date_columns = ['Fecha_de_Ingreso', 'Fecha_de_nacimiento']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Normalizar Porcentaje_Banda_Salarial (asegurar que esté entre 0 y 1)
    if 'Porcentaje_Banda_Salarial' in df.columns:
        df['Porcentaje_Banda_Salarial'] = pd.to_numeric(df['Porcentaje_Banda_Salarial'], errors='coerce')
        df['Porcentaje_Banda_Salarial'] = df['Porcentaje_Banda_Salarial'].apply(lambda x: x / 100 if x > 1 else x)

    # Filtros en la barra lateral
    st.sidebar.header("Filtros")
    filtros = {}
    filter_columns = [
        'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
        'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior',
        'Personaapellido', 'Personanombre'
    ]
    for col in filter_columns:
        if col in df.columns:
            label = "Apellido" if col == "Personaapellido" else "Nombre" if col == "Personanombre" else col.replace('_', ' ').title()
            filtros[col] = st.sidebar.multiselect(label, df[col].unique())
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
        # Calcular métricas (sin Edad ni Antigüedad)
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

        # Métricas en columnas (sin Edad ni Antigüedad)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Personas", len(df_filtered))
        col2.metric("Sueldo Bruto Promedio", f"${promedio_sueldo:,.0f}")
        col3.metric("Sueldo Mínimo", f"${minimo_sueldo:,.0f}")
        col4.metric("Sueldo Máximo", f"${maximo_sueldo:,.0f}")

        col5, col6 = st.columns(2)
        col5.metric("Dispersión Salarial", f"${dispersion_sueldo:,.0f} ({dispersion_porcentaje:.1f}%)")
        col6.metric("Costo Laboral Total", f"${costo_total:,.0f}")

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
            puestos_opciones = ['Todos los puestos'] + sorted(df_filtered['Puesto_tabla_salarial'].unique().tolist())
            puesto_seleccionado = st.selectbox("Selecciona un Puesto Tabla Salarial", puestos_opciones)
            
            # Filtro de Gerencia
            gerencias = sorted(df_filtered['Gerencia'].unique().tolist())
            gerencia_seleccionada = st.multiselect("Selecciona Gerencia(s)", gerencias, default=gerencias)

            # Filtrar datos según selección
            if puesto_seleccionado == 'Todos los puestos':
                df_puesto = df_filtered[df_filtered['Gerencia'].isin(gerencia_seleccionada)]
            else:
                df_puesto = df_filtered[
                    (df_filtered['Puesto_tabla_salarial'] == puesto_seleccionado) &
                    (df_filtered['Gerencia'].isin(gerencia_seleccionada))
                ]

            if len(df_puesto) > 0:
                # Calcular distribución de seniority
                seniority_dist = df_puesto['seniority'].value_counts(normalize=True) * 100
                seniority_dist = seniority_dist.reset_index()
                seniority_dist.columns = ['Seniority', 'Porcentaje']

                # Gráfico de distribución
                seniority_chart = alt.Chart(seniority_dist).mark_arc().encode(
                    theta=alt.Theta('Porcentaje:Q', stack=True),
                    color=alt.Color('Seniority:N', legend=alt.Legend(title="Seniority")),
                    tooltip=['Seniority', alt.Tooltip('Porcentaje:Q', format='.1f')]
                ).properties(width=300, height=300)
                st.altair_chart(seniority_chart, use_container_width=True)

                # Mostrar porcentajes de seniority
                st.markdown("**Porcentajes de Seniority**:")
                for _, row in seniority_dist.iterrows():
                    st.write(f"- {row['Seniority']}: {row['Porcentaje']:.1f}%")

                # Mostrar sueldos para el puesto seleccionado (si no es "Todos los puestos")
                if puesto_seleccionado != 'Todos los puestos' and 'Total_sueldo_bruto' in df_puesto.columns:
                    sueldo_stats = df_puesto['Total_sueldo_bruto'].agg(['min', 'mean', 'max']).round(0)
                    st.markdown(f"**Sueldos para {puesto_seleccionado} (filtrado por Gerencia)**:")
                    st.write(f"- Mínimo: ${sueldo_stats['min']:,.0f}")
                    st.write(f"- Promedio: ${sueldo_stats['mean']:,.0f}")
                    st.write(f"- Máximo: ${sueldo_stats['max']:,.0f}")
            else:
                st.warning("No hay datos para el puesto tabla salarial y gerencia seleccionados.")

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
        file_name='sueldos_filtrados.csv',
        mime='text/csv',
    )

    # Exportar a Excel
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

        # Agregar cuadro con datos si hay menos de 20 personas
        if len(df_filtered) < 20 and all(col in df_filtered.columns for col in ['Personaapellido', 'Personanombre', 'Puesto', 'Seniority', 'Porcentaje_Banda_Salarial', 'Total_sueldo_bruto']):
            pdf.ln(20)
            pdf.set_font("Arial", size=10)
            pdf.cell(200, 10, txt="Detalles de Personas (ordenado por Total Sueldo Bruto descendente)", ln=True, align='C')
            pdf.ln(5)

            # Crear tabla
            columns = ['Personaapellido', 'Personanombre', 'Puesto', 'Seniority', 'Porcentaje_Banda_Salarial', 'Total_sueldo_bruto']
            df_table = df_filtered[columns].sort_values(by='Total_sueldo_bruto', ascending=False)
            pdf.set_font("Arial", size=8)

            # Encabezados de la tabla
            for col in columns:
                pdf.cell(33, 10, clean_text(col.replace('_', ' ').title()), border=1, align='C')
            pdf.ln()

            # Datos de la tabla
            for index, row in df_table.iterrows():
                pdf.cell(33, 10, clean_text(str(row['Personaapellido'])), border=1)
                pdf.cell(33, 10, clean_text(str(row['Personanombre'])), border=1)
                pdf.cell(33, 10, clean_text(str(row['Puesto'])), border=1)
                pdf.cell(33, 10, clean_text(str(row['Seniority'])), border=1)
                pdf.cell(33, 10, clean_text(f"{row['Porcentaje_Banda_Salarial']*100:.1f}%"), border=1)
                pdf.cell(35, 10, clean_text(f"${row['Total_sueldo_bruto']:,.0f}"), border=1)
                pdf.ln()

        # Guardar PDF
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

    # Conclusión Final
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

    # Comparativa: Selección de dos combinaciones
    st.subheader("Comparativa de Valores Salariales")

    # Primera selección
    st.markdown("**Primera Selección**")
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_puesto_1 = st.selectbox("Selecciona un Puesto (1)", puestos, key="puesto_1")
    with col2:
        selected_seniority_1 = st.selectbox("Selecciona un Seniority (1)", seniorities, key="seniority_1")
    with col3:
        selected_locacion_1 = st.selectbox("Selecciona una Locación (1)", locaciones, key="locacion_1")

    # Filtrar datos para la primera selección
    df_selected_1 = df_tabla[
        (df_tabla['Puesto'] == selected_puesto_1) &
        (df_tabla['Seniority'] == selected_seniority_1) &
        (df_tabla['Locacion'] == selected_locacion_1)
    ]

    # Mostrar valores de la primera selección
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

    # Segunda selección
    st.markdown("**Segunda Selección**")
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_puesto_2 = st.selectbox("Selecciona un Puesto (2)", puestos, key="puesto_2")
    with col2:
        selected_seniority_2 = st.selectbox("Selecciona un Seniority (2)", seniorities, key="seniority_2")
    with col3:
        selected_locacion_2 = st.selectbox("Selecciona una Locación (2)", locaciones, key="locacion_2")

    # Filtrar datos para la segunda selección
    df_selected_2 = df_tabla[
        (df_tabla['Puesto'] == selected_puesto_2) &
        (df_tabla['Seniority'] == selected_seniority_2) &
        (df_tabla['Locacion'] == selected_locacion_2)
    ]

    # Mostrar valores de la segunda selección
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

    # Calcular y mostrar el porcentaje de diferencia
    if valores_1 is not None and valores_2 is not None:
        st.markdown("### Comparativa de Sueldos")
        # Calcular promedio de Q1 a Q5 para ambas selecciones
        promedio_1 = valores_1[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].mean()
        promedio_2 = valores_2[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].mean()
        # Calcular porcentaje de diferencia
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

    # Opción para descargar la tabla salarial completa
    st.markdown("### Descargar Tabla Salarial Completa")
    col1, col2 = st.columns(2)
    
    with col1:
        # Descarga como CSV
        csv = df_tabla.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar tabla salarial completa como CSV",
            data=csv,
            file_name='tabla_salarial.csv',
            mime='text/csv',
        )

    with col2:
        # Descarga como Excel
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

# --- Página: Análisis de Legajos ---
elif page == "Análisis de Legajos":
    st.title("Análisis de Legajos")

    # Cargar el archivo de análisis de legajos
    @st.cache_data
    def load_analisis_legajos():
        return pd.read_excel("Análisis de legajos.xlsx", sheet_name=0)

    try:
        df_legajos = load_analisis_legajos()
    except FileNotFoundError:
        st.error("No se encontró el archivo Análisis de legajos.xlsx")
        st.stop()

    # Limpiar nombres de columnas
    df_legajos.columns = df_legajos.columns.str.strip().str.replace(' ', '_')

    # Convertir columnas categóricas a string y manejar valores inválidos
    categorical_columns = [col for col in df_legajos.columns if df_legajos[col].dtype == 'object']
    for col in categorical_columns:
        df_legajos[col] = df_legajos[col].astype(str).replace(['#Ref', 'nan'], '')

    # Convertir columnas de fecha
    date_columns = [col for col in df_legajos.columns if 'fecha' in col.lower() or 'date' in col.lower()]
    for col in date_columns:
        df_legajos[col] = pd.to_datetime(df_legajos[col], errors='coerce')

    # Filtros en la barra lateral
    st.sidebar.header("Filtros")
    filtros = {}
    for col in categorical_columns:
        if col in df_legajos.columns:
            filtros[col] = st.sidebar.multiselect(col.replace('_', ' ').title(), df_legajos[col].unique())
        else:
            filtros[col] = []

    # Aplicar filtros
    df_filtered = df_legajos.copy()
    for key, values in filtros.items():
        if values:
            df_filtered = df_filtered[df_filtered[key].isin(values)]

    # Resumen General
    st.subheader("Resumen General - Análisis de Legajos")
    if len(df_filtered) > 0:
        st.metric("Total Registros", len(df_filtered))
    else:
        st.info("No hay datos disponibles con los filtros actuales.")

    # Tabla de datos filtrados
    st.subheader("Tabla de Datos Filtrados")
    st.dataframe(df_filtered)

    # Exportar a CSV
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar datos filtrados como CSV",
        data=csv,
        file_name='analisis_legajos_filtrados.csv',
        mime='text/csv',
    )

    # Exportar a Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='Datos Filtrados')
    excel_data = output.getvalue()
    st.download_button(
        label="Descargar datos filtrados como Excel",
        data=excel_data,
        file_name='analisis_legajos_filtrados.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

# --- Página: Comparar Personas ---
elif page == "Comparar Personas":
    st.title("Comparar Personas")

    # Cargar el archivo de sueldos para comparar personas
    @st.cache_data
    def load_data():
        return pd.read_excel("SUELDOS PARA INFORMES.xlsx", sheet_name=0)

    try:
        df = load_data()
    except FileNotFoundError:
        st.error("No se encontró el archivo SUELDOS PARA INFORMES.xlsx")
        st.stop()

    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.replace(' ', '_')

    # Convertir columnas categóricas a string y manejar valores inválidos
    categorical_columns = [
        'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
        'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior',
        'Personaapellido', 'Personanombre'
    ]
    for col in categorical_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(['#Ref', 'nan'], '')

    # Filtros previos: Gerencia, Puesto_tabla_salarial, Grupo y Seniority
    st.subheader("Filtros Previos")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        gerencias = ['Todas'] + sorted(df['Gerencia'].unique())
        selected_gerencia = st.selectbox("Selecciona una Gerencia", gerencias)
    with col2:
        puestos = ['Todos'] + sorted(df['Puesto_tabla_salarial'].unique())
        selected_puesto = st.selectbox("Selecciona un Puesto Tabla Salarial", puestos)
    with col3:
        grupos = ['Todos'] + sorted(df['Grupo'].unique())
        selected_grupo = st.selectbox("Selecciona un Grupo", grupos)
    with col4:
        seniorities = ['Todos'] + sorted(df['seniority'].unique())
        selected_seniority = st.selectbox("Selecciona un Seniority", seniorities)

    # Filtrar el DataFrame según las selecciones
    df_filtered = df.copy()
    if selected_gerencia != 'Todas':
        df_filtered = df_filtered[df_filtered['Gerencia'] == selected_gerencia]
    if selected_puesto != 'Todos':
        df_filtered = df_filtered[df_filtered['Puesto_tabla_salarial'] == selected_puesto]
    if selected_grupo != 'Todos':
        df_filtered = df_filtered[df_filtered['Grupo'] == selected_grupo]
    if selected_seniority != 'Todos':
        df_filtered = df_filtered[df_filtered['seniority'] == selected_seniority]

    # Verificar si hay datos después de aplicar los filtros
    if len(df_filtered) == 0:
        st.warning("No hay datos disponibles con los filtros seleccionados. Por favor, ajusta los filtros.")
        st.stop()

    # Selección para comparar
    st.subheader("Selección para comparar")

    # Opción para elegir el tipo de comparación
    comparison_type = st.selectbox(
        "Tipo de comparación",
        ["Comparar dos personas", "Comparar todas las personas filtradas"]
    )

    if comparison_type == "Comparar dos personas":
        # Selección de personas para comparar (basado en el DataFrame filtrado)
        apellidos = sorted(df_filtered['Personaapellido'].unique())
        
        col1, col2 = st.columns(2)
        with col1:
            persona_1 = st.selectbox("Selecciona el primer apellido", apellidos, key="persona_1")
        with col2:
            persona_2 = st.selectbox("Selecciona el segundo apellido", apellidos, key="persona_2")

        # Filtrar datos para las personas seleccionadas (usando el DataFrame original para mantener todas las columnas)
        df_persona_1 = df[df['Personaapellido'] == persona_1]
        df_persona_2 = df[df['Personaapellido'] == persona_2]

        # Mostrar comparación si ambas personas tienen datos
        if not df_persona_1.empty and not df_persona_2.empty:
            st.markdown("### Comparativa de Personas")

            # Obtener datos relevantes
            metrics = ['Personaapellido', 'Personanombre', 'Total_sueldo_bruto', 'seniority', 'Puesto', 'Gerencia']
            comparison_data = []

            for df_persona, label in [(df_persona_1, "Persona 1"), (df_persona_2, "Persona 2")]:
                row = df_persona.iloc[0]  # Tomar la primera fila (asumiendo un solo registro por apellido)
                data = {metric: row[metric] if metric in df_persona.columns else "N/A" for metric in metrics}
                data['Label'] = label
                comparison_data.append(data)

            # Crear DataFrame para comparación
            comparison_df = pd.DataFrame(comparison_data)

            # Mostrar tabla de comparación
            st.dataframe(comparison_df.set_index('Label')[metrics])

            # Comparar sueldos
            if 'Total_sueldo_bruto' in df_persona_1.columns and 'Total_sueldo_bruto' in df_persona_2.columns:
                sueldo_1 = float(df_persona_1['Total_sueldo_bruto'].iloc[0])
                sueldo_2 = float(df_persona_2['Total_sueldo_bruto'].iloc[0])
                if sueldo_1 != 0:
                    diferencia_porcentual = ((sueldo_2 - sueldo_1) / sueldo_1) * 100
                    st.markdown(f"**Diferencia porcentual en sueldo bruto:** {diferencia_porcentual:.2f}%")
                    if diferencia_porcentual > 0:
                        st.write(f"El sueldo de {persona_2} es {diferencia_porcentual:.2f}% mayor que el de {persona_1}.")
                    elif diferencia_porcentual < 0:
                        st.write(f"El sueldo de {persona_2} es {abs(diferencia_porcentual):.2f}% menor que el de {persona_1}.")
                    else:
                        st.write("Ambas personas tienen el mismo sueldo bruto.")
                else:
                    st.warning("No se puede calcular la diferencia porcentual porque el sueldo de la primera persona es 0.")
        else:
            st.warning("Una o ambas personas seleccionadas no tienen datos disponibles.")

    else:  # Comparar todas las personas filtradas
        st.markdown("### Comparativa de Todas las Personas Filtradas")

        # Asegurarse de que hay datos para comparar
        if len(df_filtered) > 0 and 'Total_sueldo_bruto' in df_filtered.columns:
            # Preparar los datos para el gráfico
            # Combinar apellido y nombre para etiquetas más claras
            df_filtered['Nombre_Completo'] = df_filtered['Personaapellido'] + ', ' + df_filtered['Personanombre']
            
            # Ordenar de mayor a menor según sueldo bruto
            df_filtered = df_filtered.sort_values(by='Total_sueldo_bruto', ascending=False)

            # Crear gráfico de barras con Altair
            chart = alt.Chart(df_filtered).mark_bar().encode(
                x=alt.X('Nombre_Completo:N', title='Persona', sort='-y', axis=alt.Axis(labelAngle=45)),
                y=alt.Y('Total_sueldo_bruto:Q', title='Sueldo Bruto ($)'),
                tooltip=[
                    'Nombre_Completo',
                    alt.Tooltip('Total_sueldo_bruto:Q', title='Sueldo Bruto', format='$,.0f'),
                    'Puesto',
                    'Gerencia',
                    'seniority'
                ]
            ).properties(
                height=400,
                title='Sueldos Brutos de las Personas Filtradas (de Mayor a Menor)'
            )

            # Mostrar el gráfico
            st.altair_chart(chart, use_container_width=True)

            # Mostrar la tabla completa con los datos filtrados
            st.subheader("Datos Detallados")
            display_columns = ['Nombre_Completo', 'Total_sueldo_bruto', 'seniority', 'Puesto', 'Gerencia']
            st.dataframe(df_filtered[display_columns])
        else:
            st.warning("No hay datos disponibles para comparar con los filtros seleccionados.")
